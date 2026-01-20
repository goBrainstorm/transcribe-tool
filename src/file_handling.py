from pathlib import Path


class FileHandler:
    """Handles file operations for the transcription tool, including XML output management."""

    DEFAULT_MODEL_PATH = Path("models/whisper.cpp")
    DEFAULT_OUTPUT_FOLDER = Path("output")
    OUTPUT_FILE_PATH = DEFAULT_OUTPUT_FOLDER / "output.xml"

    def __init__(self):
        """Initialize the FileHandler instance."""
        pass  # TODO: add functionality to create new individual output files

    def create_file(self) -> bool:
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

    def get_available_models(self) -> list:
        """
        Get a list of available Whisper model files.

        Scans the DEFAULT_MODEL_PATH directory for .bin files.

        Returns:
            list: List of filenames ending with '.bin' in the models directory.
        """
        return [f.name for f in self.DEFAULT_MODEL_PATH.glob("*.bin")]