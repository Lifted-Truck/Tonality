"""Display context shared across analyzers and presentation layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class DisplayLayer:
    """Single layer of display preferences (e.g., defaults, session, view)."""

    name: str
    settings: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.settings[key] = value


class DisplayContext:
    """Stacked display preferences resolved from multiple layers."""

    def __init__(self) -> None:
        self._layers: list[DisplayLayer] = [DisplayLayer(name="defaults", settings={
            "spelling": "auto",
            "label_mode": "names",
            "layout_mode": "chromatic",
            "hide_out_of_key": False,
        })]
        self._listeners: list[callable[[str, Any], None]] = []

    # Layer management --------------------------------------------------

    def push_layer(self, layer: DisplayLayer) -> None:
        self._layers.append(layer)
        self._notify("layer_added", layer.name)

    def pop_layer(self, *, name: Optional[str] = None) -> DisplayLayer:
        if len(self._layers) == 1:
            raise RuntimeError("Cannot remove base layer")
        if name is None:
            layer = self._layers.pop()
        else:
            for idx in range(len(self._layers) - 1, -1, -1):
                if self._layers[idx].name == name:
                    layer = self._layers.pop(idx)
                    break
            else:
                raise KeyError(f"Layer {name!r} not found")
        self._notify("layer_removed", layer.name)
        return layer

    # Settings ---------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        for layer in reversed(self._layers):
            if key in layer.settings:
                return layer.settings[key]
        return default

    def set(self, key: str, value: Any, *, layer: str = "session") -> None:
        target = self._ensure_layer(layer)
        target.set(key, value)
        self._notify("setting_changed", {"key": key, "value": value, "layer": layer})

    def _ensure_layer(self, name: str) -> DisplayLayer:
        for layer in self._layers:
            if layer.name == name:
                return layer
        new_layer = DisplayLayer(name=name)
        self._layers.append(new_layer)
        return new_layer

    # Observation ------------------------------------------------------

    def add_listener(self, callback: callable[[str, Any], None]) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback: callable[[str, Any], None]) -> None:
        try:
            self._listeners.remove(callback)
        except ValueError:
            pass

    def _notify(self, event: str, payload: Any) -> None:
        for listener in list(self._listeners):
            listener(event, payload)

    # Serialization ----------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layers": [
                {"name": layer.name, "settings": dict(layer.settings)}
                for layer in self._layers
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DisplayContext":
        ctx = cls()
        ctx._layers.clear()
        for layer_data in data.get("layers", []):
            ctx._layers.append(
                DisplayLayer(name=layer_data.get("name", "layer"), settings=layer_data.get("settings", {}))
            )
        if not ctx._layers:
            ctx._layers.append(DisplayLayer(name="defaults"))
        return ctx


__all__ = ["DisplayContext", "DisplayLayer"]
