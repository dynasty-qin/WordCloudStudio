from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
                               QPushButton, QInputDialog, QMessageBox, QLabel)
from PySide6.QtCore import Qt


class ProfileManagerDialog(QDialog):
    """
    配置方案管理器
    """

    def __init__(self, profiles, current_profile, parent=None):
        super().__init__(parent)
        self.setWindowTitle("管理配置方案")
        self.resize(400, 500)
        self.profiles = profiles  # 字典引用
        self.current_profile = current_profile

        # 样式
        self.setStyleSheet("""
            QDialog { background-color: #FFFFFF; }
            QListWidget {
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                padding: 5px;
                font-size: 14px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #F0F0F0;
            }
            QListWidget::item:selected {
                background-color: #E5F1FB;
                color: #007AFF;
                border-radius: 4px;
            }
            QPushButton {
                border-radius: 6px;
                padding: 6px 12px;
                background-color: #F5F5F7;
                border: 1px solid #D1D1D6;
            }
            QPushButton:hover { background-color: #E5E5EA; }
            QPushButton#BtnPrimary {
                background-color: #007AFF;
                color: white;
                border: none;
            }
            QPushButton#BtnPrimary:hover { background-color: #0062CC; }
            QPushButton#BtnDanger {
                color: #FF3B30;
                background-color: white;
                border: 1px solid #FF3B30;
            }
            QPushButton#BtnDanger:hover { background-color: #FFF0F0; }
        """)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("已保存的方案列表:"))

        self.list_widget = QListWidget()
        self.refresh_list()
        layout.addWidget(self.list_widget)

        # 按钮组
        btn_layout = QHBoxLayout()

        self.btn_add = QPushButton("➕ 新建")
        self.btn_add.clicked.connect(self.add_profile)

        self.btn_rename = QPushButton("✏️ 重命名")
        self.btn_rename.clicked.connect(self.rename_profile)

        self.btn_delete = QPushButton("🗑️ 删除")
        self.btn_delete.setObjectName("BtnDanger")
        self.btn_delete.clicked.connect(self.delete_profile)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_rename)
        btn_layout.addWidget(self.btn_delete)

        layout.addLayout(btn_layout)

        self.btn_close = QPushButton("完成")
        self.btn_close.setObjectName("BtnPrimary")
        self.btn_close.clicked.connect(self.accept)
        layout.addWidget(self.btn_close)

    def refresh_list(self):
        self.list_widget.clear()
        for name in self.profiles.keys():
            self.list_widget.addItem(name)
        # 选中当前
        items = self.list_widget.findItems(self.current_profile, Qt.MatchExactly)
        if items:
            self.list_widget.setCurrentItem(items[0])

    def add_profile(self):
        name, ok = QInputDialog.getText(self, "新建方案", "请输入方案名称:")
        if ok and name:
            name = name.strip()
            if name in self.profiles:
                QMessageBox.warning(self, "错误", "该方案名称已存在")
                return
            # 继承当前默认设置
            self.profiles[name] = {
                "custom_dict": "",
                "stop_words": ""
            }
            self.current_profile = name
            self.refresh_list()

    def rename_profile(self):
        item = self.list_widget.currentItem()
        if not item: return
        old_name = item.text()
        if old_name == "默认配置":
            QMessageBox.warning(self, "提示", "“默认配置”不能重命名")
            return

        new_name, ok = QInputDialog.getText(self, "重命名", "请输入新名称:", text=old_name)
        if ok and new_name:
            new_name = new_name.strip()
            if new_name == old_name: return
            if new_name in self.profiles:
                QMessageBox.warning(self, "错误", "该名称已存在")
                return

            # 迁移数据
            self.profiles[new_name] = self.profiles.pop(old_name)
            if self.current_profile == old_name:
                self.current_profile = new_name
            self.refresh_list()

    def delete_profile(self):
        item = self.list_widget.currentItem()
        if not item: return
        name = item.text()

        if name == "默认配置":
            QMessageBox.warning(self, "提示", "“默认配置”不能删除")
            return

        ret = QMessageBox.question(self, "确认删除", f"确定要删除方案“{name}”吗？\n此操作不可恢复。",
                                   QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            del self.profiles[name]
            self.current_profile = "默认配置"  # 回滚到默认
            self.refresh_list()