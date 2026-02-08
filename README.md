# Transcribe Tool with Whisper
A tool to transcribe recordings with [**faster-whisper**](https://github.com/SYSTRAN/faster-whisper) (CTranslate2) and [**ffmpeg**](https://ffmpeg.org/).

## Idea of the project
I want to transcribe all of my voice messages that I save for myself. The target is to transcribe them with whisper, then summarize them and save information from them with a locally running LLM.

### Structure of the Project

```
transcribe-tool/
├── models/
│   └── download_model.py   # Model download script
├── output/                 # Transcription output (XML)
├── src/
│   ├── main.py             # CLI entry point
│   ├── transcribe_tool.py  # Audio cleaning + transcription pipeline
│   └── file_handling.py    # XML output management
├── run.sh                  # Convenience runner (creates venv, runs tool)
└── requirements.txt
```

### Models

faster-whisper downloads models from Hugging Face automatically on first use. Available sizes:

| Size | Notes |
|------|-------|
| `tiny`, `tiny.en` | Fastest, least accurate |
| `base`, `base.en` | Good for quick tests |
| `small`, `small.en` | Balanced speed/accuracy |
| `medium`, `medium.en` | Higher accuracy |
| `large-v3` | Best accuracy, slowest |
| `large-v3-turbo` | Good balance of speed and accuracy |

`.en` variants are English-only and slightly better for English content.

To pre-download a model to the local `models/` directory:

```bash
python models/download_model.py tiny
python models/download_model.py large-v3-turbo
python models/download_model.py --list
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Requires `ffmpeg` to be installed on your system.

## Usage

```bash
# Basic transcription (downloads 'tiny' model on first run)
python src/main.py recording.m4a

# Use a larger model
python src/main.py recording.m4a --model large-v3-turbo

# Skip noise reduction
python src/main.py recording.m4a --no-clean

# Different language
python src/main.py recording.m4a --language en

# List available models
python src/main.py --list-models
```

Or use the convenience script which handles the virtual environment:

```bash
./run.sh recording.m4a
./run.sh recording.m4a --model small --language en
```

Transcriptions are saved to `output/output.xml`.

## Precursor
I want to use as little vibe coding as possible; but I will be using AI to help me.