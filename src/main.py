# main functinality to transcribe a recording with whisper.cpp
# import whisper.cpp as whisper
import os

def get_available_models(path: str = "models/whisper.cpp"):
    return os.listdir(path)


def transcribe_recording(recording_path, model_size: str = "base"):
    # TODO: insert logic to transcribe recording with the use of file_handling.py 
    pass

def main():
    # get available models
    available_models = get_available_models()
    print(available_models)


if __name__ == "__main__":
    main()