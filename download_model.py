#!/usr/bin/env python3
"""
Download faster-whisper models to the local models/ directory.

Usage:
    python download_model.py --list
    python download_model.py tiny
    python download_model.py base.en
    python download_model.py distil-large-v3 --force
"""

# TODO: what is this shit: Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.


import argparse
import shutil
import sys
from pathlib import Path

MODELS_DIR = Path("models")

# Keep one model source for cleaner and more predictable local folders.
SYSTRAN_MODEL_REPOS = {
    "tiny": "Systran/faster-whisper-tiny",
    "tiny.en": "Systran/faster-whisper-tiny.en",
    "base": "Systran/faster-whisper-base",
    "base.en": "Systran/faster-whisper-base.en",
    "small": "Systran/faster-whisper-small",
    "small.en": "Systran/faster-whisper-small.en",
    "medium": "Systran/faster-whisper-medium",
    "medium.en": "Systran/faster-whisper-medium.en",
    "large-v1": "Systran/faster-whisper-large-v1",
    "large-v2": "Systran/faster-whisper-large-v2",
    "large-v3": "Systran/faster-whisper-large-v3",
    "distil-large-v2": "Systran/faster-distil-whisper-large-v2",
    "distil-large-v3": "Systran/faster-distil-whisper-large-v3",
}

ALLOWED_FILE_PATTERNS = [
    "model.bin",
    "config.json",
    "preprocessor_config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "normalizer.json",
    "generation_config.json",
    "vocabulary.*",
]


def get_downloaded_models() -> list[str]:
    """Return clean local model folders that contain model.bin."""
    if not MODELS_DIR.exists():
        return []

    return sorted(
        d.name
        for d in MODELS_DIR.iterdir()
        if d.is_dir() and (d / "model.bin").exists()
    )


def list_models() -> None:
    """Print supported model sizes and locally downloaded models."""
    print("Available Systran faster-whisper model sizes:")
    print()
    for model in sorted(SYSTRAN_MODEL_REPOS):
        print(f"  {model}")

    print()
    print("Notes:")
    print("  .en variants are English-only (slightly better for English).")
    print("  Distil variants are smaller/faster but can be less accurate.")
    print("  large-v3-turbo is not available in the Systran-only source policy.")

    local_models = get_downloaded_models()
    if local_models:
        print()
        print("Locally downloaded models:")
        for name in local_models:
            print(f"  - {name}")


def download_model(model_size: str, force: bool = False) -> None:
    """Download one Systran faster-whisper model into models/<model_size>/."""
    if model_size == "large-v3-turbo":
        print("Error: 'large-v3-turbo' is not available in the Systran-only source policy.")
        print("Run with --list to see supported models.")
        sys.exit(1)

    repo_id = SYSTRAN_MODEL_REPOS.get(model_size)
    if repo_id is None:
        print(f"Error: Unsupported model '{model_size}'.")
        print("Run with --list to see supported models.")
        sys.exit(1)

    model_dir = MODELS_DIR / model_size
    model_bin_path = model_dir / "model.bin"

    if model_bin_path.exists() and not force:
        print(f"Model '{model_size}' already exists at {model_dir}.")
        print("Use --force to re-download it.")
        return

    if force and model_dir.exists():
        shutil.rmtree(model_dir)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading model '{model_size}' from '{repo_id}'")
    print(f"Target folder: {model_dir}")
    print("This may take a while depending on model size and connection speed.")
    print()

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("Error: huggingface_hub is not installed.")
        print("Install it with: pip install huggingface_hub")
        sys.exit(1)

    try:
        snapshot_download(
            repo_id=repo_id,
            local_dir=str(model_dir),
            local_dir_use_symlinks=False,
            allow_patterns=ALLOWED_FILE_PATTERNS,
        )
    except Exception as exc:
        print(f"Error downloading model: {exc}")
        if model_dir.exists() and not any(model_dir.iterdir()):
            model_dir.rmdir()
        sys.exit(1)

    if not model_bin_path.exists():
        print("Error: Download finished but model.bin was not found.")
        print(f"Please inspect: {model_dir}")
        sys.exit(1)

    # snapshot_download stores metadata under <local_dir>/.cache; keep model folders clean.
    hf_metadata_dir = model_dir / ".cache"
    if hf_metadata_dir.exists():
        shutil.rmtree(hf_metadata_dir, ignore_errors=True)

    print()
    print(f"Model '{model_size}' downloaded successfully to {model_dir}")
    print(f"You can now transcribe with: python src/main.py <audio_file> --model {model_size}")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Download Systran faster-whisper models for local transcription."
    )
    parser.add_argument(
        "model_size",
        nargs="?",
        default=None,
        help="Model size to download (for example: tiny, base, large-v3).",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all supported model sizes and local downloads.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if the model already exists locally.",
    )

    args = parser.parse_args()

    if args.list:
        list_models()
        return

    if args.model_size is None:
        parser.print_help()
        sys.exit(0)

    download_model(args.model_size, force=args.force)


if __name__ == "__main__":
    main()
