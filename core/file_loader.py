import os
import docx
import pdfplumber

class FileLoader:
    @staticmethod
    def read_file(file_path):
        """
        统一的文件读取接口
        :param file_path: 文件路径
        :return: 读取到的文本内容 (str)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件未找到: {file_path}")

        # 获取文件扩展名（小写）
        ext = os.path.splitext(file_path)[1].lower()

        try:
            if ext == '.txt':
                return FileLoader._read_txt(file_path)
            elif ext == '.docx':
                return FileLoader._read_docx(file_path)
            elif ext == '.pdf':
                return FileLoader._read_pdf(file_path)
            elif ext == '.doc':
                return "错误: 不支持直接读取 .doc 格式，请先另存为 .docx 或 .txt"
            else:
                return "错误: 不支持的文件格式"
        except Exception as e:
            return f"读取失败: {str(e)}"

    @staticmethod
    def _read_txt(path):
        # 尝试常见编码读取
        encodings = ['utf-8', 'gbk', 'utf-16']
        for enc in encodings:
            try:
                with open(path, 'r', encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        raise ValueError("无法识别的文件编码，请确保是UTF-8或GBK")

    @staticmethod
    def _read_docx(path):
        doc = docx.Document(path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)

    @staticmethod
    def _read_pdf(path):
        text = ""
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text

if __name__ == "__main__":
    print("FileLoader 模块已准备就绪。")