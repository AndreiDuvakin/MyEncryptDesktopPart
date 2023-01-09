import json
import sys
import os
import time

import paramiko
from scp import SCPClient
from threading import Thread

from PyQt5 import uic
from PyQt5.QtCore import QSize, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QListWidgetItem, QLineEdit

PASSWORD_VISITOR = open('visitor_password', 'r', encoding='utf-8').read()


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
        self.auth_status = False
        self.password_vis = False
        self.initUI()

    def initUI(self):
        self.lineEdit_2.setEchoMode(QLineEdit.Password)
        self.pushButton.clicked.connect(self.lets_auth)
        self.pushButton_2.clicked.connect(self.register)
        self.pushButton_3.clicked.connect(self.change_password_vis)

    def change_password_vis(self):
        if self.password_vis:
            self.pushButton_3.setIcon(QIcon('files/app_images/none_password.png'))
            self.password_vis = False
            self.lineEdit_2.setEchoMode(QLineEdit.Password)
        else:
            self.pushButton_3.setIcon(QIcon('files/app_images/password.png'))
            self.password_vis = True
            self.lineEdit_2.setEchoMode(QLineEdit.Normal)

    def register(self):
        self.reg = RegisterWindow(self)
        self.reg.show()

    def message_to_user(self, message, timer):
        self.statusBar.showMessage(message, timer)

    def lets_auth(self):
        th = Thread(target=self.auth, args=[])
        th.start()
        QTimer.singleShot(4500, self.open_dialog)

    def auth(self):
        path = 'files/outgoing/login.encr'
        open(path, 'w', encoding='utf-8').write(
            f'{self.lineEdit.text()} {self.lineEdit_2.text()}')
        ssh = createSSHClient("188.68.223.151", 22, "visitor", password=PASSWORD_VISITOR)
        scp = SCPClient(ssh.get_transport())
        scp.put(path, 'incoming')
        scp.close()
        ssh.close()
        os.remove(path)
        self.wait_login()

    def wait_login(self):
        ssh = createSSHClient("188.68.223.151", 22, "visitor", password=PASSWORD_VISITOR)
        find, login = False, self.lineEdit.text()
        for i in range(5):
            time.sleep(1)
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("ls outgoing")
            data = ssh_stdout.read()
            if f'{login}_login.encr' in str(data):
                find = True
                break
        if find:
            ssh = createSSHClient("188.68.223.151", 22, "visitor", password=PASSWORD_VISITOR)
            scp = SCPClient(ssh.get_transport())
            scp.get(f'outgoing/{login}_login.encr', 'files/incoming')
            ssh.close()
            scp.close()
            file = open(f'files/incoming/{login}_login.encr', 'r', encoding='utf-8').read()
            os.remove(f'files/incoming/{login}_login.encr')
            if file == '403':
                self.statusBar.showMessage('                      Ошибка доступа', 5000)
            else:
                self.statusBar.showMessage('                          Успешно', 5000)
                self.auth_status = True
        else:
            self.statusBar.showMessage('Сервер не отвечает, попробуйте позже', 5000)

    def open_dialog(self):
        if self.auth_status:
            self.dialog = DialogWindow(self.lineEdit.text(), self.lineEdit_2.text())
            self.dialog.show()
            self.close()
        else:
            self.statusBar.showMessage('                      Ошибка входа', 5000)

    def keyPressEvent(self, event):
        if event.key() == 16777220:
            self.lets_auth()


