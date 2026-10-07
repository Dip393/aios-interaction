from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .gesture_engine import (
    GestureEngine,
    GestureEvent,
    GestureThresholds,
    GestureType,
)

from .hand_tracking import (
    BaseHandTracker,
    HandLandmarks,
    HandSide,
    HandTracker,
    HandTrackingResult,
)


@dataclass
class VisionFrameResult:
    """
    Complete result of processing one vision frame.
    """

    tracking: HandTrackingResult

    gestures: list[GestureEvent] = field(
        default_factory=list
    )

    frame_id: int | None = None

    timestamp: float = field(
        default_factory=time.time
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def hand_count(self) -> int:
        return self.tracking.hand_count

    @property
    def has_gesture(self) -> bool:
        return bool(self.gestures)

    def to_dict(self) -> dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "hand_count": self.hand_count,
            "tracking": self.tracking.to_dict(),
            "gestures": [
                gesture.to_dict()
                for gesture in self.gestures
            ],
            "metadata": dict(self.metadata),
        }


@dataclass
class VisionSession:
    """
    State of one AIOS vision session.
    """

    session_id: str

    enabled: bool = True

    last_frame_id: int | None = None
    last_result: VisionFrameResult | None = None

    created_at: float = field(
        default_factory=time.time
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "enabled": self.enabled,
            "last_frame_id": self.last_frame_id,
            "last_result": (
                self.last_result.to_dict()
                if self.last_result
                else None
            ),
            "created_at": self.created_at,
        }


class VisionManager:
    """
    Unified AIOS vision subsystem.

    Pipeline:

        Camera / Frame
              ↓
        Hand Tracker
              ↓
        Hand Landmarks
              ↓
        Gesture Engine
              ↓
        Gesture Event
              ↓
        AIOS Kernel / Action Registry

    The manager deliberately does not directly execute OS actions.
    """

    def __init__(
        self,
        *,
        tracker: BaseHandTracker | None = None,
        thresholds: GestureThresholds | None = None,
    ) -> None:
        self.hand_tracker = HandTracker(
            tracker=tracker,
        )

        self.gesture_engine = GestureEngine(
            thresholds=thresholds,
        )

        self._sessions: dict[
            str,
            VisionSession,
        ] = {}

        self._callbacks: list[
            Callable[[GestureEvent], None]
        ] = []

        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # SESSION
    # ------------------------------------------------------------------

    def create_session(
        self,
        session_id: str,
    ) -> VisionSession:
        session = VisionSession(
            session_id=session_id
        )

        with self._lock:
            self._sessions[session_id] = session

        return session

    def get_session(
        self,
        session_id: str,
    ) -> VisionSession | None:
        with self._lock:
            return self._sessions.get(
                session_id
            )

    def get_or_create_session(
        self,
        session_id: str,
    ) -> VisionSession:
        with self._lock:
            existing = self._sessions.get(
                session_id
            )

            if existing is not None:
                return existing

            return self.create_session(
                session_id
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

    def enable(
        self,
        session_id: str,
    ) -> None:
        session = self.get_or_create_session(
            session_id
        )

        session.enabled = True

    def disable(
        self,
        session_id: str,
    ) -> None:
        session = self.get_or_create_session(
            session_id
        )

        session.enabled = False

    # ------------------------------------------------------------------
    # FRAME PROCESSING
    # ------------------------------------------------------------------

    def process_frame(
        self,
        session_id: str,
        frame: Any,
        *,
        frame_id: int | None = None,
        tracker: str | None = None,
    ) -> VisionFrameResult:
        session = self.get_or_create_session(
            session_id
        )

        if not session.enabled:
            result = VisionFrameResult(
                tracking=HandTrackingResult(
                    provider="disabled"
                ),
                frame_id=frame_id,
                metadata={
                    "vision_enabled": False,
                },
            )

            session.last_result = result
            session.last_frame_id = frame_id

            return result

        tracking = self.hand_tracker.process(
            frame,
            tracker=tracker,
        )

        gestures = self.gesture_engine.detect_many(
            tracking.hands
        )

        result = VisionFrameResult(
            tracking=tracking,
            gestures=gestures,
            frame_id=frame_id,
            metadata={
                "vision_enabled": True,
                "tracker": tracking.provider,
            },
        )

        session.last_result = result
        session.last_frame_id = frame_id

        for gesture in gestures:
            self._emit_gesture(gesture)

        return result

    # ------------------------------------------------------------------
    # GESTURE CALLBACKS
    # ------------------------------------------------------------------

    def on_gesture(
        self,
        callback: Callable[[GestureEvent], None],
    ) -> None:
        with self._lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)

    def off_gesture(
        self,
        callback: Callable[[GestureEvent], None],
    ) -> bool:
        with self._lock:
            if callback not in self._callbacks:
                return False

            self._callbacks.remove(callback)

            return True

    def on_specific_gesture(
        self,
        gesture: GestureType,
        callback: Callable[[GestureEvent], None],
    ) -> None:
        self.gesture_engine.on(
            gesture,
            callback,
        )

    def _emit_gesture(
        self,
        event: GestureEvent,
    ) -> None:
        with self._lock:
            callbacks = list(
                self._callbacks
            )

        for callback in callbacks:
            try:
                callback(event)
            except Exception:
                continue

    # ------------------------------------------------------------------
    # TRACKER MANAGEMENT
    # ------------------------------------------------------------------

    def register_tracker(
        self,
        name: str,
        tracker: BaseHandTracker,
        *,
        make_active: bool = False,
    ) -> None:
        self.hand_tracker.register_tracker(
            name,
            tracker,
            make_active=make_active,
        )

    def set_tracker(
        self,
        name: str,
    ) -> None:
        self.hand_tracker.set_active_tracker(
            name
        )

    # ------------------------------------------------------------------
    # STATE
    # ------------------------------------------------------------------

    def last_result(
        self,
        session_id: str,
    ) -> VisionFrameResult | None:
        session = self.get_session(
            session_id
        )

        if session is None:
            return None

        return session.last_result

    def reset_gestures(self) -> None:
        self.gesture_engine.reset()

    def status(
        self,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            session_count = len(
                self._sessions
            )

            session = (
                self._sessions.get(
                    session_id
                )
                if session_id
                else None
            )

        return {
            "tracker": {
                "active": (
                    self.hand_tracker.active_tracker
                ),
                "available": (
                    self.hand_tracker.trackers()
                ),
            },
            "session_count": session_count,
            "session": (
                session.to_dict()
                if session
                else None
            ),
        }

    def clear_sessions(self) -> None:
        with self._lock:
            self._sessions.clear()

        self.reset_gestures()