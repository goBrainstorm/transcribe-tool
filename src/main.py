"""CLI entry point for argument parsing and Logic invocation."""

import argparse
from pathlib import Path
from typing import Optional

from app_logging import configure_logging, get_logger
from file_handling import FileHandler
from logic import Logic
from transcribe_tool import TranscribeTool
from LLM_handler import LLMHandler

logger = get_logger(__name__)

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Transcribe voice messages with noise reduction and faster-whisper"
    )
    parser.add_argument(
        "audio_file",
        type=Path,
        nargs="?",
        help="Path to one audio file. If omitted, all files in input/ are processed.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="tiny",
        help=(
            "Whisper model size to use (e.g., tiny, base, small, medium, "
            "large-v3, large-v3-turbo). Default: tiny"
        ),
    )
    parser.add_argument(
        "--language",
        type=str,
        default="auto",
        help="Source language hint for transcription (ISO code). Default: auto",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Skip audio noise reduction before transcription.",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save transcription to XML output.",
    )
    parser.add_argument(
        "--print-result",
        action="store_true",
        help="Print full transcription text to stdout.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging.",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available whisper models.",
    )
    parser.add_argument(
        "--translate",
        action="store_true",
        help="Translate the transcriptions.",
    )
    parser.add_argument(
        "--summarize",
        action="store_true",
        help="Summarize the translations.",
    )
    return parser.parse_args()


def list_available_models() -> None:
    """List all available whisper models (locally downloaded)."""
    models = FileHandler.get_available_models()

    print("Known local model sizes (Systran downloader):")
    print("  tiny, tiny.en, base, base.en, small, small.en, medium, medium.en")
    print("  large-v1, large-v2, large-v3, distil-large-v2, distil-large-v3")
    print()

    if models:
        print("Locally downloaded models:")
        for model in models:
            print(f"  - {model}")
    else:
        print("No models downloaded locally yet.")
        print("Run: python download_model.py tiny")


def _build_llm_handler() -> Optional[LLMHandler]:
    """Initialize translation dependencies once and return a shared tool."""
    try:
        return LLMHandler()
    except Exception as exc:
        logger.warning("LLM initialization failed: %s", exc)
        return None


def main() -> None:
    """Main entry point."""
    args = parse_args()
    configure_logging(args.debug)


    # TODO: Improve startup guidance for model download and setup.
    # TODO: Evaluate showing help when no actionable args are provided.
    if args.list_models:
        list_available_models()
        return

    file_handler = FileHandler()
    llm_handler: Optional[LLMHandler] = None
    needs_llm = args.translate or args.summarize

    with TranscribeTool(model_size=args.model) as transcribe_tool:
        if args.audio_file:
            Logic.transcribe_file(
                audio_path=args.audio_file,
                file_handler=file_handler,
                transcribe_tool=transcribe_tool,
                clean=not args.no_clean,
                language=args.language,
                save=not args.no_save,
                print_result=args.print_result,
                debug=args.debug,
            )
            if needs_llm:
                llm_handler = _build_llm_handler()
            if args.translate:
                Logic.translate_entries(
                    file_handler=file_handler,
                    llm_handler=llm_handler,
                    debug=args.debug,
                )
            if args.summarize:
                Logic.summarize_entries_with_translation(
                    file_handler=file_handler,
                    llm_handler=llm_handler,
                    debug=args.debug,
                )
            return

        # TODO: Validate mutually dependent CLI args.
        # TODO: Expand checks for partially processed files.
        Logic.transcribe_files_from_folder(
            file_handler=file_handler,
            transcribe_tool=transcribe_tool,
            clean=not args.no_clean,
            language=args.language,
            save=not args.no_save,
            print_result=args.print_result,
            debug=args.debug,
            skip_existing=True,
        )
        if needs_llm:
            llm_handler = _build_llm_handler()
        if args.translate:
            Logic.translate_entries(
                file_handler=file_handler,
                llm_handler=llm_handler,
                debug=args.debug,
            )
        if args.summarize:
            Logic.summarize_entries_with_translation(
                file_handler=file_handler,
                llm_handler=llm_handler,
                debug=args.debug,
            )



if __name__ == "__main__":
    main()
