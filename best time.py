import sys
import time
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPainter, QColor, QFont, QKeySequence, QIcon
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel,
    QProgressBar, QHBoxLayout, QDialog, QSpinBox, QComboBox,
    QShortcut, QToolTip, QSystemTrayIcon, QMenu
)

all_windows = []

class ReverseProgressBar(QProgressBar):
    def __init__(self, total_time=60, parent=None):
        super().__init__(parent)
        self.total_time = total_time
        self.start_time = None
        self.setTextVisible(True)
        self.setMaximum(total_time)
        self.setValue(total_time)
        self.setAlignment(Qt.AlignCenter)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.setInterval(100)

    def start(self):
        self.start_time = time.time()
        self.timer.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.rect()

        elapsed = 0 if self.start_time is None else time.time() - self.start_time
        remaining = max(0, self.total_time - elapsed)

        if remaining <= 0:
            self.timer.stop()

        progress_ratio = remaining / self.total_time
        progress_width = int(rect.width() * progress_ratio)

        if remaining > 40:
            color = QColor(0, 200, 0)
        elif remaining > 20:
            color = QColor(255, 200, 0)
        else:
            color = QColor(200, 0, 0)

        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(rect.width() - progress_width, 0, progress_width, rect.height(), color)

        painter.setPen(Qt.black)
        painter.drawRect(rect.adjusted(0, 0, -1, -1))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(rect, Qt.AlignCenter, f"{int(remaining)}s")


class ModifyDialog(QDialog):
    def __init__(self, current_n, current_a, parent=None):
        super().__init__(parent)
        self.setWindowTitle("修改 N / A")
        self.parent_counter = parent

        layout = QVBoxLayout(self)

        self.n_spin = QSpinBox()
        self.n_spin.setRange(0, 9999)
        self.n_spin.setValue(current_n)
        layout.addWidget(QLabel("当前已完成（N）："))
        layout.addWidget(self.n_spin)

        self.a_spin = QSpinBox()
        self.a_spin.setRange(1, 9999)
        self.a_spin.setValue(current_a)
        layout.addWidget(QLabel("目标（A）："))
        layout.addWidget(self.a_spin)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)

        destroy_btn = QPushButton("销毁计数器")
        destroy_btn.setStyleSheet("color: white; background-color: red;")
        destroy_btn.clicked.connect(self.destroy_counter)
        btn_layout.addWidget(destroy_btn)

        layout.addLayout(btn_layout)

    def get_values(self):
        return self.n_spin.value(), self.a_spin.value()

    def destroy_counter(self):
        if self.parent_counter:
            self.parent_counter.close()
            if self.parent_counter in all_windows:
                all_windows.remove(self.parent_counter)
        self.accept()

class CounterWindow(QWidget):
    def __init__(self, name, default_target=30, total_time=60, parent=None):
        super().__init__(parent)
        self.name = name
        self.count = 0
        self.target = default_target
        self.old_pos = None
        self.locked = False

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        self.button = QPushButton("交互")
        self.button.setStyleSheet("""
            QPushButton {
                background-color: pink;
                color: red;
                font-weight: bold;
                font-size: 18px;
                padding: 10px;
            }
            QPushButton:pressed {
                background-color: #ffb6c1;
                transform: scale(0.95);
            }
        """)
        self.button.clicked.connect(self.increment_count)
        layout.addWidget(self.button)

        self.label = QLabel(self.get_label_text())
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont("Arial", 14, QFont.Bold))
        self.label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.label)

        self.label.mouseDoubleClickEvent = self.modify_values

        self.progress = ReverseProgressBar(total_time)
        layout.addWidget(self.progress)

        self.setLayout(layout)

        # 快捷键：Ctrl+L
        shortcut_lock = QShortcut(QKeySequence("Ctrl+L"), self)
        shortcut_lock.activated.connect(self.toggle_lock)

        all_windows.append(self)

    def get_label_text(self):
        return f"🔵 {self.count} / 🎯 {self.target}"

    def increment_count(self):
        self.count += 1
        self.label.setText(self.get_label_text())
        self.progress.start()

    def modify_values(self, event):
        dialog = ModifyDialog(self.count, self.target, self)
        if dialog.exec_():
            self.count, self.target = dialog.get_values()
            self.label.setText(self.get_label_text())

    def toggle_lock(self):
        self.locked = not self.locked
        status = "🔒 已锁定，无法移动" if self.locked else "🔓 已解锁，可以移动"
        QToolTip.showText(self.mapToGlobal(QPoint(50, 50)), status)

    def mousePressEvent(self, event):
        if self.locked:
            return
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.locked:
            return
        if self.old_pos:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if self.locked:
            return
        self.old_pos = None


class StartWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("启动设置")
        self.counter_index = 1

        layout = QVBoxLayout(self)

        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 6)
        self.count_spin.setValue(1)
        layout.addWidget(QLabel("要添加的计数器数量："))
        layout.addWidget(self.count_spin)

        self.width_combo = QComboBox()
        self.width_combo.addItems(["210","480","720","1080","1440","1680","1920", "2560", "3440"])
        self.width_combo.setCurrentText("210")
        layout.addWidget(QLabel("每个窗口宽度："))
        layout.addWidget(self.width_combo)

        usage_label = QLabel(
            "使用说明：\n"
            "1. 点击“交互”按钮增加计数。\n"
            "2. 双击计数显示可修改 N/A。\n"
            "3. 进度条从右向左倒计时，颜色随时间变化。\n"
            "4. 拖动窗口可移动位置。\n"
            "5. 按 Ctrl+L 切换锁定/解锁状态。\n"
            "6. 按 Alt+P 切换隐藏/显示所有计数器窗口。\n"
            "7. 点击“添加新窗口”添加指定数量的新计数器。\n"
            "8. 关闭此窗口将隐藏到系统托盘，可右键托盘图标重新打开。"
        )
        usage_label.setWordWrap(True)
        layout.addWidget(usage_label)

        add_btn = QPushButton("添加新窗口")
        add_btn.clicked.connect(self.add_new_windows)
        layout.addWidget(add_btn)

        # 系统托盘
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(QIcon(r"d:\ee.png"))  # 请确保有一个名为 icon.png 的图标文件
        self.tray.setToolTip("计数器应用")
        menu = QMenu()
        show_action = menu.addAction("显示")
        show_action.triggered.connect(self.show)
        quit_action = menu.addAction("退出")
        quit_action.triggered.connect(app.quit)
        self.tray.setContextMenu(menu)

        # 快捷键：Ctrl+P for toggle all
        self.shortcut_hide = QShortcut(QKeySequence("Alt+P"), self)
        self.shortcut_hide.setContext(Qt.ApplicationShortcut)
        self.shortcut_hide.activated.connect(self.toggle_all_visibility)
        self.tray.show()

    def closeEvent(self, event):
    # 重写关闭事件，隐藏窗口到系统托盘
        event.ignore()  # 阻止窗口关闭
        self.hide()  # 隐藏窗口
        self.tray.showMessage(
        "计数器应用",
        "程序已最小化到托盘。右键托盘图标可重新打开。",
        QSystemTrayIcon.Information,
        3000  # 显示时间（毫秒）
    )

    def get_width(self):
        return int(self.width_combo.currentText())

    def add_new_windows(self):
        count = self.count_spin.value()
        width = self.get_width()
        for i in range(count):
            name = f"计数器{self.counter_index}"
            self.counter_index += 1
            window = CounterWindow(name)
            window.resize(width, 120)
            window.move(100 * i, 100)  # Offset to avoid overlap
            window.show()

    def toggle_all_visibility(self):
        if all_windows:
            visible = any(w.isVisible() for w in all_windows)  # 检查是否有窗口是可见的
            for w in all_windows:
                if visible:
                    w.hide()  # 如果有窗口可见，则隐藏所有窗口
                else:
                    w.show()  # 如果所有窗口都隐藏，则显示所有窗口

    def closeEvent(self, event):
    # 重写关闭事件，隐藏窗口到系统托盘
        event.ignore()  # 阻止窗口关闭
        self.hide()  # 隐藏窗口

if __name__ == "__main__":
    app = QApplication(sys.argv)

    start_window = StartWindow()
    start_window.show()
    sys.exit(app.exec_())