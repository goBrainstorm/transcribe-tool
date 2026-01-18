import os
import json
import time


class FileHandler:
    DEFAULT_MODEL_PATH = "models/whisper"
    
    DEFAULT_OUTPUT_FOLDER = "output"
    DEFAULT_OUTPUT_FILE = DEFAULT_OUTPUT_FOLDER + "/output.json"
    DEFAULT_STRUCTURE = {
        "date": "YYYY-MM-DD",
        "time": "HH:MM:SS",
        "duration": "HH:MM:SS",
        "transcript": "",
    }

    DEFAULT_FILE_EXTENSION = ".json"

    files_in_output_folder = []

    def __init__(self, output_folder: str = DEFAULT_OUTPUT_FOLDER, output_file: str = DEFAULT_OUTPUT_FILE):
        self.output_folder = output_folder
        self.output_file = output_file

    def create_output_folder(self) -> None:
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

    def create_output_file(self, ignore_existing: bool = False) -> None: #TODO: add functionallity to create new individual output files
        """Create a new output file. If the file already exists, the file will be overwritten."""
        self.create_output_folder()
        if not os.path.exists(self.output_file) or ignore_existing:
            if ignore_existing:
                self.output_file = self.output_file + "_" + time.strftime("%Y%m%d_%H%M%S") + self.DEFAULT_FILE_EXTENSION
            with open(self.output_file, "w") as f:
                json.dump(self.DEFAULT_STRUCTURE, f)
            self.files_in_output_folder.append(self.output_file)

    def write_to_output_file(self, data: dict) -> None:
        with open(self.output_file, "w") as f:
            json.dump(data, f)

    def get_output_path(self) -> str:
        return os.path.join(self.output_folder, self.output_file)

    def get_available_models(self, path: str = DEFAULT_MODEL_PATH):
        return [f for f in os.listdir(path) if f.endswith('.bin')]