class RegisterWindow(QMainWindow):
    def __init__(self, login_self):
        super().__init__()
        uic.loadUi('templates/RegisterWindow.ui', self)
        self.login_obj = login_self
        self.reg_status = False
        self.password_vis = False
        self.initUI()

    def initUI(self):
        self.lineEdit_2.setEchoMode(QLineEdit.Password)
        self.lineEdit_3.setEchoMode(QLineEdit.Password)
        self.pushButton_2.clicked.connect(self.lets_reg)
        self.pushButton_3.clicked.connect(self.change_password_vis)

    def change_password_vis(self):
        if self.password_vis:
            self.pushButton_3.setIcon(QIcon('files/app_images/none_password.png'))
            self.password_vis = False
            self.lineEdit_2.setEchoMode(QLineEdit.Password)
            self.lineEdit_3.setEchoMode(QLineEdit.Password)
        else:
            self.pushButton_3.setIcon(QIcon('files/app_images/password.png'))
            self.password_vis = True
            self.lineEdit_2.setEchoMode(QLineEdit.Normal)
            self.lineEdit_3.setEchoMode(QLineEdit.Normal)

    def lets_reg(self):
        th = Thread(target=self.check_data, args=[])
        th.start()
        QTimer.singleShot(8500, self.close_reg)

    def registrator_procedure(self):
        path = 'files/outgoing/register.encr'
        open(path, 'w', encoding='utf-8').write(
            f'{self.lineEdit_4.text()} {self.lineEdit.text()} {self.lineEdit_3.text()}')
        ssh = createSSHClient("188.68.223.151", 22, "visitor", password=PASSWORD_VISITOR)
        scp = SCPClient(ssh.get_transport())
        scp.put(path, 'incoming')
        scp.close()
        ssh.close()
        os.remove(path)
        self.statusBar.showMessage('                           Запрос отправлен', 5000)
        time.sleep(1)
        self.wait_reg()

    def close_reg(self):
        if self.reg_status:
            self.login_obj.lineEdit.setText(self.lineEdit.text())
            self.login_obj.lineEdit_2.setText(self.lineEdit_3.text())
            self.login_obj.statusBar.showMessage('              Регистрация прошла успешно', 4000)
            self.close()
        else:
            self.statusBar.showMessage('                  Ошибка регистрации', 4000)

    def wait_reg(self):
        ssh = createSSHClient("188.68.223.151", 22, "visitor", password=PASSWORD_VISITOR)
        find = False
        for i in range(5):
            time.sleep(1)
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("ls outgoing")
            data = ssh_stdout.read()
            if f'{self.lineEdit.text()}_reg.encr' in str(data):
                find = True
                break
        if find:
            scp = SCPClient(ssh.get_transport())
            scp.get(f'outgoing/{self.lineEdit.text()}_reg.encr', 'files/incoming')
            ssh.close()
            scp.close()
            file = open(f'files/incoming/{self.lineEdit.text()}_reg.encr', 'r', encoding='utf-8').read()
            os.remove(f'files/incoming/{self.lineEdit.text()}_reg.encr')
            if file == 'error':
                self.statusBar.showMessage('Ошибка при регистрации, проверьте вводимые данные', 5000)
            elif file == '200':
                self.statusBar.showMessage('                                Успешно', 5000)
                self.reg_status = True
        else:
            self.statusBar.showMessage('Сервер не отвечает, попробуйте позже', 5000)

    def check_data(self):
        try:
            if not self.lineEdit.text():
                raise Exception('                            Введите логин')
            if not self.lineEdit_4.text():
                raise Exception('                              Введите имя')
            if self.lineEdit_2.text() != self.lineEdit_3.text():
                raise Exception('                      Пароли не совпадают')
            if len(self.lineEdit_2.text()) < 8:
                raise Exception('      Пароль короткий, минимум 8 символов')
            self.check_login()
            self.registrator_procedure()
        except Exception as e:
            self.statusBar.showMessage(str(e), 5000)

    def check_login(self):
        path = 'files/outgoing/check_login.encr'
        open(path, 'w', encoding='utf-8').write(
            f'{self.lineEdit.text()}')
        ssh = createSSHClient("188.68.223.151", 22, "visitor", password=PASSWORD_VISITOR)
        scp = SCPClient(ssh.get_transport())
        scp.put(path, 'incoming')
        scp.close()
        os.remove(path)
        find = False
        for i in range(5):
            time.sleep(1)
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("ls outgoing")
            data = ssh_stdout.read()
            if f'{self.lineEdit.text()}_check_login.encr' in str(data):
                find = True
                break
        if find:
            ssh = createSSHClient("188.68.223.151", 22, "visitor", password=PASSWORD_VISITOR)
            scp = SCPClient(ssh.get_transport())
            scp.get(f'outgoing/{self.lineEdit.text()}_check_login.encr', 'files/incoming')
            ssh.close()
            scp.close()
            file = open(f'files/incoming/{self.lineEdit.text()}_check_login.encr', 'r', encoding='utf-8').read()
            os.remove(f'files/incoming/{self.lineEdit.text()}_check_login.encr')
            if file == '200':
                raise Exception('                       Такой логин уже есть')
        else:
            raise Exception('         Сервер не отвечает, попробуйте позже')

    def keyPressEvent(self, event):
        if event.key() == 16777220:
            self.check_data()


