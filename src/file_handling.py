from pathlib import Path
import string
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
        pass  # TODO: add functionality to create new individual output files

    def get_available_models(self) -> list:
        """
        Get list of available whisper models (locally downloaded).

        Returns:
            list: List of model names found in the models directory.
        """
        if not self.DEFAULT_MODEL_PATH.exists():
            return []

        models = []
        for d in self.DEFAULT_MODEL_PATH.iterdir():
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
            xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<transcriptions>\n</transcriptions>'

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

    def get_transcription_content(self, entry_id: str) -> str:
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
        filename: str = None
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
        def valid_date(date_str: str) -> bool:
            """Check if date string is a valid ISO format datetime."""
            if date_str is None:
                return False
            try:
                datetime.fromisoformat(date_str)
                return True
            except (ValueError, TypeError):
                return False

        def generate_hash(text: str) -> str:
            """Generate a short hash from the transcription text."""
            return hashlib.md5(text.encode()).hexdigest()[:8]

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
            entry_id = f"ID-{generate_hash(transcription)}"
            has_date_as_id = "0"
    
        # Parse existing XML
        try:
            tree = ET.parse(self.OUTPUT_FILE_PATH)
            root = tree.getroot()
        except ET.ParseError:
            # File might be malformed or empty, try to create root element
            root = ET.Element("transcriptions")
            tree = ET.ElementTree(root)

        # Create new entry element
        entry = ET.SubElement(root, "entry", id=entry_id, has_date_as_id=has_date_as_id)
        
        # Add filename attribute if provided
        if filename:
            entry.set("filename", filename)

        # 1. Transcription element (with attributes)
        trans_elem = ET.SubElement(entry, "transcription")
        if language:
            trans_elem.set("language", language)
        if model:
            trans_elem.set("model", model)
        trans_elem.text = f"\n{transcription.strip()}\n" if transcription else ""

        # 2. Translation element
        trans_elem = ET.SubElement(entry, "translation")
        trans_elem.text = f"\n{translation.strip()}\n" if translation else ""

        # 3. Extracted Information
        extracted_info = ET.SubElement(entry, "extracted_information")

        # Tags
        tags_elem = ET.SubElement(extracted_info, "tags")
        
        # set information 
        ET.SubElement(tags_elem, "tag")
        ET.SubElement(extracted_info, "summary")

        # Write back to file with proper formatting
        try:
            ET.indent(tree, space="    ")
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
        if not self.OUTPUT_FILE_PATH.exists():
            return None

        try:
            tree = ET.parse(self.OUTPUT_FILE_PATH)
            root = tree.getroot()
        except ET.ParseError:
            return None

        entries = root.findall("entry")
        if not entries:
            return None

        return entries[-1].get("id")

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
        
        print("Getting all entries without translation: ")
        entries_without_translation = []
        for entry in root.findall("entry"):
            translation_elem = entry.find("translation")
            # Check if translation element doesn't exist or has no text or only whitespace
            if translation_elem is None or not translation_elem.text or translation_elem.text.strip() == "":
                entries_without_translation.append(entry.get("id"))

        print("\n" * 2, "-" *40, "\n" * 2)
        
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

    def get_input_audio_files(self) -> list[Path]:
        """
        Get all audio files from the input directory.
        
        Returns:
            list[Path]: List of Path objects for audio files found in the input directory.
        """
        if not self.DEFAULT_INPUT_FOLDER.exists():
            return []
        
        audio_files = []
        for file_path in self.DEFAULT_INPUT_FOLDER.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in AUDIO_EXTENSIONS:
                audio_files.append(file_path)
        
        return sorted(audio_files)

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