from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from .hand_tracking import (
    HandLandmarks,
    HandSide,
    Point3D,
)


class GestureType(str, Enum):
    NONE = "none"

    OPEN_PALM = "open_palm"
    CLOSED_FIST = "closed_fist"
    POINT = "point"
    PEACE = "peace"
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"

    PINCH = "pinch"
    OK = "ok"

    SWIPE_LEFT = "swipe_left"
    SWIPE_RIGHT = "swipe_right"
    SWIPE_UP = "swipe_up"
    SWIPE_DOWN = "swipe_down"


@dataclass
class GestureEvent:
    """
    A detected gesture.
    """

    gesture: GestureType
    confidence: float

    hand: HandSide = HandSide.UNKNOWN

    timestamp: float = field(
        default_factory=time.time
    )

    metadata: dict = field(
        default_factory=dict
    )

    def to_dict(self) -> dict:
        return {
            "gesture": self.gesture.value,
            "confidence": self.confidence,
            "hand": self.hand.value,
            "timestamp": self.timestamp,
            "metadata": dict(self.metadata),
        }


@dataclass
class GestureThresholds:
    """
    Tunable thresholds for gesture recognition.
    """

    pinch_distance: float = 0.08
    ok_distance: float = 0.08

    swipe_distance: float = 0.18

    finger_extension_ratio: float = 1.15

    minimum_confidence: float = 0.50


def _distance(a: Point3D, b: Point3D) -> float:
    return math.sqrt(
        (a.x - b.x) ** 2
        + (a.y - b.y) ** 2
        + (a.z - b.z) ** 2
    )


def _finger_extended(
    hand: HandLandmarks,
    finger: str,
) -> bool:
    tip = hand.finger_tip(finger)
    pip = hand.finger_pip(finger)
    mcp = hand.finger_mcp(finger)

    wrist = hand.wrist

    tip_distance = _distance(
        tip,
        wrist,
    )

    pip_distance = _distance(
        pip,
        wrist,
    )

    mcp_distance = _distance(
        mcp,
        wrist,
    )

    if pip_distance <= 0.0001:
        return False

    ratio = tip_distance / pip_distance

    return (
        ratio >= 1.15
        and tip_distance > mcp_distance
    )


def _extended_fingers(
    hand: HandLandmarks,
) -> set[str]:
    fingers = {
        "index",
        "middle",
        "ring",
        "pinky",
    }

    return {
        finger
        for finger in fingers
        if _finger_extended(hand, finger)
    }


def detect_basic_gesture(
    hand: HandLandmarks,
    *,
    thresholds: GestureThresholds | None = None,
) -> GestureEvent:
    """
    Detect a basic static gesture from 21 landmarks.
    """

    thresholds = (
        thresholds
        or GestureThresholds()
    )

    confidence = hand.confidence

    if confidence < thresholds.minimum_confidence:
        return GestureEvent(
            gesture=GestureType.NONE,
            confidence=confidence,
            hand=hand.side,
        )

    extended = _extended_fingers(hand)

    thumb_tip = hand.landmarks[4]
    index_tip = hand.landmarks[8]
    middle_tip = hand.landmarks[12]

    pinch_distance = _distance(
        thumb_tip,
        index_tip,
    )

    ok_distance = _distance(
        thumb_tip,
        index_tip,
    )

    # --------------------------------------------------------------
    # PINCH
    # --------------------------------------------------------------

    if pinch_distance <= thresholds.pinch_distance:
        return GestureEvent(
            gesture=GestureType.PINCH,
            confidence=min(
                1.0,
                confidence
                * (
                    1.0
                    - pinch_distance
                    / max(
                        thresholds.pinch_distance,
                        0.0001,
                    )
                ),
            ),
            hand=hand.side,
        )

    # --------------------------------------------------------------
    # OK
    # --------------------------------------------------------------

    middle_extended = (
        "middle" in extended
    )

    ring_extended = (
        "ring" in extended
    )

    pinky_extended = (
        "pinky" in extended
    )

    if (
        ok_distance <= thresholds.ok_distance
        and middle_extended
        and ring_extended
        and pinky_extended
    ):
        return GestureEvent(
            gesture=GestureType.OK,
            confidence=confidence,
            hand=hand.side,
        )

    # --------------------------------------------------------------
    # OPEN PALM
    # --------------------------------------------------------------

    if len(extended) == 4:
        return GestureEvent(
            gesture=GestureType.OPEN_PALM,
            confidence=confidence,
            hand=hand.side,
        )

    # --------------------------------------------------------------
    # PEACE
    # --------------------------------------------------------------

    if (
        "index" in extended
        and "middle" in extended
        and "ring" not in extended
        and "pinky" not in extended
    ):
        return GestureEvent(
            gesture=GestureType.PEACE,
            confidence=confidence,
            hand=hand.side,
        )

    # --------------------------------------------------------------
    # POINT
    # --------------------------------------------------------------

    if (
        "index" in extended
        and "middle" not in extended
        and "ring" not in extended
        and "pinky" not in extended
    ):
        return GestureEvent(
            gesture=GestureType.POINT,
            confidence=confidence,
            hand=hand.side,
        )

    # --------------------------------------------------------------
    # FIST
    # --------------------------------------------------------------

    if len(extended) == 0:
        return GestureEvent(
            gesture=GestureType.CLOSED_FIST,
            confidence=confidence,
            hand=hand.side,
        )

    # --------------------------------------------------------------
    # THUMBS UP / DOWN
    # --------------------------------------------------------------

    thumb = hand.landmarks[4]
    thumb_mcp = hand.landmarks[2]
    wrist = hand.wrist

    thumb_vertical = thumb.y - thumb_mcp.y

    other_fingers_closed = (
        len(extended) == 0
    )

    if other_fingers_closed:
        if thumb_vertical < -0.05:
            return GestureEvent(
                gesture=GestureType.THUMBS_UP,
                confidence=confidence,
                hand=hand.side,
            )

        if thumb_vertical > 0.05:
            return GestureEvent(
                gesture=GestureType.THUMBS_DOWN,
                confidence=confidence,
                hand=hand.side,
            )

    return GestureEvent(
        gesture=GestureType.NONE,
        confidence=confidence,
        hand=hand.side,
    )


