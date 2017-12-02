# Copyright 2017 GABRIEL JABLONSKI
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from PyQt5 import QtCore, QtGui, QtWidgets
import os
import stat
import subprocess
import threading
import time
import webbrowser

run_list = {}
compiled_list = {}

original_wd = os.getcwd()
user_count = 0
user_number = 0
progress_count = 0
progress_max = 0
run_total = 0
run_count = 1
users_file_info = {}
users_compiled = {}
output_verification = -1
compiled = False

clone_buffer = []
compile_buffer = []
output_buffer = []


def rmtree(path):  # alternative to shutil.rmtree()
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            filename = os.path.join(root, name)
            os.chmod(filename, stat.S_IWUSR)
            os.remove(filename)
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(path)


def _clone(user):
    user_path = original_wd + "\\Usuarios\\" + user[0]
    os.chdir(original_wd + "\\Usuarios\\")
    if os.path.exists(user_path):
        rmtree(user_path)

    clone_buffer.append("#Clonando repositório de %s..." % user[0])
    p = subprocess.Popen(["git", "clone", "http://github.com/%s/%s" % (user[0], user[1]), user[0]],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         creationflags=0x08000000)
    clone_response = p.communicate()
    if 'fatal' in clone_response[1].decode('latin-1'):
        clone_buffer.append("#Erro ao clonar respositório de %s. Erro: %s" %
                            (user[0], clone_response[1].decode('latin-1')))
    else:
        clone_buffer.append("-Repositório de %s clonado com sucesso." % user[0])

    global user_number, user_count

    user_count += 1
    if user_count == user_number:
        clone_buffer.append("==Clonagem finalizada.")

# def queue_compile(users, c_files_list):
#     for user in users:
#         _compile(user, c_files_list)


def _compile(user, c_files_list):
    global progress_count, compiled
    if user not in users_file_info:
        users_file_info[user] = [[], []]
    user_c_files = []
    user_log = open(original_wd + "\\Compilados\\" + user + "\\%s_log.txt" % user, "w")
    user_log.write("Compilando\n" + 60 * "-" + "\n")
    compile_buffer.append("--" + user + " iniciado.")
    for root, dirs, files in os.walk(os.path.join(original_wd, "Usuarios", user)):
        for name in files:
            if name[-2:] == ".c":
                user_c_files.append(name)
                if name in c_files_list:
                    comp_process = subprocess.Popen(["g++", "-o",
                                                     os.path.join(original_wd,
                                                                  "Compilados\\%s\\%s.exe" % (user, name[0:-2])),
                                                     os.path.join(root, name)], stdin=subprocess.PIPE,
                                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                                    creationflags=0x08000000)
                    comp_response = comp_process.communicate()[1].decode('UTF-8')
                    if comp_response is "":
                        compile_buffer.append("#%s: %s compilado com sucesso." % (user, name))
                        user_log.write("#%s compilado com sucesso.\n" % name)
                        users_file_info[user][0].append(name)
                    else:
                        compile_buffer.append("--Erro ao compilar " + name + ". Erro: \n\n" + comp_response + "\n\n")
                        user_log.write("\n--Erro ao compilar " + name + ". Erro: \n===============\n" + comp_response
                                       + "\n===============\n\n")
                        pass
                    progress_count += 1

    user_log.write("\n")

    for c_file in c_files_list:
        if c_file not in user_c_files:
            compile_buffer.append("#%s: %s não encontrado.\n" % (user, c_file))
            user_log.write("#%s não encontrado.\n" % c_file)
            time.sleep(1)
            progress_count += 1
    compile_buffer.append("--%s finalizado.\n" % user)
    user_log.write(60 * "-" + "\n")

    user_log.close()

    global user_number, user_count

    user_count += 1
    if user_count == user_number:
        compile_buffer.append("==Compilação finalizada.")
        compiled = True


