"""Run a single model request without blocking the Qt event loop."""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QWidget

from llm import LlmSettings, chat


class ChatWorker(QThread):
    replied = Signal(str)
    failed = Signal(str)

    def __init__(self, settings: LlmSettings, key: str, history: list[dict[str, str]], message: str, parent: QWidget):
        super().__init__(parent)
        self.settings, self.key, self.history, self.message = settings, key, history, message

    def run(self) -> None:
        try:
            self.replied.emit(chat(self.settings, self.key, self.history, self.message))
        except Exception as error:
            self.failed.emit(str(error))
