from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable


class HandSide(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Point3D:
    """
    Represents a normalized 3D landmark.

    x/y are normally expected to be in the range [0, 1].
    z is relative depth and depends on the tracking provider.
    """

    x: float
    y: float
    z: float = 0.0

    def distance_to(self, other: "Point3D") -> float:
        return math.sqrt(
            (self.x - other.x) ** 2
            + (self.y - other.y) ** 2
            + (self.z - other.z) ** 2
        )

    def midpoint(self, other: "Point3D") -> "Point3D":
        return Point3D(
            x=(self.x + other.x) / 2.0,
            y=(self.y + other.y) / 2.0,
            z=(self.z + other.z) / 2.0,
        )

    def to_dict(self) -> dict[str, float]:
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z,
        }


@dataclass
class HandLandmarks:
    """
    Standardized hand landmark representation.

    The expected landmark ordering follows the common
    21-point hand model:

        0  = wrist
        1-4   = thumb
        5-8   = index
        9-12  = middle
        13-16 = ring
        17-20 = pinky
    """

    landmarks: list[Point3D]

    side: HandSide = HandSide.UNKNOWN
    confidence: float = 1.0

    timestamp: float = field(
        default_factory=time.time
    )

    handedness_score: float | None = None

    def __post_init__(self) -> None:
        if len(self.landmarks) != 21:
            raise ValueError(
                "A hand must contain exactly 21 landmarks."
            )

        self.confidence = max(
            0.0,
            min(1.0, self.confidence),
        )

    @property
    def wrist(self) -> Point3D:
        return self.landmarks[0]

    @property
    def thumb(self) -> list[Point3D]:
        return self.landmarks[1:5]

    @property
    def index(self) -> list[Point3D]:
        return self.landmarks[5:9]

    @property
    def middle(self) -> list[Point3D]:
        return self.landmarks[9:13]

    @property
    def ring(self) -> list[Point3D]:
        return self.landmarks[13:17]

    @property
    def pinky(self) -> list[Point3D]:
        return self.landmarks[17:21]

    def finger_tip(self, finger: str) -> Point3D:
        tips = {
            "thumb": 4,
            "index": 8,
            "middle": 12,
            "ring": 16,
            "pinky": 20,
        }

        index = tips.get(finger.lower())

        if index is None:
            raise ValueError(
                f"Unknown finger: {finger}"
            )

        return self.landmarks[index]

    def finger_pip(self, finger: str) -> Point3D:
        pips = {
            "thumb": 3,
            "index": 6,
            "middle": 10,
            "ring": 14,
            "pinky": 18,
        }

        index = pips.get(finger.lower())

        if index is None:
            raise ValueError(
                f"Unknown finger: {finger}"
            )

        return self.landmarks[index]

    def finger_mcp(self, finger: str) -> Point3D:
        mcps = {
            "thumb": 2,
            "index": 5,
            "middle": 9,
            "ring": 13,
            "pinky": 17,
        }

        index = mcps.get(finger.lower())

        if index is None:
            raise ValueError(
                f"Unknown finger: {finger}"
            )

        return self.landmarks[index]

    def to_dict(self) -> dict[str, Any]:
        return {
            "side": self.side.value,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "handedness_score": self.handedness_score,
            "landmarks": [
                point.to_dict()
                for point in self.landmarks
            ],
        }


@dataclass
class HandTrackingResult:
    """
    Result returned by a hand tracking provider.
    """

    hands: list[HandLandmarks] = field(
        default_factory=list
    )

    frame_id: int | None = None
    timestamp: float = field(
        default_factory=time.time
    )

    frame_width: int | None = None
    frame_height: int | None = None

    provider: str = "unknown"

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def hand_count(self) -> int:
        return len(self.hands)

    @property
    def has_hands(self) -> bool:
        return bool(self.hands)

    def get_hand(
        self,
        side: HandSide,
    ) -> HandLandmarks | None:
        for hand in self.hands:
            if hand.side == side:
                return hand

        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "frame_width": self.frame_width,
            "frame_height": self.frame_height,
            "provider": self.provider,
            "hand_count": self.hand_count,
            "hands": [
                hand.to_dict()
                for hand in self.hands
            ],
            "metadata": dict(self.metadata),
        }


class BaseHandTracker:
    """
    Interface for real hand-tracking engines.

    MediaPipe, OpenCV-based trackers or another vision engine
    can implement this interface.
    """

    name = "base"

    def process(
        self,
        frame: Any,
    ) -> HandTrackingResult:
        raise NotImplementedError


