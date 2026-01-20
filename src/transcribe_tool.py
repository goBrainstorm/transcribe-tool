"""
Transcribe tool for processing voice messages.

This module provides audio cleaning and transcription capabilities using:
- audio-denoiser for noise reduction
- pywhispercpp for whisper.cpp transcription
"""

from pathlib import Path
from datetime import datetime
import tempfile
import shutil
import subprocess

import numpy as np
import torch
import torchaudio
from audio_denoiser.AudioDenoiser import AudioDenoiser
from pywhispercpp.model import Model as WhisperModel

from file_handling import FileHandler


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
    """Handles audio transcription using whisper.cpp via pywhispercpp."""

    DEFAULT_MODEL_PATH = Path("models/whisper.cpp")

    def __init__(self, model_path: Path = None):
        """
        Initialize the Transcriber with a whisper model.

        Args:
            model_path: Path to the whisper.cpp model file (.bin).
                       If None, uses ggml-tiny.bin from default location.
        """
        if model_path is None:
            model_path = self.DEFAULT_MODEL_PATH / "ggml-tiny.bin"

        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Whisper model not found: {model_path}")

        self.model_path = model_path
        self.model = WhisperModel(str(model_path))

    def transcribe(self, audio_path: Path, language: str = "en") -> dict:
        """
        Transcribe an audio file.

        Args:
            audio_path: Path to the audio file (should be 16kHz mono WAV).
            language: Language code for transcription (e.g., "en", "de", "es").

        Returns:
            dict with keys:
                - text: The full transcription text
                - segments: List of transcription segments with timestamps
                - language: Detected or specified language

        Raises:
            FileNotFoundError: If audio file doesn't exist.
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Transcribe using pywhispercpp
        segments = self.model.transcribe(
            str(audio_path),
            language=language
        )

        # Extract text from segments
        full_text = " ".join(segment.text.strip() for segment in segments)

        return {
            "text": full_text,
            "segments": [
                {
                    "start": segment.t0 / 100.0,  # Convert to seconds
                    "end": segment.t1 / 100.0,
                    "text": segment.text.strip()
                }
                for segment in segments
            ],
            "language": language
        }


class TranscribeTool:
    """
    Main transcription tool that combines audio cleaning and transcription.

    Provides a complete pipeline from raw audio to saved transcription.
    """

    def __init__(
        self,
        model_name: str = "ggml-tiny.bin",
        model_dir: Path = None,
        temp_dir: Path = None
    ):
        """
        Initialize the TranscribeTool.

        Args:
            model_name: Name of the whisper model file to use.
            model_dir: Directory containing whisper models.
            temp_dir: Directory for temporary cleaned audio files.
        """
        model_dir = model_dir or Path("models/whisper.cpp")
        model_path = model_dir / model_name

        self.cleaner = AudioCleaner(output_dir=temp_dir)
        self.transcriber = Transcriber(model_path=model_path)
        self.file_handler = FileHandler()

    def process(
        self,
        audio_path: Path,
        clean: bool = True,
        language: str = "en",
        save_to_xml: bool = True,
        date: str = None,
        tags: list = None
    ) -> dict:
        """
        Process an audio file through the full transcription pipeline.

        Args:
            audio_path: Path to the input audio file.
            clean: Whether to apply noise reduction before transcription.
            language: Language code for transcription.
            save_to_xml: Whether to save the transcription to the XML output file.
            date: Optional date string for the entry (ISO format).
            tags: Optional list of tags for the entry.

        Returns:
            dict with keys:
                - text: The full transcription text
                - segments: List of transcription segments
                - language: Language used
                - cleaned_path: Path to cleaned audio (if clean=True)
                - saved: Whether entry was saved to XML
        """
        audio_path = Path(audio_path)
        result = {
            "text": "",
            "segments": [],
            "language": language,
            "cleaned_path": None,
            "saved": False
        }

        # Step 1: Clean audio if requested
        if clean:
            cleaned_path = self.cleaner.clean_audio(audio_path)
            result["cleaned_path"] = cleaned_path
            transcribe_path = cleaned_path
        else:
            transcribe_path = audio_path

        # Step 2: Transcribe
        transcription = self.transcriber.transcribe(transcribe_path, language=language)
        result["text"] = transcription["text"]
        result["segments"] = transcription["segments"]
        result["language"] = transcription["language"]

        # Step 3: Save to XML if requested
        if save_to_xml:
            # Ensure output file exists
            if not self.file_handler.OUTPUT_FILE_PATH.exists():
                self.file_handler.create_output_file()

            # Use provided date or generate current timestamp
            entry_date = date or datetime.now().isoformat()

            success = self.file_handler.add_entry(
                transcription=result["text"],
                date=entry_date,
                summary="",  # Summary can be added later (e.g., by LLM)
                tags=tags or [],
                language=language
            )
            result["saved"] = success

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
