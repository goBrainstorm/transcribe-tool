import argparse
from pathlib import Path

from transcribe_tool import TranscribeTool
from file_handling import FileHandler
from translate import TranslateTool
from datetime import datetime


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
    parser.add_argument(
        "--translate",
        action="store_true",
        help="Translate the transcription"
    )
    parser.add_argument(
        "--target-lang",
        type=str,
        default="en",
        help="Target language for translation (default: en)"
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


def translate_text(text: str, target_language: str):
    """
    Translate the given text to the target language.
    """
    tool = TranslateTool()
    translation = tool.translate(text, target_language, source_language="auto")
    return translation


def transcribe_file(audio_path: Path, model_size: str, clean: bool, language: str, save: bool, translate: bool = False, target_lang: str = "en"):
    """
    Transcribe a single audio file.

    Args:
        audio_path: Path to the audio file.
        model_size: Whisper model size string (e.g., "tiny", "base", "small").
        clean: Whether to apply noise reduction.
        language: Language code for transcription.
        save: Whether to save to XML output.
        translate: Whether to translate the transcription.
        target_lang: Target language code for translation.
    """
    if not audio_path.exists():
        print(f"Error: Audio file not found: {audio_path}")
        return

    print(f"Processing: {audio_path}")
    print(f"Model: {model_size}")
    print(f"Noise reduction: {'enabled' if clean else 'disabled'}")
    print(f"Language: {language}")
    if translate:
        print(f"Translation: enabled (target: {target_lang})")
    print("-" * 40)

    with TranscribeTool(model_size=model_size) as tool:
        # We disable auto-save in tool.process if we want to add translation before saving
        # OR we save first and then update.
        # But `process` doesn't support translation argument directly.
        # So we do: process(save=False) -> translate -> manual save.
        
        result = tool.process(
            audio_path=audio_path,
            clean=clean,
            language=language,
            save_to_xml=False
        )

        print("\nTranscription:")
        print(result["text"])
        
        translation_text = None
        if translate and result["text"]:
            print(f"\nTranslating to {target_lang}...")
            try:
                translation_text = translate_text(result["text"], target_lang)
                print(f"Translation: {translation_text}")
            except Exception as e:
                print(f"Translation failed: {e}")

        print("-" * 40)

        if result.get("cleaned_path"):
            print(f"Cleaned audio saved to: {result['cleaned_path']}")

        if save:
            file_handler = FileHandler()
            if not file_handler.OUTPUT_FILE_PATH.exists():
                file_handler.create_output_file()
                
            entry_date = datetime.now().isoformat()
            
            success = file_handler.add_entry(
                transcription=result["text"],
                date=entry_date,
                summary="", 
                tags=[],
                language=result.get("language", language),
                confidence=result.get("language_probability"),
                translation=translation_text
            )
            
            if success:
                print("Transcription saved to output/output.xml")
            else:
                print("Error saving to output.xml")


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
        model_size=args.model,
        clean=not args.no_clean,
        language=args.language,
        save=not args.no_save,
        translate=args.translate,
        target_lang=args.target_lang
    )


if __name__ == "__main__":
    main()