class NullHandTracker(BaseHandTracker):
    """
    Safe default tracker.

    It does not attempt to interpret camera frames.
    """

    name = "null"

    def process(
        self,
        frame: Any,
    ) -> HandTrackingResult:
        return HandTrackingResult(
            hands=[],
            provider=self.name,
            metadata={
                "tracking_available": False,
            },
        )


class LandmarkHandTracker(BaseHandTracker):
    """
    Development tracker accepting already extracted landmarks.

    Expected input:

        [
            {
                "landmarks": [
                    {"x": ..., "y": ..., "z": ...},
                    ...
                ],
                "side": "left",
                "confidence": 0.95
            }
        ]

    This is useful for testing the gesture system without a camera.
    """

    name = "landmark-input"

    def process(
        self,
        frame: Any,
    ) -> HandTrackingResult:
        if frame is None:
            return HandTrackingResult(
                provider=self.name
            )

        if not isinstance(frame, Iterable):
            raise TypeError(
                "Landmark input must be iterable."
            )

        hands: list[HandLandmarks] = []

        for raw_hand in frame:
            if not isinstance(raw_hand, dict):
                continue

            raw_landmarks = raw_hand.get(
                "landmarks",
                [],
            )

            points = [
                Point3D(
                    x=float(point["x"]),
                    y=float(point["y"]),
                    z=float(point.get("z", 0.0)),
                )
                for point in raw_landmarks
            ]

            if len(points) != 21:
                continue

            raw_side = str(
                raw_hand.get(
                    "side",
                    HandSide.UNKNOWN.value,
                )
            ).lower()

            try:
                side = HandSide(raw_side)
            except ValueError:
                side = HandSide.UNKNOWN

            hands.append(
                HandLandmarks(
                    landmarks=points,
                    side=side,
                    confidence=float(
                        raw_hand.get(
                            "confidence",
                            1.0,
                        )
                    ),
                    handedness_score=(
                        float(
                            raw_hand["handedness_score"]
                        )
                        if raw_hand.get(
                            "handedness_score"
                        )
                        is not None
                        else None
                    ),
                )
            )

        return HandTrackingResult(
            hands=hands,
            provider=self.name,
        )


class HandTracker:
    """
    Provider manager for hand tracking.
    """

    def __init__(
        self,
        tracker: BaseHandTracker | None = None,
    ) -> None:
        self._trackers: dict[str, BaseHandTracker] = {}
        self._active_tracker: str | None = None

        self._lock = threading.RLock()

        if tracker is not None:
            self.register_tracker(
                tracker.name,
                tracker,
                make_active=True,
            )
        else:
            self.register_tracker(
                "null",
                NullHandTracker(),
                make_active=True,
            )

    def register_tracker(
        self,
        name: str,
        tracker: BaseHandTracker,
        *,
        make_active: bool = False,
    ) -> None:
        if not name.strip():
            raise ValueError(
                "Tracker name cannot be empty."
            )

        with self._lock:
            self._trackers[name] = tracker

            if (
                make_active
                or self._active_tracker is None
            ):
                self._active_tracker = name

    def unregister_tracker(
        self,
        name: str,
    ) -> bool:
        with self._lock:
            if name not in self._trackers:
                return False

            del self._trackers[name]

            if self._active_tracker == name:
                self._active_tracker = next(
                    iter(self._trackers),
                    None,
                )

            return True

    def set_active_tracker(
        self,
        name: str,
    ) -> None:
        with self._lock:
            if name not in self._trackers:
                raise ValueError(
                    f"Unknown hand tracker: {name}"
                )

            self._active_tracker = name

    def process(
        self,
        frame: Any,
        *,
        tracker: str | None = None,
    ) -> HandTrackingResult:
        with self._lock:
            selected_name = (
                tracker
                or self._active_tracker
            )

            if selected_name is None:
                raise RuntimeError(
                    "No active hand tracker."
                )

            selected = self._trackers.get(
                selected_name
            )

            if selected is None:
                raise RuntimeError(
                    f"Hand tracker unavailable: "
                    f"{selected_name}"
                )

        return selected.process(frame)

    @property
    def active_tracker(self) -> str | None:
        with self._lock:
            return self._active_tracker

    def trackers(self) -> list[str]:
        with self._lock:
            return list(self._trackers.keys())