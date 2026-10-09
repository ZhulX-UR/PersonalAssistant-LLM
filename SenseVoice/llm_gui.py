"""Typed conversation exercise, kept separate from microphone capture for now."""

from __future__ import annotations

import sys

from PySide6.QtCore import Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget,
)

from chat_worker import ChatWorker
from llm import DEFAULT_MODEL, DEFAULT_PROMPT, LlmSettings, PROVIDERS, SILICONFLOW_URL, load_key, load_settings, save_key, save_settings


class ChatWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Shimano · LLM 对话测试")
        self.resize(680, 760)
        self.setMinimumSize(560, 640)
        self.history: list[dict[str, str]] = []
        self.worker: ChatWorker | None = None
        saved = load_settings()

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)
        title = QLabel("Shimano · 文字对话测试")
        title.setObjectName("title")
        layout.addWidget(title)
        layout.addWidget(QLabel("先验证模型连接、角色提示词与多轮对话；语音接入下一步进行。"))

        form = QFormLayout()
        form.setSpacing(10)
        self.provider = QComboBox()
        for code, label in PROVIDERS.items():
            self.provider.addItem(label, code)
        self.provider.setCurrentIndex(self.provider.findData(saved.provider))
        self.provider.currentIndexChanged.connect(self.provider_changed)
        form.addRow("供应商", self.provider)

        self.url = QLineEdit(saved.base_url)
        form.addRow("API 地址", self.url)
        self.model = QComboBox()
        self.model.setEditable(True)
        self.model.addItems([DEFAULT_MODEL, "Pro/zai-org/GLM-5.1"])
        self.model.setCurrentText(saved.model)
        form.addRow("模型 ID", self.model)

        self.key_edit = QLineEdit()
        self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_edit.setPlaceholderText("输入后点击保存；已保存密钥不会回显")
        self.key_status = QLabel()
        key_row = QHBoxLayout()
        key_row.addWidget(self.key_edit, 1)
        key_row.addWidget(self.key_status)
        form.addRow("API Key", key_row)

        self.prompt = QPlainTextEdit(saved.system_prompt or DEFAULT_PROMPT)
        self.prompt.setMaximumHeight(100)
        form.addRow("角色提示词", self.prompt)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        self.save_button = QPushButton("保存设置与密钥")
        self.save_button.clicked.connect(self.save)
        self.clear_button = QPushButton("清空当前对话")
        self.clear_button.clicked.connect(self.clear_history)
        buttons.addWidget(self.save_button)
        buttons.addWidget(self.clear_button)
        buttons.addStretch()
        layout.addLayout(buttons)

        self.status = QLabel("就绪 · 对话历史仅保存在本次窗口中")
        self.status.setObjectName("status")
        layout.addWidget(self.status)
        self.transcript = QPlainTextEdit()
        self.transcript.setReadOnly(True)
        self.transcript.setPlaceholderText("模型回复会显示在这里")
        layout.addWidget(self.transcript, 1)
        entry = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("输入一句话，例如：爱莉，你好")
        self.input.returnPressed.connect(self.send)
        self.send_button = QPushButton("发送")
        self.send_button.clicked.connect(self.send)
        entry.addWidget(self.input, 1)
        entry.addWidget(self.send_button)
        layout.addLayout(entry)

        self.setStyleSheet("""
            QWidget { color:#243041; font-size:14px; background:#f6f8fb; }
            QLabel#title { font-size:23px; font-weight:700; }
            QLabel#status { color:#617186; }
            QLineEdit, QComboBox, QPlainTextEdit { background:white; border:1px solid #cfd9e5; border-radius:7px; padding:7px; }
            QPushButton { background:white; border:1px solid #cbd6e2; border-radius:7px; padding:8px 13px; }
            QPushButton:hover { background:#edf4fb; }
            QPushButton:disabled { color:#9daab9; }
            QPushButton#send { background:#2468c5; color:white; border-color:#2468c5; }
        """)
        self.send_button.setObjectName("send")
        self.provider_changed()

    @Slot()
    def provider_changed(self) -> None:
        code = self.provider.currentData()
        self.url.setReadOnly(code == "siliconflow")
        if code == "siliconflow":
            self.url.setText(SILICONFLOW_URL)
        elif self.url.text() == SILICONFLOW_URL:
            self.url.setText("http://localhost:11434/v1")
        self.key_status.setText("已保存" if load_key(code) else "未保存")

    def current_settings(self) -> LlmSettings:
        return LlmSettings(
            provider=self.provider.currentData(), base_url=self.url.text(),
            model=self.model.currentText(), system_prompt=self.prompt.toPlainText(),
        ).validated()

    @Slot()
    def save(self) -> bool:
        try:
            settings = self.current_settings()
            save_settings(settings)
            if self.key_edit.text().strip():
                save_key(settings.provider, self.key_edit.text())
                self.key_edit.clear()
            self.key_status.setText("已保存" if load_key(settings.provider) else "未保存")
            self.status.setText("设置已保存 · 密钥保存在本机 .env.local")
            return True
        except (OSError, ValueError) as error:
            self.status.setText(f"保存失败：{error}")
            return False

    @Slot()
    def clear_history(self) -> None:
        if self.worker is not None:
            return
        self.history.clear()
        self.transcript.clear()
        self.status.setText("当前对话已清空")

    @Slot()
    def send(self) -> None:
        if self.worker is not None:
            return
        message = self.input.text().strip()
        if not message:
            self.status.setText("请先输入消息")
            return
        if not self.save():
            return
        settings = self.current_settings()
        key = load_key(settings.provider)
        if settings.provider == "siliconflow" and not key:
            self.status.setText("请先输入并保存硅基流动 API Key")
            return
        self.worker = ChatWorker(settings, key, list(self.history), message, self)
        self.worker.replied.connect(self.show_reply)
        self.worker.failed.connect(self.show_error)
        self.worker.finished.connect(self.worker_finished)
        self.input.setEnabled(False)
        self.send_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.status.setText("正在等待模型回复…")
        self.worker.start()

    @Slot(str)
    def show_reply(self, reply: str) -> None:
        assert self.worker is not None
        message = self.worker.message
        self.history.extend(({"role": "user", "content": message}, {"role": "assistant", "content": reply}))
        self.history = self.history[-12:]
        self.transcript.appendPlainText(f"你：{message}\n爱莉：{reply}\n")
        self.input.clear()
        self.status.setText("回复完成")

    @Slot(str)
    def show_error(self, error: str) -> None:
        self.status.setText(f"请求失败：{error}")

    @Slot()
    def worker_finished(self) -> None:
        worker = self.worker
        self.worker = None
        if worker is not None:
            worker.deleteLater()
        self.input.setEnabled(True)
        self.send_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.input.setFocus()

    def closeEvent(self, event) -> None:
        if self.worker is not None and self.worker.isRunning():
            self.worker.wait()
        super().closeEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei UI", 10))
    window = ChatWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
