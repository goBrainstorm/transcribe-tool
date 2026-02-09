"""
Transcribe tool for processing voice messages.

This module provides audio cleaning and transcription capabilities using:
- audio-denoiser for noise reduction
- faster-whisper (CTranslate2) for transcription
"""

from pathlib import Path
import tempfile
import shutil
import subprocess
import os
import json
import time

import numpy as np
import torch
from audio_denoiser.AudioDenoiser import AudioDenoiser
from faster_whisper import WhisperModel

from file_handling import FileHandler


def _debug_log(message: str, data: dict, hypothesis_id: str, location: str, run_id: str = "pre-fix") -> None:
    log_path = "/home/gobrainstorm/Documents/coding/transcribe-tool/.cursor/debug.log"
    payload = {
        "id": f"log_{int(time.time() * 1000)}_{os.getpid()}",
        "timestamp": int(time.time() * 1000),
        "location": location,
        "message": message,
        "data": data,
        "runId": run_id,
        "hypothesisId": hypothesis_id,
    }
    try:
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(payload) + "\n")
    except OSError:
        pass


def load_audio_with_ffmpeg(input_path: Path, sample_rate: int = 16000) -> tuple[torch.Tensor, int]:
    """
    Load audio file using ffmpeg, converting to mono WAV at specified sample rate.
    
    This bypasses torchaudio's backend issues by using ffmpeg directly.
    
    Args:
        input_path: Path to the input audio file.
        sample_rate: Target sample rate (default 16000 for Whisper).
    
    Returns:
        Tuple of (waveform tensor, sample_rate).
    """
    import wave
    
    # Create a temporary file for the converted audio
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
        tmp_path = tmp_file.name
    
    try:
        # Use ffmpeg to convert to 16kHz mono 16-bit PCM WAV
        cmd = [
            "ffmpeg", "-y", "-i", str(input_path),
            "-ar", str(sample_rate),
            "-ac", "1",
            "-acodec", "pcm_s16le",
            "-f", "wav",
            tmp_path
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        
        # Load the WAV file using standard library (no torchaudio)
        with wave.open(tmp_path, 'rb') as wav_file:
            n_frames = wav_file.getnframes()
            audio_data = wav_file.readframes(n_frames)
            sr = wav_file.getframerate()
        
        # Convert bytes to numpy array then to torch tensor
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
        # Normalize to [-1, 1] range
        audio_array = audio_array / 32768.0
        # Convert to torch tensor with shape [1, samples] (mono)
        waveform = torch.from_numpy(audio_array).unsqueeze(0)
        
        return waveform, sr
    finally:
        # Clean up temp file
        Path(tmp_path).unlink(missing_ok=True)


class AudioCleaner:
    """Handles audio noise reduction using audio-denoiser ML model."""

    def __init__(self, output_dir: Path = None):
        """
        Initialize the AudioCleaner.

        Args:
            output_dir: Directory for cleaned audio files. If None, uses a temp directory.
        """
        self.output_dir = output_dir or Path(tempfile.mkdtemp(prefix="transcribe_clean_"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize the audio denoiser model
        # Uses GPU if available, otherwise CPU
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.denoiser = AudioDenoiser(device=self.device)

    def clean_audio(self, input_path: Path) -> Path:
        """
        Clean audio file by removing background noise.

        Args:
            input_path: Path to the input audio file.

        Returns:
            Path to the cleaned audio file (16kHz mono WAV).

        Raises:
            FileNotFoundError: If input file doesn't exist.
            RuntimeError: If audio processing fails.
        """
        input_path = Path(input_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Audio file not found: {input_path}")

        # Load audio using ffmpeg (bypasses torchaudio backend issues)
        # Already converts to 16kHz mono
        waveform, sample_rate = load_audio_with_ffmpeg(input_path, sample_rate=16000)

        # Denoise the audio
        # audio-denoiser expects [batch, channels, samples] or [channels, samples]
        denoised_waveform = self.denoiser.process_waveform(
            waveform=waveform,
            sample_rate=sample_rate
        )

        # Generate output filename
        output_filename = f"{input_path.stem}_cleaned.wav"
        output_path = self.output_dir / output_filename

        # Save the cleaned audio using scipy (avoids torchaudio issues)
        from scipy.io import wavfile
        # Convert tensor to numpy and scale to int16 range
        audio_np = denoised_waveform.squeeze().cpu().numpy()
        audio_int16 = (audio_np * 32767).astype(np.int16)
        wavfile.write(str(output_path), sample_rate, audio_int16)

        return output_path

    def cleanup(self):
        """Remove temporary files created during cleaning."""
        if self.output_dir.exists() and "transcribe_clean_" in str(self.output_dir):
            shutil.rmtree(self.output_dir, ignore_errors=True)


class Transcriber:
    """Handles audio transcription using faster-whisper (CTranslate2)."""

    DEFAULT_MODELS_DIR = Path("models")

    def __init__(self, model_size: str = "tiny", models_dir: Path = None):
        """
        Initialize the Transcriber with a faster-whisper model.

        Args:
            model_size: Whisper model size string (e.g., "tiny", "base", "small",
                       "medium", "large-v3", "large-v3-turbo") or path to a
                       local CTranslate2 model directory.
            models_dir: Directory for caching downloaded models.
                       If None, uses the default "models/" directory.
        """
        self.models_dir = models_dir or self.DEFAULT_MODELS_DIR
        self.model_size = model_size
        
        # Set Hugging Face cache to use our models directory
        # This ensures models are loaded from our local folder
        os.environ["HF_HOME"] = str(self.models_dir.absolute())
        os.environ["HF_HUB_CACHE"] = str(self.models_dir.absolute() / "hub")
        
        self.model = WhisperModel(
            model_size,
            device="auto",
            compute_type="int8",
            download_root=str(self.models_dir)
        )

    def transcribe(self, audio_path: Path, language: str = "en") -> dict:
        """
        Transcribe an audio file.

        Args:
            audio_path: Path to the audio file (WAV, MP3, etc. -- ffmpeg formats supported).
            language: Language code for transcription (e.g., "en", "de", "es").

        Returns:
            dict with keys:
                - text: The full transcription text
                - segments: List of transcription segments with timestamps
                - language: Detected or specified language
                - language_probability: Confidence of the detected language

        Raises:
            FileNotFoundError: If audio file doesn't exist.
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Transcribe using faster-whisper
        segments_generator, info = self.model.transcribe(
            str(audio_path),
            language=language,
            beam_size=5
        )

        # Consume the generator into a list so we can iterate twice
        segments_list = list(segments_generator)

        # Extract full text from segments
        full_text = " ".join(segment.text.strip() for segment in segments_list)

        return {
            "text": full_text,
            "segments": [
                {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                }
                for segment in segments_list
            ],
            "language": info.language,
            "language_probability": info.language_probability
        }


class TranscribeTool:
    """
    Main transcription tool that combines audio cleaning and transcription.

    Provides a complete pipeline from raw audio to saved transcription.
    """

    def __init__(
        self,
        model_size: str = "tiny",
        models_dir: Path = None,
        temp_dir: Path = None
    ):
        """
        Initialize the TranscribeTool.

        Args:
            model_size: Whisper model size (e.g., "tiny", "base", "small",
                       "medium", "large-v3", "large-v3-turbo").
            models_dir: Directory for caching downloaded models.
            temp_dir: Directory for temporary cleaned audio files.
        """
        self.cleaner = AudioCleaner(output_dir=temp_dir)
        self.transcriber = Transcriber(model_size=model_size, models_dir=models_dir)
        self.file_handler = FileHandler()

    def process(
        self,
        audio_path: Path,
        clean: bool = True,
        language: str = "de",
    ) -> dict:
        """
        Process an audio file through the full transcription pipeline.

        Args:
            audio_path: Path to the input audio file.
            clean: Whether to apply noise reduction before transcription.
            language: Language code for transcription.

        Returns:
            dict with keys:
                - text: The full transcription text
                - segments: List of transcription segments
                - language: Language used
                - cleaned_path: Path to cleaned audio (if clean=True)
        """
        audio_path = Path(audio_path)
        result = {
            "text": "",
            "segments": [],
            "cleaned_path": None,
        }
        max_denoise_mb = int(os.getenv("TRANSCRIBE_MAX_DENOISE_MB", "50"))
        max_denoise_bytes = max_denoise_mb * 1024 * 1024
        file_size_bytes = audio_path.stat().st_size
        # region agent log
        _debug_log(
            "process_entry",
            {
                "audio_path": str(audio_path),
                "clean": clean,
                "language": language,
                "file_size_bytes": file_size_bytes,
                "max_denoise_bytes": max_denoise_bytes,
                "max_denoise_mb": max_denoise_mb,
            },
            "H1",
            "transcribe_tool.py:287",
        )
        # endregion

        # Step 1: Clean audio if requested
        if clean and file_size_bytes > max_denoise_bytes:
            clean = False
            print(
                f"Skipping denoiser: file is {file_size_bytes / (1024 * 1024):.1f} MB "
                f"(limit {max_denoise_mb} MB)."
            )
            # region agent log
            _debug_log(
                "skip_denoise_due_to_size",
                {"file_size_bytes": file_size_bytes, "max_denoise_bytes": max_denoise_bytes},
                "H2",
                "transcribe_tool.py:303",
            )
            # endregion
        # Step 1: Clean audio if requested
        if clean:
            # region agent log
            _debug_log(
                "denoise_start",
                {"file_size_bytes": file_size_bytes},
                "H3",
                "transcribe_tool.py:315",
            )
            # endregion
            cleaned_path = self.cleaner.clean_audio(audio_path)
            result["cleaned_path"] = cleaned_path
            transcribe_path = cleaned_path
            # region agent log
            _debug_log(
                "denoise_done",
                {"cleaned_path": str(cleaned_path)},
                "H3",
                "transcribe_tool.py:322",
            )
            # endregion
        else:
            transcribe_path = audio_path
            # region agent log
            _debug_log(
                "denoise_skipped",
                {"transcribe_path": str(transcribe_path)},
                "H2",
                "transcribe_tool.py:329",
            )
            # endregion

        # Step 2: Transcribe
        transcription = self.transcriber.transcribe(transcribe_path, language=language)
        result["text"] = transcription["text"]
        result["segments"] = transcription["segments"]
        result["language"] = transcription["language"]

        return result

    def get_available_models(self) -> list:
        """Get list of available whisper models."""
        return self.file_handler.get_available_models()

    def cleanup(self):
        """Clean up temporary files."""
        self.cleaner.cleanup()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup temp files."""
        self.cleanup()
        return False
