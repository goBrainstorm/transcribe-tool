from pathlib import Path
from typing import Optional

from app_logging import get_logger
from file_handling import FileHandler
from transcribe_tool import TranscribeTool
from LLM_handler import LLMHandler

logger = get_logger(__name__)


class Logic:
    """Static orchestration layer for transcription and translation workflows."""

    @staticmethod
    def log(message: str, debug: bool = False) -> None:
        """Print debug messages only when debug mode is enabled."""
        if debug:
            logger.debug(message)

    @staticmethod
    def translate_text(
        text: str,
        llm_handler: Optional[LLMHandler],
        target_language: str = "en",
        debug: bool = False,
    ) -> Optional[str]:
        """Translate text."""
        if llm_handler is None:
            return None

        if debug:
            Logic.log(f"Translating text to {target_language}...", debug)

        try:
            return llm_handler.translate(text, target_language=target_language)
        except ConnectionError:
            logger.warning("Translation skipped: Ollama is not reachable.")
            return None
        except ValueError as exc:
            logger.warning("Translation skipped: %s", exc)
            return None

    @staticmethod
    def summarize_text(
        text: str,
        llm_handler: Optional[LLMHandler],
        debug: bool = False,
    ) -> Optional[str]:
        """Summarize text."""
        if llm_handler is None:
            return None
        if debug:
            Logic.log(f"Summarizing text...", debug)
        try:
            return llm_handler.summarize(text)
        except Exception as exc:
            logger.warning("Summarization skipped: %s", exc)
            return None

    @staticmethod
    def transcribe_file(
        audio_path: Path,
        file_handler: FileHandler,
        transcribe_tool: TranscribeTool,
        clean: bool = True,
        language: str = "auto",
        save: bool = True,
        print_result: bool = False,
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
        transcription_text = result.get("text", "")
        has_transcription = bool(transcription_text and transcription_text.strip())
        error_message = None

        if not has_transcription:
            error_message = "Transcription result is empty."
            logger.warning("Empty transcription result. Skipping save.")

        if save:
            if not file_handler.OUTPUT_FILE_PATH.exists():
                file_handler.create_output_file()

            if has_transcription:
                transcription_id = file_handler._generate_transcription_id(transcription_text)
                already_exists = (
                    file_handler.entry_exists_by_filename(audio_path.name)
                    or file_handler.entry_exists_by_id(transcription_id)
                )

                if already_exists:
                    Logic.log("Skipping save: entry already exists in output.", debug)
                else:
                    try:
                        saved = file_handler.add_entry(
                            transcription=transcription_text,
                            model=transcribe_tool.transcriber.model_size,
                            language=result.get("language", language),
                            translation=None,
                            filename=audio_path.name,
                        )
                    except ValueError as exc:
                        saved = False
                        error_message = f"Failed to save transcription: {exc}"
                        logger.warning(error_message)

                    if saved:
                        Logic.log("Transcription saved to output/output.xml", debug)
                    else:
                        if error_message is None:
                            error_message = "Failed to save transcription."
                        logger.warning("Failed to save transcription.")

        if print_result:
            print("\nTranscription:")
            print(result["text"])
            print("-" * 40)

        if result.get("cleaned_path"):
            logger.info("Cleaned audio saved to: %s", result["cleaned_path"])

        return {
            "file": audio_path,
            "text": transcription_text,
            "segments": result.get("segments", []),
            "language": result.get("language", language),
            "success": has_transcription and error_message is None,
            "error": error_message,
        }

    @staticmethod
    def translate_entries(
        file_handler: FileHandler,
        llm_handler: Optional[LLMHandler],
        debug: bool = False,
    ) -> dict:
        """Translate entries missing translations to English and persist updates."""
        if llm_handler is None:
            return {"processed": 0, "translated": 0, "skipped": 0, "failed": 0}

        entry_ids = file_handler.get_all_entry_ids_without_translation()
        if not entry_ids:
            logger.info("No entries require translation.")
            return {"processed": 0, "translated": 0, "skipped": 0, "failed": 0}

        n = len(entry_ids)
        logger.info("Translating %s entr%s...", n, "y" if n == 1 else "ies")
        stats = {"processed": len(entry_ids), "translated": 0, "skipped": 0, "failed": 0}
        for i, entry_id in enumerate(entry_ids, 1):
            logger.info("  Entry %s/%s (id=%s)...", i, n, entry_id)
            transcription = file_handler.get_transcription_from_entry_id(entry_id)
            if not transcription:
                stats["skipped"] += 1
                continue

            translation = Logic.translate_text(
                text=transcription,
                llm_handler=llm_handler,
                target_language="en",
                debug=debug,
            )
            if not translation:
                stats["failed"] += 1
                continue

            updated = file_handler.update_entry(
                entry_id=entry_id,
                translation=translation,
            )
            if updated:
                stats["translated"] += 1
            else:
                stats["failed"] += 1

        logger.info(
            "Translation done: %s translated, %s failed.",
            stats["translated"],
            stats["failed"],
        )
        return stats

    @staticmethod
    def summarize_entries_with_translation(
        file_handler: FileHandler,
        llm_handler: Optional[LLMHandler],
        debug: bool = False,
    ) -> dict:
        """Summarize translations."""
        if llm_handler is None:
            logger.warning("Summary tool not found. Skipping summarization.")
            return {"processed": 0, "summarized": 0, "skipped": 0, "failed": 0}

        entry_ids = file_handler.get_all_entry_ids_with_translation(debug=debug)
        if not entry_ids:
            logger.info("No entries require summarization.")
            return {"processed": 0, "summarized": 0, "skipped": 0, "failed": 0}

        n = len(entry_ids)
        logger.info("Summarizing %s entr%s...", n, "y" if n == 1 else "ies")
        stats = {"processed": len(entry_ids), "summarized": 0, "skipped": 0, "failed": 0}
        for i, entry_id in enumerate(entry_ids, 1):
            logger.info("  Entry %s/%s (id=%s)...", i, n, entry_id)
            translation = file_handler.get_content_from_entry_id(entry_id, "translation")
            if not translation:
                stats["skipped"] += 1
                continue

            summary = Logic.summarize_text(
                text=translation,
                llm_handler=llm_handler,
                debug=debug,
            )

            if not summary:
                stats["failed"] += 1
                continue

            updated = file_handler.update_entry(
                entry_id=entry_id,
                summary=summary,
            )
            if updated:
                stats["summarized"] += 1
            else:
                stats["failed"] += 1

        logger.info(
            "Summarization done: %s summarized, %s failed.",
            stats["summarized"],
            stats["failed"],
        )
        return stats

    @staticmethod
    def transcribe_files_from_folder(
        file_handler: FileHandler,
        transcribe_tool: TranscribeTool,
        clean: bool = True,
        language: str = "auto",
        save: bool = True,
        print_result: bool = False,
        debug: bool = False,
        skip_existing: bool = True,
    ) -> list[dict]:
        """Transcribe all tracked input files from FileHandler state."""
        file_handler.refresh_input_audio_files()
        audio_files = file_handler.get_pending_audio_files(skip_existing=skip_existing)

        if not audio_files:
            if skip_existing:
                logger.info("No new audio files found in input directory.")
            else:
                logger.info("No audio files found in input directory.")
            return []

        logger.info("Found %s audio file(s) to process.", len(audio_files))

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
                    debug=debug,
                )
            except Exception as exc:
                logger.error("Error processing %s: %s", audio_file.name, exc)
                result = {
                    "file": audio_file,
                    "text": "",
                    "segments": [],
                    "language": language,
                    "success": False,
                    "error": str(exc),
                }

            results.append(result)

        logger.info("\n%s", "=" * 40)
        logger.info("Transcription Summary:")
        logger.info("Total files: %s", len(audio_files))
        logger.info("Successful: %s", sum(1 for r in results if r["success"]))
        logger.info("Failed: %s", sum(1 for r in results if not r["success"]))
        logger.info("%s", "=" * 40)

        return results

