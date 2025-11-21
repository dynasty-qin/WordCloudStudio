from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout)


class StepItem(QFrame):
    """单个步骤条目"""

    def __init__(self, title, icon, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: transparent;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)

        # 状态图标 (圆点)
        self.status_dot = QLabel("●")
        self.status_dot.setFixedSize(30, 30)
        self.status_dot.setAlignment(Qt.AlignCenter)
        self.status_dot.setStyleSheet("color: #E5E5EA; font-size: 20px;")  # 默认灰色

        # 文本区域
        text_layout = QVBoxLayout()
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #8E8E93;")

        self.lbl_desc = QLabel("等待中...")
        self.lbl_desc.setStyleSheet("font-size: 13px; color: #AEAEB2;")

        text_layout.addWidget(self.lbl_title)
        text_layout.addWidget(self.lbl_desc)

        # 耗时标签
        self.lbl_time = QLabel("")
        self.lbl_time.setStyleSheet("font-family: monospace; color: #007AFF; font-weight: bold;")

        layout.addWidget(self.status_dot)
        layout.addSpacing(10)
        layout.addLayout(text_layout)
        layout.addStretch()
        layout.addWidget(self.lbl_time)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.start_time = 0
        self.is_running = False

    def reset(self, title, desc="等待中..."):
        """重置状态"""
        self.lbl_title.setText(title)
        self.lbl_desc.setText(desc)
        self.lbl_time.setText("")
        self.status_dot.setText("●")
        self.status_dot.setStyleSheet("color: #E5E5EA; font-size: 20px;")
        self.lbl_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #8E8E93;")
        self.lbl_desc.setStyleSheet("font-size: 13px; color: #AEAEB2;")
        self.is_running = False
        self.timer.stop()

    def set_active(self, desc):
        """设置为进行中"""
        self.status_dot.setStyleSheet("color: #007AFF; font-size: 20px;")  # 蓝色
        self.lbl_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #000000;")
        self.lbl_desc.setText(desc)
        self.lbl_desc.setStyleSheet("font-size: 13px; color: #333;")
        self.is_running = True

    def set_finished(self, final_time_str, summary_text=None):
        """设置为完成"""
        self.is_running = False
        self.status_dot.setText("✓")
        self.status_dot.setStyleSheet("color: #34C759; font-size: 20px; font-weight: bold;")  # 绿色
        self.lbl_time.setText(final_time_str)

        # 如果提供了总结文本，更新描述
        if summary_text:
            self.lbl_desc.setText(summary_text)
            self.lbl_desc.setStyleSheet("font-size: 13px; color: #34C759;")  # 绿色文字表示成功

    def update_time(self):
        pass


class LoadingView(QWidget):
    """
    右侧进度面板
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #FFFFFF; border-radius: 12px;")

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        # 容器
        container = QFrame()
        container.setFixedWidth(400)
        container.setStyleSheet("background-color: #FFFFFF;")

        layout = QVBoxLayout(container)
        layout.setSpacing(0)

        # 标题
        lbl_header = QLabel("正在生成词云")
        lbl_header.setAlignment(Qt.AlignCenter)
        lbl_header.setStyleSheet("font-size: 24px; font-weight: 800; color: #1D1D1F; margin-bottom: 30px;")
        layout.addWidget(lbl_header)

        # 步骤
        self.step_read = StepItem("读取文件", "")
        self.step_seg = StepItem("智能分词", "")
        self.step_render = StepItem("图形渲染", "")

        layout.addWidget(self.step_read)
        layout.addWidget(self.step_seg)
        layout.addWidget(self.step_render)

        main_layout.addWidget(container)

        # 计时器
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.current_step_index = -1
        self.step_start_time = 0

    def start_loading(self):
        self.current_step_index = -1
        self.step_read.reset("读取文件")
        self.step_seg.reset("智能分词")
        self.step_render.reset("图形渲染")
        self.timer.start(100)  # 0.1秒刷新一次

    def update_step(self, step_index, desc, prev_summary=None):
        """
        :param step_index: 当前开始的步骤索引
        :param desc: 当前步骤的描述
        :param prev_summary: 上一步骤完成后的总结信息 (例如: "共5000字")
        """
        import time
        now = time.time()

        # 1. 结束上一步
        if self.current_step_index >= 0:
            prev_item = self._get_item(self.current_step_index)
            elapsed = now - self.step_start_time
            # 更新上一步的状态和总结信息
            prev_item.set_finished(f"{elapsed:.1f}s", prev_summary)

        # 2. 开始新一步 (如果 step_index == 3，表示全部完成，不需要 set_active)
        if step_index <= 2:
            self.current_step_index = step_index
            self.step_start_time = now

            curr_item = self._get_item(step_index)
            curr_item.set_active(desc)
        else:
            # 全部完成，停止计时
            self.current_step_index = -1
            self.timer.stop()

    def _get_item(self, index):
        if index == 0: return self.step_read
        if index == 1: return self.step_seg
        return self.step_render

    def _tick(self):
        if self.current_step_index >= 0:
            import time
            elapsed = time.time() - self.step_start_time
            item = self._get_item(self.current_step_index)
            item.lbl_time.setText(f"{elapsed:.1f}s")

    def stop_loading(self):
        self.timer.stop()