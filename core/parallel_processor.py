import jieba
import jieba.posseg as pseg
import multiprocessing
from multiprocessing import Pool, cpu_count

# 🟢 智能导入加速库
try:
    import jieba_fast as jieba
    import jieba_fast.posseg as pseg
except ImportError:
    pass


# ---------------------------------------------------------
# 必须定义在顶层函数
# ---------------------------------------------------------

def _init_jieba_worker(custom_dict):
    """子进程初始化：加载字典"""
    # 让 jieba 知道这些词
    if custom_dict:
        for word in custom_dict:
            jieba.add_word(word, freq=20000)


def _worker_task(args):
    """
    子进程执行的具体任务
    args: (text_chunk, filter_type, stop_words, custom_dict)
    """
    # 🟢 接收 custom_dict
    text_chunk, filter_type, stop_words, custom_dict = args

    stop_words_set = set(stop_words)
    # 🟢 建立 VIP 名单 (转小写以匹配)
    vip_words_set = set(w.strip().lower() for w in custom_dict) if custom_dict else set()

    valid_words = []

    if filter_type == "all":
        # 全文模式
        words = jieba.cut(text_chunk, cut_all=False)
        for w in words:
            w = w.strip().lower()

            # 🟢 VIP 检查：如果是强制保留词，直接通过
            if w in vip_words_set:
                valid_words.append(w)
                continue

            # 普通规则：去空、去停用词、去单字
            if w and w not in stop_words_set and len(w) > 1:
                valid_words.append(w)
    else:
        # 智能提取模式
        words = pseg.cut(text_chunk)

        for word_pair in words:
            w = word_pair.word
            flag = word_pair.flag
            w = w.strip().lower()

            # 🟢 VIP 检查：强制保留词，无视词性，无视停用词，无视单字限制
            if w in vip_words_set:
                valid_words.append(w)
                continue

            # 普通规则过滤
            if not w or w in stop_words_set or len(w) < 2:
                continue

            keep = False
            if filter_type == "name":
                if flag.startswith('nr'): keep = True
            elif filter_type == "location":
                if flag.startswith('ns'): keep = True
            elif filter_type == "name_location":
                if flag.startswith('nr') or flag.startswith('ns'): keep = True
            elif filter_type == "org":
                if flag.startswith('nt'): keep = True

            if keep:
                valid_words.append(w)

    return valid_words


class ParallelTokenizer:
    """
    多进程分词管理器
    """

    @staticmethod
    def run_parallel(text, filter_type, custom_dict, stop_words):
        # 1. 准备数据
        lines = text.split('\n')

        # 2. 确定并行数量
        num_cores = max(1, cpu_count())

        # 3. 智能分块
        chunk_size = len(lines) // num_cores + 1
        chunks = []
        current_chunk = []

        for line in lines:
            current_chunk.append(line)
            if len(current_chunk) >= chunk_size:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
        if current_chunk:
            chunks.append("\n".join(current_chunk))

        # 4. 准备任务参数
        # 🟢 关键修改：把 custom_dict 也传给每个任务，用于做 VIP 校验
        tasks = [(chunk, filter_type, stop_words, custom_dict) for chunk in chunks]

        # 5. 启动多进程
        results = []
        with Pool(processes=num_cores, initializer=_init_jieba_worker, initargs=(custom_dict,)) as pool:
            raw_results = pool.map(_worker_task, tasks)

            for sub_list in raw_results:
                results.extend(sub_list)

        return results