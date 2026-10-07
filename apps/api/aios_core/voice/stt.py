from __future__ import annotations

import threading
import time
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


class STTError(Exception):
    """Base exception for speech-to-text errors."""


class STTProvider(Protocol):
    """
    Protocol for speech-to-text providers.

    Any future provider such as Whisper, faster-whisper, Vosk,
    cloud STT, etc. can implement this interface.
    """

    name: str

    def transcribe(
        self,
        audio: bytes | str | Path,
        *,
        language: str | None = None,
    ) -> "TranscriptionResult":
        ...


@dataclass
class TranscriptionSegment:
    """
    A segment of transcribed speech.
    """

    text: str
    start: float = 0.0
    end: float = 0.0
    confidence: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
        }


@dataclass
class TranscriptionResult:
    """
    Standardized STT result returned by AIOS.
    """

    text: str

    language: str | None = None
    confidence: float | None = None

    duration: float | None = None

    provider: str = "unknown"

    segments: list[TranscriptionSegment] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: float = field(
        default_factory=time.time
    )

    @property
    def success(self) -> bool:
        return bool(self.text.strip())

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "language": self.language,
            "confidence": self.confidence,
            "duration": self.duration,
            "provider": self.provider,
            "segments": [
                segment.to_dict()
                for segment in self.segments
            ],
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


class BaseSTTProvider:
    """
    Base class for STT providers.

    Subclass this class when integrating a real speech recognition
    engine.
    """

    name = "base"

    def transcribe(
        self,
        audio: bytes | str | Path,
        *,
        language: str | None = None,
    ) -> TranscriptionResult:
        raise NotImplementedError


class TextPassthroughSTT(BaseSTTProvider):
    """
    Development/testing STT provider.

    If the input is already text, it returns the text as-is.

    This allows the AIOS voice pipeline to be tested before installing
    a real speech recognition engine.
    """

    name = "text-passthrough"

    def transcribe(
        self,
        audio: bytes | str | Path,
        *,
        language: str | None = None,
    ) -> TranscriptionResult:
        if isinstance(audio, Path):
            audio = str(audio)

        if isinstance(audio, str):
            return TranscriptionResult(
                text=audio,
                language=language,
                confidence=1.0,
                provider=self.name,
            )

        if isinstance(audio, bytes):
            try:
                text = audio.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise STTError(
                    "TextPassthroughSTT received non-text bytes."
                ) from exc

            return TranscriptionResult(
                text=text,
                language=language,
                confidence=1.0,
                provider=self.name,
            )

        raise STTError(
            "Unsupported audio input type."
        )


class WAVMetadataSTT(BaseSTTProvider):
    """
    Minimal WAV inspection provider.

    It does not perform speech recognition.

    It is useful for validating that an audio file can be opened
    before passing it to a real STT provider.
    """

    name = "wav-metadata"

    def transcribe(
        self,
        audio: bytes | str | Path,
        *,
        language: str | None = None,
    ) -> TranscriptionResult:
        if isinstance(audio, bytes):
            raise STTError(
                "WAVMetadataSTT currently expects a WAV file path."
            )

        path = Path(audio)

        if not path.exists():
            raise STTError(
                f"Audio file does not exist: {path}"
            )

        if not path.is_file():
            raise STTError(
                f"Audio path is not a file: {path}"
            )

        try:
            with wave.open(str(path), "rb") as wav:
                frames = wav.getnframes()
                rate = wav.getframerate()

                duration = (
                    frames / rate
                    if rate > 0
                    else 0.0
                )

                metadata = {
                    "channels": wav.getnchannels(),
                    "sample_width": wav.getsampwidth(),
                    "sample_rate": rate,
                    "frames": frames,
                }

        except (wave.Error, OSError) as exc:
            raise STTError(
                f"Unable to inspect WAV file: {path}"
            ) from exc

        return TranscriptionResult(
            text="",
            language=language,
            confidence=None,
            duration=duration,
            provider=self.name,
            metadata=metadata,
        )


class SpeechToText:
    """
    Provider manager for speech-to-text.

    Example future providers:

        speech_to_text.register_provider(
            "whisper",
            WhisperProvider(...)
        )

    The active provider can then be selected dynamically.
    """

    def __init__(
        self,
        provider: STTProvider | None = None,
    ) -> None:
        self._providers: dict[str, STTProvider] = {}
        self._active_provider: str | None = None

        self._lock = threading.RLock()

        if provider is not None:
            self.register_provider(
                provider.name,
                provider,
                make_active=True,
            )
        else:
            self.register_provider(
                "text",
                TextPassthroughSTT(),
                make_active=True,
            )

    def register_provider(
        self,
        name: str,
        provider: STTProvider,
        *,
        make_active: bool = False,
    ) -> None:
        if not name.strip():
            raise ValueError(
                "STT provider name cannot be empty."
            )

        with self._lock:
            self._providers[name] = provider

            if (
                make_active
                or self._active_provider is None
            ):
                self._active_provider = name

    def unregister_provider(
        self,
        name: str,
    ) -> bool:
        with self._lock:
            if name not in self._providers:
                return False

            del self._providers[name]

            if self._active_provider == name:
                self._active_provider = (
                    next(
                        iter(self._providers),
                        None,
                    )
                )

            return True

    def set_active_provider(
        self,
        name: str,
    ) -> None:
        with self._lock:
            if name not in self._providers:
                raise STTError(
                    f"Unknown STT provider: {name}"
                )

            self._active_provider = name

    def get_active_provider(self) -> STTProvider:
        with self._lock:
            if self._active_provider is None:
                raise STTError(
                    "No active STT provider."
                )

            provider = self._providers.get(
                self._active_provider
            )

            if provider is None:
                raise STTError(
                    "Active STT provider is unavailable."
                )

            return provider

    def transcribe(
        self,
        audio: bytes | str | Path,
        *,
        language: str | None = None,
        provider: str | None = None,
    ) -> TranscriptionResult:
        selected_provider = (
            self.get_active_provider()
            if provider is None
            else self._get_provider(provider)
        )

        return selected_provider.transcribe(
            audio,
            language=language,
        )

    def _get_provider(
        self,
        name: str,
    ) -> STTProvider:
        with self._lock:
            provider = self._providers.get(name)

            if provider is None:
                raise STTError(
                    f"Unknown STT provider: {name}"
                )

            return provider

    def providers(self) -> list[str]:
        with self._lock:
            return list(self._providers.keys())

    @property
    def active_provider(self) -> str | None:
        with self._lock:
            return self._active_provider