class DialogWindow(QMainWindow):
    def __init__(self, login, password):
        super().__init__()
        uic.loadUi('templates/ChatsWindow.ui', self)
        self.login = login
        self.password = password
        self.list_chats = []
        self.list_buttons = []
        self.statusBar.showMessage('Загрузка списка пользователей', 5000)
        self.initUI()

    def initUI(self):
        self.pushButton.clicked.connect(self.lets_new_chat)
        self.pushButton_3.clicked.connect(self.edit_profile)
        self.pushButton_5.clicked.connect(self.find_chats)
        self.pushButton_7.clicked.connect(self.reload)
        th = Thread(target=self.update_list_chats, args=[])
        th.start()
        QTimer.singleShot(5500, self.load_window)

    def find_chats(self):
        find_text = self.lineEdit.text()
        self.listWidget.clear()
        list(map(lambda x: self.make_buttons(x, find_text), self.list_chats))

    def lets_new_chat(self):
        self.new_chat = NewChatWindow(self.login, self.password, self)
        self.new_chat.show()

    def update_list_chats(self):
        path = 'files/outgoing/get_chats.encr'
        open(path, 'w', encoding='utf-8').write(
            f'{self.login} {self.password}')
        ssh = createSSHClient("188.68.223.151", 22, "visitor", password=PASSWORD_VISITOR)
        scp = SCPClient(ssh.get_transport())
        scp.put(path, 'incoming')
        os.remove(path)
        scp.close()
        ssh.close()
        self.wait_chats()

    def wait_chats(self):
        ssh = createSSHClient("188.68.223.151", 22, "visitor", password=PASSWORD_VISITOR)
        find = False
        for i in range(5):
            time.sleep(1)
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("ls outgoing")
            data = ssh_stdout.read()
            if f'{self.login}_chats.encr' in str(data):
                find = True
                break
        if find:
            ssh = createSSHClient("188.68.223.151", 22, "visitor", password=PASSWORD_VISITOR)
            scp = SCPClient(ssh.get_transport())
            scp.get(f'outgoing/{self.login}_chats.encr', 'files/incoming')
            ssh.close()
            scp.close()
            file = open(f'files/incoming/{self.login}_chats.encr', 'r', encoding='utf-8').read()
            os.remove(f'files/incoming/{self.login}_chats.encr')
            if file == '403':
                self.statusBar.showMessage('                      Ошибка доступа', 5000)
            else:
                data = json.loads(file)
                if data:
                    self.list_chats = data
                else:
                    self.list_chats = ['200']
        else:
            self.statusBar.showMessage('Сервер не отвечает, попробуйте позже', 5000)

    def load_window(self):
        if self.list_chats:
            if self.list_chats[0] != '200':
                self.listWidget.clear()
                list(map(lambda x: self.make_buttons(x), self.list_chats))
            else:
                self.statusBar.showMessage('                      Активные чаты не найдены', 5000)
        else:
            self.statusBar.showMessage('                      Ошибка доступа', 5000)

    def make_buttons(self, data, find_text=''):
        mate = data[1][2] if data[1][2] != self.login else data[2][2]
        if not find_text or find_text.strip().lower() in mate.strip().lower():
            button = QPushButton(f'{mate}')
            button.clicked.connect(self.open_chat)
            list_widget_item = QListWidgetItem()
            list_widget_item.setSizeHint(QSize(25, 50))
            self.listWidget.addItem(list_widget_item)
            self.listWidget.setItemWidget(list_widget_item, button)

    def open_chat(self):
        self.chat = ChatWindows()
        self.chat.show()

    def edit_profile(self):
        self.profile = ProfileWindow(self.login, self.password, self)
        self.profile.show()

    def reload(self):
        self.update_list_chats()


