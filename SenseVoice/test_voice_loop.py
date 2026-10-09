import os
import threading
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, Signal
from PySide6.QtTextToSpeech import QTextToSpeech
from PySide6.QtWidgets import QApplication

import gui
from wake import ConversationGate


class FakeCapture:
    def __init__(self):
        self.stop_requested = threading.Event()
        self.paused = False

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False


class FakeStream:
    def __init__(self):
        self.stops = 0
        self.starts = 0

    def stop(self):
        self.stops += 1

    def start(self):
        self.starts += 1


class FakeChatWorker(QObject):
    replied = Signal(str)
    failed = Signal(str)
    finished = Signal()
    messages = []

    def __init__(self, _settings, _key, _history, message, _parent):
        super().__init__()
        self.message = message
        self.messages.append(message)

    def start(self):
        self.replied.emit("你好，我在这里。")
        self.finished.emit()


class FakeTts:
    def __init__(self):
        self.spoken = []

    def say(self, text):
        self.spoken.append(text)

    def state(self):
        return QTextToSpeech.State.Speaking

    def stop(self):
        pass


class VoiceLoopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_wake_sends_command_once_and_resumes_capture(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(gui, "SETTINGS", Path(directory) / "settings.json"):
            window = gui.MainWindow()
            window.speak_reply.setChecked(False)
            window.gate = ConversationGate("爱莉", ("爱丽",), 30)
            window.continuous_worker = FakeCapture()
            window.continuous_stream = FakeStream()
            FakeChatWorker.messages.clear()
            try:
                with patch.object(gui, "ChatWorker", FakeChatWorker), patch.object(gui, "load_key", return_value="test-only-key"):
                    window.continuous_result("普通讲话", "zh")
                    self.assertEqual(FakeChatWorker.messages, [])
                    window.continuous_result("爱丽，你好", "zh")
                self.assertEqual(FakeChatWorker.messages, ["你好"])
                self.assertEqual(window.chat_history[-1]["content"], "你好，我在这里。")
                self.assertIn("你：爱莉，你好", window.result_edit.toPlainText())
                self.assertEqual(window.continuous_stream.stops, 1)
                self.assertEqual(window.continuous_stream.starts, 1)
                self.assertFalse(window.continuous_worker.paused)
            finally:
                window.continuous_worker = None
                window.continuous_stream = None
                window.close()

    def test_microphone_resumes_after_speech_finishes(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(gui, "SETTINGS", Path(directory) / "settings.json"):
            window = gui.MainWindow()
            window.tts = FakeTts()
            window.gate = ConversationGate("爱莉", ("爱丽",), 30)
            window.continuous_worker = FakeCapture()
            window.continuous_stream = FakeStream()
            try:
                with patch.object(gui, "ChatWorker", FakeChatWorker), patch.object(gui, "load_key", return_value="test-only-key"):
                    window.continuous_result("爱莉，你好", "zh")
                self.assertEqual(window.tts.spoken, ["你好，我在这里。"])
                self.assertEqual(window.continuous_stream.starts, 0)
                self.assertTrue(window.continuous_worker.paused)
                window.tts_state_changed(QTextToSpeech.State.Ready)
                self.assertEqual(window.continuous_stream.starts, 1)
                self.assertFalse(window.continuous_worker.paused)
            finally:
                window.continuous_worker = None
                window.continuous_stream = None
                window.close()


if __name__ == "__main__":
    unittest.main()
