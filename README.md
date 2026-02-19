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

Models are downloaded from the Systran faster-whisper repositories on Hugging Face
and stored in clean local folders: `models/<model_name>/`.

Supported download targets:

| Size | Notes |
|------|-------|
| `tiny`, `tiny.en` | Fastest, least accurate |
| `base`, `base.en` | Good for quick tests |
| `small`, `small.en` | Balanced speed/accuracy |
| `medium`, `medium.en` | Higher accuracy |
| `large-v1`, `large-v2`, `large-v3` | Larger multilingual models |
| `distil-large-v2`, `distil-large-v3` | Smaller/faster distilled variants |

`.en` variants are English-only and slightly better for English content.
`large-v3-turbo` is intentionally excluded from the downloader to keep one model source.

To pre-download a model to the local `models/` directory:

```bash
python download_model.py tiny
python download_model.py distil-large-v3
python download_model.py --list
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
# Basic transcription (after downloading a model, e.g. tiny)
python src/main.py

# Use a larger model
python src/main.py --model large-v3

# Skip noise reduction
python src/main.py --no-clean
```

Transcriptions are saved to `output/output.xml`.

## TODOs
### BUGS
#### OLLAMA does not unload model after use
I've used the program and qwen was still loaded in gpu. another instance of gpu was too much for my poor gpu.
```bash
ollama ps
NAME        ID              SIZE      PROCESSOR    CONTEXT    UNTIL              
qwen3:8b    500a1f067a9f    6.0 GB    100% GPU     4096       3 minutes from now   
```
got me this error:
```
python3 src/main.py --model large-v3
Found 4 audio file(s) to process.
clean_audio() took 0.30 s
process() took 0.51 s
Error processing Record-028.aac: CUDA failed with error out of memory
process() took 0.19 s
Error processing WhatsApp Audio 2026-02-12 at 12.15.30.ogg: CUDA out of memory. Tried to allocate 24.00 MiB. GPU 0 has a total capacity of 7.60 GiB of which 15.38 MiB is free. Process 3936 has 5.38 GiB memory in use. Including non-PyTorch memory, this process has 2.19 GiB memory in use. Of the allocated memory 217.80 MiB is allocated by PyTorch, and 50.20 MiB is reserved by PyTorch but unallocated. If reserved but unallocated memory is large try setting PYTORCH_ALLOC_CONF=expandable_segments:True to avoid fragmentation.  See documentation for Memory Management  (https://pytorch.org/docs/stable/notes/cuda.html#environment-variables)
process() took 0.13 s
Error processing schwindelig.aac: CUDA out of memory. Tried to allocate 24.00 MiB. GPU 0 has a total capacity of 7.60 GiB of which 11.38 MiB is free. Process 3936 has 5.38 GiB memory in use. Including non-PyTorch memory, this process has 2.19 GiB memory in use. Of the allocated memory 217.60 MiB is allocated by PyTorch, and 54.40 MiB is reserved by PyTorch but unallocated. If reserved but unallocated memory is large try setting PYTORCH_ALLOC_CONF=expandable_segments:True to avoid fragmentation.  See documentation for Memory Management  (https://pytorch.org/docs/stable/notes/cuda.html#environment-variables)
process() took 0.17 s
Error processing test-voice.m4a: CUDA out of memory. Tried to allocate 24.00 MiB. GPU 0 has a total capacity of 7.60 GiB of which 11.38 MiB is free. Process 3936 has 5.38 GiB memory in use. Including non-PyTorch memory, this process has 2.19 GiB memory in use. Of the allocated memory 224.63 MiB is allocated by PyTorch, and 47.37 MiB is reserved by PyTorch but unallocated. If reserved but unallocated memory is large try setting PYTORCH_ALLOC_CONF=expandable_segments:True to avoid fragmentation.  See documentation for Memory Management  (https://pytorch.org/docs/stable/notes/cuda.html#environment-variables)

========================================
Transcription Summary:
Total files: 4
Successful: 0
Failed: 4
========================================
```

### CODE MARKS
| File | Message |
|------|---------|
| `src/logic.py` | what if text is empty? |
| `src/ollama_handler.py` | sooooo many returns that could be used...use em :( |
| `src/file_handling.py` | get date from meta data or title (title is more reliable(valid_date)) |
| `src/file_handling.py` | test this |
| `src/file_handling.py` | why sort? |
| `download_model.py` | what is this shit: Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads. |
| `src/transcribe_tool.py` | add more parameters (play around with them) |
| `src/transcribe_tool.py` | what happens to tmp file? eg: PosixPath('/tmp/transcribe_clean_5o9fl8al/test-voice_cleaned.wav') |
| `src/transcribe_tool.py` | add language_probability to result |

### Later implementation ideas

- **Different STT Tool**
  - Try out `https://huggingface.co/Qwen/Qwen3-ASR-1.7B` a model by alibaba

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