class ProfileWindow(QMainWindow):
    def __init__(self, login, password, dialog_self):
        super().__init__()
        uic.loadUi('templates/ProfileWindow.ui', self)
        self.user_data = []
        self.login = login
        self.password = password
        self.statusBar.showMessage('                  Загрузка данных пользователя', 5000)
        self.pushButton_4.setVisible(False)
        self.dialog_obj = dialog_self
        th = Thread(target=self.get_user_data, args=[])
        th.start()
        QTimer.singleShot(5500, self.initUI)

    def initUI(self):
        self.pushButton_4.clicked.connect(self.save_data)
        self.lineEdit_2.setEnabled(False)
        self.lineEdit.setText(self.user_data[1])
        self.lineEdit.textChanged.connect(self.check_data)
        self.lineEdit_2.setText(self.login)
        self.pushButton_2.clicked.connect(self.change_password)

    def change_password(self):
        self.password_window = ChangePasswordWindow(self)
        self.password_window.show()

    def save_data(self):
        path = 'files/outgoing/change_user_data.encr'
        open(path, 'w', encoding='utf-8').write(
            f'{self.login} {self.password} name {self.lineEdit.text()}')
        ssh = createSSHClient("188.68.223.151", 22, "visitor", password=PASSWORD_VISITOR)
        scp = SCPClient(ssh.get_transport())
        scp.put(path, 'incoming')
        os.remove(path)
        scp.close()
        ssh.close()
        self.wait_change_data()

    def wait_change_data(self):
        ssh = createSSHClient("188.68.223.151", 22, "visitor", password=PASSWORD_VISITOR)
        find = False
        for i in range(5):
            time.sleep(1)
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("ls outgoing")
            data = ssh_stdout.read()
            if f'{self.login}_change_user_data.encr' in str(data):
                find = True
                break
        if find:
            ssh = createSSHClient("188.68.223.151", 22, "visitor", password=PASSWORD_VISITOR)
            scp = SCPClient(ssh.get_transport())
            scp.get(f'outgoing/{self.login}_change_user_data.encr', 'files/incoming')
            ssh.close()
            scp.close()
            file = open(f'files/incoming/{self.login}_change_user_data.encr', 'r', encoding='utf-8').read()
            os.remove(f'files/incoming/{self.login}_change_user_data.encr')
            if file == '200':
                self.user_data[1] = self.lineEdit.text()
                self.pushButton_4.setVisible(False)
                self.statusBar.showMessage('                Успешно изменено', 5000)
            else:
                self.statusBar.showMessage('                  Ошибка доступа', 5000)
        else:
            self.statusBar.showMessage('Сервер не отвечает, попробуйте позже', 5000)

    def check_data(self):
        if self.lineEdit.text() != self.user_data[1]:
            self.pushButton_4.setVisible(True)
        else:
            self.pushButton_4.setVisible(False)

    def get_user_data(self):
        path = 'files/outgoing/get_data_users.encr'
        open(path, 'w', encoding='utf-8').write(
            f'{self.login} {self.password}')
        ssh = createSSHClient("188.68.223.151", 22, "visitor", password=PASSWORD_VISITOR)
        scp = SCPClient(ssh.get_transport())
        scp.put(path, 'incoming')
        os.remove(path)
        scp.close()
        ssh.close()
        self.wait_user_data()

    def wait_user_data(self):
        ssh = createSSHClient("188.68.223.151", 22, "visitor", password=PASSWORD_VISITOR)
        find = False
        for i in range(5):
            time.sleep(1)
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("ls outgoing")
            data = ssh_stdout.read()
            if f'{self.login}_get_data_user.encr' in str(data):
                find = True
                break
        if find:
            ssh = createSSHClient("188.68.223.151", 22, "visitor", password=PASSWORD_VISITOR)
            scp = SCPClient(ssh.get_transport())
            scp.get(f'outgoing/{self.login}_get_data_user.encr', 'files/incoming')
            ssh.close()
            scp.close()
            file = json.loads(open(f'files/incoming/{self.login}_get_data_user.encr', 'r', encoding='utf-8').read())
            os.remove(f'files/incoming/{self.login}_get_data_user.encr')
            if file == '403':
                self.statusBar.showMessage('                  Ошибка доступа', 5000)
            else:
                self.user_data = file
        else:
            self.statusBar.showMessage('Сервер не отвечает, попробуйте позже', 5000)


