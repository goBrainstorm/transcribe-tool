from pathlib import Path
import hashlib
from datetime import datetime
import xml.etree.ElementTree as ET


AUDIO_EXTENSIONS = {'.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac', '.opus', '.wma'}


class FileHandler:
    """Handles file operations for the transcription tool, including XML output management."""

    DEFAULT_MODEL_PATH = Path("models")
    DEFAULT_INPUT_FOLDER = Path("input")
    DEFAULT_OUTPUT_FOLDER = Path("output")
    OUTPUT_FILE_PATH = DEFAULT_OUTPUT_FOLDER / "output.xml"

    def __init__(self):
        """Initialize the FileHandler instance."""
        self.root = ET.Element("entries")
        self._input_audio_files: list[Path] = []

    @staticmethod
    def _generate_transcription_id(transcription: str) -> str:
        """Generate a stable entry ID from transcription text."""
        transcription = transcription or ""
        return f"ID-{hashlib.md5(transcription.encode()).hexdigest()[:8]}"

    
    # TODO: buggy. Does not work with faster-whisper models.
    @staticmethod
    def get_available_models() -> list:
        """
        Get list of available whisper models (locally downloaded).

        Returns:
            list: List of model names found in the models directory.
        """
        if not FileHandler.DEFAULT_MODEL_PATH.exists():
            print(f"Error: Models directory not found: {FileHandler.DEFAULT_MODEL_PATH}")
            return []

        models = []
        for d in FileHandler.DEFAULT_MODEL_PATH.iterdir():
            if d.is_dir() and (d / "model.bin").exists():
                models.append(d.name)
        return sorted(models)

    
    def create_output_file(self) -> bool:
        """
        Create an XML file at OUTPUT_FILE_PATH with the base transcriptions structure.

        Creates the output directory if it doesn't exist, then writes an empty
        XML transcriptions file with proper encoding declaration.

        Returns:
            bool: True if the file was created successfully, False otherwise.
        """
        try:
            # Create output directory if it doesn't exist
            self.DEFAULT_OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

            # Create XML content with base structure
            xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<entries>\n</entries>'

            # Write the XML file
            self.OUTPUT_FILE_PATH.write_text(xml_content, encoding='utf-8')

            return True
        except (IOError, OSError) as e:
            print(f"Error creating file: {e}")
            return False

    def get_entry(self, entry_id: str) -> ET.Element:
        """
        Get an entry by its ID.
        
        Args:
            entry_id: The ID of the entry to retrieve.
            
        Returns:
            ET.Element: The entry element if found, None otherwise.
        """
        if not self.OUTPUT_FILE_PATH.exists():
            return None
        
        try:
            tree = ET.parse(self.OUTPUT_FILE_PATH)
            root = tree.getroot()
            return root.find(f".//entry[@id='{entry_id}']")
        except ET.ParseError:
            return None

    def get_transcription_from_entry_id(self, entry_id: str) -> str:
        """
        Get the transcription content from an entry by its ID.
        
        Args:
            entry_id: The ID of the entry to retrieve transcription from.
            
        Returns:
            str: The transcription text content if found, None otherwise.
        """
        entry = self.get_entry(entry_id)
        if entry is None:
            return None
        
        transcription_elem = entry.find("transcription")
        if transcription_elem is None or transcription_elem.text is None:
            return None
        
        return transcription_elem.text.strip()

    def add_entry(
        self,
        transcription: str = "",
        model: str = "",
        date: str = None,
        language: str = None,
        translation: str = None,
        filename: str = ""
    ) -> bool:
        """
        Add an entry to the output XML file with the structured format.

        Args:
            transcription: The transcription text content.
            date: Optional date string in ISO format (e.g., "2026-01-20T14:30:00").
            summary: Optional summary of the transcription.
            tags: Optional list of tags.
            language: Language code, defaults to "en".
            confidence: Optional confidence score for the transcription.
            translation: Optional translation of the text.
            filename: Optional original audio filename for tracking.

        Returns:
            bool: True if entry was added successfully, False otherwise.

        Raises:
            ValueError: If date is invalid and transcription is empty.
        """
        def valid_date(date_str: str) -> bool: # TODO not working ... make it work
            """Check if date string is a valid ISO format datetime."""
            if date_str is None:
                return False
            try:
                datetime.fromisoformat(date_str)
                return True
            except (ValueError, TypeError):
                return False

        # Check if output file exists
        if not self.OUTPUT_FILE_PATH.exists():
            return False

        # Determine ID and has_date_as_id
        if valid_date(date):
            entry_id = date
            has_date_as_id = "1"
        else:
            # Date is invalid, need to create hash from transcription
            if not transcription or transcription.strip() == "":
                raise ValueError("Cannot generate entry ID: date is invalid and transcription is empty.")
            entry_id = self._generate_transcription_id(transcription)
            has_date_as_id = "0"
    
        # Parse existing XML
        try:
            tree = ET.parse(self.OUTPUT_FILE_PATH)
            root = tree.getroot()
        except ET.ParseError:
            # File might be malformed or empty, try to create root element
            root = ET.Element("entries")
            tree = ET.ElementTree(root)

        # Create new entry element
        entry = ET.SubElement(root, "entry", id=entry_id, has_date_as_id=has_date_as_id)
        
        # Add filename attribute if provided
        if filename:
            entry.set("filename", filename)

        # 1. Transcription element (with attributes)
        transcription_elem = ET.SubElement(entry, "transcription")
        if language:
            transcription_elem.set("language", language)
        if model:
            transcription_elem.set("model", model)
        transcription_elem.text = f"\n{transcription.strip()}\n" if transcription else ""

        # 2. Translation element
        translation_elem = ET.SubElement(entry, "translation")
        translation_elem.text = f"\n{translation.strip()}\n" if translation else ""

        # 3. Extracted Information
        extracted_info = ET.SubElement(entry, "extracted_information")

        # Tags
        tags_elem = ET.SubElement(extracted_info, "tags")
        
        # set information 
        ET.SubElement(tags_elem, "tag")
        ET.SubElement(extracted_info, "summary")

        # Write back to file with proper formatting
        try:
            ET.indent(tree)
            tree.write(self.OUTPUT_FILE_PATH, encoding="unicode", xml_declaration=True)
            return True
        except (IOError, OSError) as e:
            print(f"Error writing entry: {e}")
            return False

    def update_entry(
        self,
        entry_id: str,
        transcription: str = None,
        transcription_model: str = None,
        translation: str = None,
        translation_model: str = None,
        summary: str = None,
        tags: list = None,
        language: str = None
    ) -> bool:
        """
        Update an existing entry by its ID. Only provided fields are updated.

        Args:
            entry_id: The ID of the entry to update.
            transcription: New transcription text (optional).
            translation: New translation text (optional).
            summary: New summary text (optional).
            tags: New list of tags (optional). Replaces existing tags.
            language: New language code (optional).

        Returns:
            bool: True if entry was found and updated, False otherwise.
        """
        if not self.OUTPUT_FILE_PATH.exists():
            return False

        try:
            tree = ET.parse(self.OUTPUT_FILE_PATH)
            root = tree.getroot()
        except ET.ParseError:
            return False

        # Find the entry
        entry = root.find(f".//entry[@id='{entry_id}']")
        if entry is None:
            print(f"Entry with ID {entry_id} not found.")
            return False

        # Update Transcription
        trans_elem = entry.find("transcription")
        if trans_elem is None and (transcription is not None or language is not None):
            # Create if doesn't exist but we have data for it
            trans_elem = ET.SubElement(entry, "transcription")
            # Ensure it's the first child (optional but good for consistency)
            # ElementTree doesn't support insert easily at specific index without list manipulation
            # simple append is fine for now, or re-ordering if strictly needed.
            # However, XML order matters less usually unless specified.
        
        if trans_elem is not None:
            if transcription is not None:
                trans_elem.text = f"\n{transcription.strip()}\n"
            if language is not None:
                trans_elem.set("language", language)
            if transcription_model is not None:
                trans_elem.set("model", transcription_model)

        # Update Translation
        trans_l_elem = entry.find("translation")
        if trans_l_elem is None and translation is not None:
            # Create if doesn't exist but we have data for it
            trans_l_elem = ET.SubElement(entry, "translation")
        
        if trans_l_elem is not None and translation is not None:
            trans_l_elem.text = f"\n{translation.strip()}\n" if translation else ""
            if translation_model is not None:
                trans_l_elem.set("model", translation_model)

        # Update Extracted Information (Summary and Tags)
        extracted_info = entry.find("extracted_information")
        if extracted_info is None and (summary is not None or tags is not None):
            extracted_info = ET.SubElement(entry, "extracted_information")
        
        if extracted_info is not None:
            # Summary
            summary_elem = extracted_info.find("summary")
            if summary_elem is None and summary is not None:
                summary_elem = ET.SubElement(extracted_info, "summary")
            
            if summary_elem is not None and summary is not None:
                summary_elem.text = summary

            # Tags
            if tags is not None:
                tags_elem = extracted_info.find("tags")
                if tags_elem is not None:
                    extracted_info.remove(tags_elem)
                
                tags_elem = ET.SubElement(extracted_info, "tags")
                for tag in tags:
                    tag_elem = ET.SubElement(tags_elem, "tag")
                    tag_elem.text = tag

        # Write back
        try:
            ET.indent(tree, space="    ")
            tree.write(self.OUTPUT_FILE_PATH, encoding="unicode", xml_declaration=True)
            return True
        except (IOError, OSError) as e:
            print(f"Error writing entry: {e}")
            return False

    def get_last_entry_id(self) -> str:
        """
        Get the ID of the last entry in the output XML file.

        Returns:
            str: The ID of the last entry, or None if no entries exist.
        """
        

        return self.get_all_entries()[-1].get("id") # TODO: test this

    def get_all_entries(self) -> list:
        """
        Get all entries from the output XML file.
        
        Returns:
            list: List of entry elements.
        """
        if not self.OUTPUT_FILE_PATH.exists():
            print(f"Error: Output file not found: {self.OUTPUT_FILE_PATH}")
            return []
        try:
            tree = ET.parse(self.OUTPUT_FILE_PATH)
            root = tree.getroot()
            return root.findall("entry")
        except ET.ParseError:
            print(f"Error: Failed to parse output file: {self.OUTPUT_FILE_PATH}")
            return []

    def get_all_entries_without_translation(self) -> list:
        """
        Get all entries without a translation.
        
        Returns:
            list: List of entry elements that have no translation or empty translation text.
        """
        if not self.OUTPUT_FILE_PATH.exists():
            return []
        tree = ET.parse(self.OUTPUT_FILE_PATH)
        root = tree.getroot()
        
        print("\n"*2 + "Getting all entries without translation..." + "\n"*2)
        entries_without_translation = []
        for entry in root.findall("entry"):
            translation_elem = entry.find("translation")
            # Check if translation element doesn't exist or has no text or only whitespace
            if translation_elem is None or not translation_elem.text or translation_elem.text.strip() == "":
                entries_without_translation.append(entry.get("id"))
        
        return entries_without_translation
    
    def get_transcribed_filenames(self) -> set[str]:
        """
        Get all filenames that have already been transcribed.
        
        Returns:
            set[str]: Set of filenames that exist in the output XML.
        """
        if not self.OUTPUT_FILE_PATH.exists():
            return set()
        
        try:
            tree = ET.parse(self.OUTPUT_FILE_PATH)
            root = tree.getroot()
        except ET.ParseError:
            return set()
        
        filenames = set()
        for entry in root.findall("entry"):
            filename = entry.get("filename")
            if filename:
                filenames.add(filename)
        
        return filenames

    def get_entry_ids(self) -> set[str]:
        """Get all entry IDs from the output XML."""
        if not self.OUTPUT_FILE_PATH.exists():
            return set()
        try:
            tree = ET.parse(self.OUTPUT_FILE_PATH)
            root = tree.getroot()
        except ET.ParseError:
            return set()
        return {entry.get("id") for entry in root.findall("entry") if entry.get("id")}

    def entry_exists_by_id(self, entry_id: str) -> bool:
        """Check if an entry with the given ID already exists."""
        if not entry_id:
            return False
        return entry_id in self.get_entry_ids()

    def entry_exists_by_filename(self, filename: str) -> bool:
        """Check if an entry with the given filename already exists."""
        if not filename:
            return False
        return filename in self.get_transcribed_filenames()

    def get_input_audio_files(self) -> list[Path]:
        """
        Get all audio files from the input directory.
        
        Returns:
            list[Path]: List of Path objects for audio files found in the input directory.
        """
        return self.refresh_input_audio_files()

    def refresh_input_audio_files(self) -> list[Path]:
        """
        Scan the input directory and update in-memory file state.

        Returns:
            list[Path]: Sorted list of detected audio files.
        """
        if not self.DEFAULT_INPUT_FOLDER.exists():
            self._input_audio_files = []
            return []

        audio_files = []
        for file_path in self.DEFAULT_INPUT_FOLDER.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in AUDIO_EXTENSIONS:
                audio_files.append(file_path)

        self._input_audio_files = sorted(audio_files) # TODO: why sort?
        return list(self._input_audio_files)

    def get_cached_input_audio_files(self) -> list[Path]:
        """
        Return the currently cached audio file list without rescanning.
        """
        return list(self._input_audio_files)

    def get_audio_file_info(self, file_path: Path) -> dict:
        """
        Return normalized metadata for one audio file path.
        """
        resolved = Path(file_path)
        size_bytes = resolved.stat().st_size if resolved.exists() else 0
        return {
            "path": resolved,
            "name": resolved.name,
            "stem": resolved.stem,
            "suffix": resolved.suffix.lower(),
            "size_bytes": size_bytes,
        }

    def get_pending_audio_files(self, skip_existing: bool = True) -> list[Path]:
        """
        Return audio files that should be processed next.

        This uses cached scan state if available, otherwise it performs a scan.
        """
        audio_files = self._input_audio_files or self.refresh_input_audio_files()
        if not skip_existing:
            return list(audio_files)

        transcribed_filenames = self.get_transcribed_filenames()
        return [file_path for file_path in audio_files if file_path.name not in transcribed_filenames]

    def transcribe_all_input_files(
        self,
        model_size: str = "tiny",
        clean: bool = True,
        language: str = "de",
        save: bool = True,
        skip_existing: bool = True
    ) -> list[dict]:
        """
        Transcribe all audio files from the input directory.
        
        Args:
            model_size: Whisper model size string (e.g., "tiny", "base", "small").
            clean: Whether to apply noise reduction before transcription.
            language: Language code for transcription (default: "de").
            save: Whether to save transcriptions to XML output (default: True).
            skip_existing: Whether to skip files that have already been transcribed (default: True).
        
        Returns:
            list[dict]: List of results for each transcribed file. Each dict contains:
                - file: Path to the original audio file
                - text: The transcription text
                - segments: List of transcription segments
                - language: Detected/specified language
                - success: Boolean indicating if transcription succeeded
                - error: Error message if transcription failed (None otherwise)
        """
        from transcribe_tool import TranscribeTool
        
        audio_files = self.get_input_audio_files()
        
        if not audio_files:
            print("No audio files found in input directory.")
            return []
        
        # Filter out already transcribed files if skip_existing is True
        if skip_existing:
            transcribed_filenames = self.get_transcribed_filenames()
            audio_files = [f for f in audio_files if f.name not in transcribed_filenames]
            
            if not audio_files:
                print("All files in input directory have already been transcribed.")
                return []
            
            print(f"Found {len(audio_files)} new audio file(s) to transcribe:")
        else:
            print(f"Found {len(audio_files)} audio file(s) to transcribe:")
        
        for audio_file in audio_files:
            print(f"  - {audio_file.name}")
        print("-" * 40)
        
        results = []
        
        # Initialize output file if saving is enabled
        if save and not self.OUTPUT_FILE_PATH.exists():
            self.create_output_file()
        
        # Use context manager to handle cleanup
        with TranscribeTool(model_size=model_size) as tool:
            for audio_file in audio_files:
                print(f"\nProcessing: {audio_file.name}")
                
                result = {
                    "file": audio_file,
                    "text": "",
                    "segments": [],
                    "language": language,
                    "success": False,
                    "error": None
                }
                
                try:
                    # Transcribe the audio file
                    transcription_result = tool.process(
                        audio_path=audio_file,
                        clean=clean,
                        language=language
                    )
                    
                    result["text"] = transcription_result["text"]
                    result["segments"] = transcription_result["segments"]
                    result["language"] = transcription_result["language"]
                    result["success"] = True
                    
                    print(f"Transcription: {transcription_result['text'][:100]}...")
                    
                    # Save to XML if requested
                    if save:
                        transcription_id = self._generate_transcription_id(transcription_result["text"])
                        if self.entry_exists_by_filename(audio_file.name) or self.entry_exists_by_id(transcription_id):
                            print("Skipping save: entry already exists in output.")
                        else:
                            add_success = self.add_entry(
                                transcription=transcription_result["text"],
                                model=model_size,
                                language=transcription_result["language"],
                                filename=audio_file.name
                            )
                            
                            if add_success:
                                print(f"Saved to {self.OUTPUT_FILE_PATH}")
                            else:
                                print("Warning: Failed to save transcription to XML")
                
                except Exception as e:
                    result["error"] = str(e)
                    print(f"Error processing {audio_file.name}: {e}")
                
                results.append(result)
        
        # Summary
        print("\n" + "=" * 40)
        print("Transcription Summary:")
        print(f"Total files: {len(audio_files)}")
        print(f"Successful: {sum(1 for r in results if r['success'])}")
        print(f"Failed: {sum(1 for r in results if not r['success'])}")
        print("=" * 40)
        
        return results