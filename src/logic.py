from file_handling import FileHandler
from translate import TranslateTool
from transcribe_tool import TranscribeTool
from pathlib import Path
from typing import Optional

class Logic:
    
    @staticmethod
    def log(message: str, debug: bool = False):
        if debug:
            print(message + "\n")

    @staticmethod
    def transcribe_file(
        audio_path: Path,
        model_size: str,
        clean: bool,
        language: str,
        save: bool = True,
        print_result: bool = False,
        translator: Optional[TranslateTool] = None,
        debug: bool = False
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

        if debug:
            Logic.log(f"Processing: {audio_path}")
            Logic.log(f"Model: {model_size}")
            Logic.log(f"Noise reduction: {'enabled' if clean else 'disabled'}")
            Logic.log(f"Language: {language}")
            Logic.log(f"Processing: {audio_path}", debug)

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
                    Logic.log("Skipping save: entry already exists in output.")
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

    @staticmethod
    def translate_text(text: str, translator: TranslateTool, target_language: str = "en", debug: bool = False):
        """
        Translate the given text to the target language.
        """
        if debug:
            print(f"Translating: {text}")
            print(f"Target language: {target_language}")
            print("-" * 40)

        try:
            translation = translator.translate(text, target_language=target_language)
            return translation
        except ConnectionError:
            print("Warning: Translation skipped -- Ollama is not reachable.")
            return None

    @staticmethod
    def process_files_from_folder():

        pass
