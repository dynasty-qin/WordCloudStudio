import jieba
import jieba.posseg as pseg  # 引入词性标注模块


class Tokenizer:
    def __init__(self):
        self.stop_words = set()
        # 基础标点停用词
        self.stop_words.update(
            ['\n', '\t', ' ', '，', '。', '！', '：', '“', '”', '、', '（', '）', '【', '】', '《', '》', '—', '-', '·', '…'])
        self.stop_words.update(
            [',', '.', '!', ':', ';', '?', '(', ')', '[', ']', '{', '}', '-', '_', '=', '+', '/', '\\', '|', '"', "'",
             '`', '~', '<', '>', '@', '#', '$', '%', '^', '&', '*'])

    def set_stop_words(self, stop_words_list):
        """设置停用词"""
        self.stop_words.update(set(stop_words_list))

    def process_text(self, text, filter_type="all"):
        """
        核心分词逻辑
        :param text: 原始长文本
        :param filter_type: 过滤模式 "all", "name", "location", "name_location"
        :return: 空格分隔的词语字符串
        """
        if not text:
            return ""

        valid_words = []

        # 策略分支
        if filter_type == "all":
            # --- 模式 1: 普通分词 (速度快) ---
            words = jieba.cut(text, cut_all=False)
            for w in words:
                w = w.strip().lower()
                if w and w not in self.stop_words and len(w) > 1:
                    valid_words.append(w)
        else:
            # --- 模式 2: 词性标注分词 (稍慢，但智能) ---
            words = pseg.cut(text)

            # 🟢 修复点：不能直接 for w, flag in words
            # 必须先获取对象，再访问 .word 和 .flag 属性
            for word_pair in words:
                w = word_pair.word
                flag = word_pair.flag

                w = w.strip().lower()
                if not w or w in self.stop_words or len(w) < 2:
                    continue

                # 根据 flag 筛选
                keep = False
                if filter_type == "name":
                    # nr: 人名
                    if flag.startswith('nr'): keep = True

                elif filter_type == "location":
                    # ns: 地名
                    if flag.startswith('ns'): keep = True

                elif filter_type == "name_location":
                    # nr: 人名, ns: 地名
                    if flag.startswith('nr') or flag.startswith('ns'): keep = True

                elif filter_type == "org":
                    # nt: 机构
                    if flag.startswith('nt'): keep = True

                if keep:
                    valid_words.append(w)

        return " ".join(valid_words)