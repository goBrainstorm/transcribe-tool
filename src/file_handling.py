import os
import json
import time


class FileHandler:
    DEFAULT_MODEL_PATH = "models/whisper"
    
    DEFAULT_OUTPUT_FOLDER = "output/"
    DEFAULT_OUTPUT_FILE_NAME = "output"
    DEFAULT_FILE_EXTENSION = ".json"
    DEFAULT_OUTPUT_FILE = DEFAULT_OUTPUT_FILE_NAME + DEFAULT_FILE_EXTENSION
    DEFAULT_STRUCTURE = {
        "date": "YYYY-MM-DD",
        "time": "HH:MM:SS",
        "duration": "HH:MM:SS",
        "transcript": "",
    }

    def __init__(self, output_folder: str = DEFAULT_OUTPUT_FOLDER, output_file: str = DEFAULT_OUTPUT_FILE):
        pass #TODO: add functionallity to create new individual output files

    def create_output_folder(self) -> None:
        if not os.path.exists(self.DEFAULT_OUTPUT_FOLDER):
            os.makedirs(self.DEFAULT_OUTPUT_FOLDER)

    def create_output_file(self, ignore_existing: bool = False) -> None: #TODO: add functionallity to create new individual output files
        """Create a new output file. If the file already exists, the file will be overwritten."""
        self.create_output_folder()
        if not os.path.exists(self.DEFAULT_OUTPUT_FOLDER + self.DEFAULT_OUTPUT_FILE) or ignore_existing:
            with open(self.DEFAULT_OUTPUT_FOLDER + self.DEFAULT_OUTPUT_FILE, "w") as f:
                json.dump(self.DEFAULT_STRUCTURE, f)

    def write_to_output_file(self, data: dict) -> None:
        with open(self.DEFAULT_OUTPUT_FOLDER + self.DEFAULT_OUTPUT_FILE, "w") as f:
            json.dump(data, f)

    def get_available_models(self) -> list:
        return [f for f in os.listdir(self.DEFAULT_MODEL_PATH) if f.endswith('.bin')]