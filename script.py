import subprocess
import os
import stat
from multiprocessing.pool import ThreadPool as Pool


def rmtree(path):  # alternative to shutil.rmtree
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            filename = os.path.join(root, name)
            os.chmod(filename, stat.S_IWUSR)
            os.remove(filename)
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(path)


original_wd = os.getcwd()
user_list = []
c_files_list = {}

user_file = open('lista_usuarios.txt', 'r')
for line in user_file:
    username, repname = line.split()
    user_list.append([username, repname, 0, 0])  # (0, 0) -> Score = (Compiled, Right Answer)


prog_names_file = open('lista_programas.txt', 'r')
for line in prog_names_file:
    line = line.split(':')
    c_files_list[line[0][0:-2]] = (line[1], line[2], line[3].split()[0])


# Step 1: Cloning...
########################################################################################################################
if not os.path.exists(original_wd + "\\compiled"):
    os.mkdir("compiled")

if not os.path.exists(original_wd + "\\users"):
    os.makedirs(os.getcwd() + '\\users')

option = input("Clonar repositórios? Y/N\n")

if option is 'y' or option is 'Y':

    os.chdir(os.getcwd() + '\\users')

    # def clone_user(user):
    for user in user_list:
        print("Clonando repositório de %s..." % user[0])
        user_path = original_wd + "\\users" + '\\' + user[0]
        if os.path.exists(user_path):
            rmtree(user_path)
            os.makedirs(user_path)
            os.chdir(user_path)
            p = subprocess.Popen(["git", "clone", "http://github.com/%s/%s" % (user[0], user[1])],
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            clone_response = p.communicate()
            # subprocess.call(["git", "clone", "http://github.com/%s/MTP" % user])
        else:
            os.makedirs(user_path)
            os.chdir(user_path)
            p = subprocess.Popen(["git", "clone", "http://github.com/%s/%s" % (user[0], user[1])],
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            clone_response = p.communicate()
            # subprocess.call(["git", "clone", "http://github.com/%s/MTP" % user])
        if clone_response[1].decode("latin-1") is not "Cloning into '%s'...\n" % user[1]:
            print("Erro ao clonar respositório. Erro: " + clone_response[1].decode("latin-1"))
        else:
            print("Repositório de %s clonado com sucesso." % user[0])
        os.chdir(original_wd + '\\users')

# pool_clone = Pool(20)
#
# for user in user_list:
#     pool_clone.apply_async(clone_user, (user,))
#
# pool_clone.close()
# pool_clone.join()


# Step 2: Compiling...
########################################################################################################################

users_compiled = {}


def compile_user(user):
    users_compiled[user[0]] = []
    user_c_files = []
    user_log = open(original_wd + "\\compiled\\" + user[0] + "\\%s_log.txt" % user[0], "w")
    user_log.write("Compilando\n" + 45*"-" + "\n")
    for root, dirs, files in os.walk(os.path.join(original_wd, "users", user[0])):
        for name in files:
            if name[-2:] == ".c":
                user_c_files.append(name[0:-2])
                if name[0:-2] in c_files_list:
                    comp_process = subprocess.Popen(["g++", "-o", os.path.join(original_wd,
                                                    "compiled\\%s\\%s.exe" % (user[0], name[0:-2])),
                                                    os.path.join(root, name)], stdin=subprocess.PIPE,
                                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    comp_response = comp_process.communicate()[1].decode('UTF-8')
                    if comp_response is "":
                        print("%s compilado com sucesso.\n" % name)
                        user_log.write("#%s compilado com sucesso.\n" % name)
                        user[2] += 1
                        users_compiled[user[0]].append(name[0:-2])
                    else:
                        print("\n\nErro ao compilar " + name + ". Erro: \n\n" + comp_response + "\n\n")
                        user_log.write("\n\n#Erro ao compilar " + name + ". Erro: \n===============\n" + comp_response
                                       + "\n===============\n")

    user_log.write("\n")

    for c_file in c_files_list:
        if c_file not in user_c_files:
            print("%s.c não encontrado.\n" % c_file)
            user_log.write("#%s.c não encontrado.\n" % c_file)

    user_log.write(60*"-" + "\n\n")

    user_log.close()


pool_compile = Pool(25)

for user in user_list:
    if not os.path.exists(original_wd + "\\compiled\\" + user[0]):
        os.mkdir(original_wd + "\\compiled\\" + user[0])
    print("******************************\n " + user[0] + "\n")
    pool_compile.apply_async(compile_user, (user,))

pool_compile.close()
pool_compile.join()

os.chdir(original_wd)


# Step 3: Running...
########################################################################################################################

run_list = []
for c_file in c_files_list:
    if c_files_list[c_file][2] == '1':
        run_list.append(c_file)
    else:
        for user in user_list:
            if c_file in users_compiled[user[0]]:
                user[3] += 1

# def run_user(user):
for user in user_list:
    print(user)
    user_log = open(original_wd + "\\compiled\\" + user[0] + "\\%s_log.txt" % user[0], "a")
    user_log.write("Rodando\n" + 60*"-" + "\n")
    for root, dirs, files in os.walk(os.getcwd() + "\\compiled\\" + user[0]):
        for name in files:
            if name[0:-4] in run_list:
                user_log.write('#' + name + '\n')
                time_out = 0
                prog_input, prog_output = c_files_list[name[0:-4]][0], c_files_list[name[0:-4]][1]
                run_process = subprocess.Popen(["%s" % os.path.join(original_wd, "compiled", user[0], name)],
                                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                run_process.stdin.write(bytes(prog_input, 'UTF-8'))
                try:
                    run_response = run_process.communicate(timeout=1)[0].decode('latin-1')
                except:
                    print("Timed out")
                    user_log.write("==Tempo de execução excedido.\n")
                    time_out = 1
                if not time_out:
                    print(run_response)
                    user_log.write("--Entrada fornecida: '%s'\n" % prog_input)
                    user_log.write("--Saída do programa:\n" + 45*"\\" + "\n%s\n" % run_response + 45*"/" + "\n")
                    print("Saída esperada: %s" % prog_output)
                    user_log.write("--Saída esperada: '%s'\n" % prog_output)
                    correction_input = input("Saída correta? Y/N\n")
                    while 1:
                        if correction_input == 'Y' or correction_input == 'y':
                            user[3] += 1
                            user_log.write("==Saída correta!\n\n")
                            print(user)
                            break
                        elif correction_input == 'N' or correction_input == 'n':
                            user_log.write("==Saída incorreta!\n\n")
                            break
                        else:
                            correction_input = input("Resposta deve ser 'Y' ou 'N'.\n")
    user_log.write(45*"-" + "\n")
    user_log.close()

# pool_run = Pool(20)
#
# for user in user_list:
#     print("Executando para " + user[0])
#     pool_run.apply_async(run_user, (user,))
#
# pool_run.close()
# pool_run.join()


f = open('notas_lab1.txt', 'w')
for user in user_list:
    f.write(str(user[0]) + (20 - len(str(user[0]))) * " " + " :" + (2 - user[2] // 10) * " " + str(user[2]) + "  : "
            + str(user[3]) + "\n")
f.close()

print("\nNotas computadas.")
