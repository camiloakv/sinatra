from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Protocol


@dataclass
class AudioDevice:
    name: str
    index: int
    is_input: bool


class AudioBackend(ABC):
    @abstractmethod
    def list_devices(self) -> list[AudioDevice]:
        pass

    @abstractmethod
    def record(
        self,
        device: AudioDevice | None,
        duration: float | None,
        output_file: str,
        progress_callback: Callable[[float], None] | None = None,
    ) -> None:
        pass