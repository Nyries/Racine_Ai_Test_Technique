"""Download the fine-tuned CPT model from HuggingFace into /data/models/qwen3-cpt."""

import argparse
import sys
from pathlib import Path

from huggingface_hub import snapshot_download


MODEL_ID = "Nyries/qwen3-0.8b-middle-east-cpt"
DEFAULT_DIR = "/data/models/qwen3-cpt"


def main() -> None:
    parser = argparse.ArgumentParser(description="Download CPT model from HuggingFace")
    parser.add_argument(
        "--local-dir",
        default=DEFAULT_DIR,
        help=f"Destination directory (default: {DEFAULT_DIR})",
    )
    args = parser.parse_args()

    dest = Path(args.local_dir)
    dest.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {MODEL_ID} → {dest}")
    snapshot_download(
        repo_id=MODEL_ID,
        repo_type="model",
        local_dir=str(dest),
    )

    if not (dest / "config.json").exists():
        print("ERROR: config.json not found after download", file=sys.stderr)
        sys.exit(1)

    total_mb = sum(f.stat().st_size for f in dest.rglob("*") if f.is_file()) / 1_000_000
    print(f"Done — {total_mb:.0f} MB")


if __name__ == "__main__":
    main()
