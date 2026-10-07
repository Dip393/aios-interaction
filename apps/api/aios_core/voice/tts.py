from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


class TTSError(Exception):
    """Base exception for text-to-speech errors."""


class TTSProvider(Protocol):
    """
    Protocol for text-to-speech providers.
    """

    name: str

    def synthesize(
        self,
        text: str,
        *,
        language: str | None = None,
        voice: str | None = None,
        output_path: str | Path | None = None,
    ) -> "SpeechResult":
        ...


@dataclass
class SpeechResult:
    """
    Standardized TTS result.
    """

    text: str
    provider: str

    language: str | None = None
    voice: str | None = None

    audio_path: str | None = None

    duration: float | None = None

    success: bool = True

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: float = field(
        default_factory=time.time
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "provider": self.provider,
            "language": self.language,
            "voice": self.voice,
            "audio_path": self.audio_path,
            "duration": self.duration,
            "success": self.success,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


class BaseTTSProvider:
    """
    Base class for TTS implementations.
    """

    name = "base"

    def synthesize(
        self,
        text: str,
        *,
        language: str | None = None,
        voice: str | None = None,
        output_path: str | Path | None = None,
    ) -> SpeechResult:
        raise NotImplementedError


class NullTTSProvider(BaseTTSProvider):
    """
    Development-safe TTS provider.

    Does not generate actual audio.

    It validates the text and returns a successful logical
    speech result so the rest of AIOS can be developed independently
    of an audio engine.
    """

    name = "null"

    def synthesize(
        self,
        text: str,
        *,
        language: str | None = None,
        voice: str | None = None,
        output_path: str | Path | None = None,
    ) -> SpeechResult:
        if not isinstance(text, str):
            raise TTSError(
                "TTS text must be a string."
            )

        if not text.strip():
            raise TTSError(
                "Cannot synthesize empty text."
            )

        return SpeechResult(
            text=text,
            provider=self.name,
            language=language,
            voice=voice,
            audio_path=None,
            duration=None,
            success=True,
            metadata={
                "audio_generated": False,
                "reason": "null_provider",
            },
        )


class FileTTSProvider(BaseTTSProvider):
    """
    Minimal local development TTS provider.

    This provider does NOT perform real speech synthesis.

    Instead, it writes the requested text into a UTF-8 text file
    using an .txt extension.

    Useful for testing the complete TTS pipeline without installing
    an audio engine.
    """

    name = "file-text"

    def synthesize(
        self,
        text: str,
        *,
        language: str | None = None,
        voice: str | None = None,
        output_path: str | Path | None = None,
    ) -> SpeechResult:
        if not isinstance(text, str):
            raise TTSError(
                "TTS text must be a string."
            )

        if not text.strip():
            raise TTSError(
                "Cannot synthesize empty text."
            )

        if output_path is None:
            raise TTSError(
                "FileTTSProvider requires output_path."
            )

        path = Path(output_path)

        if path.suffix.lower() != ".txt":
            path = path.with_suffix(".txt")

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        path.write_text(
            text,
            encoding="utf-8",
        )

        return SpeechResult(
            text=text,
            provider=self.name,
            language=language,
            voice=voice,
            audio_path=str(path),
            success=True,
            metadata={
                "audio_generated": False,
                "text_output": True,
            },
        )


class TextToSpeech:
    """
    Provider manager for text-to-speech.
    """

    def __init__(
        self,
        provider: TTSProvider | None = None,
    ) -> None:
        self._providers: dict[str, TTSProvider] = {}
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
                "null",
                NullTTSProvider(),
                make_active=True,
            )

    def register_provider(
        self,
        name: str,
        provider: TTSProvider,
        *,
        make_active: bool = False,
    ) -> None:
        if not name.strip():
            raise ValueError(
                "TTS provider name cannot be empty."
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
                raise TTSError(
                    f"Unknown TTS provider: {name}"
                )

            self._active_provider = name

    def get_active_provider(self) -> TTSProvider:
        with self._lock:
            if self._active_provider is None:
                raise TTSError(
                    "No active TTS provider."
                )

            provider = self._providers.get(
                self._active_provider
            )

            if provider is None:
                raise TTSError(
                    "Active TTS provider is unavailable."
                )

            return provider

    def synthesize(
        self,
        text: str,
        *,
        language: str | None = None,
        voice: str | None = None,
        output_path: str | Path | None = None,
        provider: str | None = None,
    ) -> SpeechResult:
        selected_provider = (
            self.get_active_provider()
            if provider is None
            else self._get_provider(provider)
        )

        return selected_provider.synthesize(
            text,
            language=language,
            voice=voice,
            output_path=output_path,
        )

    def _get_provider(
        self,
        name: str,
    ) -> TTSProvider:
        with self._lock:
            provider = self._providers.get(name)

            if provider is None:
                raise TTSError(
                    f"Unknown TTS provider: {name}"
                )

            return provider

    def providers(self) -> list[str]:
        with self._lock:
            return list(self._providers.keys())

    @property
    def active_provider(self) -> str | None:
        with self._lock:
            return self._active_provider