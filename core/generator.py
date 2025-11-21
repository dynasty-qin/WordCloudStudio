import numpy as np
from wordcloud import WordCloud
from PIL import Image
import os


class WordCloudGenerator:
    def __init__(self, font_path=None):
        self.font_path = font_path
        if not self.font_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            local_font = os.path.join(base_dir, "assets", "msyh.ttc")

            if os.path.exists(local_font):
                self.font_path = local_font
            else:
                win_font = "C:/Windows/Fonts/msyh.ttc"
                if os.path.exists(win_font):
                    self.font_path = win_font
                else:
                    print("警告：未找到默认中文字体！")

    def generate(self, text, mask_image_path=None, bg_color='white',
                 max_words=200, color_map='viridis', width=800, height=600):
        if not text or not text.strip():
            raise ValueError("文本内容为空")

        mask = None
        final_width, final_height = width, height

        # 1. 蒙版处理
        if mask_image_path and os.path.exists(mask_image_path):
            try:
                original_mask = Image.open(mask_image_path).convert("RGBA")
                orig_w, orig_h = original_mask.size

                # 保持比例缩放
                ratio = min(width / orig_w, height / orig_h)
                new_w = int(orig_w * ratio)
                new_h = int(orig_h * ratio)
                final_width, final_height = new_w, new_h

                resized_mask = original_mask.resize((final_width, final_height), Image.Resampling.LANCZOS)
                icon_array = np.array(resized_mask)

                # 创建 WordCloud 蒙版 (255白=背景, 0黑=内容)
                new_mask = np.full((final_height, final_width), 255, dtype=np.uint8)

                # 智能判定：不透明 且 颜色深
                is_opaque = icon_array[:, :, 3] > 128
                brightness = np.mean(icon_array[:, :, :3], axis=2)
                is_dark = brightness < 220

                target_indices = np.logical_and(is_opaque, is_dark)
                new_mask[target_indices] = 0
                mask = new_mask

            except Exception as e:
                print(f"蒙版处理错误: {e}")
                mask = None

        # 2. 🟢 核心修复：模式分流策略
        # 为了避免 wordcloud 库在 RGBA 模式下画轮廓报错：
        # - 透明背景 -> RGBA 模式 -> 强制 contour_width=0
        # - 实色背景 -> RGB 模式 -> 允许 contour_width>0

        is_transparent = False
        wc_mode = "RGB"  # 默认 RGB (支持轮廓)
        wc_bg_color = "white"  # 默认白
        contour_w = 0

        if bg_color == "transparent" or bg_color is None:
            is_transparent = True
            wc_mode = "RGBA"  # 必须 RGBA
            wc_bg_color = None  # 背景 None
            contour_w = 0  # ❌ 透明模式严禁轮廓，否则崩溃
        else:
            is_transparent = False
            wc_mode = "RGB"  # 🟢 实色背景切回 RGB，稳！
            wc_bg_color = bg_color
            # 有蒙版且非透明时，才画轮廓
            if mask is not None:
                contour_w = 3  # 浅色轮廓宽度

        # 3. 动态参数
        dynamic_min_font = max(4, final_height // 150)
        dynamic_step = 2 if final_height < 2000 else 3

        params = {
            "font_path": self.font_path,
            "background_color": wc_bg_color,
            "mode": wc_mode,
            "max_words": max_words,
            "width": final_width,
            "height": final_height,
            "colormap": color_map,
            "collocations": False,
            "margin": 2,
            "mask": mask,
            "contour_width": contour_w,
            "contour_color": '#CCCCCC',  # 浅灰色轮廓
            "min_font_size": dynamic_min_font,
            "font_step": dynamic_step,
            "relative_scaling": 0.5,
            "prefer_horizontal": 0.9
        }

        wc = WordCloud(**params)
        wc.generate(text)

        image = wc.to_image()

        # 4. 强制透明化后处理 (仅针对透明模式)
        if is_transparent:
            image = image.convert("RGBA")
            datas = image.getdata()
            new_data = []
            for item in datas:
                # 如果像素是纯白(背景)，且我们在透明模式，将其 Alpha 设为 0
                # WordCloud 有时会在边缘留下白色像素，这里统一清理
                if item[0] > 250 and item[1] > 250 and item[2] > 250:
                    new_data.append((255, 255, 255, 0))
                else:
                    new_data.append(item)
            image.putdata(new_data)

        return image