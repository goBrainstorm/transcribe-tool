from pathlib import Path
from typing import Optional

from file_handling import FileHandler
from transcribe_tool import TranscribeTool
from translate import TranslateTool


class Logic:
    """Static orchestration layer for transcription and translation workflows."""

    @staticmethod
    def log(message: str, debug: bool = False) -> None:
        """Print debug messages only when debug mode is enabled."""
        if debug:
            print(message)

    @staticmethod
    def translate_text(
        text: str,
        translator: Optional[TranslateTool],
        target_language: str = "en",
        debug: bool = False,
    ) -> Optional[str]:
        """Translate text."""
        if translator is None:
            return None

        if debug:
            Logic.log(f"Translating text to {target_language}...", debug)

        try:
            return translator.translate(text, target_language=target_language)
        except ConnectionError:
            print("Warning: Translation skipped -- Ollama is not reachable.")
            return None
        except ValueError as exc:
            print(f"Warning: Translation skipped -- {exc}")
            return None

    @staticmethod
    def transcribe_file(
        audio_path: Path,
        file_handler: FileHandler,
        transcribe_tool: TranscribeTool,
        clean: bool = True,
        language: str = "en",
        save: bool = True,
        print_result: bool = False,
        translator: Optional[TranslateTool] = None,
        debug: bool = False,
    ) -> dict:
        """Transcribe one file and optionally persist it to XML output."""
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        Logic.log(f"Processing: {audio_path}", debug)
        Logic.log(f"Model: {transcribe_tool.transcriber.model_size}", debug)
        Logic.log(f"Noise reduction: {'enabled' if clean else 'disabled'}", debug)
        Logic.log(f"Language: {language}", debug)

        result = transcribe_tool.process(
            audio_path=audio_path,
            clean=clean,
            language=language,
        )

        if save:
            if not file_handler.OUTPUT_FILE_PATH.exists():
                file_handler.create_output_file()

            transcription_id = file_handler._generate_transcription_id(result["text"]) # TODO: what if text is empty?
            already_exists = (
                file_handler.entry_exists_by_filename(audio_path.name)
                or file_handler.entry_exists_by_id(transcription_id)
            )

            if already_exists:
                Logic.log("Skipping save: entry already exists in output.", debug)
            else:
                translation = Logic.translate_text(
                    text=result["text"], # TODO: what if text is empty?
                    translator=translator,
                    target_language=language,
                    debug=debug,
                )
                saved = file_handler.add_entry(
                    transcription=result["text"],
                    model=transcribe_tool.transcriber.model_size,
                    language=result.get("language", language),
                    translation=translation,
                    filename=audio_path.name,
                )
                if saved:
                    Logic.log("Transcription saved to output/output.xml", debug)
                else:
                    print("Warning: Failed to save transcription.")

        if print_result:
            print("\nTranscription:")
            print(result["text"])
            print("-" * 40)

        if result.get("cleaned_path"):
            print(f"Cleaned audio saved to: {result['cleaned_path']}")

        return {
            "file": audio_path,
            "text": result.get("text", ""),
            "segments": result.get("segments", []),
            "language": result.get("language", language),
            "success": True,
            "error": None,
        }

    @staticmethod
    def process_files_from_folder(
        file_handler: FileHandler,
        transcribe_tool: TranscribeTool,
        clean: bool = True,
        language: str = "de",
        save: bool = True,
        print_result: bool = False,
        translator: Optional[TranslateTool] = None,
        debug: bool = False,
        skip_existing: bool = True,
    ) -> list[dict]:
        """Transcribe all tracked input files from FileHandler state."""
        file_handler.refresh_input_audio_files()
        audio_files = file_handler.get_pending_audio_files(skip_existing=skip_existing)

        if not audio_files:
            if skip_existing:
                print("No new audio files found in input directory.")
            else:
                print("No audio files found in input directory.")
            return []

        print(f"Found {len(audio_files)} audio file(s) to process.")

        results = []
        for audio_file in audio_files:
            try:
                result = Logic.transcribe_file(
                    audio_path=audio_file,
                    file_handler=file_handler,
                    transcribe_tool=transcribe_tool,
                    clean=clean,
                    language=language,
                    save=save,
                    print_result=print_result,
                    translator=translator,
                    debug=debug,
                )
            except Exception as exc:
                print(f"Error processing {audio_file.name}: {exc}")
                result = {
                    "file": audio_file,
                    "text": "",
                    "segments": [],
                    "language": language,
                    "success": False,
                    "error": str(exc),
                }

            results.append(result)

        # TODO: add translation summary
        print("\n" + "=" * 40)
        print("Transcription Summary:")
        print(f"Total files: {len(audio_files)}")
        print(f"Successful: {sum(1 for r in results if r['success'])}")
        print(f"Failed: {sum(1 for r in results if not r['success'])}")
        print("=" * 40)

        return results

