import sys
import os
import ctypes  # 🟢 引入 ctypes 用于修复任务栏图标
import multiprocessing
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon  # 🟢 引入 QIcon
from gui.main_window import MainWindow


# 🟢 定义资源路径获取函数 (兼容开发环境和打包后的 exe)
def resource_path(relative_path):
    """获取资源的绝对路径"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包后的临时目录
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def main():
    # 1. Windows 任务栏图标修复 (关键步骤！)
    # 设置 AppUserModelID，让 Windows 认为这是独立程序
    try:
        myappid = 'mycompany.wordcloud.tool.v1'  # 这里的名字随便起，唯一即可
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except ImportError:
        pass

    # 2. 创建应用
    app = QApplication(sys.argv)

    # 3. 设置全局图标 (窗口 + 任务栏)
    # 假设你的图标在 assets/logo.ico
    icon_path = resource_path(os.path.join("assets", "logo.ico"))
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # 4. 显示主窗口
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()