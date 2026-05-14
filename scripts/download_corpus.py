"""Download the cleaned corpus from HuggingFace Datasets into /data/clean."""

import argparse
import sys
from pathlib import Path

from huggingface_hub import snapshot_download


REPO_ID = "Nyries/middle-east-geopolitics-corpus"
DEFAULT_DIR = "/data/clean"
IGNORE = ["*.md", ".gitattributes", "*.json"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Download corpus from HuggingFace")
    parser.add_argument(
        "--local-dir",
        default=DEFAULT_DIR,
        help=f"Destination directory (default: {DEFAULT_DIR})",
    )
    args = parser.parse_args()

    dest = Path(args.local_dir)
    dest.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {REPO_ID} → {dest}")
    snapshot_download(
        repo_id=REPO_ID,
        repo_type="dataset",
        local_dir=str(dest),
        ignore_patterns=IGNORE,
    )

    files = list(dest.glob("*.jsonl"))
    if not files:
        print("ERROR: no .jsonl files found after download", file=sys.stderr)
        sys.exit(1)

    total_mb = sum(f.stat().st_size for f in files) / 1_000_000
    print(f"Done — {len(files)} files, {total_mb:.1f} MB")


if __name__ == "__main__":
    main()