class ChangePasswordWindow(QMainWindow):
    def __init__(self, profile_self):
        super().__init__()
        uic.loadUi('templates/ChangePasswordWindow.ui', self)
        self.password_vis = False
        self.password_change = False
        self.profile_obj = profile_self
        self.login = profile_self.login
        self.password = profile_self.password
        self.initUI()

    def initUI(self):
        self.lineEdit.setEchoMode(QLineEdit.Password)
        self.lineEdit_2.setEchoMode(QLineEdit.Password)
        self.pushButton.clicked.connect(self.lets_check_password)
        self.pushButton_2.clicked.connect(self.change_visible)

    def lets_check_password(self):
        th = Thread(target=self.check_data, args=[])
        th.start()
        QTimer.singleShot(5500, self.close_window)

    def close_window(self):
        if self.password_change:
            self.profile_obj.statusBar.showMessage('            Пароль успешно изменен')
            self.close()
        else:
            self.statusBar.showMessage('      Ошибка смены пароля')

    def check_data(self):
        try:
            if self.lineEdit_2.text() != self.lineEdit.text():
                raise Exception('                      Пароли не совпадают')
            if len(self.lineEdit_2.text()) < 8:
                raise Exception('      Пароль короткий, минимум 8 символов')
            self.change_procedure()
        except Exception as e:
            self.statusBar.showMessage(str(e), 3500)

    def change_procedure(self):
        path = 'files/outgoing/change_user_data.encr'
        open(path, 'w', encoding='utf-8').write(
            f'{self.login} {self.password} password {self.lineEdit_2.text()}')
        ssh = createSSHClient("188.68.223.151", 22, "visitor", password=PASSWORD_VISITOR)
        scp = SCPClient(ssh.get_transport())
        scp.put(path, 'incoming')
        os.remove(path)
        scp.close()
        ssh.close()
        self.wait_change_data()

    def wait_change_data(self):
        ssh = createSSHClient("188.68.223.151", 22, "visitor", password=PASSWORD_VISITOR)
        find = False
        for i in range(5):
            time.sleep(1)
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("ls outgoing")
            data = ssh_stdout.read()
            if f'{self.login}_change_user_data.encr' in str(data):
                find = True
                break
        if find:
            ssh = createSSHClient("188.68.223.151", 22, "visitor", password=PASSWORD_VISITOR)
            scp = SCPClient(ssh.get_transport())
            scp.get(f'outgoing/{self.login}_change_user_data.encr', 'files/incoming')
            ssh.close()
            scp.close()
            file = open(f'files/incoming/{self.login}_change_user_data.encr', 'r', encoding='utf-8').read()
            os.remove(f'files/incoming/{self.login}_change_user_data.encr')
            if file == '200':
                self.password = self.lineEdit_2.text()
                self.profile_obj.password = self.lineEdit_2.text()
                self.profile_obj.dialog_obj.password = self.lineEdit_2.text()
                self.password_change = True
                self.statusBar.showMessage('                Успешно изменено', 5000)
            else:
                self.statusBar.showMessage('                  Ошибка доступа', 5000)
        else:
            self.statusBar.showMessage('Сервер не отвечает, попробуйте позже', 5000)

    def change_visible(self):
        if self.password_vis:
            self.pushButton_2.setIcon(QIcon('files/app_images/none_password.png'))
            self.password_vis = False
            self.lineEdit.setEchoMode(QLineEdit.Password)
            self.lineEdit_2.setEchoMode(QLineEdit.Password)
        else:
            self.pushButton_2.setIcon(QIcon('files/app_images/password.png'))
            self.password_vis = True
            self.lineEdit.setEchoMode(QLineEdit.Normal)
            self.lineEdit_2.setEchoMode(QLineEdit.Normal)


