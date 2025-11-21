import multiprocessing
import os
import time
from collections import Counter

from PySide6.QtCore import QThread, Signal

from core.file_loader import FileLoader
from core.generator import WordCloudGenerator
from core.parallel_processor import ParallelTokenizer


class WordCloudWorker(QThread):
    finished = Signal(object, dict, dict)
    error = Signal(str)
    progress_step = Signal(int, str, str)

    def __init__(self, file_path, font_path=None, bg_color='white', mask_path=None,
                 custom_dict=None, stop_words=None, resolution_setting="auto",
                 max_words=1000, filter_type="all"):
        super().__init__()
        self.file_path = file_path
        self.font_path = font_path
        self.bg_color = bg_color
        self.mask_path = mask_path
        self.custom_dict = custom_dict if custom_dict is not None else []
        self.stop_words = stop_words if stop_words is not None else []
        self.resolution_setting = resolution_setting
        self.max_words = max_words
        self.filter_type = filter_type

    def run(self):
        timings = {}
        total_start = time.time()

        try:
            self.progress_step.emit(0, "正在加载文件内容...", "")
            t_start = time.time()
            file_size = os.path.getsize(self.file_path)
            size_str = self._format_size(file_size)

            text = FileLoader.read_file(self.file_path)
            if not text.strip():
                self.error.emit("文件中没有任何文字内容！")
                return

            char_count = len(text)
            read_summary = f"大小: {size_str} | 字数: {char_count:,}"
            timings['read'] = time.time() - t_start

            cpu_cores = multiprocessing.cpu_count()
            mode_name = self._get_mode_name()
            self.progress_step.emit(1, f"正在进行并行分词 ({cpu_cores}核)...", read_summary)
            t_start = time.time()

            clean_words_list = ParallelTokenizer.run_parallel(
                text,
                self.filter_type,
                self.custom_dict,
                self.stop_words
            )

            if not clean_words_list:
                self.error.emit(f"在'{mode_name}'模式下未找到有效词汇。")
                return

            word_counts = dict(Counter(clean_words_list).most_common(self.max_words))
            clean_text_for_cloud = " ".join(clean_words_list)

            unique_words = len(set(clean_words_list))
            total_words = len(clean_words_list)
            seg_summary = f"总词数: {total_words:,} | 唯一词: {unique_words:,}"
            timings['segment'] = time.time() - t_start

            target_width, target_height = self._calculate_resolution(len(clean_words_list))
            self.progress_step.emit(2, f"正在渲染高清图片 ({target_width}x{target_height})...", seg_summary)
            t_start = time.time()

            generator = WordCloudGenerator(self.font_path)
            pil_image = generator.generate(
                clean_text_for_cloud,
                mask_image_path=self.mask_path,
                bg_color=self.bg_color,
                width=target_width,
                height=target_height,
                max_words=self.max_words
            )

            render_summary = f"分辨率: {target_width}x{target_height}"
            timings['render'] = time.time() - t_start
            timings['total'] = time.time() - total_start

            self.progress_step.emit(3, "完成", render_summary)
            self.finished.emit(pil_image, word_counts, timings)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error.emit(f"错误: {str(e)}")

    def _format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def _calculate_resolution(self, word_count):
        if self.resolution_setting != "auto":
            try:
                dim_part = self.resolution_setting.split(' ')[0]
                w, h = dim_part.split('x')
                return int(w), int(h)
            except:
                pass

        if word_count < 200:
            return 1024, 768
        elif word_count < 800:
            return 1920, 1080
        elif word_count < 2000:
            return 2560, 1440
        else:
            return 3840, 2160
        return 800, 600

    def _get_mode_name(self):
        mapping = {"all": "全文", "name": "人名", "location": "地名", "name_location": "实体", "org": "机构"}
        return mapping.get(self.filter_type, "未知")