#!/usr/bin/env python3
"""
Download faster-whisper models to the local models/ directory.

Usage:
    python download_model.py [model_size]
    python download_model.py --list
    python download_model.py tiny
    python download_model.py large-v3-turbo

Models are downloaded from Hugging Face and cached in the models/ directory
so they are available for offline use with the transcription tool.
"""

import argparse
import os
import sys
from pathlib import Path

MODELS_DIR = Path("models")

# Set Hugging Face cache to use our models directory
# This ensures models are downloaded directly to our local folder
os.environ["HF_HOME"] = str(MODELS_DIR.absolute())
os.environ["HF_HUB_CACHE"] = str(MODELS_DIR.absolute() / "hub")

AVAILABLE_MODELS = [
    "tiny", "tiny.en",
    "base", "base.en",
    "small", "small.en",
    "medium", "medium.en",
    "large-v1",
    "large-v2",
    "large-v3",
    "large-v3-turbo",
    "distil-large-v2",
    "distil-large-v3",
]


def list_models():
    """Print all available model sizes and any locally downloaded models."""
    print("Available faster-whisper model sizes:")
    print()
    for model in AVAILABLE_MODELS:
        print(f"  {model}")

    print()
    print("Notes:")
    print("  .en variants are English-only (slightly better for English).")
    print("  Larger models are more accurate but slower and use more memory.")
    print("  'large-v3-turbo' offers a good balance of speed and accuracy.")

    # Check for locally downloaded models
    if MODELS_DIR.exists():
        local = [
            d.name for d in MODELS_DIR.iterdir()
            if d.is_dir() and (d / "model.bin").exists()
        ]
        if local:
            print()
            print("Locally downloaded models:")
            for name in sorted(local):
                print(f"  - {name}")


def download_model(model_size: str):
    """Download a faster-whisper model to the local models/ directory."""
    print(f"Downloading model '{model_size}' to {MODELS_DIR}/")
    print("This may take a while depending on the model size and connection speed.")
    print()

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        from faster_whisper import WhisperModel

        # Instantiating the model triggers the download if not cached locally
        _ = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8",
            download_root=str(MODELS_DIR),
        )

        print()
        print(f"Model '{model_size}' downloaded successfully to {MODELS_DIR}/")
        print(f"You can now transcribe with: python src/main.py <audio_file> --model {model_size}")

    except ValueError as e:
        print(f"Error: Invalid model size '{model_size}'.")
        print(f"Details: {e}")
        print("Run with --list to see available models.")
        sys.exit(1)
    except Exception as e:
        print(f"Error downloading model: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Download faster-whisper models for local transcription."
    )
    parser.add_argument(
        "model_size",
        nargs="?",
        default=None,
        help="Model size to download (e.g., tiny, base, small, medium, "
             "large-v3, large-v3-turbo). Default: tiny"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available model sizes"
    )

    args = parser.parse_args()

    if args.list:
        list_models()
        return

    if args.model_size is None:
        model_size = "tiny"
        print(f"No model size specified, defaulting to '{model_size}'.")
        print()
    else:
        model_size = args.model_size

    download_model(model_size)


if __name__ == "__main__":
    main()
