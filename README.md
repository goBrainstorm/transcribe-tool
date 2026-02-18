# Transcribe Tool with Whisper
A tool to transcribe recordings with [**faster-whisper**](https://github.com/SYSTRAN/faster-whisper) (CTranslate2) and [**ffmpeg**](https://ffmpeg.org/).

## Idea of the project
I want to transcribe all of my voice messages that I save for myself. The target is to transcribe them with whisper, then summarize them and save gathered information (information as in ideas, thoughts, location, mood, people, etc.) with a locally running LLM.

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

## Usage - transcribes all files located in `input/`

```bash
# Basic transcription (downloads 'tiny' model on first run)
python src/main.py

# Use a larger model
python src/main.py --model large-v3-turbo

# Skip noise reduction
python src/main.py --no-clean
```

Transcriptions are saved to `output/output.xml`.

## Later implementation ideas

- **Responsibility split**
  - Keep `src/logic.py` as static orchestration/core workflow only.
  - Keep `src/file_handling.py` as the state holder for input audio file data and XML persistence.
  - Keep `src/main.py` as the CLI entrypoint that parses args and wires dependencies.

- **Single initialization for heavy tools**
  - Initialize `TranscribeTool`, `TranslateTool`, and `OllamaHandler` once in `src/main.py`.
  - Pass initialized instances into `Logic` functions to avoid repeated setup cost.

- **File metadata model**
  - Introduce a typed file metadata object (for example, a dataclass) with path, name, extension, size, and status fields.
  - Use this object across logic/persistence instead of loose dictionaries.

- **Queue functionality**
  - Add a queue class (for example, `TranscriptionQueue`) to manage pending/running/failed/completed files.
  - Support retries, progress status, and optional persistence of queue state.
  - Make queue processing the default path for folder-based runs.

- **Logging and observability**
  - Replace ad-hoc `print` calls with a unified logger and log levels (debug/info/warning/error).
  - Add runtime metrics for processing time per file and per stage (cleaning, transcription, translation, XML write).

- **Tests**
  - Add tests for duplicate detection, pending file filtering, malformed XML handling, and queue behavior.
  - Add integration tests for single-file and folder processing flows.
