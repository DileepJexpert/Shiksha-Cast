from abc import ABC, abstractmethod
from pathlib import Path


class TTSProvider(ABC):
    @abstractmethod
    def synthesize(self, text: str, description: str, output_path: Path) -> float:
        """Synthesize speech from text.

        Returns the duration of the generated audio in seconds.
        """
        ...

    @abstractmethod
    def name(self) -> str:
        ...
