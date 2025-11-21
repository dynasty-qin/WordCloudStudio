import csv
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QHeaderView, QLabel, QPushButton,
                               QFileDialog, QMessageBox, QMenu, QLineEdit)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush, QAction, QCursor


class StatsViewer(QWidget):
    stop_word_added = Signal(str)
    stop_word_removed = Signal(str)
    batch_action_signal = Signal(list, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.toolbar = QWidget()
        self.toolbar.setStyleSheet("background-color: #FAFAFA; border-bottom: 1px solid #E5E5E5;")
        self.toolbar.setFixedHeight(50)

        tool_layout = QHBoxLayout(self.toolbar)
        tool_layout.setContentsMargins(15, 8, 15, 8)
        tool_layout.setSpacing(10)

        self.lbl_info = QLabel("暂无数据")
        self.lbl_info.setStyleSheet("color: #666; font-size: 12px; font-weight: 500;")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 搜索词语...")
        self.search_input.setFixedWidth(180)
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setFixedHeight(32)
        self.search_input.setStyleSheet("""
            QLineEdit { border: 1px solid #D1D1D6; border-radius: 16px; padding: 0 12px; background-color: #FFFFFF; font-size: 12px; }
            QLineEdit:focus { border: 1px solid #007AFF; }
        """)
        self.search_input.textChanged.connect(self.filter_data)

        self.btn_export = QPushButton("📥 导出 Excel")
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.setFixedHeight(32)
        self.btn_export.setStyleSheet("""
            QPushButton { background-color: #FFFFFF; border: 1px solid #D1D1D6; border-radius: 16px; padding: 0 12px; font-size: 12px; color: #333; }
            QPushButton:hover { background-color: #F0F0F5; border-color: #007AFF; color: #007AFF; }
            QPushButton:disabled { color: #CCC; background-color: #F9F9F9; border-color: #E0E0E0; }
        """)
        self.btn_export.clicked.connect(self.export_data)
        self.btn_export.setEnabled(False)

        tool_layout.addWidget(self.lbl_info)
        tool_layout.addStretch()
        tool_layout.addWidget(self.search_input)
        tool_layout.addWidget(self.btn_export)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["排名", "词语", "频率", "操作"])
        self.table.setFrameShape(QTableWidget.NoFrame)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed);
        self.table.setColumnWidth(0, 60)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed);
        self.table.setColumnWidth(2, 80)
        header.setSectionResizeMode(3, QHeaderView.Fixed);
        self.table.setColumnWidth(3, 140)

        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setFocusPolicy(Qt.StrongFocus)
        self.current_data = []
        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.table)

    def set_data(self, counts_dict, blocked_words=None):
        self.current_data = []
        self.table.setRowCount(0)
        self.btn_export.setEnabled(False)
        self.search_input.clear()
        if not counts_dict: self.lbl_info.setText("暂无数据"); return
        blocked_words = set(blocked_words) if blocked_words else set()
        sorted_data = sorted(counts_dict.items(), key=lambda x: x[1], reverse=True)
        self.current_data = sorted_data
        self.lbl_info.setText(f"统计结果: {len(sorted_data)} 个词")
        self.btn_export.setEnabled(True)
        self.table.setRowCount(len(sorted_data))
        self.table.setSortingEnabled(False)
        for row, (word, count) in enumerate(sorted_data):
            item_rank = QTableWidgetItem(str(row + 1));
            item_rank.setTextAlignment(Qt.AlignCenter)
            item_word = QTableWidgetItem(str(word));
            item_word.setTextAlignment(Qt.AlignCenter)
            item_count = QTableWidgetItem(str(count));
            item_count.setTextAlignment(Qt.AlignCenter)
            if row < 3:
                color = QColor("#FF3B30") if row == 0 else (QColor("#FF9500") if row == 1 else QColor("#FFCC00"))
                font = self.table.font();
                font.setBold(True)
                item_rank.setForeground(QBrush(color));
                item_rank.setFont(font);
                item_count.setFont(font)
            self.table.setItem(row, 0, item_rank);
            self.table.setItem(row, 1, item_word);
            self.table.setItem(row, 2, item_count)

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4);
            btn_layout.setAlignment(Qt.AlignCenter)
            btn_action = QPushButton("屏蔽")
            btn_action.setCursor(Qt.PointingHandCursor)
            btn_action.setFixedSize(80, 26)
            btn_action.setStyleSheet("""
                QPushButton { border: 1px solid #E5E5E5; border-radius: 4px; background-color: white; color: #666; font-size: 11px; padding: 0 10px; }
                QPushButton:hover { background-color: #FFF0F0; color: #FF3B30; border-color: #FF3B30; }
            """)
            btn_action.clicked.connect(lambda checked, r=row, w=word: self.toggle_block_status(r, w))
            btn_layout.addWidget(btn_action)
            self.table.setCellWidget(row, 3, btn_widget)
            if word in blocked_words: self.set_row_blocked(row, True)

    def filter_data(self, text):
        text = text.strip().lower()
        rows = self.table.rowCount()
        for row in range(rows):
            item = self.table.item(row, 1)
            if not item: continue
            word = item.text().lower()
            self.table.setRowHidden(row, not (not text or text in word))

    def toggle_block_status(self, row, word):
        btn = self.get_btn_at(row)
        if not btn: return
        is_currently_blocked = (btn.text() == "恢复")
        if is_currently_blocked:
            self.set_row_blocked(row, False);
            self.stop_word_removed.emit(word)
        else:
            self.set_row_blocked(row, True);
            self.stop_word_added.emit(word)

    def set_row_blocked(self, row, blocked):
        btn = self.get_btn_at(row)
        if not btn: return
        if blocked:
            color = QColor("#CCCCCC")
            btn.setText("恢复")
            btn.setStyleSheet("""
                QPushButton { border: 1px solid #34C759; color: #34C759; background-color: #FFF; font-size: 11px; border-radius: 4px; padding: 0 10px; }
                QPushButton:hover { background-color: #F0FFF4; }
            """)
        else:
            color = QColor("#000000")
            if row == 0:
                color = QColor("#FF3B30")
            elif row == 1:
                color = QColor("#FF9500")
            elif row == 2:
                color = QColor("#FFCC00")
            btn.setText("屏蔽")
            btn.setStyleSheet("""
                QPushButton { border: 1px solid #E5E5E5; color: #666; background-color: #FFF; font-size: 11px; border-radius: 4px; padding: 0 10px; }
                QPushButton:hover { border-color: #FF3B30; color: #FF3B30; background-color: #FFF0F0; }
            """)
        brush = QBrush(color)
        for col in range(3):
            item = self.table.item(row, col)
            if item: item.setForeground(brush)

    def get_btn_at(self, row):
        widget = self.table.cellWidget(row, 3)
        if widget: return widget.findChild(QPushButton)
        return None

    def show_context_menu(self, pos):
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges: return
        selected_rows = set()
        for r in selected_ranges:
            for i in range(r.topRow(), r.bottomRow() + 1):
                if not self.table.isRowHidden(i): selected_rows.add(i)
        if not selected_rows: return
        menu = QMenu(self.table)
        action_block = QAction(f"🚫 批量屏蔽选中 ({len(selected_rows)})", self)
        action_unblock = QAction(f"✅ 批量恢复选中 ({len(selected_rows)})", self)
        action_block.triggered.connect(lambda: self.batch_process(list(selected_rows), True))
        action_unblock.triggered.connect(lambda: self.batch_process(list(selected_rows), False))
        menu.addAction(action_block);
        menu.addAction(action_unblock)
        menu.exec(QCursor.pos())

    def batch_process(self, rows, is_block):
        words = []
        for row in rows:
            item = self.table.item(row, 1)
            if item:
                word = item.text()
                words.append(word)
                self.set_row_blocked(row, is_block)
        if words: self.batch_action_signal.emit(words, is_block)

    def export_data(self):
        if not self.current_data: return
        save_path, _ = QFileDialog.getSaveFileName(self, "导出数据", "词频统计.csv", "CSV Files (*.csv)")
        if save_path:
            try:
                with open(save_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(["排名", "词语", "出现次数"])
                    for idx, (word, count) in enumerate(self.current_data):
                        writer.writerow([idx + 1, word, count])
                QMessageBox.information(self, "成功", f"数据已导出")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", str(e))