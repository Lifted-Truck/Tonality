"""
Audio backend abstractions for the Qt GUI.

These classes are intentionally small so we can swap in a different backend
when targeting other interfaces (e.g., a web client delegating to WebAudio).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Sequence


class AudioBackend(ABC):
    """Interface for playing back notes or voicings."""

    @abstractmethod
    def play_scale(self, midi_notes: Sequence[int], *, velocity: int = 96) -> None:
        """Trigger a scale playback (e.g., arpeggiated) using MIDI note numbers."""

    @abstractmethod
    def play_voicing(self, midi_notes: Sequence[int], *, velocity: int = 96) -> None:
        """Trigger a chord voicing playback."""

    @abstractmethod
    def stop_all(self) -> None:
        """Halt any active playback."""


class NullAudioBackend(AudioBackend):
    """Safe default backend that does nothing (useful for testing)."""

    def play_scale(self, midi_notes: Sequence[int], *, velocity: int = 96) -> None:  # noqa: D401
        pass

    def play_voicing(self, midi_notes: Sequence[int], *, velocity: int = 96) -> None:  # noqa: D401
        pass

    def stop_all(self) -> None:  # noqa: D401
        pass


class QtMultimediaAudioBackend(AudioBackend):
    """
    Placeholder backend using Qt Multimedia.

    The actual implementation will load short samples or synthesize tones via
    `QAudioSink`/`QMediaDevices`.  We defer the heavy lifting to keep the
    scaffolding light until audio requirements solidify.
    """

    def __init__(self) -> None:
        try:
            from PySide6.QtMultimedia import QAudioSink  # type: ignore
            from PySide6.QtCore import QByteArray  # noqa: F401  # type: ignore
        except ImportError as exc:  # pragma: no cover - import guard
            raise ImportError(
                "QtMultimediaAudioBackend requires PySide6 to be installed. "
                "Install the 'tonality[qt]' extra once it is defined."
            ) from exc
        self._sink_class = QAudioSink

    def play_scale(self, midi_notes: Sequence[int], *, velocity: int = 96) -> None:  # noqa: D401
        raise NotImplementedError("Audio playback not implemented yet.")

    def play_voicing(self, midi_notes: Sequence[int], *, velocity: int = 96) -> None:  # noqa: D401
        raise NotImplementedError("Audio playback not implemented yet.")

    def stop_all(self) -> None:  # noqa: D401
        raise NotImplementedError("Audio playback not implemented yet.")


__all__ = ["AudioBackend", "NullAudioBackend", "QtMultimediaAudioBackend"]
