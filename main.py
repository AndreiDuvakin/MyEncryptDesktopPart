import json
import sys
import os
import time

import paramiko
from scp import SCPClient
from threading import Timer, Thread, enumerate

from PyQt5 import uic
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QListWidgetItem, QFileDialog, QLineEdit


def createSSHClient(server, port, user, password):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    return client


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('templates/LoginWindow.ui', self)
        self.initUI()

    def initUI(self):
        self.lineEdit_2.setEchoMode(QLineEdit.Password)
        self.pushButton.clicked.connect(self.auth)

    def message_to_user(self, message, timer):
        self.statusBar.showMessage(message, timer)

    def auth(self):
        path = 'files/outgoing/login.encr'
        open(path, 'w', encoding='utf-8').write(
            f'{self.lineEdit.text()} {self.lineEdit_2.text()}')
        ssh = createSSHClient("188.68.223.151", 22, "root", password="")
        scp = SCPClient(ssh.get_transport())
        scp.put(path, '~/EncryptServer/files/incoming')
        scp.close()
        ssh.close()
        os.remove(path)
        self.wait_login()

    def wait_login(self):
        ssh = createSSHClient("188.68.223.151", 22, "root", password="")
        find, login = False, self.lineEdit.text()
        for i in range(15):
            time.sleep(1)
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("ls ~/EncryptServer/files/outgoing")
            data = ssh_stdout.read()
            if f'{login}_login.encr' in str(data):
                find = True
                break
        if find:
            ssh = createSSHClient("188.68.223.151", 22, "root", password="")
            scp = SCPClient(ssh.get_transport())
            scp.get(f'~/EncryptServer/files/outgoing/{login}_login.encr', 'files/incoming')
            ssh.close()
            scp.close()
            file = open(f'files/incoming/{login}_login.encr', 'r', encoding='utf-8').read()
            os.remove(f'files/incoming/{login}_login.encr')
            if file == '403':
                self.statusBar.showMessage('                      Ошибка доступа', 5000)
            else:
                self.statusBar.showMessage('                          Успешно', 5000)
                self.open_dialog()
        else:
            self.statusBar.showMessage('Сервер не отвечает, попробуйте позже', 5000)

    def open_dialog(self):
        self.dialog = DialogWindow(self.lineEdit.text(), self.lineEdit_2.text())
        self.dialog.show()
        self.close()


class DialogWindow(QMainWindow):
    def __init__(self, login, password):
        super().__init__()
        uic.loadUi('templates/ChatsWindow.ui', self)
        self.login = login
        self.password = password
        self.list_chats = []
        self.list_buttons = []
        self.initUI()

    def initUI(self):
        self.pushButton.clicked.connect(self.new_dialog)
        self.pushButton_3.clicked.connect(self.edit_profile)
        self.pushButton_7.clicked.connect(self.setting)
        self.update_list_chats()

    def update_list_chats(self):
        path = 'files/outgoing/get_chats.encr'
        open(path, 'w', encoding='utf-8').write(
            f'{self.login} {self.password}')
        ssh = createSSHClient("188.68.223.151", 22, "root", password="")
        scp = SCPClient(ssh.get_transport())
        scp.put(path, '~/EncryptServer/files/incoming')
        os.remove(path)
        scp.close()
        ssh.close()
        self.wait_chats()

    def wait_chats(self):
        ssh = createSSHClient("188.68.223.151", 22, "root", password="")
        find = False
        for i in range(15):
            time.sleep(1)
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("ls ~/EncryptServer/files/outgoing")
            data = ssh_stdout.read()
            if f'{self.login}_chats.encr' in str(data):
                find = True
                break
        if find:
            ssh = createSSHClient("188.68.223.151", 22, "root", password="")
            scp = SCPClient(ssh.get_transport())
            scp.get(f'~/EncryptServer/files/outgoing/{self.login}_chats.encr', 'files/incoming')
            ssh.close()
            scp.close()
            file = open(f'files/incoming/{self.login}_chats.encr', 'r', encoding='utf-8').read()
            os.remove(f'files/incoming/{self.login}_chats.encr')
            if file == '403':
                self.statusBar.showMessage('                      Ошибка доступа', 5000)
            else:
                data = json.loads(file)
                self.list_chats = data
                self.load_window(data)
        else:
            self.statusBar.showMessage('Сервер не отвечает, попробуйте позже', 5000)

    def load_window(self, data):
        self.listWidget.clear()
        list(map(lambda x: self.make_buttons(x), data))

    def make_buttons(self, data):
        button = QPushButton(f'{data[1][2]}')
        button.clicked.connect(self.open_chat)
        list_widget_item = QListWidgetItem()
        list_widget_item.setSizeHint(QSize(25, 50))
        self.listWidget.addItem(list_widget_item)
        self.listWidget.setItemWidget(list_widget_item, button)

    def open_chat(self):
        self.chat = ChatWindows()
        self.chat.show()

    def new_dialog(self):
        pass

    def edit_profile(self):
        pass

    def setting(self):
        pass


class ChatWindows(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('templates/ChatWindow.ui', self)
        self.initUI()

    def initUI(self):
        pass


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    encrypt_app = LoginWindow()
    encrypt_app.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
