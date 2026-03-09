# Transcribe Tool

Transcribe audio files with local `faster-whisper`, optionally clean audio first, then optionally translate and summarize with locally running Ollama models. Results are stored in `output/output.xml`.

## What It Does

- Transcribes one file (`python src/main.py path/to/file.m4a`) or all supported files from `input/` (`python src/main.py`).
- Optionally denoises audio before transcription.
- Optionally translates entries missing translations (`--translate`).
- Optionally summarizes entries that already have translations (`--summarize`).
- Avoids duplicate XML entries by checking both filename and generated transcription ID.

## Current Project Layout

```text
transcribe-tool/
├── config.json
├── download_model.py
├── input/
├── models/
├── output/
│   └── output.xml
└── src/
    ├── app_logging.py
    ├── file_handling.py
    ├── LLM_handler.py
    ├── logic.py
    ├── main.py
    ├── ollama_handler.py
    └── transcribe_tool.py
```

## Requirements

- Python 3.10+
- `ffmpeg` available on PATH
- Python packages from `requirements.txt`
- For LLM features (`--translate`, `--summarize`):
  - Ollama installed and running (`ollama serve`)
  - models from `config.json` pulled locally
- For token counting metadata in Ollama responses: `tiktoken` (optional; generation still works without it)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Install `ffmpeg` using your OS package manager if it is missing.

## Whisper Model Download

Models are expected in `models/<model_name>/` and can be downloaded with:

```bash
python download_model.py --list
python download_model.py tiny
python download_model.py distil-large-v3
```

## Ollama Configuration

`config.json` controls Ollama integration:

```json
{
  "ollama_host": "http://localhost:11434",
  "translate_model": "translategemma:4b",
  "summary_model": "qwen3:0.6b",
  "default_transcribe_model": "tiny"
}
```

Pull configured models before using translation/summarization:

```bash
ollama pull translategemma:4b
ollama pull qwen3:0.6b
```

## CLI Usage

### List local whisper models

```bash
python src/main.py --list-models
```

### Transcribe all files from `input/`

```bash
python src/main.py
```

### Transcribe one file

```bash
python src/main.py "/absolute/or/relative/path/to/audio.m4a"
```

### Common options

```bash
# Use a specific whisper model
python src/main.py --model large-v3

# Hint source language ("auto" is default)
python src/main.py --language de

# Disable denoising
python src/main.py --no-clean

# Do not write output.xml
python src/main.py --no-save

# Print full transcription text to stdout
python src/main.py --print-result

# Enable debug logging
python src/main.py --debug
```

### Translation and summarization

```bash
# Translate entries that have no translation yet
python src/main.py --translate

# Summarize entries that already have translations
python src/main.py --summarize

# Typical full post-processing run
python src/main.py --translate --summarize
```

Important behavior:

- `--translate` and `--summarize` are opt-in. They are not run unless explicitly requested.
- `--summarize` only works on entries that already contain translation text.

## Output Format (`output/output.xml`)

Each entry is written roughly as:

```xml
<entry id="ID-xxxxxxxx" has_date_as_id="0" filename="audio-file.m4a">
  <transcription language="de" model="tiny">...</transcription>
  <translation>...</translation>
  <extracted_information>
    <tags>
      <tag />
    </tags>
    <summary>...</summary>
  </extracted_information>
</entry>
```

## Processing Notes

- Supported input extensions: `.mp3`, `.wav`, `.ogg`, `.m4a`, `.flac`, `.aac`, `.opus`, `.wma`
- Folder mode processes pending files from `input/` and skips already-transcribed filenames by default.
- Denoising is skipped automatically for large files above `TRANSCRIBE_MAX_DENOISE_MB` (default: `50`).
- Empty transcription text is treated as a failure and is not saved.
- If `tiktoken` is missing, Ollama generation continues; token count metadata may be `null`.

## Known Limitations / Follow-Ups

- Ollama model lifecycle (unload behavior) is not actively managed by this project.
- In `src/ollama_handler.py`, base-name model matching is currently permissive and marked as uncertain in code.
- In `src/transcribe_tool.py`, a temporary monkey patch around `AudioNoiseModel.from_pretrained` is marked as uncertain in code.
- No automated tests yet; CLI and runtime behavior are currently validated manually.