class GestureEngine:
    """
    Stateful gesture engine.

    Handles:

    - static gesture detection
    - swipe detection
    - gesture callbacks
    - duplicate suppression
    """

    def __init__(
        self,
        thresholds: GestureThresholds | None = None,
        *,
        debounce_seconds: float = 0.35,
    ) -> None:
        self.thresholds = (
            thresholds
            or GestureThresholds()
        )

        self.debounce_seconds = max(
            0.0,
            debounce_seconds,
        )

        self._previous_positions: dict[
            HandSide,
            tuple[float, float, float],
        ] = {}

        self._last_events: dict[
            tuple[HandSide, GestureType],
            float,
        ] = {}

        self._callbacks: dict[
            GestureType,
            list[Callable[[GestureEvent], None]],
        ] = {}

        self._lock = threading.RLock()

    def detect(
        self,
        hand: HandLandmarks,
    ) -> GestureEvent:
        static_event = detect_basic_gesture(
            hand,
            thresholds=self.thresholds,
        )

        swipe_event = self._detect_swipe(hand)

        if swipe_event.gesture != GestureType.NONE:
            event = swipe_event
        else:
            event = static_event

        if event.gesture != GestureType.NONE:
            self._emit(event)

        return event

    def detect_many(
        self,
        hands: list[HandLandmarks],
    ) -> list[GestureEvent]:
        return [
            event
            for event in (
                self.detect(hand)
                for hand in hands
            )
            if event.gesture != GestureType.NONE
        ]

    def _detect_swipe(
        self,
        hand: HandLandmarks,
    ) -> GestureEvent:
        tip = hand.index_tip

        current = (
            tip.x,
            tip.y,
            tip.z,
        )

        previous = self._previous_positions.get(
            hand.side
        )

        self._previous_positions[
            hand.side
        ] = current

        if previous is None:
            return GestureEvent(
                gesture=GestureType.NONE,
                confidence=hand.confidence,
                hand=hand.side,
            )

        dx = current[0] - previous[0]
        dy = current[1] - previous[1]

        threshold = self.thresholds.swipe_distance

        if abs(dx) >= threshold:
            gesture = (
                GestureType.SWIPE_RIGHT
                if dx > 0
                else GestureType.SWIPE_LEFT
            )

            return GestureEvent(
                gesture=gesture,
                confidence=hand.confidence,
                hand=hand.side,
                metadata={
                    "delta_x": dx,
                    "delta_y": dy,
                },
            )

        if abs(dy) >= threshold:
            gesture = (
                GestureType.SWIPE_DOWN
                if dy > 0
                else GestureType.SWIPE_UP
            )

            return GestureEvent(
                gesture=gesture,
                confidence=hand.confidence,
                hand=hand.side,
                metadata={
                    "delta_x": dx,
                    "delta_y": dy,
                },
            )

        return GestureEvent(
            gesture=GestureType.NONE,
            confidence=hand.confidence,
            hand=hand.side,
        )

    def on(
        self,
        gesture: GestureType,
        callback: Callable[[GestureEvent], None],
    ) -> None:
        with self._lock:
            self._callbacks.setdefault(
                gesture,
                [],
            ).append(callback)

    def off(
        self,
        gesture: GestureType,
        callback: Callable[[GestureEvent], None],
    ) -> bool:
        with self._lock:
            callbacks = self._callbacks.get(
                gesture,
                [],
            )

            if callback not in callbacks:
                return False

            callbacks.remove(callback)

            return True

    def _emit(
        self,
        event: GestureEvent,
    ) -> None:
        now = time.time()

        key = (
            event.hand,
            event.gesture,
        )

        with self._lock:
            last_time = self._last_events.get(
                key
            )

            if (
                last_time is not None
                and now - last_time
                < self.debounce_seconds
            ):
                return

            self._last_events[key] = now

            callbacks = list(
                self._callbacks.get(
                    event.gesture,
                    [],
                )
            )

        for callback in callbacks:
            try:
                callback(event)
            except Exception:
                # A callback must never break the vision pipeline.
                continue

    def reset(self) -> None:
        with self._lock:
            self._previous_positions.clear()
            self._last_events.clear()