from pathlib import Path
import string
import hashlib
from datetime import datetime
import xml.etree.ElementTree as ET


class FileHandler:
    """Handles file operations for the transcription tool, including XML output management."""

    DEFAULT_MODEL_PATH = Path("models")
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

    def add_entry(
        self,
        transcription: str = "",
        date: str = None,
        summary: str = "",
        tags: list = None,
        language: str = None,
        confidence: float = None,
        translation: str = None
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

        # 1. Transcription element (with attributes)
        trans_elem = ET.SubElement(entry, "transcription")
        if language:
            trans_elem.set("language", language)
        if confidence is not None:
            trans_elem.set("confidence", str(confidence))
        trans_elem.text = f"\n{transcription.strip()}\n" if transcription else ""

        # 2. Translation element
        trans_elem = ET.SubElement(entry, "translation")
        trans_elem.text = f"\n{translation.strip()}\n" if translation else ""

        # 3. Extracted Information
        extracted_info = ET.SubElement(entry, "extracted_information")

        # Tags
        tags_elem = ET.SubElement(extracted_info, "tags")
        if tags:
            for tag in tags:
                tag_elem = ET.SubElement(tags_elem, "tag")
                tag_elem.text = tag

        # Summary
        summary_elem = ET.SubElement(extracted_info, "summary")
        summary_elem.text = summary

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
        translation: str = None,
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

        # Update Translation
        trans_l_elem = entry.find("translation")
        if trans_l_elem is None and translation is not None:
            trans_l_elem = ET.SubElement(entry, "translation")
        
        if trans_l_elem is not None and translation is not None:
            trans_l_elem.text = f"\n{translation.strip()}\n"

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
