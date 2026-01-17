# Transcribe Tool with Whisper
A tool to transcribe recrodings with [**whisper.cpp**](https://github.com/ggml-org/whisper.cpp) and obviously glorious [**ffmpeg**](https://ffmpeg.org/). I will try to implement [nemotron](https://huggingface.co/nvidia/nemotron-speech-streaming-en-0.6b).
## Idea of the project
I want to transcribe all of my voice messages that I save for myself. The target is it to transcribe them with whisper; then summarize them and even save information from in with an local running LLM. 

### Stucture of the Project
Currently the structure looks like this but will evolve over the course of development. 
├── Models
│   └── Whisper
├── output
└── src

### Using models from [**whisper.cpp**](https://github.com/ggml-org/whisper.cpp/blob/master/models/README.md) is not as straighforward as just downloading...or wait it is...? Yes! [HERE](https://huggingface.co/ggerganov/whisper.cpp/tree/main)
If you want to download the models yourself: go to the [whisper.cpp/models/README](https://github.com/ggml-org/whisper.cpp/blob/master/models/README.md) and follow their instructions. 

## Precursor
I want to use as little vibe coding as possible; but I will be using AI to help me. 