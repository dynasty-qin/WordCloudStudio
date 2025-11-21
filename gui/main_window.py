import json
import os

from PIL.ImageQt import ImageQt
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QCursor
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QPushButton, QLabel, QFileDialog, QMessageBox,
                               QComboBox, QProgressBar, QTextEdit, QFrame,
                               QStackedWidget, QButtonGroup, QScrollArea, QColorDialog, QMenu, QSizePolicy,
                               QApplication)

from gui.image_viewer import ImageViewer
from gui.loading_view import LoadingView
from gui.mask_selector import MaskSelectorDialog
from gui.profile_manager import ProfileManagerDialog
from gui.stats_viewer import StatsViewer
from gui.word_editor import WordEditorDialog
from gui.workers import WordCloudWorker

DEFAULT_STOP_WORDS = """的
了
在
是
我
有
和
就
不
人
都
一
一个
上
也
很
到
说
要
去
你
会
着
没有
看
好
自己
这"""

APPLE_ULTRA_QSS = """
/* 全局字体 */
QWidget { font-family: "Segoe UI", "Microsoft YaHei", sans-serif; font-size: 13px; color: #1D1D1F; }
QMainWindow { background-color: #F5F5F7; }

QFrame#LeftContainer { background-color: #F5F5F7; border-right: 1px solid #E5E5E5; }
QScrollArea { background-color: transparent; border: none; }
QScrollArea > QWidget { background-color: transparent; }
QScrollArea > QWidget > QWidget { background-color: transparent; }

QFrame#ConfigCard { background-color: #FFFFFF; border: 1px solid #E5E5E5; border-radius: 12px; }
QLabel#CardTitle { font-size: 14px; font-weight: 700; color: #1D1D1F; padding-bottom: 4px; }
QLabel[class="SubLabel"] { font-size: 12px; color: #86868B; margin-top: 6px; margin-bottom: 2px; }

/* 🟢 按钮样式：强制边框和颜色 */
QPushButton { 
    background-color: #FFFFFF; 
    border: 1px solid #D1D1D6; 
    border-radius: 6px; 
    padding: 0 12px; 
    font-weight: 500; 
    color: #333333; 
    min-height: 30px;
}
QPushButton:hover { background-color: #F2F2F7; border-color: #C7C7CC; }
QPushButton:pressed { background-color: #E5E5EA; }

/* 主按钮 (开始生成) */
QPushButton#PrimaryButton { 
    background-color: #FFFFFF; 
    color: #030303; 
    border: 1px solid #FFFFFF; 
    font-size: 15px; 
    font-weight: 600; 
    padding: 0px; 
    border-radius: 8px; 
    min-height: 42px; /* 🟢 确保高度 */
}
QPushButton#PrimaryButton:hover { background-color: #0062CC; border-color: #0062CC; }

/* 禁用状态：深灰底+深灰字 */
QPushButton#PrimaryButton:disabled { 
    background-color: #E5E5E5; 
    color: #888888; 
    border: 1px solid #D1D1D6; 
}

/* 次级按钮 (保存) */
QPushButton#SecondaryButton {
    background-color: #FFFFFF; color: #007AFF; border: 1px solid #007AFF;
    font-size: 14px; font-weight: 600; min-height: 42px; border-radius: 8px;
}
QPushButton#SecondaryButton:hover { background-color: #F0F8FF; border-color: #007AFF; }
QPushButton#SecondaryButton:disabled { background-color: #FAFAFA; color: #CCC; border-color: #E5E5E5; }

QPushButton#DangerButton { color: #FF3B30; border: 1px solid #FF3B30; background-color: transparent; font-weight: bold; }
QPushButton#DangerButton:hover { background-color: #FF3B30; color: #FFFFFF; }

QPushButton.SmallBtn { padding: 2px 8px; font-size: 11px; border-radius: 5px; color: #007AFF; border: 1px solid #E5F0FF; background-color: #F5FAFF; }
QPushButton.SmallBtn:hover { border-color: #007AFF; background-color: #EBF5FF; }

QComboBox { background-color: #F9F9FA; border: 1px solid #E5E5E5; border-radius: 6px; padding: 2px 24px 2px 10px; color: #333333; min-height: 28px; }
QComboBox:hover { background-color: #FFFFFF; border: 1px solid #C7C7CC; }
QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: top right; width: 24px; border: none; }
QComboBox::down-arrow { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid #666; width: 0px; height: 0px; margin-right: 8px; }
QComboBox QAbstractItemView { border: 1px solid #D1D1D6; border-radius: 6px; background-color: #FFFFFF; color: #333333; selection-background-color: #007AFF; selection-color: #FFFFFF; outline: 0px; padding: 4px; }
QComboBox QAbstractItemView::item { height: 24px; padding-left: 8px; border-radius: 4px; }

QTextEdit { background-color: #F9F9FA; border: 1px solid #E5E5E5; border-radius: 6px; padding: 4px; color: #333; }
QTextEdit:focus { background-color: #FFF; border: 1px solid #007AFF; }

QProgressBar { border: none; background-color: #E5E5EA; border-radius: 3px; height: 4px; }
QProgressBar::chunk { background-color: #007AFF; border-radius: 3px; }

QFrame#SegmentContainer { background-color: #EEEEF0; border-radius: 8px; }
QPushButton.SegmentBtn { border: none; border-radius: 6px; background-color: transparent; color: #666; font-weight: 500; margin: 2px; min-height: 28px; }
QPushButton.SegmentBtn:checked { background-color: #FFFFFF; color: #000; border: 1px solid #00000010; border-bottom: 1px solid #CCCCCC; }
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WordCloud Studio - Pro")
        self.resize(1380, 950)
        self.setStyleSheet(APPLE_ULTRA_QSS)

        # Data
        self.current_file = None
        self.generated_image = None
        self.worker = None
        self.current_mask_file = None
        self.current_bg_color = "#FFFFFF"
        self.profiles = {"默认配置": {"custom_dict": "", "stop_words": DEFAULT_STOP_WORDS}}
        self.current_profile_name = "默认配置"
        self.is_loading_profile = False

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.elapsed_seconds = 0

        self.setup_ui()
        self.load_settings()

        # 🟢 强制初始化按钮状态
        self.update_generate_button_state()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        left_container = QFrame()
        left_container.setObjectName("LeftContainer")
        left_container.setFixedWidth(360)
        left_layout_main = QVBoxLayout(left_container)
        left_layout_main.setContentsMargins(0, 0, 0, 0)
        left_layout_main.setSpacing(0)

        # 1. 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        card_layout = QVBoxLayout(scroll_content)
        card_layout.setContentsMargins(15, 20, 15, 20)
        card_layout.setSpacing(15)

        # [Card 1] 文档
        card_file = self.create_card("文档来源")
        l_file = card_file.layout()
        row_file = QHBoxLayout()
        self.lbl_file = QLabel("未选择文件")
        self.lbl_file.setStyleSheet("color: #86868B; font-style: italic;")
        self.lbl_file.setWordWrap(True)
        btn_select = QPushButton("📂 浏览...")
        btn_select.setFixedWidth(80)
        btn_select.setCursor(Qt.PointingHandCursor)
        btn_select.clicked.connect(self.select_file)
        row_file.addWidget(self.lbl_file, 1)
        row_file.addWidget(btn_select)
        l_file.addLayout(row_file)
        card_layout.addWidget(card_file)

        # [Card 2] 词库
        card_words = self.create_card("词库管理")
        l_words = card_words.layout()
        row_profile = QHBoxLayout()
        row_profile.addWidget(self.create_sub_label("配置方案:"))
        self.combo_profile = QComboBox()
        self.combo_profile.setFixedHeight(30)
        self.combo_profile.currentIndexChanged.connect(self.on_profile_changed)
        btn_profile_mgr = QPushButton("⚙️")
        btn_profile_mgr.setFixedSize(50, 50)
        btn_profile_mgr.clicked.connect(self.open_profile_manager)
        row_profile.addWidget(self.combo_profile, 1)
        row_profile.addWidget(btn_profile_mgr)
        l_words.addLayout(row_profile)
        l_words.addSpacing(4)
        line = QFrame()
        line.setStyleSheet("background-color: #F0F0F0;")
        line.setFixedHeight(1)
        l_words.addWidget(line)
        l_words.addSpacing(4)
        row_d = QHBoxLayout()
        row_d.addWidget(self.create_sub_label("强制保留:"))
        row_d.addStretch()
        btn_edit_dict = QPushButton("编辑")
        btn_edit_dict.setProperty("class", "SmallBtn")
        btn_edit_dict.clicked.connect(self.open_dict_editor)
        row_d.addWidget(btn_edit_dict)
        l_words.addLayout(row_d)
        self.custom_dict_input = QTextEdit()
        self.custom_dict_input.setPlaceholderText("专有名词...")
        self.custom_dict_input.setFixedHeight(32)
        l_words.addWidget(self.custom_dict_input)
        row_s = QHBoxLayout()
        row_s.addWidget(self.create_sub_label("屏蔽/停用:"))
        row_s.addStretch()
        btn_edit_stop = QPushButton("编辑")
        btn_edit_stop.setProperty("class", "SmallBtn")
        btn_edit_stop.clicked.connect(self.open_stop_editor)
        row_s.addWidget(btn_edit_stop)
        l_words.addLayout(row_s)
        self.stop_words_input = QTextEdit()
        self.stop_words_input.setPlaceholderText("无效词...")
        self.stop_words_input.setFixedHeight(32)
        l_words.addWidget(self.stop_words_input)
        card_layout.addWidget(card_words)

        # [Card 3] 设置
        card_settings = self.create_card("生成设置")
        grid_container = QWidget()
        l_settings = QGridLayout(grid_container)
        l_settings.setContentsMargins(1, 1, 1, 1)
        l_settings.setVerticalSpacing(10)
        l_settings.setHorizontalSpacing(10)

        l_settings.addWidget(self.create_sub_label("提取模式:"), 0, 0)
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["默认 (All)", "仅人名", "仅地名", "人名+地名"])
        self.combo_mode.setFixedHeight(28)
        l_settings.addWidget(self.combo_mode, 1, 0)

        l_settings.addWidget(self.create_sub_label("最大词数:"), 0, 1)
        self.combo_max_words = QComboBox()
        self.combo_max_words.addItems(["200", "500", "1000", "2000", "5000", "10000", "20000"])
        self.combo_max_words.setCurrentIndex(2)
        self.combo_max_words.setFixedHeight(28)
        l_settings.addWidget(self.combo_max_words, 1, 1)

        l_settings.addWidget(self.create_sub_label("画质:"), 2, 0)
        self.combo_res = QComboBox()
        self.combo_res.addItems(["自动", "1080P", "2K", "4K", "8K"])
        self.combo_res.setFixedHeight(28)
        l_settings.addWidget(self.combo_res, 3, 0)

        l_settings.addWidget(self.create_sub_label("背景颜色:"), 2, 1)
        bg_widget = QWidget()
        bg_layout = QHBoxLayout(bg_widget)
        bg_layout.setContentsMargins(0, 0, 0, 0)
        self.lbl_color_preview = QLabel()
        self.lbl_color_preview.setFixedSize(18, 18)
        self.lbl_color_preview.setStyleSheet(
            f"background-color: {self.current_bg_color}; border: 1px solid #CCC; border-radius: 9px;")
        btn_bg = QPushButton("选择")
        btn_bg.setProperty("class", "SmallBtn")
        btn_bg.clicked.connect(self.pick_bg_color)
        bg_layout.addWidget(self.lbl_color_preview)
        bg_layout.addWidget(btn_bg)
        l_settings.addWidget(bg_widget, 3, 1)

        l_settings.addWidget(self.create_sub_label("形状蒙版:"), 4, 0, 1, 2)
        mask_row = QHBoxLayout()
        self.lbl_mask_preview = QLabel("无")
        self.lbl_mask_preview.setFixedSize(60, 60)
        self.lbl_mask_preview.setAlignment(Qt.AlignCenter)
        self.lbl_mask_preview.setStyleSheet(
            "border: 1px dashed #D1D1D6; border-radius: 8px; color: #AAA; font-size: 11px; background-color: #F9F9FA;")

        btn_vbox = QVBoxLayout()
        btn_vbox.setSpacing(6)
        self.btn_preset_mask = QPushButton("📚 素材库")
        self.btn_preset_mask.setFixedHeight(29)
        self.btn_preset_mask.setCursor(Qt.PointingHandCursor)
        self.btn_preset_mask.clicked.connect(self.open_mask_selector)

        self.btn_clear_mask = QPushButton("✕ 清除形状")
        self.btn_clear_mask.setObjectName("DangerButton")
        self.btn_clear_mask.setFixedHeight(29)
        self.btn_clear_mask.setCursor(Qt.PointingHandCursor)
        self.btn_clear_mask.clicked.connect(self.clear_mask)

        btn_vbox.addWidget(self.btn_preset_mask)
        btn_vbox.addWidget(self.btn_clear_mask)
        btn_vbox.addStretch()
        mask_row.addWidget(self.lbl_mask_preview)
        mask_row.addLayout(btn_vbox)
        l_settings.addLayout(mask_row, 5, 0, 1, 2)
        card_settings.layout().addWidget(grid_container)
        card_layout.addWidget(card_settings)
        card_layout.addStretch()

        self.scroll_area.setWidget(scroll_content)

        # 2. 底部固定操作区
        bottom_container = QFrame()
        bottom_container.setStyleSheet("background-color: #F5F5F7; border-top: 1px solid #E5E5E5;")
        bottom_container.setMinimumHeight(160)  # 🟢 强制高度
        bottom_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        bottom_layout = QVBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(16, 10, 16, 20)
        bottom_layout.setSpacing(10)

        h_status = QHBoxLayout()
        self.lbl_status = QLabel("就绪")
        self.lbl_status.setStyleSheet("color: #86868B; font-size: 11px;")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(4)
        h_status.addWidget(self.lbl_status)
        h_status.addStretch()

        bottom_layout.addLayout(h_status)
        bottom_layout.addWidget(self.progress_bar)

        self.btn_generate = QPushButton("开始生成")
        self.btn_generate.setObjectName("PrimaryButton")  # 🟢 使用修复后的 QSS
        self.btn_generate.setCursor(Qt.PointingHandCursor)
        self.btn_generate.clicked.connect(self.start_generation)
        self.btn_generate.setEnabled(False)

        self.btn_save = QPushButton("保存结果")
        self.btn_save.setObjectName("SecondaryButton")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.clicked.connect(self.save_image)
        self.btn_save.setEnabled(False)

        bottom_layout.addWidget(self.btn_generate)
        bottom_layout.addWidget(self.btn_save)

        left_layout_main.addWidget(self.scroll_area, 1)
        left_layout_main.addWidget(bottom_container, 0)

        # ===========================
        # 右侧容器
        # ===========================
        self.right_frame = QFrame()
        self.right_frame.setObjectName("RightPanel")
        right_layout = QVBoxLayout(self.right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        top_bar = QWidget()
        top_bar.setStyleSheet("background-color: #FFFFFF; border-bottom: 1px solid #E5E5E5;")
        top_bar.setFixedHeight(50)
        tb_layout = QHBoxLayout(top_bar)
        tb_layout.setContentsMargins(20, 5, 20, 5)

        self.view_group = QButtonGroup(self)
        segment_container = QFrame()
        segment_container.setObjectName("SegmentContainer")
        segment_container.setFixedSize(200, 36)
        seg_layout = QHBoxLayout(segment_container)
        seg_layout.setContentsMargins(3, 3, 3, 3)
        seg_layout.setSpacing(0)
        self.btn_view_cloud = QPushButton("词云图")
        self.btn_view_cloud.setCheckable(True)
        self.btn_view_cloud.setChecked(True)
        self.btn_view_cloud.setProperty("class", "SegmentBtn")
        self.btn_view_stats = QPushButton("数据表")
        self.btn_view_stats.setCheckable(True)
        self.btn_view_stats.setProperty("class", "SegmentBtn")
        self.view_group.addButton(self.btn_view_cloud, 0)
        self.view_group.addButton(self.btn_view_stats, 1)
        self.view_group.idClicked.connect(self.switch_view)
        seg_layout.addWidget(self.btn_view_cloud)
        seg_layout.addWidget(self.btn_view_stats)
        tb_layout.addWidget(segment_container)
        tb_layout.addStretch()
        self.lbl_perf = QLabel("")
        self.lbl_perf.setStyleSheet("color: #007AFF; font-family: monospace; font-weight: 600; font-size: 12px;")
        tb_layout.addWidget(self.lbl_perf)
        right_layout.addWidget(top_bar)

        self.stack = QStackedWidget()
        self.image_viewer = ImageViewer()
        self.stats_viewer = StatsViewer()
        self.loading_view = LoadingView()

        # 🟢 修复：正确连接信号
        self.stats_viewer.stop_word_added.connect(self.add_stop_word)
        self.stats_viewer.stop_word_removed.connect(self.remove_stop_word)
        self.stats_viewer.batch_action_signal.connect(self.handle_batch_action)

        self.stack.addWidget(self.image_viewer)
        self.stack.addWidget(self.stats_viewer)
        self.stack.addWidget(self.loading_view)
        right_layout.addWidget(self.stack)

        main_layout.addWidget(left_container)
        main_layout.addWidget(self.right_frame)

    def create_card(self, title):
        frame = QFrame()
        frame.setObjectName("ConfigCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(6)
        lbl = QLabel(title)
        lbl.setObjectName("CardTitle")
        layout.addWidget(lbl)
        return frame

    def create_sub_label(self, text):
        lbl = QLabel(text)
        lbl.setProperty("class", "SubLabel")
        return lbl

    def update_generate_button_state(self):
        if self.current_file:
            self.btn_generate.setEnabled(True)
        else:
            self.btn_generate.setEnabled(False)

    def switch_view(self, id):
        if self.worker and self.worker.isRunning():
            self.stack.setCurrentIndex(2)
        else:
            self.stack.setCurrentIndex(id)

    def open_mask_selector(self):
        dialog = MaskSelectorDialog(self)
        if dialog.exec():
            path = dialog.selected_mask_path
            if path and os.path.exists(path):
                self.current_mask_file = path
                pixmap = QPixmap(path)
                self.lbl_mask_preview.setPixmap(pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.lbl_mask_preview.setText("")
                # self.current_bg_color = "#FFFFFF"
                # self.lbl_color_preview.setStyleSheet(
                #     f"background-color: {self.current_bg_color}; border: 1px solid #CCC; border-radius: 9px;")

    def start_generation(self):
        if not self.current_file: return
        self.save_settings()

        self.btn_generate.setEnabled(False)
        self.btn_generate.setText("生成中...")
        self.progress_bar.setVisible(True)
        self.stack.setCurrentIndex(2)
        self.loading_view.start_loading()
        self.lbl_perf.setText("")

        bg_color = self.current_bg_color
        custom_dict = [line.strip() for line in self.custom_dict_input.toPlainText().split('\n') if line.strip()]
        stop_words = [line.strip() for line in self.stop_words_input.toPlainText().split('\n') if line.strip()]
        res_text = self.combo_res.currentText()
        res_setting = "auto" if "自动" in res_text else res_text.split(' ')[0]
        max_words = int(self.combo_max_words.currentText().split(' ')[0])
        mode_text = self.combo_mode.currentText()
        if "人名" in mode_text and "地名" in mode_text:
            filter_type = "name_location"
        elif "人名" in mode_text:
            filter_type = "name"
        elif "地名" in mode_text:
            filter_type = "location"
        else:
            filter_type = "all"

        self.worker = WordCloudWorker(
            file_path=self.current_file,
            bg_color=bg_color,
            mask_path=self.current_mask_file,
            custom_dict=custom_dict,
            stop_words=stop_words,
            resolution_setting=res_setting,
            max_words=max_words,
            filter_type=filter_type
        )
        self.worker.progress_step.connect(self.loading_view.update_step)
        self.worker.finished.connect(self.on_generation_finished)
        self.worker.error.connect(self.on_generation_error)
        self.worker.start()

    def on_generation_finished(self, pil_image, stats_data, timings):
        self.btn_generate.setEnabled(True)
        self.btn_generate.setText("开始生成")
        self.btn_save.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.loading_view.stop_loading()
        perf_text = f"耗时: {timings['total']:.1f}s"
        self.lbl_perf.setText(perf_text)
        self.generated_image = pil_image
        QApplication.processEvents()
        target_view = 0 if self.view_group.button(0).isChecked() else 1
        self.stack.setCurrentIndex(target_view)
        qim = ImageQt(pil_image)
        pix = QPixmap.fromImage(qim)
        self.image_viewer.set_image(pix)
        current_stop_words = [line.strip() for line in self.stop_words_input.toPlainText().split('\n') if line.strip()]
        self.stats_viewer.set_data(stats_data, blocked_words=current_stop_words)

    def on_generation_error(self, err_msg):
        self.loading_view.stop_loading()
        self.btn_generate.setEnabled(True)
        self.btn_generate.setText("开始生成")
        self.progress_bar.setVisible(False)
        self.switch_view(0)
        msg = QMessageBox(self)
        msg.setWindowTitle("生成失败")
        msg.setText(err_msg)
        msg.setIcon(QMessageBox.Critical)
        msg.addButton("确定", QMessageBox.AcceptRole)
        msg.exec()

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文档", "",
                                                   "Text Files (*.txt *.docx *.pdf);;All Files (*)")
        if file_path:
            self.current_file = file_path
            self.lbl_file.setText(os.path.basename(file_path))
            self.lbl_file.setStyleSheet("color: #007AFF; font-weight: 600;")
            self.btn_generate.setEnabled(True)
            self.lbl_status.setText("文件已加载")
            self.update_generate_button_state()

    def pick_bg_color(self):
        menu = QMenu(self)
        act_color = menu.addAction("🎨 选择颜色...")
        act_trans = menu.addAction("🌫️ 设为透明")
        action = menu.exec(QCursor.pos())
        if action == act_color:
            color = QColorDialog.getColor(initial=self.current_bg_color, parent=self, title="选择背景颜色")
            if color.isValid():
                self.current_bg_color = color.name()
                self.lbl_color_preview.setStyleSheet(
                    f"background-color: {self.current_bg_color}; border: 1px solid #CCC; border-radius: 10px;")
        elif action == act_trans:
            self.current_bg_color = "transparent"
            self.lbl_color_preview.setStyleSheet("""
                background-color: #FFFFFF; border: 1px dashed #999; border-radius: 9px;
                background-image: linear-gradient(45deg, #E0E0E0 25%, transparent 25%, transparent 75%, #E0E0E0 75%, #E0E0E0),
                                  linear-gradient(45deg, #E0E0E0 25%, transparent 25%, transparent 75%, #E0E0E0 75%, #E0E0E0);
                background-size: 6px 6px; background-position: 0 0, 3px 3px;
            """)

    def clear_mask(self):
        self.current_mask_file = None
        self.lbl_mask_preview.clear()
        self.lbl_mask_preview.setText("无")
        self.lbl_mask_preview.setStyleSheet(
            "border: 1px dashed #D1D1D6; border-radius: 8px; color: #AAA; font-size: 11px; background-color: #F9F9FA;")

    def save_image(self):
        if not self.generated_image: return
        save_path, _ = QFileDialog.getSaveFileName(self, "保存图片", "wordcloud.png", "PNG Images (*.png)")
        if save_path:
            self.generated_image.save(save_path)
            msg = QMessageBox(self)
            msg.setWindowTitle("保存成功")
            msg.setText(f"图片已保存至:\n{save_path}")
            msg.setIcon(QMessageBox.Information)
            msg.addButton("确定", QMessageBox.AcceptRole)
            msg.exec()

    def refresh_profile_combo(self):
        self.is_loading_profile = True
        self.combo_profile.clear()
        for name in self.profiles.keys():
            self.combo_profile.addItem(name)
        self.combo_profile.setCurrentText(self.current_profile_name)
        self.is_loading_profile = False

    def on_profile_changed(self, index):
        if self.is_loading_profile: return
        new_profile_name = self.combo_profile.currentText()
        if not new_profile_name: return
        self.save_text_to_profile(self.current_profile_name)
        self.current_profile_name = new_profile_name
        self.load_text_from_profile(new_profile_name)
        self.save_settings()

    def save_text_to_profile(self, profile_name):
        if profile_name in self.profiles:
            self.profiles[profile_name]["custom_dict"] = self.custom_dict_input.toPlainText()
            self.profiles[profile_name]["stop_words"] = self.stop_words_input.toPlainText()

    def load_text_from_profile(self, profile_name):
        if profile_name in self.profiles:
            data = self.profiles[profile_name]
            self.custom_dict_input.setPlainText(data.get("custom_dict", ""))
            self.stop_words_input.setPlainText(data.get("stop_words", ""))

    def open_profile_manager(self):
        self.save_text_to_profile(self.current_profile_name)
        dialog = ProfileManagerDialog(self.profiles, self.current_profile_name, self)
        if dialog.exec():
            self.current_profile_name = dialog.current_profile
            self.refresh_profile_combo()
            self.load_text_from_profile(self.current_profile_name)
            self.save_settings()

    def open_dict_editor(self):
        dialog = WordEditorDialog("编辑强制保留词", self.custom_dict_input.toPlainText(), self)
        if dialog.exec():
            self.custom_dict_input.setPlainText(dialog.get_text())
            self.save_settings()

    def open_stop_editor(self):
        dialog = WordEditorDialog("编辑停用/屏蔽词", self.stop_words_input.toPlainText(), self)
        if dialog.exec():
            self.stop_words_input.setPlainText(dialog.get_text())
            self.save_settings()

    def add_stop_word(self, word):
        self.handle_batch_action([word], True)

    def remove_stop_word(self, word):
        self.handle_batch_action([word], False)

    def handle_batch_action(self, words_list, is_block):
        current_text = self.stop_words_input.toPlainText()
        existing_words = [w.strip() for w in current_text.split('\n') if w.strip()]
        modified = False
        if is_block:
            for w in words_list:
                if w not in existing_words:
                    existing_words.append(w)
                    modified = True
        else:
            for w in words_list:
                if w in existing_words:
                    existing_words.remove(w)
                    modified = True
        if modified:
            self.stop_words_input.setPlainText("\n".join(existing_words))
            self.save_settings()
            if len(words_list) == 1:
                self.lbl_status.setText(f"✅ 已{'屏蔽' if is_block else '恢复'} “{words_list[0]}”")
            else:
                self.lbl_status.setText(f"✅ 批量处理 {len(words_list)} 个词")

    def load_settings(self):
        config_path = "settings.json"
        self.refresh_profile_combo()
        self.load_text_from_profile("默认配置")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                if "bg_color" in config:
                    self.current_bg_color = config["bg_color"]
                    self.lbl_color_preview.setStyleSheet(
                        f"background-color: {self.current_bg_color}; border-radius: 10px; border: 1px solid #CCC;")
                    if self.current_bg_color == "transparent":
                        self.lbl_color_preview.setStyleSheet(
                            "background-color: white; border: 1px dashed #999; border-radius: 9px;")
                if "max_words_index" in config: self.combo_max_words.setCurrentIndex(config["max_words_index"])
                if "res_index" in config: self.combo_res.setCurrentIndex(config["res_index"])
                if "mode_index" in config: self.combo_mode.setCurrentIndex(config["mode_index"])
                if "profiles" in config:
                    self.profiles = config["profiles"]
                    self.current_profile_name = config.get("current_profile_name", "默认配置")
                    if "默认配置" not in self.profiles:
                        self.profiles["默认配置"] = {"custom_dict": "", "stop_words": DEFAULT_STOP_WORDS}
                self.refresh_profile_combo()
                self.load_text_from_profile(self.current_profile_name)
            except:
                pass

    def save_settings(self):
        self.save_text_to_profile(self.current_profile_name)
        config = {
            "bg_color": self.current_bg_color,
            "max_words_index": self.combo_max_words.currentIndex(),
            "res_index": self.combo_res.currentIndex(),
            "mode_index": self.combo_mode.currentIndex(),
            "profiles": self.profiles,
            "current_profile_name": self.current_profile_name
        }
        try:
            with open("settings.json", "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except:
            pass

    def update_timer(self):
        pass

    def update_status(self, msg):
        pass

    def closeEvent(self, event):
        self.save_settings()
        event.accept()