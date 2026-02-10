"""
Main entry point for the transcription tool.

Usage:
    python main.py <audio_file> [--model MODEL_SIZE] [--no-clean] [--language LANG]
"""

import argparse
from pathlib import Path
from typing import Optional

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


def transcribe_file(
    audio_path: Path,
    model_size: str,
    clean: bool,
    language: str,
    save: bool = True,
    print_result: bool = True,
    translator: Optional[TranslateTool] = None
):
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
            transcription_id = file_handler._generate_transcription_id(result["text"])
            if file_handler.entry_exists_by_filename(audio_path.name) or file_handler.entry_exists_by_id(transcription_id):
                print("Skipping save: entry already exists in output.")
            else:
                effective_translator = translator or TranslateTool()
                success = file_handler.add_entry(
                    transcription=result["text"],
                    model=model_size,
                    language=language,
                    translation=translate_text(result["text"], effective_translator, language),
                    filename=audio_path.name
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
    
def transcribe_all_files(model_size: str = "tiny", clean: bool = True, language: str = "de", save: bool = True, print_result: bool = False, skip_existing: bool = True):
    """
    Transcribe all audio files from the input directory.
    
    Args:
        model_size: Whisper model size string (e.g., "tiny", "base", "small").
        clean: Whether to apply noise reduction.
        language: Language code for transcription.
        save: Whether to save to XML output.
        print_result: Whether to print individual results.
        skip_existing: Whether to skip files that have already been transcribed.
    """
    file_handler = FileHandler()
    results = file_handler.transcribe_all_input_files(
        model_size=model_size,
        clean=clean,
        language=language,
        save=save,
        skip_existing=skip_existing
    )
    
    if print_result:
        for result in results:
            if result["success"]:
                print(f"\n{result['file'].name}:")
                print("-" * 40)
    
    return results


def translate_text(text: str, translator: TranslateTool, target_language: str = "en"):
    """
    Translate the given text to the target language.
    """
    try:
        translation = translator.translate(text, target_language=target_language)
        return translation
    except ConnectionError:
        print("Warning: Translation skipped -- Ollama is not reachable.")
        return None

def translate_entries_without_translation(ids: list[str], translator: TranslateTool):
    """
    Translate all entries without a translation.
    """
    if len(ids) == 0:
        return
    print(f"Translating {len(ids)} entries without translation: {ids}")
    file_handler = FileHandler()
    for entry_id in ids:
        content = file_handler.get_transcription_content(entry_id)
        translation = translate_text(
            content,
            translator
        )
        file_handler.update_entry(entry_id, translation=translation)

def main():
    """Main entry point."""
    args = parse_args()

    if args.list_models:
        list_available_models()
        return

    # if args.audio_file is None:
    #     print("Error: Please provide an audio file to transcribe.")
    #     print("Usage: python main.py <audio_file> [options]")
    #     print("Use --help for more information.")
    #     return

    # transcribe_and_translate_file(
    #     audio_path=args.audio_file,
    #     model_size=args.model,
    #     clean=not args.no_clean,
    #     language=args.language,
    #     save=not args.no_save,
    #     print_result=False,
    # )

    transcribe_all_files(model_size=args.model)

    translator = TranslateTool()
    missing_translation_ids = FileHandler().get_all_entries_without_translation()
    print(missing_translation_ids)
    translate_entries_without_translation(missing_translation_ids, translator)



if __name__ == "__main__":
    main()
