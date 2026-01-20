from pathlib import Path
import string
import hashlib
from datetime import datetime
import xml.etree.ElementTree as ET


class FileHandler:
    """Handles file operations for the transcription tool, including XML output management."""

    DEFAULT_MODEL_PATH = Path("models/whisper.cpp")
    DEFAULT_OUTPUT_FOLDER = Path("output")
    OUTPUT_FILE_PATH = DEFAULT_OUTPUT_FOLDER / "output.xml"

    def __init__(self):
        """Initialize the FileHandler instance."""
        pass  # TODO: add functionality to create new individual output files

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
        language: str = None
    ) -> bool:
        """
        Add an entry to the output XML file.

        Args:
            transcription: The transcription text content.
            date: Optional date string in ISO format (e.g., "2026-01-20T14:30:00").
            summary: Optional summary of the transcription.
            tags: Optional list of tags.
            language: Language code, defaults to "en".

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

        # Add transcription
        trans_elem = ET.SubElement(entry, "transcription")
        trans_elem.text = f"\n{transcription.strip()}\n" if transcription else ""

        # Add summary
        summary_elem = ET.SubElement(entry, "summary")
        summary_elem.text = summary

        # Add tags
        tags_elem = ET.SubElement(entry, "tags")
        if tags:
            for tag in tags:
                tag_elem = ET.SubElement(tags_elem, "tag")
                tag_elem.text = tag

        # Add language
        lang_elem = ET.SubElement(entry, "language")
        lang_elem.text = language

        # Write back to file with proper formatting
        try:
            ET.indent(tree, space="    ")
            tree.write(self.OUTPUT_FILE_PATH, encoding="unicode", xml_declaration=True)
            return True
        except (IOError, OSError) as e:
            print(f"Error writing entry: {e}")
            return False

    def get_available_models(self) -> list:
        """
        Get a list of available Whisper model files.

        Scans the DEFAULT_MODEL_PATH directory for .bin files.

        Returns:
            list: List of filenames ending with '.bin' in the models directory.
        """
        return [f.name for f in self.DEFAULT_MODEL_PATH.glob("*.bin")]