import os
import shutil
import sys

from PIL import Image, ImageDraw
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QVBoxLayout, QListWidget,
                               QListWidgetItem, QLabel, QPushButton, QFrame,
                               QMenu, QInputDialog,
                               QMessageBox, QFileDialog)


class MaskSelectorDialog(QDialog):
    """
    素材库选择器 (读写分离版)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择形状模板")
        self.resize(900, 650)
        self.selected_mask_path = None

        # 🟢 1. 初始化存储路径 (核心修改)
        self._init_storage()

        # 2. 初始化 UI
        self.setup_ui()

        # 3. 加载数据
        self.load_categories()

    def _init_storage(self):
        """
        智能路径管理：
        将只读的程序资源复制到可写的用户文档目录，
        解决打包安装后无法添加/删除素材的问题。
        """
        # A. 确定程序内置资源路径 (只读源)
        if getattr(sys, 'frozen', False):
            # 打包后的 exe 目录
            app_dir = os.path.dirname(sys.executable)
        else:
            # 开发环境根目录
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        built_in_masks = os.path.join(app_dir, "assets", "masks")

        # B. 确定用户数据路径 (可写目标: 我的文档/WordCloudStudio/masks)
        docs_dir = os.path.join(os.path.expanduser("~"), "Documents")
        self.user_masks_dir = os.path.join(docs_dir, "WordCloudStudio", "masks")

        # C. 迁移逻辑
        # 如果用户目录还不存在，说明是第一次运行
        if not os.path.exists(self.user_masks_dir):
            try:
                if os.path.exists(built_in_masks):
                    # 🟢 关键：将内置素材完整克隆到用户目录
                    shutil.copytree(built_in_masks, self.user_masks_dir)
                else:
                    # 如果内置都没有，生成演示素材
                    os.makedirs(self.user_masks_dir)
                    self._ensure_demo_assets(self.user_masks_dir)
            except Exception as e:
                print(f"初始化素材库失败: {e}")
                # 兜底：尝试在当前目录创建
                self.user_masks_dir = os.path.join(app_dir, "user_masks")
                if not os.path.exists(self.user_masks_dir):
                    os.makedirs(self.user_masks_dir)

        # D. 将后续所有操作指向用户目录
        self.base_dir = self.user_masks_dir

    def setup_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #FFFFFF; }
            QListWidget { border: none; outline: none; }

            QListWidget#CategoryList {
                background-color: #F5F5F7; border-right: 1px solid #E5E5E5; min-width: 140px; max-width: 160px; font-size: 14px; color: #333;
            }
            QListWidget#CategoryList::item {
                height: 45px; padding-left: 15px; border-left: 4px solid transparent;
            }
            QListWidget#CategoryList::item:selected {
                background-color: #FFFFFF; color: #007AFF; border-left: 4px solid #007AFF; font-weight: bold;
            }
            QListWidget#CategoryList::item:hover { background-color: #EAEAEA; }

            QListWidget#IconGrid { background-color: #FFFFFF; padding: 15px; color: #333; }
            QListWidget#IconGrid::item {
                border: 1px solid #F0F0F0; border-radius: 8px; margin: 8px; background-color: #FAFAFA; color: #333;
            }
            QListWidget#IconGrid::item:selected {
                background-color: #E5F1FB; border: 2px solid #007AFF;
            }
            QListWidget#IconGrid::item:hover {
                background-color: #F0F8FF; border: 1px solid #007AFF;
            }

            QPushButton { border-radius: 6px; font-size: 13px; min-height: 36px; color: #333; border: 1px solid #D1D1D6; }

            /* 确定按钮 */
            QPushButton#BtnPrimary { 
                background-color: #F5F5F7; 
                color: #000000; 
                border: 1px solid #D1D1D6; 
                font-weight: bold; 
                padding: 0 24px; 
                min-width: 120px;
            }
            QPushButton#BtnPrimary:hover { background-color: #0062CC; }

            QPushButton#BtnNormal { 
                background-color: #F5F5F7; color: #333; border: 1px solid #D1D1D6; padding: 0 15px; 
            }
            QPushButton#BtnNormal:hover { background-color: #E5E5EA; }

            QPushButton#BtnAdd { color: #007AFF; border: 1px dashed #007AFF; background-color: #FFFFFF; border-radius: 6px; min-height: 32px;}
            QPushButton#BtnAdd:hover { background-color: #F0F8FF; }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 顶部
        top_bar = QFrame()
        top_bar.setStyleSheet("border-bottom: 1px solid #E5E5E5; background-color: #FAFAFA;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 10, 20, 10)
        self.lbl_title = QLabel("素材库")
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 16px; color: #333;")
        self.btn_add_mask = QPushButton("+ 上传素材")
        self.btn_add_mask.setObjectName("BtnAdd")
        self.btn_add_mask.setCursor(Qt.PointingHandCursor)
        self.btn_add_mask.clicked.connect(self.upload_mask_to_category)
        top_layout.addWidget(self.lbl_title)
        top_layout.addStretch()
        top_layout.addWidget(self.btn_add_mask)
        main_layout.addWidget(top_bar)

        # 中间
        content_widget = QFrame()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.category_list = QListWidget()
        self.category_list.setObjectName("CategoryList")
        self.category_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.category_list.customContextMenuRequested.connect(self.show_category_menu)
        self.category_list.currentRowChanged.connect(self.on_category_changed)

        self.icon_grid = QListWidget()
        self.icon_grid.setObjectName("IconGrid")
        self.icon_grid.setViewMode(QListWidget.IconMode)
        self.icon_grid.setResizeMode(QListWidget.Adjust)
        self.icon_grid.setIconSize(QSize(100, 100))
        self.icon_grid.setSpacing(12)
        self.icon_grid.setMovement(QListWidget.Static)
        self.icon_grid.setContextMenuPolicy(Qt.CustomContextMenu)
        self.icon_grid.customContextMenuRequested.connect(self.show_icon_menu)
        self.icon_grid.itemDoubleClicked.connect(self.confirm_selection)

        content_layout.addWidget(self.category_list)
        content_layout.addWidget(self.icon_grid, 1)
        main_layout.addWidget(content_widget, 1)

        # 底部
        bottom_bar = QFrame()
        bottom_bar.setMinimumHeight(80)
        bottom_bar.setStyleSheet("border-top: 1px solid #E5E5E5; background-color: #FFFFFF;")
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(20, 15, 20, 15)

        self.lbl_hint = QLabel("提示: 右键可管理分类和素材，双击图片直接选中。")
        self.lbl_hint.setStyleSheet("color: #999; font-size: 12px;")

        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setObjectName("BtnNormal")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_confirm = QPushButton("确定使用")
        self.btn_confirm.setObjectName("BtnPrimary")
        self.btn_confirm.setCursor(Qt.PointingHandCursor)
        self.btn_confirm.clicked.connect(self.confirm_selection)

        bottom_layout.addWidget(self.lbl_hint)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_cancel)
        bottom_layout.addSpacing(10)
        bottom_layout.addWidget(self.btn_confirm)

        main_layout.addWidget(bottom_bar)

    def load_categories(self):
        current_row = self.category_list.currentRow()
        self.category_list.clear()
        # 使用 base_dir (现在是用户文档目录)
        if not os.path.exists(self.base_dir): os.makedirs(self.base_dir)

        categories = [d for d in os.listdir(self.base_dir) if os.path.isdir(os.path.join(self.base_dir, d))]
        categories.sort()

        # 如果用户目录也是空的（极端情况），才生成 demo
        if not categories:
            self._ensure_demo_assets(self.base_dir)
            categories = ["基础图形", "动物", "植物"]

        for cat in categories:
            item = QListWidgetItem(cat)
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.category_list.addItem(item)

        if self.category_list.count() > 0:
            target = current_row if current_row >= 0 and current_row < self.category_list.count() else 0
            self.category_list.setCurrentRow(target)
        else:
            self.icon_grid.clear()

    def on_category_changed(self, row):
        self.icon_grid.clear()
        item = self.category_list.item(row)
        if not item: return

        category = item.text()
        self.current_cat_path = os.path.join(self.base_dir, category)

        if not os.path.exists(self.current_cat_path): return

        images = [f for f in os.listdir(self.current_cat_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        for img_name in images:
            full_path = os.path.join(self.current_cat_path, img_name)
            icon_item = QListWidgetItem()
            icon_item.setIcon(QIcon(full_path))
            icon_item.setText(os.path.splitext(img_name)[0])
            icon_item.setData(Qt.UserRole, full_path)
            icon_item.setTextAlignment(Qt.AlignBottom | Qt.AlignHCenter)
            self.icon_grid.addItem(icon_item)

    def show_category_menu(self, pos):
        menu = QMenu()
        add_action = menu.addAction("➕ 新建分类")
        item = self.category_list.itemAt(pos)
        rename_action = None
        del_action = None
        if item:
            rename_action = menu.addAction(f"✏️ 重命名“{item.text()}”")
            del_action = menu.addAction(f"🗑️ 删除“{item.text()}”")
        action = menu.exec(self.category_list.mapToGlobal(pos))
        if action == add_action:
            self.add_category()
        elif rename_action and action == rename_action:
            self.rename_category(item)
        elif del_action and action == del_action:
            self.delete_category(item)

    def show_icon_menu(self, pos):
        item = self.icon_grid.itemAt(pos)
        if not item: return
        menu = QMenu()
        rename_action = menu.addAction("✏️ 重命名")
        del_action = menu.addAction(f"🗑️ 删除素材")
        action = menu.exec(self.icon_grid.mapToGlobal(pos))
        if action == rename_action:
            self.rename_icon(item)
        elif action == del_action:
            self.delete_icon(item)

    def add_category(self):
        dialog = QInputDialog(self)
        dialog.setWindowTitle("新建分类")
        dialog.setLabelText("请输入分类名称:")
        dialog.setOkButtonText("确定")
        dialog.setCancelButtonText("取消")
        if dialog.exec():
            name = dialog.textValue().strip()
            if name:
                path = os.path.join(self.base_dir, name)
                if not os.path.exists(path):
                    os.makedirs(path)
                    self.load_categories()
                else:
                    self.show_warning("错误", "分类已存在")

    def rename_category(self, item):
        old_name = item.text()
        dialog = QInputDialog(self)
        dialog.setWindowTitle("重命名分类")
        dialog.setLabelText("请输入新名称:")
        dialog.setTextValue(old_name)
        dialog.setOkButtonText("确定")
        dialog.setCancelButtonText("取消")
        if dialog.exec():
            new_name = dialog.textValue().strip()
            if new_name and new_name != old_name:
                old_path = os.path.join(self.base_dir, old_name)
                new_path = os.path.join(self.base_dir, new_name)
                try:
                    os.rename(old_path, new_path)
                    self.load_categories()
                except Exception as e:
                    self.show_warning("错误", f"重命名失败: {e}")

    def delete_category(self, item):
        cat_name = item.text()
        msg = QMessageBox(self)
        msg.setWindowTitle("确认删除")
        msg.setText(f"确定要删除分类“{cat_name}”及其下所有图片吗？")
        msg.setIcon(QMessageBox.Question)
        btn_yes = msg.addButton("删除", QMessageBox.YesRole)
        btn_no = msg.addButton("取消", QMessageBox.NoRole)
        msg.exec()
        if msg.clickedButton() == btn_yes:
            path = os.path.join(self.base_dir, cat_name)
            shutil.rmtree(path)
            self.load_categories()

    def upload_mask_to_category(self):
        item = self.category_list.currentItem()
        if not item:
            self.show_warning("提示", "请先选择一个分类")
            return
        cat_path = os.path.join(self.base_dir, item.text())
        file_paths, _ = QFileDialog.getOpenFileNames(self, "选择图片", "", "Images (*.png *.jpg *.jpeg)")
        if file_paths:
            for src_path in file_paths:
                filename = os.path.basename(src_path)
                dst_path = os.path.join(cat_path, filename)
                shutil.copy(src_path, dst_path)
            self.on_category_changed(self.category_list.currentRow())

    def rename_icon(self, item):
        old_path = item.data(Qt.UserRole)
        old_name = item.text()
        ext = os.path.splitext(old_path)[1]
        dialog = QInputDialog(self)
        dialog.setWindowTitle("重命名素材")
        dialog.setLabelText("请输入新名称:")
        dialog.setTextValue(old_name)
        dialog.setOkButtonText("确定")
        dialog.setCancelButtonText("取消")
        if dialog.exec():
            new_name = dialog.textValue().strip()
            if new_name and new_name != old_name:
                new_filename = new_name + ext
                new_path = os.path.join(os.path.dirname(old_path), new_filename)
                try:
                    os.rename(old_path, new_path)
                    self.on_category_changed(self.category_list.currentRow())
                except Exception as e:
                    self.show_warning("错误", f"重命名失败: {e}")

    def delete_icon(self, item):
        path = item.data(Qt.UserRole)
        msg = QMessageBox(self)
        msg.setWindowTitle("确认删除")
        msg.setText("确定要删除这张素材吗？")
        msg.setIcon(QMessageBox.Question)
        btn_yes = msg.addButton("删除", QMessageBox.YesRole)
        btn_no = msg.addButton("取消", QMessageBox.NoRole)
        msg.exec()
        if msg.clickedButton() == btn_yes:
            os.remove(path)
            self.on_category_changed(self.category_list.currentRow())

    def show_warning(self, title, text):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(QMessageBox.Warning)
        msg.addButton("确定", QMessageBox.AcceptRole)
        msg.exec()

    def confirm_selection(self):
        selected_items = self.icon_grid.selectedItems()
        if not selected_items: return
        self.selected_mask_path = selected_items[0].data(Qt.UserRole)
        self.accept()

    def _ensure_demo_assets(self, target_dir):
        """生成默认素材"""
        if os.path.exists(os.path.join(target_dir, "基础图形")): return
        demo_data = {
            "基础图形": ["圆形", "正方形", "心形"],
            "动物": ["猫", "狗", "兔子"]
        }
        for cat, shapes in demo_data.items():
            cat_dir = os.path.join(target_dir, cat)
            os.makedirs(cat_dir, exist_ok=True)
            for shape_name in shapes:
                img = Image.new('RGBA', (400, 400), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                if shape_name == "圆形":
                    draw.ellipse((50, 50, 350, 350), fill=(0, 0, 0))
                elif shape_name == "正方形":
                    draw.rectangle((50, 50, 350, 350), fill=(0, 0, 0))
                else:
                    draw.ellipse((50, 100, 250, 300), fill=(0, 0, 0))
                img.save(os.path.join(cat_dir, f"{shape_name}.png"))