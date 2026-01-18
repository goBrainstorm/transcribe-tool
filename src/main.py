# main functinality to transcribe a recording with whisper.cpp
# import whisper.cpp as whisper
import os

def get_available_models(path: str = "models/whisper"):
    return os.listdir(path)

# define model sizes
MODEL_SIZES = {
}



def transcribe_recording(recording_path, model_size: str = "base"):
    model = whisper.load_model(model_size)
    result = model.transcribe(recording_path)
    return result

def main():
    # get available models
    available_models = get_available_models()
    print(available_models)


if __name__ == "__main__":
    main()