import base64
import random
import sys
from inspect import currentframe
import time
from datetime import datetime

from PyQt5.QtCore import QThread, pyqtSignal, QWaitCondition, QMutex
import pygetwindow as gw
from PyQt5.QtWidgets import QTextBrowser, QWidget, QPushButton, QHBoxLayout, QProgressBar, QVBoxLayout, QMessageBox
from pynput.keyboard import Key, Controller

BLACK_LIST = [""]


class MyThread(QThread):
    valueChangeSignal = pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._isPause = True

        self.w_instance = args[0]
        self.browser = self.w_instance.browser

        self.cond = QWaitCondition()
        self.mutex = QMutex()
        self.init_index()

    def init_index(self):
        self.index = 0
        self.step = self.w_instance.step
        self.total = self.w_instance.total

    def display_now(self):
        f = currentframe()
        f = f.f_back
        co = f.f_code
        now = datetime.now()
        print(now)
        self.browser.append(f'{co.co_name}@{now.strftime("%Y-%m-%d %H:%M:%S")}')

    def pause(self):
        self._isPause = True
        self.display_now()

    def resume(self):
        self._isPause = False
        self.init_index()
        self.cond.wakeAll()
        self.display_now()

    @staticmethod
    def get_next_title():
        all_titles = gw.getAllTitles()
        next_title_list = []
        for title in all_titles:
            if title not in BLACK_LIST:
                next_title_list.append(title)

        next_title = random.choice(next_title_list)

        return next_title

    def get_from_title(self):
        from_title = ""
        w = gw.getActiveWindow()
        if w is not None:
            from_title = w.title
        if from_title == "搜索":
            b = Controller()
            b.press(Key.cmd)
            b.release(Key.cmd)
            self.msleep(1000)

        return from_title

    def run_sleep(self, from_title, to_title):
        seconds = random.randint(10, 120)
        self.total = self.total - seconds
        out_put = f"index: {self.index}\t" \
                  f" from_title-> {from_title}" \
                  f" to_title-> {to_title}" \
                  f" {seconds}s"
        print(out_put)
        self.browser.append(out_put)

        i = 0

        next_window = gw.getWindowsWithTitle(to_title)[0]
        next_window.activate()

        for i in range(1, seconds, self.step):
            if self._isPause:
                break

            self.valueChangeSignal.emit(int(i / seconds * 100))
            self.msleep(100 * self.step)

        else:
            self.valueChangeSignal.emit(100)
            remainder = seconds - i
            if remainder > 0:
                self.msleep(1000 * remainder)

    def switch_window(self):
        from_title = self.get_from_title()
        to_title = self.get_next_title()
        self.run_sleep(from_title, to_title)

    def main(self):
        while 1:
            self.index += 1
            if self._isPause: self.cond.wait(self.mutex)
            b = Controller()
            b.press(Key.f20)
            b.release(Key.f20)
            self.switch_window()

    def run(self):
        while 1:
            self.mutex.lock()
            if self._isPause: self.cond.wait(self.mutex)
            self.main()
            self.mutex.unlock()
            if self.total < 0:
                self._isPause = True


class AutoScrollTextBrowser(QTextBrowser):
    def __init__(self, parent=None):
        super(AutoScrollTextBrowser, self).__init__(parent)
        self.textChanged.connect(self.scroll_to_end)

    def scroll_to_end(self):
        cursor = self.textCursor()
        self.EnsureCursorMoveToEnd(cursor)

    def EnsureCursorMoveToEnd(self, cursor):
        position = cursor.position()
        block = self.document().findBlockByNumber(position)
        while block.isValid() and block.next().isValid():
            position = block.next().position()
            cursor.setPosition(position)
            block = block.next()

        self.setTextCursor(cursor)


_TOTAL = 60 * 60 * 2


class Window(QWidget):
    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)

        self.browser = AutoScrollTextBrowser(self)
        self.total = None
        self.step = None
        self.t = MyThread(self)
        self.initUI()
        self.t.start()

    def init_params(self, total, step):
        self.total = _TOTAL if total is None else int(total) * 60 * 60
        self.step = 3 if step is None else int(step)

    def initUI(self):
        self.setWindowTitle('PyQt5 Demo')
        self.setGeometry(300, 300, 900, 300)
        self.browser.setReadOnly(True)
        self.browser.setStyleSheet("background-color: black; color: white;")

        self.startButton = QPushButton('Start', self)
        self.startButton.clicked.connect(self.t.resume)
        self.startButton.setStyleSheet(
            "background-color: lightgreen; border-top-left-radius: 20px; border-bottom-left-radius: 20px;")
        self.startButton.setFixedSize(88, 40)

        self.stopButton = QPushButton('Stop', self)
        self.stopButton.clicked.connect(self.t.pause)
        self.stopButton.setStyleSheet(
            "background-color: skyblue; border-top-right-radius: 20px; border-bottom-right-radius: 20px;")
        self.stopButton.setFixedSize(88, 40)

        self.exitButton = QPushButton('Exit', self)
        self.exitButton.clicked.connect(self.exit_program)
        self.exitButton.setStyleSheet(
            "background-color: rgb(255, 192, 203);")
        self.exitButton.setFixedSize(200, 40)

        layout1 = QHBoxLayout()
        layout2 = QHBoxLayout()
        layout3 = QHBoxLayout()

        self.progressBar = QProgressBar(self)
        layout1.addWidget(self.progressBar)
        self.t.valueChangeSignal.connect(self.progressBar.setValue)

        layout2.addWidget(self.startButton)
        layout2.addWidget(self.exitButton)
        layout2.addWidget(self.stopButton)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.browser)
        main_layout.addLayout(layout1)
        main_layout.addLayout(layout2)
        main_layout.addLayout(layout3)

        self.setLayout(main_layout)

    def exit_program(self):
        reply = QMessageBox.question(self, 'Message', 'Are you sure to quit?', QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.t.terminate()

            QApplication.exit()


def get_param(params, name):
    for p in params:
        if p.startswith(name):
            return p.split('=')[1]

    return None


if __name__ == '__main__':
    import cgitb
    from PyQt5.QtWidgets import QApplication

    sys.excepthook = cgitb.enable(1, None, 5, "")
    app = QApplication(sys.argv)

    parms = sys.argv[1:]
    total = get_param(parms, 'total')
    step = get_param(parms, 'step')

    w = Window()
    w.init_params(total, step)
    w.show()
    sys.exit(app.exec_())
