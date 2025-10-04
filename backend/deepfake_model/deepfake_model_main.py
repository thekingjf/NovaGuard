# deepfake_model_main.py  (only the key parts shown; replace your file if easier)
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

    mcfg = cfg['model']
    model = DeepfakeModel(
        mcfg['arch'],
        num_classes=mcfg.get('num_classes', 2),
        ckpt_path=mcfg.get('ckpt_path', None),
        fake_index=mcfg.get('fake_index', 1),
    )
    model.set_temperature(cfg['calibration'].get('temperature', 1.0))

    # sample crops
    scfg = cfg['data']
    sampler = FaceSampler(
        fps=scfg['fps'],
        input_size=mcfg['input_size'],
        margin=scfg['face_margin'],
        min_face=scfg['min_face'],
        align_eyes=scfg['align_eyes'],
        device=device
    )
    crops, meta = sampler.sample(video_path, max_frames=scfg['max_frames'])

    # inference with config mean/std
    icfg = cfg['inference']
    logits = run_inference(
        model, crops,
        mean=mcfg['mean'], std=mcfg['std'],
        batch_size=icfg['batch_size'], half=icfg['half'], device=device
    )

    if len(logits) == 0:
        return {"video": os.path.basename(video_path), "path": video_path, "score": None, "ci": [None, None], "frames": 0}

    # aggregate respecting head_type + fake_index
    head_type = getattr(model, "head_type", "2c")
    p, logit = aggregate_logits(
        logits,
        head_type=head_type,
        fake_index=mcfg.get('fake_index', 1),
        temperature=float(model.temperature)
    )

    # CI on per-frame fake_log
    if head_type == "1c":
        fake_log = logits.view(-1)
    else:
        fi = int(mcfg.get('fake_index', 1)); other = 1 - fi
        fake_log = logits[:, fi] - logits[:, other]
    lo, hi = bootstrap_ci(fake_log, B=300)

    return {
        "video": os.path.basename(video_path),
        "path": video_path,
        "score": float(p),
        "ci": [float(lo), float(hi)],
        "frames": int(len(crops)),
        "temp": float(model.temperature),
        "logit_mean": float(logit),
        "face_frames_pct": float(100*sum(m['face'] for m in meta)/max(1,len(meta))),
    }

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
    ap.add_argument("--video")
    ap.add_argument("--dir")
    ap.add_argument("--manifest")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--out")
    args = ap.parse_args()

    cfg = load_cfg(args.config)
    out_path = args.out or os.path.join(cfg["io"]["save_dir"], "scores.jsonl")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    def write(fp, obj):
        fp.write(json.dumps(obj) + "\n"); fp.flush()

    with open(out_path, "w") as fp:
        if args.video:
            try:
                write(fp, score_video(args.video, cfg))
            except Exception as e:
                write(fp, {"video": os.path.basename(args.video), "path": args.video, "error": str(e), "score": None})
        elif args.dir:
            for p in iter_videos_from_dir(args.dir):
                try:
                    write(fp, score_video(p, cfg))
                except Exception as e:
                    write(fp, {"video": os.path.basename(p), "path": p, "error": str(e), "score": None})
        elif args.manifest:
            for p, lbl, split in iter_videos_from_manifest(args.manifest):
                try:
                    res = score_video(p, cfg)
                    res.update({"label": lbl, "split": split})
                except Exception as e:
                    res = {"video": os.path.basename(p), "path": p, "label": lbl, "split": split, "error": str(e), "score": None}
                write(fp, res)
        else:
            for p in iter_videos_from_dir(cfg["io"]["input_glob"].rsplit("/**",1)[0]):
                try:
                    write(fp, score_video(p, cfg))
                except Exception as e:
                    write(fp, {"video": os.path.basename(p), "path": p, "error": str(e), "score": None})
    print(f"Wrote results to {out_path}")

if __name__ == "__main__":
    main()
