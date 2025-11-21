from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QPlainTextEdit)


class WordEditorDialog(QDialog):
    """
    大屏文本编辑器对话框
    """

    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(500, 600)
        self.result_text = content

        # 应用样式
        self.setStyleSheet("""
            QDialog { background-color: #FFFFFF; }
            QLabel { font-weight: bold; font-size: 14px; color: #333; }
            QPlainTextEdit {
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                padding: 10px;
                font-family: "Consolas", "Monaco", monospace;
                font-size: 13px;
                background-color: #FAFAFA;
                selection-background-color: #007AFF;
            }
            QPlainTextEdit:focus { border: 1px solid #007AFF; background-color: #FFF; }

            QPushButton {
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: 500;
            }
            QPushButton#BtnCancel {
                background-color: #F5F5F7;
                color: #333;
                border: 1px solid #D1D1D6;
            }
            QPushButton#BtnCancel:hover { background-color: #E5E5EA; }

            QPushButton#BtnSave {
                background-color: #007AFF;
                color: white;
                border: none;
            }
            QPushButton#BtnSave:hover { background-color: #0062CC; }

            QPushButton#BtnClear {
                color: #FF3B30;
                background: transparent;
                border: none;
            }
            QPushButton#BtnClear:hover { text-decoration: underline; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 顶部标题栏
        top_layout = QHBoxLayout()
        self.lbl_title = QLabel(title)
        self.btn_clear = QPushButton("清空内容")
        self.btn_clear.setObjectName("BtnClear")
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.clicked.connect(self.clear_content)

        top_layout.addWidget(self.lbl_title)
        top_layout.addStretch()
        top_layout.addWidget(self.btn_clear)

        # 文本编辑区
        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlainText(content)
        self.text_edit.setPlaceholderText("请输入词语，每行一个...")

        # 底部按钮栏
        btn_layout = QHBoxLayout()
        self.lbl_count = QLabel("行数: 0")
        self.lbl_count.setStyleSheet("color: #888; font-weight: normal; font-size: 12px;")

        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setObjectName("BtnCancel")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("保存修改")
        self.btn_save.setObjectName("BtnSave")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.clicked.connect(self.save_content)

        btn_layout.addWidget(self.lbl_count)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(top_layout)
        layout.addWidget(self.text_edit)
        layout.addLayout(btn_layout)

        # 连接文本变化信号以更新行数
        self.text_edit.textChanged.connect(self.update_count)
        self.update_count()

    def update_count(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            count = 0
        else:
            count = len([line for line in text.split('\n') if line.strip()])
        self.lbl_count.setText(f"当前词数: {count}")

    def clear_content(self):
        self.text_edit.clear()
        self.text_edit.setFocus()

    def save_content(self):
        self.result_text = self.text_edit.toPlainText()
        self.accept()

    def get_text(self):
        return self.result_text