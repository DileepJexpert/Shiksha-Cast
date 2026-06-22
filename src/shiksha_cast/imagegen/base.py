from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class ImageProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, output_path: Path, width: int = 1920, height: int = 1080) -> Path:
        ...

    @abstractmethod
    def name(self) -> str:
        ...
