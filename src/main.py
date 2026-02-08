"""
Main entry point for the transcription tool.

Usage:
    python main.py <audio_file> [--model MODEL_SIZE] [--no-clean] [--language LANG]
"""

import argparse
from pathlib import Path

from transcribe_tool import TranscribeTool
from file_handling import FileHandler
from translate import TranslateTool


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Transcribe voice messages with noise reduction and faster-whisper"
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
        default="tiny",
        help="Whisper model size to use (e.g., tiny, base, small, medium, "
             "large-v3, large-v3-turbo). Default: tiny"
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
    """List all available whisper models (locally downloaded)."""
    file_handler = FileHandler()
    models = file_handler.get_available_models()

    print("Known faster-whisper model sizes:")
    print("  tiny, base, small, medium, large-v3, large-v3-turbo")
    print()

    if models:
        print("Locally downloaded models:")
        for model in models:
            print(f"  - {model}")
    else:
        print("No models downloaded locally yet.")
        print("Run: python models/download_model.py <model_size>  (e.g., python models/download_model.py tiny)")


def transcribe_file(audio_path: Path, model_size: str, clean: bool, language: str, save: bool = True, print_result: bool = True):
    """
    Transcribe a single audio file.

    Args:
        audio_path: Path to the audio file.
        model_size: Whisper model size string (e.g., "tiny", "base", "small").
        clean: Whether to apply noise reduction.
        language: Language code for transcription.
        save: Whether to save to XML output.
    """
    if not audio_path.exists():
        print(f"Error: Audio file not found: {audio_path}")
        return

    print(f"Processing: {audio_path}")
    print(f"Model: {model_size}")
    print(f"Noise reduction: {'enabled' if clean else 'disabled'}")
    print(f"Language: {language}")
    print("-" * 40)

    with TranscribeTool(model_size=model_size) as tool:
        result = tool.process(
            audio_path=audio_path,
            clean=clean,
            language=language,
        )

        if save:
            file_handler = FileHandler()
            if not file_handler.OUTPUT_FILE_PATH.exists():
                file_handler.create_output_file()
            success = file_handler.add_entry(
                transcription=result["text"],
                model=model_size,
                language=language,
                translation=translate_text(result["text"], language)
            )
            if success:
                print("Transcription saved to output/output.xml")
            else:
                print("Warning: Failed to save transcription.")

        if print_result:
            print("\nTranscription:")
            print(result["text"])
            print("-" * 40)

        if result["cleaned_path"]:
            print(f"Cleaned audio saved to: {result['cleaned_path']}")
    

def transcribe_and_translate_file(audio_path: Path, model_size: str, clean: bool, language: str, save: bool = True, print_result: bool = True):
    """
    Transcribe and translate a single audio file.

    Args:
        audio_path: Path to the audio file.
        model_size: Whisper model size string (e.g., "tiny", "base", "small").
        clean: Whether to apply noise reduction.
        language: Language code for transcription.
        save: Whether to save to XML output.
        print_result: Whether to print the result.
    """
    if not audio_path.exists():
        print(f"Error: Audio file not found: {audio_path}")
        return

    print(f"Processing: {audio_path}")
    print(f"Model: {model_size}")
    print(f"Noise reduction: {'enabled' if clean else 'disabled'}")
    print(f"Language: {language}")
    print("-" * 40)

    with TranscribeTool(model_size=model_size) as tool:
        result = tool.process(
            audio_path=audio_path,
            clean=clean,
            language=language,
        )

        if save:
            file_handler = FileHandler()
            if not file_handler.OUTPUT_FILE_PATH.exists():
                file_handler.create_output_file()
            success = file_handler.add_entry(
                transcription=result["text"],
                model=model_size,
                language=language,
            )
            if success:
                print("Transcription saved to output/output.xml")
            else:
                print("Warning: Failed to save transcription.")

        if print_result:
            print("\nTranscription:")
            print(result["text"])
            print("-" * 40)

        if result["cleaned_path"]:
            print(f"Cleaned audio saved to: {result['cleaned_path']}")

        translate_tool = TranslateTool()
        health = translate_tool.check_health()
        if health["ollama_running"]:
            translation = translate_tool.translate(result["text"])
            if translation:
                print(f"Translation: {translation}")
            else:
                print("Warning: Failed to translate transcription.")
        else:
            print("Warning: Translation skipped -- Ollama is not reachable.")
            return

        if save:
            update_success = file_handler.update_entry(
                entry_id=file_handler.get_last_entry_id(),
                translation=translation,
                translation_model=translate_tool.model_name
            )
            if update_success:
                print("Translation saved to output/output.xml")
            else:
                print("Warning: Failed to save translation to output/output.xml")


def translate_text(text: str, target_language: str):
    """
    Translate the given text to the target language.
    """
    tool = TranslateTool()
    try:
        translation = tool.translate(text, target_language, source_language="auto")
        print(f"Translation: {translation}")
        return translation
    except ConnectionError:
        print("Warning: Translation skipped -- Ollama is not reachable.")
        return None

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


    # transcribe_file(
    #     audio_path=args.audio_file,
    #     model_size=args.model,
    #     clean=not args.no_clean,
    #     language=args.language,
    #     save=not args.no_save,
    #     print_result=False,
    # )
    transcribe_and_translate_file(
        audio_path=args.audio_file,
        model_size=args.model,
        clean=not args.no_clean,
        language=args.language,
        save=not args.no_save,
        print_result=False,
    )



if __name__ == "__main__":
    main()
