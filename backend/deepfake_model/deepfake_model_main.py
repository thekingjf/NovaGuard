import argparse, glob, json, os, torch, csv
from deepfake_env import set_seed
from deepfake_timm import DeepfakeModel
from deepfake_sampling import FaceSampler
from deepfake_inference import run_inference, aggregate_logits
from deepfake_bootstrap import bootstrap_ci

def load_cfg(path):
    import yaml
    with open(path) as f: return yaml.safe_load(f)

def score_video(video_path, cfg):
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    set_seed(1337)
    # 1) model
    model = DeepfakeModel(cfg['model']['arch'], cfg['model']['num_classes'], cfg['model']['ckpt_path'])
    model.set_temperature(cfg['calibration'].get('temperature', 1.0))
    # 2) sampling
    sampler = FaceSampler(fps=cfg['data']['fps'], input_size=cfg['model']['input_size'],
                          margin=cfg['data']['face_margin'], min_face=cfg['data']['min_face'],
                          align_eyes=cfg['data']['align_eyes'], device=device)
    crops, meta = sampler.sample(video_path, max_frames=cfg['data']['max_frames'])
    # 3) inference
    logits = run_inference(model, crops, batch_size=cfg['inference']['batch_size'],
                           half=cfg['inference']['half'], device=device)
    # 4) aggregate
    if len(logits)==0:
        return {'video': os.path.basename(video_path), 'score': float('nan'), 'ci': [float('nan'), float('nan')], 'frames': 0}
    fake_logits = logits[:,1] - logits[:,0]
    score, logit = aggregate_logits(logits)
    lo, hi = bootstrap_ci(fake_logits, B=300)
    return {'video': os.path.basename(video_path), 'score': score, 'ci': [lo, hi], 'frames': int(len(crops)),
            'temp': float(model.temperature), 'logit_mean': float(logit),
            'face_frames_pct': float(100*sum(m['face'] for m in meta)/max(1,len(meta)))}

def iter_videos_from_dir(d, patterns=("*.mp4","*.mov","*.avi")):
    for pat in patterns:
        for p in glob.glob(os.path.join(d, "**", pat), recursive=True):
            yield p

def iter_videos_from_manifest(mpath):
    with open(mpath) as f:
        r = csv.DictReader(f)
        for row in r:
            yield row["path"], int(row.get("label", -1)), row.get("split", "")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", help="single video path")
    ap.add_argument("--dir", help="directory of videos (recurses)")
    ap.add_argument("--manifest", help="CSV with columns path,label,split")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--out", help="JSONL path for results")
    args = ap.parse_args()

    cfg = load_cfg(args.config)
    save_dir = args.out or os.path.join(cfg["io"]["save_dir"], "scores.jsonl")
    os.makedirs(os.path.dirname(save_dir), exist_ok=True)

    def write(json_obj, fp):
        fp.write(json.dumps(json_obj) + "\n")
        fp.flush()

    with open(save_dir, "w") as fp:
        if args.video:
            res = score_video(args.video, cfg)
            write(res, fp)
        elif args.dir:
            for p in iter_videos_from_dir(args.dir):
                res = score_video(p, cfg)
                write(res, fp)
        elif args.manifest:
            for p, lbl, split in iter_videos_from_manifest(args.manifest):
                res = score_video(p, cfg)
                res.update({"label": lbl, "split": split})
                write(res, fp)
        else:
            # fallbacks to config defaults if nothing passed
            for p in iter_videos_from_dir(cfg["io"]["input_glob"].rsplit("/**",1)[0]):
                try:
                    res = score_video(p, cfg)
                except Exception as e:
                    res = {"video": os.path.basename(p), "path": p, "error": str(e), "score": None}
                write(res, fp)
                write(res, fp)
    print(f"Wrote results to {save_dir}")

if __name__ == "__main__":
    main()
