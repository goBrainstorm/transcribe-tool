"""
Main entry point for the transcription tool.

Usage:
    python main.py <audio_file> [--model MODEL_NAME] [--no-clean] [--language LANG]
"""

import argparse
from pathlib import Path

from transcribe_tool import TranscribeTool
from file_handling import FileHandler


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Transcribe voice messages with noise reduction and whisper.cpp"
    )
    parser.add_argument(
        "audio_file",
        type=Path,
        nargs="?",
        help="Path to the audio file to transcribe"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="ggml-tiny.bin",
        help="Whisper model to use (default: ggml-tiny.bin)"
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Skip audio noise reduction"
    )
    parser.add_argument(
        "--language",
        type=str,
        default="de",
        help="Language code for transcription (default: de)"
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save transcription to XML output"
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available whisper models"
    )
    return parser.parse_args()


def list_available_models():
    """List all available whisper models."""
    file_handler = FileHandler()
    models = file_handler.get_available_models()

    if models:
        print("Available whisper models:")
        for model in models:
            print(f"  - {model}")
    else:
        print("No whisper models found in models/whisper.cpp/")
        print("Download models from: https://huggingface.co/ggerganov/whisper.cpp/tree/main")


def transcribe_file(audio_path: Path, model_name: str, clean: bool, language: str, save: bool):
    """
    Transcribe a single audio file.

    Args:
        audio_path: Path to the audio file.
        model_name: Name of the whisper model to use.
        clean: Whether to apply noise reduction.
        language: Language code for transcription.
        save: Whether to save to XML output.
    """
    if not audio_path.exists():
        print(f"Error: Audio file not found: {audio_path}")
        return

    print(f"Processing: {audio_path}")
    print(f"Model: {model_name}")
    print(f"Noise reduction: {'enabled' if clean else 'disabled'}")
    print(f"Language: {language}")
    print("-" * 40)

    with TranscribeTool(model_name=model_name) as tool:
        result = tool.process(
            audio_path=audio_path,
            clean=clean,
            language=language,
            save_to_xml=save
        )

        print("\nTranscription:")
        print(result["text"])
        print("-" * 40)

        if result["cleaned_path"]:
            print(f"Cleaned audio saved to: {result['cleaned_path']}")

        if result["saved"]:
            print("Transcription saved to output/output.xml")


def main():
    """Main entry point."""
    args = parse_args()

    if args.list_models:
        list_available_models()
        return

    if args.audio_file is None:
        print("Error: Please provide an audio file to transcribe.")
        print("Usage: python main.py <audio_file> [options]")
        print("Use --help for more information.")
        return

    transcribe_file(
        audio_path=args.audio_file,
        model_name=args.model,
        clean=not args.no_clean,
        language=args.language,
        save=not args.no_save
    )


if __name__ == "__main__":
    main()
