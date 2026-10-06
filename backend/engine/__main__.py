"""CLI entrypoint for running the PhotoSorter engine: python -m backend.engine"""

from __future__ import annotations
import argparse
import sys
import time
from pathlib import Path

from backend.engine.pipeline import EngineConfig, run_pipeline


def main():
    parser = argparse.ArgumentParser(
        description="PhotoSorter Engine: Group event photos by person using face clustering."
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to local folder or zip archive containing photos.",
    )
    parser.add_argument(
        "--out", "-o",
        default="export",
        help="Output directory for the static export bundle (default: export).",
    )
    parser.add_argument(
        "--cache-dir",
        default=None,
        help="Custom cache directory for embeddings (default: <out>/.cache).",
    )
    parser.add_argument(
        "--threshold", "-t",
        type=float,
        default=0.5,
        help="Clustering cosine distance threshold (default: 0.5).",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.5,
        help="Minimum face detection confidence score (default: 0.5).",
    )
    parser.add_argument(
        "--min-size",
        type=int,
        default=64,
        help="Minimum face dimension in original pixels (default: 64).",
    )
    parser.add_argument(
        "--max-yaw",
        type=float,
        default=70.0,
        help="Maximum head yaw angle in degrees before moving to Unrecognized (default: 70.0).",
    )
    parser.add_argument(
        "--title",
        default="Event Gallery",
        help="Event title for config.json (default: 'Event Gallery').",
    )

    args = parser.parse_args()

    def print_progress(status: dict):
        stage = status.get("stage")
        msg = status.get("message", "")
        if stage == "processing":
            cur = status.get("current", 0)
            tot = status.get("total", 0)
            eta = status.get("eta_seconds", 0)
            print(f"\r[Detecting {cur}/{tot}] ETA {eta:.1f}s | {msg[:55]:<55}", end="", flush=True)
        else:
            print(f"\n[{stage.upper()}] {msg}", flush=True)

    config = EngineConfig(
        input_path=args.input,
        output_dir=args.out,
        cache_dir=args.cache_dir,
        distance_threshold=args.threshold,
        min_det_score=args.min_score,
        min_face_size=args.min_size,
        max_yaw=args.max_yaw,
        event_title=args.title,
        progress_callback=print_progress,
    )

    start_t = time.time()
    try:
        result = run_pipeline(config)
        elapsed = time.time() - start_t
        print("\n" + "=" * 60)
        print(f"SUCCESS! Finished in {elapsed:.1f}s")
        print(f"Total Photos Processed: {len(result.photos)}")
        print(f"People Discovered:      {len(result.people)}")
        print(f"Unrecognized Photos:    {len(result.unrecognized.photo_ids)}")
        print(f"Unrecognized Faces:     {len(result.unrecognized.faces)}")
        print(f"Export Bundle Ready at: {Path(args.out).resolve()}")
        print("=" * 60)
    except Exception as e:
        print(f"\nERROR: Pipeline execution failed: {e}", file=sys.stderr)
        raise e


if __name__ == "__main__":
    main()