def _run(run_list, user_list):
    global output_verification, compiled_list, run_total, run_count
    compiled_list = {}
    for user in user_list:
        compiled_list[user] = []
        if not compiled:
            users_file_info[user] = [[], []]

        for root, dirs, files in os.walk(os.getcwd() + "\\Compilados\\" + user):
            for name in files:
                if name[-4:] == ".exe":
                    compiled_list[user].append(name)
                    if name[:-4] in run_list:
                        run_total += 1

    for user in user_list:
        user_log = open(original_wd + '\\Compilados\\' + user + '\\%s_log.txt' % user, 'a')
        user_log.write("Rodando\n" + 60*'-' + '\n')
        for name in compiled_list[user]:
            if name[0:-4] in run_list:
                user_log.write('#' + name + '\n')
                output_buffer.append('#%s: %s' % (user, name))
                time_out = 0
                prog_input, prog_output = run_list[name[0:-4]][0], run_list[name[0:-4]][1]
                run_process = subprocess.Popen(["%s" % os.path.join(original_wd, "Compilados", user, name)],
                                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE, creationflags=0x08000000)
                run_process.stdin.write(bytes(prog_input, 'UTF-8'))
                try:
                    run_response = run_process.communicate(timeout=1)[0].decode('latin-1')
                except Exception:
                    output_buffer.append("====Tempo de execução excedido.")
                    user_log.write("==Tempo de execução excedido.\n")
                    time_out = 1
                if not time_out:
                    user_log.write("--Entrada fornecida: '%s'\n" % prog_input)
                    try:
                        user_log.write("--Saída do programa:\n" + 45 * "\\" + "\n%s\n"
                                       % run_response + 45 * "/" + "\n")
                    except Exception:
                        user_log.write("--Saída inesperada.\n")
                    user_log.write("--Saída esperada: '%s'\n" % prog_output)
                    output_buffer.append("--Entrada fornecida: '%s'\n" % prog_input)
                    output_buffer.append("--Saída do programa:\n" + 45 * "\\" + "\n%s\n"
                                         % run_response + 45 * "/" + "\n")
                    output_buffer.append("--Saída esperada: '%s'\n" % prog_output)

                    while 1:
                        if output_verification == 1:
                            user_log.write("==Saída correta!\n\n")
                            run_count += 1
                            users_file_info[user][1].append(name)
                            output_verification = -1
                            break
                        elif output_verification == 0:
                            user_log.write("==Saída incorreta!\n\n")
                            run_count += 1
                            output_verification = -1
                            break
                        time.sleep(.5)
                else:
                    output_buffer.append("Pressionar qualquer botão para continuar.")
                    while 1:
                        if output_verification == 1 or output_verification == 0:
                            output_verification = -1
                            run_count += 1
                            break
                        time.sleep(.5)

            elif name[-4:] == '.exe':
                users_file_info[user][1].append(name)

        if not compiled:
            for file in compiled_list[user]:
                users_file_info[user][0].append(file[:-4] + '.c')
        output_buffer.append("%s finalizado.\n" % user)
        user_log.write(60 * "-" + "\n")
        user_log.close()
    output_buffer.append("Finalizado.\n")


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(380, 510)
        self.centralWidget = QtWidgets.QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")
        self.tabWidget = QtWidgets.QTabWidget(self.centralWidget)
        self.tabWidget.setGeometry(QtCore.QRect(0, 0, 381, 501))
        self.tabWidget.setObjectName("tabWidget")
        self.cloneTab = QtWidgets.QWidget()
        self.cloneTab.setObjectName("cloneTab")
        self.lineUserEntry = QtWidgets.QLineEdit(self.cloneTab)
        self.lineUserEntry.setGeometry(QtCore.QRect(10, 10, 111, 20))
        self.lineUserEntry.setObjectName("lineUserEntry")
        self.btnAddUser = QtWidgets.QPushButton(self.cloneTab)
        self.btnAddUser.setGeometry(QtCore.QRect(10, 40, 111, 21))
        self.btnAddUser.setObjectName("btnAddUser")
        self.btnRemoveUser = QtWidgets.QPushButton(self.cloneTab)
        self.btnRemoveUser.setGeometry(QtCore.QRect(260, 130, 101, 21))
        self.btnRemoveUser.setObjectName("btnRemoveUser")
        self.lineRepEntry = QtWidgets.QLineEdit(self.cloneTab)
        self.lineRepEntry.setGeometry(QtCore.QRect(140, 10, 41, 20))
        self.lineRepEntry.setObjectName("lineRepEntry")
        self.lineListEntry = QtWidgets.QLineEdit(self.cloneTab)
        self.lineListEntry.setGeometry(QtCore.QRect(10, 70, 111, 20))
        self.lineListEntry.setObjectName("lineListEntry")
        self.btnAddList = QtWidgets.QPushButton(self.cloneTab)
        self.btnAddList.setGeometry(QtCore.QRect(10, 100, 111, 21))
        self.btnAddList.setObjectName("btnAddList")
        self.btnClone = QtWidgets.QPushButton(self.cloneTab)
        self.btnClone.setGeometry(QtCore.QRect(140, 40, 221, 81))
        self.btnClone.setObjectName("btnClone")
        self.btnRemoveAll = QtWidgets.QPushButton(self.cloneTab)
        self.btnRemoveAll.setGeometry(QtCore.QRect(260, 160, 101, 21))
        self.btnRemoveAll.setObjectName("btnRemoveAll")
        self.textCloneLog = QtWidgets.QTextEdit(self.cloneTab)
        self.textCloneLog.setGeometry(QtCore.QRect(10, 330, 351, 121))
        self.textCloneLog.setObjectName("textCloneLog")
        self.textCloneLog.setReadOnly(1)
        self.treeCloneUsers = QtWidgets.QTreeWidget(self.cloneTab)
        self.treeCloneUsers.setGeometry(QtCore.QRect(10, 130, 241, 192))
        self.treeCloneUsers.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustIgnored)
        self.treeCloneUsers.setObjectName("treeCloneUsers")
        self.treeCloneUsers.header().setDefaultSectionSize(138)
        self.pushButton = QtWidgets.QPushButton(self.cloneTab)
        self.pushButton.setGeometry(QtCore.QRect(260, 190, 101, 51))
        self.pushButton.setObjectName("pushButton")
        self.tabWidget.addTab(self.cloneTab, "")
        self.compileTab = QtWidgets.QWidget()
        self.compileTab.setObjectName("compileTab")
        self.listUsers = QtWidgets.QListWidget(self.compileTab)
        self.listUsers.setGeometry(QtCore.QRect(10, 30, 111, 181))
        self.listUsers.setObjectName("listUsers")
        self.labelUsers = QtWidgets.QLabel(self.compileTab)
        self.labelUsers.setGeometry(QtCore.QRect(10, 10, 47, 13))
        self.labelUsers.setObjectName("labelUsers")
        self.lineFileName = QtWidgets.QLineEdit(self.compileTab)
        self.lineFileName.setGeometry(QtCore.QRect(130, 160, 111, 21))
        self.lineFileName.setObjectName("lineFileName")
        self.btnAddFile = QtWidgets.QPushButton(self.compileTab)
        self.btnAddFile.setGeometry(QtCore.QRect(130, 190, 111, 21))
        self.btnAddFile.setObjectName("btnAddFile")
        self.btnAddFileList = QtWidgets.QPushButton(self.compileTab)
        self.btnAddFileList.setGeometry(QtCore.QRect(250, 190, 111, 21))
        self.btnAddFileList.setObjectName("btnAddFileList")
        self.lineEdit = QtWidgets.QLineEdit(self.compileTab)
        self.lineEdit.setGeometry(QtCore.QRect(250, 160, 111, 20))
        self.lineEdit.setObjectName("lineEdit")
        self.btnCompile = QtWidgets.QPushButton(self.compileTab)
        self.btnCompile.setGeometry(QtCore.QRect(10, 220, 351, 41))
        self.btnCompile.setObjectName("btnCompile")
        self.listFiles = QtWidgets.QListWidget(self.compileTab)
        self.listFiles.setGeometry(QtCore.QRect(130, 30, 111, 121))
        self.listFiles.setObjectName("listFiles")
        self.labelFile = QtWidgets.QLabel(self.compileTab)
        self.labelFile.setGeometry(QtCore.QRect(130, 10, 81, 16))
        self.labelFile.setObjectName("labelFile")
        self.textCompileLog = QtWidgets.QTextEdit(self.compileTab)
        self.textCompileLog.setGeometry(QtCore.QRect(10, 300, 351, 131))
        self.textCompileLog.setObjectName("textCompileLog")
        self.textCompileLog.setReadOnly(1)
        self.progressBar = QtWidgets.QProgressBar(self.compileTab)
        self.progressBar.setGeometry(QtCore.QRect(10, 270, 361, 23))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.btnRemoveFile = QtWidgets.QPushButton(self.compileTab)
        self.btnRemoveFile.setGeometry(QtCore.QRect(250, 30, 111, 23))
        self.btnRemoveFile.setObjectName("btnRemoveFile")
        self.btnRemoveAll_2 = QtWidgets.QPushButton(self.compileTab)
        self.btnRemoveAll_2.setGeometry(QtCore.QRect(250, 60, 111, 23))
        self.btnRemoveAll_2.setObjectName("btnRemoveAll_2")
        self.comboUser = QtWidgets.QComboBox(self.compileTab)
        self.comboUser.setGeometry(QtCore.QRect(10, 440, 121, 22))
        self.comboUser.setObjectName("comboUser")
        self.btnVerifyLog = QtWidgets.QPushButton(self.compileTab)
        self.btnVerifyLog.setGeometry(QtCore.QRect(140, 440, 221, 23))
        self.btnVerifyLog.setObjectName("btnVerifyLog")
        self.btnVerifyLog.setDisabled(1)
        self.tabWidget.addTab(self.compileTab, "")
        self.runTab = QtWidgets.QWidget()
        self.runTab.setObjectName("runTab")
        self.labelInput = QtWidgets.QLabel(self.runTab)
        self.labelInput.setGeometry(QtCore.QRect(10, 150, 47, 13))
        self.labelInput.setObjectName("labelInput")
        self.labelOutput = QtWidgets.QLabel(self.runTab)
        self.labelOutput.setGeometry(QtCore.QRect(140, 150, 111, 16))
        self.labelOutput.setObjectName("labelOutput")
        self.lineInput = QtWidgets.QLineEdit(self.runTab)
        self.lineInput.setGeometry(QtCore.QRect(10, 170, 111, 20))
        self.lineInput.setObjectName("lineInput")
        self.lineOutput = QtWidgets.QLineEdit(self.runTab)
        self.lineOutput.setGeometry(QtCore.QRect(140, 170, 111, 20))
        self.lineOutput.setObjectName("lineOutput")
        self.tableFiles = QtWidgets.QTreeWidget(self.runTab)
        self.tableFiles.setGeometry(QtCore.QRect(10, 10, 351, 91))
        self.tableFiles.setObjectName("tableFiles")
        self.tableFiles.header().setDefaultSectionSize(116)
        self.comboFiles = QtWidgets.QComboBox(self.runTab)
        self.comboFiles.setGeometry(QtCore.QRect(10, 120, 101, 21))
        self.comboFiles.setObjectName("comboFiles")
        self.checkNoOutput = QtWidgets.QCheckBox(self.runTab)
        self.checkNoOutput.setGeometry(QtCore.QRect(140, 120, 141, 17))
        self.checkNoOutput.setObjectName("checkNoOutput")
        self.btnUpdate = QtWidgets.QPushButton(self.runTab)
        self.btnUpdate.setGeometry(QtCore.QRect(260, 150, 101, 41))
        self.btnUpdate.setObjectName("btnUpdate")
        self.textFileOutput = QtWidgets.QTextEdit(self.runTab)
        self.textFileOutput.setGeometry(QtCore.QRect(10, 250, 351, 171))
        self.textFileOutput.setObjectName("textFileOutput")
        self.textFileOutput.setReadOnly(1)
        self.btnRun = QtWidgets.QPushButton(self.runTab)
        self.btnRun.setGeometry(QtCore.QRect(10, 200, 351, 41))
        self.btnRun.setObjectName("btnRun")
        self.btnRight = QtWidgets.QPushButton(self.runTab)
        self.btnRight.setGeometry(QtCore.QRect(10, 430, 171, 31))
        self.btnRight.setObjectName("btnRight")
        self.btnWrong = QtWidgets.QPushButton(self.runTab)
        self.btnWrong.setGeometry(QtCore.QRect(190, 430, 171, 31))
        self.btnWrong.setObjectName("btnWrong")
        self.tabWidget.addTab(self.runTab, "")
        self.resultsTab = QtWidgets.QWidget()
        self.resultsTab.setObjectName("resultsTab")
        self.treeUsers = QtWidgets.QTreeWidget(self.resultsTab)
        self.treeUsers.setGeometry(QtCore.QRect(10, 10, 351, 181))
        self.treeUsers.setObjectName("treeUsers")
        self.treeUsers.header().setCascadingSectionResizes(False)
        self.treeUsers.header().setDefaultSectionSize(124)
        self.comboUser_2 = QtWidgets.QComboBox(self.resultsTab)
        self.comboUser_2.setGeometry(QtCore.QRect(10, 200, 111, 21))
        self.comboUser_2.setObjectName("comboUser_2")
        self.treeFiles = QtWidgets.QTreeWidget(self.resultsTab)
        self.treeFiles.setGeometry(QtCore.QRect(10, 230, 161, 181))
        self.treeFiles.setObjectName("treeFiles")
        self.treeFiles.header().setDefaultSectionSize(59)
        self.comboFile = QtWidgets.QComboBox(self.resultsTab)
        self.comboFile.setGeometry(QtCore.QRect(130, 200, 111, 22))
        self.comboFile.setObjectName("comboFile")
        self.btnRectify = QtWidgets.QPushButton(self.resultsTab)
        self.btnRectify.setGeometry(QtCore.QRect(250, 230, 111, 23))
        self.btnRectify.setObjectName("btnRectify")
        self.btnLogs = QtWidgets.QPushButton(self.resultsTab)
        self.btnLogs.setGeometry(QtCore.QRect(180, 420, 181, 41))
        self.btnLogs.setObjectName("btnLogs")
        self.btnVerify = QtWidgets.QPushButton(self.resultsTab)
        self.btnVerify.setGeometry(QtCore.QRect(250, 200, 111, 23))
        self.btnVerify.setObjectName("btnVerify")
        self.textOutput = QtWidgets.QTextEdit(self.resultsTab)
        self.textOutput.setGeometry(QtCore.QRect(180, 260, 181, 151))
        self.textOutput.setObjectName("textOutput")
        self.textOutput.setReadOnly(1)
        self.lineLog = QtWidgets.QLineEdit(self.resultsTab)
        self.lineLog.setGeometry(QtCore.QRect(60, 430, 113, 20))
        self.lineLog.setObjectName("lineLog")
        self.tabWidget.addTab(self.resultsTab, "")
        MainWindow.setCentralWidget(self.centralWidget)
        self.statusBar = QtWidgets.QStatusBar(MainWindow)
        self.statusBar.setObjectName("statusBar")
        MainWindow.setStatusBar(self.statusBar)

        self.compileTab.setDisabled(1)
        self.runTab.setDisabled(1)
        self.resultsTab.setDisabled(1)

        ## Tab : Clonar
        self.btnAddUser.clicked.connect(self.add_user)
        self.btnAddList.clicked.connect(self.add_user_list)
        self.btnRemoveUser.clicked.connect(self.remove_user)
        self.btnRemoveAll.clicked.connect(self.remove_all)
        self.pushButton.clicked.connect(self.update_compiling)
        self.btnClone.clicked.connect(self.clone_users)

        self.clone_timer = QtCore.QTimer()
        self.clone_timer.setInterval(1000)
        self.clone_timer.timeout.connect(self.update_clone_log)

        ## Tab : Compilar
        self.btnAddFile.clicked.connect(self.add_file)
        self.btnAddFileList.clicked.connect(self.add_file_list)
        self.btnRemoveFile.clicked.connect(self.remove_file)
        self.btnRemoveAll_2.clicked.connect(self.remove_all_files)
        self.btnCompile.clicked.connect(self.compile_files)
        self.btnVerifyLog.clicked.connect(self.open_log)

        self.compile_timer = QtCore.QTimer()
        self.compile_timer.setInterval(1000)
        self.compile_timer.timeout.connect(self.update_compile_log)

        ## Tab : Rodar
        self.btnUpdate.clicked.connect(self.update_files)
        self.tableFiles.itemClicked.connect(self.new_tree_selection_run)
        self.comboFiles.currentTextChanged.connect(self.new_combo_selection_run)
        self.btnRun.clicked.connect(self.run_files)
        self.btnRight.clicked.connect(self.right_answer)
        self.btnWrong.clicked.connect(self.wrong_answer)

        self.output_timer = QtCore.QTimer()
        self.output_timer.setInterval(100)
        self.output_timer.timeout.connect(self.update_file_output)

        ## Tab : Resultados
        self.comboUser_2.currentTextChanged.connect(self.new_combo_selection_results)
        self.btnVerify.clicked.connect(self.verify_output)
        self.btnRectify.clicked.connect(self.rectify_result)
        self.treeUsers.itemClicked.connect(self.new_tree_selection_results)
        self.btnLogs.clicked.connect(self.save_log)

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Corretor MTP v1.0"))
        self.lineUserEntry.setText(_translate("MainWindow", "Usuário do Github"))
        self.btnAddUser.setText(_translate("MainWindow", "Adicionar"))
        self.btnRemoveUser.setText(_translate("MainWindow", "Remover"))
        self.lineRepEntry.setText(_translate("MainWindow", "MTP"))
        self.lineListEntry.setText(_translate("MainWindow", "lista_usuarios.txt"))
        self.btnAddList.setText(_translate("MainWindow", "Adicionar lista"))
        self.btnClone.setText(_translate("MainWindow", "Clonar\nrepositórios"))
        self.btnRemoveAll.setText(_translate("MainWindow", "Remover todos"))
        self.treeCloneUsers.headerItem().setText(0, _translate("MainWindow", "Usuário"))
        self.treeCloneUsers.headerItem().setText(1, _translate("MainWindow", "Repositório"))
        self.pushButton.setText(_translate("MainWindow", "Atualizar\nlista para\ncompilação"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.cloneTab), _translate("MainWindow", "Clonar"))
        self.labelUsers.setText(_translate("MainWindow", "Usuários:"))
        self.lineFileName.setText(_translate("MainWindow", "exemplo.c"))
        self.btnAddFile.setText(_translate("MainWindow", "Adicionar programa"))
        self.btnAddFileList.setText(_translate("MainWindow", "Adicionar lista"))
        self.lineEdit.setText(_translate("MainWindow", "lista_programas.txt"))
        self.btnCompile.setText(_translate("MainWindow", "Compilar"))
        self.labelFile.setText(_translate("MainWindow", "Programas:"))
        self.btnRemoveFile.setText(_translate("MainWindow", "Remover"))
        self.btnRemoveAll_2.setText(_translate("MainWindow", "Remover todos"))
        self.btnVerifyLog.setText(_translate("MainWindow", "Verificar log de compilação"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.compileTab), _translate("MainWindow", "Compilar"))
        self.labelInput.setText(_translate("MainWindow", "Input:"))
        self.labelOutput.setText(_translate("MainWindow", "Output esperado:"))
        self.lineInput.setText(_translate("MainWindow", "1 2 3"))
        self.lineOutput.setText(_translate("MainWindow", "Hello World!"))
        self.tableFiles.headerItem().setText(0, _translate("MainWindow", "Programa"))
        self.tableFiles.headerItem().setText(1, _translate("MainWindow", "Input"))
        self.tableFiles.headerItem().setText(2, _translate("MainWindow", "Output"))
        self.checkNoOutput.setText(_translate("MainWindow", "Desconsiderar Output"))
        self.btnUpdate.setText(_translate("MainWindow", "Atualizar"))
        self.btnRun.setText(_translate("MainWindow", "Rodar"))
        self.btnRight.setText(_translate("MainWindow", "Saída correta"))
        self.btnWrong.setText(_translate("MainWindow", "Saída incorreta"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.runTab), _translate("MainWindow", "Rodar"))
        self.treeUsers.headerItem().setText(0, _translate("MainWindow", "Usuário"))
        self.treeUsers.headerItem().setText(1, _translate("MainWindow", "Compilados"))
        self.treeUsers.headerItem().setText(2, _translate("MainWindow", "Saída correta"))
        self.treeFiles.headerItem().setText(0, _translate("MainWindow", "Programa"))
        self.treeFiles.headerItem().setText(1, _translate("MainWindow", "Saída correta?"))
        self.btnRectify.setText(_translate("MainWindow", "Retificar correção"))
        self.btnLogs.setText(_translate("MainWindow", "Gerar relatório"))
        self.btnVerify.setText(_translate("MainWindow", "Verificar outuput"))
        self.lineLog.setText(_translate("MainWindow", "notas_lab1.txt"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.resultsTab), _translate("MainWindow", "Resultados"))

    def add_user(self):
        current_users = []
        for i in range(self.treeCloneUsers.topLevelItemCount()):
            current_users.append(self.treeCloneUsers.topLevelItem(i).text(0))

        user_text = [self.lineUserEntry.text(), self.lineRepEntry.text()]

        if user_text[0] is not "":
            if user_text[0] not in current_users:
                user = QtWidgets.QTreeWidgetItem(user_text)
                self.treeCloneUsers.addTopLevelItem(user)
                self.lineUserEntry.clear()
                self.lineRepEntry.setText("MTP")

    def add_user_list(self):
        if os.path.isfile(self.lineListEntry.text()):
            user_list = []
            user_list_file = open(self.lineListEntry.text(), 'r')
            current_users = []
            for i in range(self.treeCloneUsers.topLevelItemCount()):
                current_users.append(self.treeCloneUsers.topLevelItem(i).text(0))
            for line in user_list_file:
                username, repname = line.split()
                user_list.append([username, repname, 0, 0])
            user_list_file.close()

            for user in user_list:
                if user[0] not in current_users:
                    self.treeCloneUsers.addTopLevelItem(QtWidgets.QTreeWidgetItem([user[0], user[1]]))

    def remove_user(self):
        user_to_remove = self.treeCloneUsers.selectedItems()
        if len(user_to_remove) != 0:
            self.treeCloneUsers.takeTopLevelItem(self.treeCloneUsers.indexOfTopLevelItem(user_to_remove[0]))

    def remove_all(self):
        self.treeCloneUsers.clear()

    def update_compiling(self):
        self.compileTab.setDisabled(0)
        self.listUsers.clear()
        self.comboUser.clear()
        for i in range(self.treeCloneUsers.topLevelItemCount()):
            self.listUsers.addItem(self.treeCloneUsers.topLevelItem(i).text(0))
            self.comboUser.addItem(self.treeCloneUsers.topLevelItem(i).text(0))

    def clone_users(self):
        if self.treeCloneUsers.topLevelItemCount() != 0:
            self.clone_timer.start()
            users_to_clone = []
            for i in range(self.treeCloneUsers.topLevelItemCount()):
                users_to_clone.append([self.treeCloneUsers.topLevelItem(i).text(0),
                                       self.treeCloneUsers.topLevelItem(i).text(1)])

            global user_number, user_count
            user_number = len(users_to_clone)
            user_count = 0

            if not os.path.exists(original_wd + "\\Usuarios"):
                os.mkdir("Usuarios")

            os.chdir(os.getcwd() + "\\Usuarios")

            for user in users_to_clone:
                thread_clone = threading.Thread(target=_clone, args=[user])
                thread_clone.start()

        self.btnClone.setDisabled(1)

    def update_clone_log(self):
        a = len(clone_buffer)
        for i in range(a):
            self.textCloneLog.append(clone_buffer[i])
            if clone_buffer[i] == "==Clonagem finalizada.":
                self.clone_timer.stop()
        for i in range(a):
            clone_buffer.pop(0)

    def add_file(self):
        self.runTab.setDisabled(0)
        current_files = []
        for i in range(self.listFiles.count()):
            current_files.append(self.listFiles.item(i).text())

        file_name = self.lineFileName.text()
        if file_name is not "":
            if file_name not in current_files:
                self.listFiles.addItem(file_name)
                self.tableFiles.addTopLevelItem(QtWidgets.QTreeWidgetItem([file_name, '-', '-']))
                self.comboFiles.addItem(file_name)
                if self.comboFiles.findText(" ") != -1:
                    self.comboFiles.removeItem(self.comboFiles.findText(" "))
                self.lineFileName.clear()

        if not self.tableFiles.topLevelItemCount() == 0:
            self.lineInput.setText(self.tableFiles.topLevelItem(0).text(1))
            self.lineOutput.setText(self.tableFiles.topLevelItem(0).text(2))

    def add_file_list(self):
        os.chdir(original_wd)
        if os.path.isfile(self.lineEdit.text()):
            file_list = []
            file_list_file = open(self.lineEdit.text(), 'r')
            self.runTab.setDisabled(0)
            current_files = []
            for i in range(self.listFiles.count()):
                current_files.append(self.listFiles.item(i).text())
            for line in file_list_file:
                file_name, file_input, file_output, file_run = line.split(":")
                file_list.append([file_name, file_input, file_output, file_run.split()[0]])
            file_list_file.close()

            for file in file_list:
                if file[0] not in current_files:
                    self.listFiles.addItem(file[0])
                    self.comboFiles.addItem(file[0])
                    if self.comboFiles.findText(" ") != -1:
                        self.comboFiles.removeItem(self.comboFiles.findText(" "))
                    if file[3] == '1':
                        self.tableFiles.addTopLevelItem(QtWidgets.QTreeWidgetItem([file[0], file[1], file[2]]))
                    else:
                        self.tableFiles.addTopLevelItem(QtWidgets.QTreeWidgetItem([file[0], '-', '-']))
            self.lineInput.setText(self.tableFiles.topLevelItem(0).text(1))
            self.lineOutput.setText(self.tableFiles.topLevelItem(0).text(2))

    def remove_file(self):
        file_to_remove = self.listFiles.selectedItems()
        if len(file_to_remove) != 0:
            if self.listFiles.count() == 1:
                self.comboFiles.addItem(" ")
            self.comboFiles.removeItem(self.listFiles.row(file_to_remove[0]))
            self.tableFiles.takeTopLevelItem(self.listFiles.row(file_to_remove[0]))
            self.listFiles.takeItem(self.listFiles.row(file_to_remove[0]))
        if self.tableFiles.topLevelItem(0):
            self.lineInput.setText(self.tableFiles.topLevelItem(0).text(1))
            self.lineOutput.setText(self.tableFiles.topLevelItem(0).text(2))
        else:
            self.lineInput.setText("1 2 3")
            self.lineOutput.setText("Hello World!")

    def remove_all_files(self):
        self.listFiles.clear()
        self.tableFiles.clear()
        self.comboFiles.clear()
        if self.tableFiles.topLevelItem(0):
            self.lineInput.setText(self.tableFiles.topLevelItem(0).text(1))
            self.lineOutput.setText(self.tableFiles.topLevelItem(0).text(2))
        else:
            self.lineInput.setText("1 2 3")
            self.lineOutput.setText("Hello World!")

    def compile_files(self):
        if self.listUsers.count() != 0 and self.listFiles.count() != 0:
            self.compile_timer.start()
            users_to_compile = []
            for i in range(self.listUsers.count()):
                users_to_compile.append(self.listUsers.item(i).text())

            c_files = []
            for i in range(self.listFiles.count()):
                c_files.append(self.listFiles.item(i).text())

            global progress_count, progress_max
            progress_max = len(users_to_compile) * len(c_files)
            progress_count = 0

            global user_number, user_count
            user_number = len(users_to_compile)
            user_count = 0

            if not os.path.exists(original_wd + "\\Compilados"):
                os.mkdir("Compilados")

            os.chdir(original_wd + "\\Compilados")

            self.textCompileLog.append("Compilando...\n")
            # self.textCompileLog.ensureCursorVisible()

            # delay = 0
            for user in users_to_compile:
                if not os.path.exists(original_wd + "\\Compilados\\" + user):
                    os.mkdir(original_wd + "\\Compilados\\" + user)
                # thread_compile = threading.Timer(delay, _compile, [user, c_files])
                thread_compile = threading.Thread(target=_compile, args=[user, c_files])
                thread_compile.start()
            #     delay += 10
            # thread_compile_all = threading.Thread(target=queue_compile, args=[users_to_compile, c_files])
            # thread_compile_all.start()

            os.chdir(original_wd)

    def update_compile_log(self):
        a = len(compile_buffer)
        for i in range(a):
            self.textCompileLog.append(compile_buffer[i])
            if compile_buffer[i] == "==Compilação finalizada.":
                self.compile_timer.stop()
                self.btnVerifyLog.setDisabled(0)
        for i in range(a):
            compile_buffer.pop(0)

        self.progressBar.setValue(100 * progress_count // progress_max)

    def open_log(self):
        user_name = self.comboUser.currentText()
        log_path = original_wd + "\\Compilados\\" + user_name + "\\%s_log.txt" % user_name
        if os.path.isfile(log_path):
            webbrowser.open(log_path)
        else:
            window = QtWidgets.QMessageBox()
            window.move(600, 200)
            QtWidgets.QMessageBox.warning(window, 'Erro', "Log não encontrado", QtWidgets.QMessageBox.Ok)

    def update_files(self):
        if self.comboFiles.currentIndex() != -1:
            table_item = self.tableFiles.topLevelItem(self.comboFiles.currentIndex())
            if self.checkNoOutput.isChecked():
                table_item.setData(1, 0, '-')
                table_item.setData(2, 0, '-')
            else:
                table_item.setData(1, 0, self.lineInput.text())
                table_item.setData(2, 0, self.lineOutput.text())

    def new_tree_selection_run(self):
        tree_selected = self.tableFiles.selectedItems()
        if tree_selected:
            self.tableFiles.clearSelection()
            self.comboFiles.setCurrentIndex(self.tableFiles.indexOfTopLevelItem(tree_selected[0]))

    def new_combo_selection_run(self):
        if self.tableFiles.topLevelItemCount():
            self.tableFiles.clearSelection()
            self.tableFiles.topLevelItem(self.comboFiles.currentIndex()).setSelected(1)
            self.lineInput.setText(self.tableFiles.selectedItems()[0].text(1))
            self.lineOutput.setText(self.tableFiles.selectedItems()[0].text(2))

    def run_files(self):
        global run_list
        run_list = {}
        self.output_timer.start()
        for i in range(self.tableFiles.topLevelItemCount()):
            if self.tableFiles.topLevelItem(i).text(2) != '-':
                if self.tableFiles.topLevelItem(i).text(1) == '-':
                    run_list[self.tableFiles.topLevelItem(i).text(0)[:-2]] \
                        = ["", self.tableFiles.topLevelItem(i).text(2)]
                else:
                    run_list[self.tableFiles.topLevelItem(i).text(0)[:-2]] = [self.tableFiles.topLevelItem(i).text(1),
                                                                              self.tableFiles.topLevelItem(i).text(2)]
            # else:
            #     for user in users_file_info:
            #         if self.tableFiles.topLevelItem(i).text(0) in users_file_info[user][0]:
            #             users_file_info[user][1].append(self.tableFiles.topLevelItem(i).text(0))
        user_list = []
        for i in range(self.listUsers.count()):
            user_list.append(self.listUsers.item(i).text())
        if run_list and user_list:
            thread_run = threading.Thread(target=_run, args=[run_list, user_list])
            thread_run.start()
            threading.Timer(2.0, self.update_file_output).start()
        self.resultsTab.setDisabled(0)

    def update_file_output(self):
        if output_buffer:
            for line in output_buffer:
                self.textFileOutput.append(line)
                self.btnRight.setDisabled(0)
                self.btnWrong.setDisabled(0)
                if line == "Finalizado.\n":
                    self.output_timer.stop()
                    self.btnRight.setDisabled(1)
                    self.btnWrong.setDisabled(1)
                    for user in users_file_info:
                        info = [user, str(len(users_file_info[user][0])), str(len(users_file_info[user][1]))]
                        self.treeUsers.addTopLevelItem(QtWidgets.QTreeWidgetItem(info))
                        self.comboUser_2.addItem(user)

                    for item in run_list:
                        self.comboFile.addItem(item + '.exe')

            output_buffer.clear()

    def right_answer(self):
        global output_verification, run_total, run_count
        self.textFileOutput.clear()
        self.textFileOutput.append("%d/%d\n==Saída correta!" % (run_count, run_total))
        output_verification = 1
        self.btnRight.setDisabled(1)
        self.btnWrong.setDisabled(1)

    def wrong_answer(self):
        global output_verification, run_total, run_count
        self.textFileOutput.clear()
        self.textFileOutput.append("%d/%d\n==Saída incorreta!" % (run_count, run_total))
        output_verification = 0
        self.btnRight.setDisabled(1)
        self.btnWrong.setDisabled(1)

    def new_combo_selection_results(self):
        if self.treeUsers.topLevelItemCount():
            self.treeUsers.clearSelection()
            self.treeUsers.topLevelItem(self.comboUser_2.currentIndex()).setSelected(1)
        self.treeFiles.clear()
        for program in users_file_info[self.comboUser_2.currentText()][0]:
            if program[:-2] in run_list:
                if program[:-2] + ".exe" in users_file_info[self.comboUser_2.currentText()][1]:
                    self.treeFiles.addTopLevelItem(QtWidgets.QTreeWidgetItem([program[:-2] + '.exe', "Sim"]))
                else:
                    self.treeFiles.addTopLevelItem(QtWidgets.QTreeWidgetItem([program[:-2] + '.exe', "Não"]))

    def new_tree_selection_results(self):
        tree_selected = self.treeUsers.selectedItems()
        if tree_selected:
            self.treeUsers.clearSelection()
            self.comboUser_2.setCurrentIndex(self.treeUsers.indexOfTopLevelItem(tree_selected[0]))

    def verify_output(self):
        cur_program = self.comboFile.currentText()
        cur_user = self.comboUser_2.currentText()
        self.textOutput.clear()
        if cur_program[0:-4] + '.c' not in users_file_info[cur_user][0]:
            self.textOutput.append("%s não compilado para %s." % (cur_program, cur_user))
        else:
            time_out = 0
            prog_input, prog_output = run_list[cur_program[0:-4]][0], run_list[cur_program[0:-4]][1]
            run_process = subprocess.Popen(["%s" % os.path.join(original_wd, "Compilados", cur_user, cur_program)],
                                           stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, creationflags=0x08000000)
            run_process.stdin.write(bytes(prog_input, 'UTF-8'))
            try:
                run_response = run_process.communicate(timeout=1)[0].decode('latin-1')
            except Exception:
                self.textOutput.append("====Tempo de execução excedido.")
                time_out = 1
            if not time_out:
                self.textOutput.append("--Entrada fornecida: '%s'\n" % prog_input)
                self.textOutput.append("--Saída do programa:\n" + 45 * "\\" + "\n%s\n"
                                       % run_response + 45 * "/" + "\n")
                self.textOutput.append("--Saída esperada: '%s'\n" % prog_output)

    def rectify_result(self):
        cur_program = self.comboFile.currentText()
        cur_user = self.comboUser_2.currentText()
        tree_item = self.treeUsers.topLevelItem(self.comboUser_2.currentIndex())
        if cur_program in users_file_info[cur_user][1]:
            users_file_info[cur_user][1].remove(cur_program)
            self.treeUsers.editItem(tree_item, 2)
            tree_item.setText(2, str(int(tree_item.text(2)) - 1))
        else:
            if cur_program[:-4] + '.c' in users_file_info[cur_user][0]:
                users_file_info[cur_user][1].append(cur_program)
                tree_item.setText(2, str(int(tree_item.text(2)) + 1))
        self.new_combo_selection_results()

    def save_log(self):
        try:
            log = open(self.lineLog.text(), 'w')
            for user in users_file_info:
                log.write(user + (20 - len(user)) * " " + " :" + (2 - len(users_file_info[user][0]) // 10) * " " +
                          str(len(users_file_info[user][0])) + "  : " + str(len(users_file_info[user][1])) + "\n")
            log.close()
        finally:
            self.btnLogs.setText("Relatório gerado com sucesso")
            self.btnLogs.setDisabled(1)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