class NewChatWindow(QMainWindow):
    def __init__(self, login, password, dialogs_self):
        super().__init__()
        uic.loadUi('templates/NewChatWindow.ui', self)
        self.data_users = []
        self.login = login
        self.password = password
        self.dialog_obj = dialogs_self
        self.statusBar.showMessage('Загрузка списка пользователей', 3000)
        self.initUI()

    def initUI(self):
        self.pushButton.clicked.connect(self.find_user)
        th = Thread(target=self.lets_new_chat, args=[])
        th.start()
        QTimer.singleShot(5000, self.load_users)

    def lets_new_chat(self):
        path = 'files/outgoing/get_new_chat.encr'
        open(path, 'w', encoding='utf-8').write(
            f'{self.login} {self.password}')
        ssh = createSSHClient("188.68.223.151", 22, "visitor", password=PASSWORD_VISITOR)
        scp = SCPClient(ssh.get_transport())
        scp.put(path, 'incoming')
        os.remove(path)
        scp.close()
        ssh.close()
        self.wait_new_chat()

    def wait_new_chat(self):
        ssh = createSSHClient("188.68.223.151", 22, "visitor", password=PASSWORD_VISITOR)
        find = False
        for i in range(5):
            time.sleep(1)
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("ls outgoing")
            data = ssh_stdout.read()
            if f'{self.login}_new_chat.encr' in str(data):
                find = True
                break
        if find:
            ssh = createSSHClient("188.68.223.151", 22, "visitor", password=PASSWORD_VISITOR)
            scp = SCPClient(ssh.get_transport())
            scp.get(f'outgoing/{self.login}_new_chat.encr', 'files/incoming')
            ssh.close()
            scp.close()
            file = json.loads(open(f'files/incoming/{self.login}_new_chat.encr', 'r', encoding='utf-8').read())
            os.remove(f'files/incoming/{self.login}_new_chat.encr')
            self.data_users = file
        else:
            self.statusBar.showMessage('Сервер не отвечает, попробуйте позже', 5000)

    def load_users(self):
        if self.data_users:
            self.listWidget.clear()
            list(map(lambda x: self.make_buttons(x[2]), self.data_users))
        else:
            self.statusBar.showMessage('Ошибка загрузки списка пользователей', 5000)

    def make_buttons(self, login, find_text=''):
        if not find_text or find_text.strip().lower() in login.strip().lower():
            button = QPushButton(login)
            button.clicked.connect(self.new_chat)
            list_widget_item = QListWidgetItem()
            list_widget_item.setSizeHint(QSize(25, 50))
            self.listWidget.addItem(list_widget_item)
            self.listWidget.setItemWidget(list_widget_item, button)

    def new_chat(self):
        path = 'files/outgoing/create_chat.encr'
        open(path, 'w', encoding='utf-8').write(
            f'{self.login} {self.password} {self.sender().text()}')
        ssh = createSSHClient("188.68.223.151", 22, "visitor", password=PASSWORD_VISITOR)
        scp = SCPClient(ssh.get_transport())
        scp.put(path, 'incoming')
        os.remove(path)
        scp.close()
        ssh.close()
        self.wait_chat()

    def wait_chat(self):
        ssh = createSSHClient("188.68.223.151", 22, "visitor", password=PASSWORD_VISITOR)
        find = False
        for i in range(5):
            time.sleep(1)
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("ls outgoing")
            data = ssh_stdout.read()
            if f'{self.login}_create.encr' in str(data):
                find = True
                break
        if find:
            ssh = createSSHClient("188.68.223.151", 22, "visitor", password=PASSWORD_VISITOR)
            scp = SCPClient(ssh.get_transport())
            scp.get(f'outgoing/{self.login}_create.encr', 'files/incoming')
            ssh.close()
            scp.close()
            file = json.loads(open(f'files/incoming/{self.login}_create.encr', 'r', encoding='utf-8').read())
            os.remove(f'files/incoming/{self.login}_create.encr')
            if file == '200':
                self.creating_chat()
            elif file == '404':
                self.statusBar.showMessage('    Такой пользователь не найден', 5000)
            elif file == '403':
                self.statusBar.showMessage('                  Ошибка доступа', 5000)
        else:
            self.statusBar.showMessage('Сервер не отвечает, попробуйте позже', 5000)

    def creating_chat(self):
        self.dialog_obj.update_list_chats()
        self.close()

    def find_user(self):
        self.listWidget.clear()
        find_text = self.lineEdit.text()
        list(map(lambda x: self.make_buttons(x[2], find_text), self.data_users))


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
