from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .stt import (
    STTProvider,
    SpeechToText,
    TranscriptionResult,
)

from .tts import (
    SpeechResult,
    TTSProvider,
    TextToSpeech,
)


@dataclass
class VoiceSession:
    """
    Represents the current voice interaction state.
    """

    session_id: str

    language: str | None = None

    listening: bool = False
    speaking: bool = False

    last_transcription: TranscriptionResult | None = None
    last_speech: SpeechResult | None = None

    created_at: float = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "language": self.language,
            "listening": self.listening,
            "speaking": self.speaking,
            "last_transcription": (
                self.last_transcription.to_dict()
                if self.last_transcription
                else None
            ),
            "last_speech": (
                self.last_speech.to_dict()
                if self.last_speech
                else None
            ),
            "created_at": self.created_at,
        }


class VoiceManager:
    """
    Unified AIOS voice subsystem.

    Pipeline:

        Audio
          ↓
        STT
          ↓
        Text
          ↓
        AIOS Kernel
          ↓
        Response Text
          ↓
        TTS
          ↓
        Audio

    The manager itself does not contain business logic.
    """

    def __init__(
        self,
        *,
        stt_provider: STTProvider | None = None,
        tts_provider: TTSProvider | None = None,
        default_language: str = "en",
    ) -> None:
        self.stt = SpeechToText(
            provider=stt_provider,
        )

        self.tts = TextToSpeech(
            provider=tts_provider,
        )

        self.default_language = default_language

        self._sessions: dict[str, VoiceSession] = {}

        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # SESSION
    # ------------------------------------------------------------------

    def create_session(
        self,
        session_id: str,
        *,
        language: str | None = None,
    ) -> VoiceSession:
        session = VoiceSession(
            session_id=session_id,
            language=(
                language
                or self.default_language
            ),
        )

        with self._lock:
            self._sessions[session_id] = session

        return session

    def get_session(
        self,
        session_id: str,
    ) -> VoiceSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def get_or_create_session(
        self,
        session_id: str,
        *,
        language: str | None = None,
    ) -> VoiceSession:
        with self._lock:
            existing = self._sessions.get(
                session_id
            )

            if existing is not None:
                return existing

            return self.create_session(
                session_id,
                language=language,
            )

    def close_session(
        self,
        session_id: str,
    ) -> bool:
        with self._lock:
            return (
                self._sessions.pop(
                    session_id,
                    None,
                )
                is not None
            )

    # ------------------------------------------------------------------
    # STT
    # ------------------------------------------------------------------

    def start_listening(
        self,
        session_id: str,
    ) -> VoiceSession:
        session = self.get_or_create_session(
            session_id
        )

        with self._lock:
            session.listening = True

        return session

    def stop_listening(
        self,
        session_id: str,
    ) -> VoiceSession:
        session = self.get_or_create_session(
            session_id
        )

        with self._lock:
            session.listening = False

        return session

    def transcribe(
        self,
        session_id: str,
        audio: bytes | str | Path,
        *,
        language: str | None = None,
        provider: str | None = None,
    ) -> TranscriptionResult:
        session = self.get_or_create_session(
            session_id,
            language=language,
        )

        session.listening = True

        try:
            result = self.stt.transcribe(
                audio,
                language=(
                    language
                    or session.language
                    or self.default_language
                ),
                provider=provider,
            )

            session.last_transcription = result

            return result

        finally:
            session.listening = False

    # ------------------------------------------------------------------
    # TTS
    # ------------------------------------------------------------------

    def speak(
        self,
        session_id: str,
        text: str,
        *,
        language: str | None = None,
        voice: str | None = None,
        output_path: str | Path | None = None,
        provider: str | None = None,
    ) -> SpeechResult:
        session = self.get_or_create_session(
            session_id,
            language=language,
        )

        session.speaking = True

        try:
            result = self.tts.synthesize(
                text,
                language=(
                    language
                    or session.language
                    or self.default_language
                ),
                voice=voice,
                output_path=output_path,
                provider=provider,
            )

            session.last_speech = result

            return result

        finally:
            session.speaking = False

    # ------------------------------------------------------------------
    # FULL VOICE PIPELINE
    # ------------------------------------------------------------------

    def process_input(
        self,
        session_id: str,
        audio: bytes | str | Path,
        *,
        language: str | None = None,
        stt_provider: str | None = None,
    ) -> TranscriptionResult:
        """
        Convert incoming voice/audio input into text.

        The resulting text can then be passed to Kernel.process().
        """

        return self.transcribe(
            session_id,
            audio,
            language=language,
            provider=stt_provider,
        )

    def respond(
        self,
        session_id: str,
        text: str,
        *,
        language: str | None = None,
        voice: str | None = None,
        output_path: str | Path | None = None,
        tts_provider: str | None = None,
    ) -> SpeechResult:
        """
        Convert AIOS response text into speech.
        """

        return self.speak(
            session_id,
            text,
            language=language,
            voice=voice,
            output_path=output_path,
            provider=tts_provider,
        )

    # ------------------------------------------------------------------
    # PROVIDER MANAGEMENT
    # ------------------------------------------------------------------

    def register_stt_provider(
        self,
        name: str,
        provider: STTProvider,
        *,
        make_active: bool = False,
    ) -> None:
        self.stt.register_provider(
            name,
            provider,
            make_active=make_active,
        )

    def register_tts_provider(
        self,
        name: str,
        provider: TTSProvider,
        *,
        make_active: bool = False,
    ) -> None:
        self.tts.register_provider(
            name,
            provider,
            make_active=make_active,
        )

    def set_stt_provider(
        self,
        name: str,
    ) -> None:
        self.stt.set_active_provider(name)

    def set_tts_provider(
        self,
        name: str,
    ) -> None:
        self.tts.set_active_provider(name)

    # ------------------------------------------------------------------
    # STATUS
    # ------------------------------------------------------------------

    def status(
        self,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            sessions = len(self._sessions)

            session = (
                self._sessions.get(session_id)
                if session_id
                else None
            )

        return {
            "stt": {
                "active_provider": self.stt.active_provider,
                "providers": self.stt.providers(),
            },
            "tts": {
                "active_provider": self.tts.active_provider,
                "providers": self.tts.providers(),
            },
            "default_language": self.default_language,
            "session_count": sessions,
            "session": (
                session.to_dict()
                if session
                else None
            ),
        }

    def clear_sessions(self) -> None:
        with self._lock:
            self._sessions.clear()