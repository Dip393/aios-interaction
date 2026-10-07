from .stt import (
    BaseSTTProvider,
    STTError,
    STTProvider,
    SpeechToText,
    TextPassthroughSTT,
    TranscriptionResult,
    TranscriptionSegment,
    WAVMetadataSTT,
)

from .tts import (
    BaseTTSProvider,
    FileTTSProvider,
    NullTTSProvider,
    SpeechResult,
    TTSProvider,
    TTSError,
    TextToSpeech,
)

from .manager import (
    VoiceManager,
    VoiceSession,
)


__all__ = [
    # Voice manager
    "VoiceManager",
    "VoiceSession",

    # STT
    "BaseSTTProvider",
    "STTError",
    "STTProvider",
    "SpeechToText",
    "TextPassthroughSTT",
    "TranscriptionResult",
    "TranscriptionSegment",
    "WAVMetadataSTT",

    # TTS
    "BaseTTSProvider",
    "FileTTSProvider",
    "NullTTSProvider",
    "SpeechResult",
    "TTSProvider",
    "TTSError",
    "TextToSpeech",
]