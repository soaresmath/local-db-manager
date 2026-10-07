import subprocess
from ldm.config.databases import bancos_conhecidos
import time
import json


def buscar_banco(nome, bancos):
    nome_tratado = nome.upper()

    for banco in bancos:
        if banco["name"].upper() == nome_tratado:
            return banco

    return False

def tratando_excecoes(lista_erros):
    mensagem_exececoes = ""

    for excecao in lista_erros:
        mensagem_exececoes += "\n" + str(excecao)

    return mensagem_exececoes

def verificar_status_servico(servico):
    try:
        resultado = subprocess.run(
            ["sc.exe", "query", servico],
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )
    except subprocess.CalledProcessError as erro:
        # o raise interrompe a execução e propaga a exceção para quem chamou.
        # Quem chamou pode tratar o erro com except ou deixar a exceção continuar subindo, como verificar status banco, inicar serviço, parar serviço - nenhum faz isso e deixa com o main

        raise Exception(
            f"\nNão foi possivel consultar o status do serviço: {servico}\n"
            f"Falha (código {erro.returncode}): {erro.stderr}"
        )

    except subprocess.TimeoutExpired as erro:
        raise Exception(
            f"O serviço demorou mais de 10 segundos — abortado."
        )

    if "STOPPED" in resultado.stdout:
        status = "STOPPED"
        return status

    return "RUNNING"

def verificar_status_banco(banco):
    for servico in banco["evidencias"]["servicos"]:
        # não tratamos o erro se verificar_status_servico explodir erro e enviar para nós
        status = verificar_status_servico(servico["name"])

        if status == "STOPPED":
            return "STOPPED"

    return "RUNNING"

def iniciar_servico(servico):

    # não tratamos o erro se por acaso o verificar status servico explodir erro se enviar para nós, mas tambem mandamos para quem nos acionar
    if verificar_status_servico(servico) == "STOPPED":
        try:
            resultado = subprocess.run(
                ["sc.exe", "start", servico],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
        except subprocess.CalledProcessError as erro:
            raise Exception(
                f"Não foi possivel iniciar o serviço: {servico}"
                f"Falha (código {erro.returncode}): {erro.stderr}"
            )

        except subprocess.TimeoutExpired as erro:
            raise Exception(
                f"O serviço demorou mais de 10 segundos — abortado."
            )

    else:
        return True  # minha logica é economizar processmento, se um serviço já está ligado, não precisa rodar as camadas abaixa do

    if "START_PENDING" in resultado.stdout:

        inicio = time.time()
        limite = 10
        tempo = 0

        status = verificar_status_servico(servico)

        while status != "RUNNING" and tempo < limite:

            status = verificar_status_servico(servico)

            if status == "RUNNING":
                return True

            time.sleep(1)
            tempo = time.time() - inicio

        return False
    else:
        raise Exception("Erro interno na verificação dos status do serviço")

def iniciar_banco(banco_str, bancos):
    lista_erro = []

    banco_encontrado = buscar_banco(banco_str, bancos)

    if banco_encontrado:
        for servico in banco_encontrado["evidencias"]["servicos"]:
            try:
                iniciar_servico(servico["name"])

            except Exception as erro:
                lista_erro.append(erro)

        if lista_erro:
            raise RuntimeError(tratando_excecoes(lista_erro))

        return "Banco iniciado com sucesso"

    return "Banco inexistente"

def parar_servico(servico):

    # não tratamos o erro se por acaso o verificar status servico explodir erro se enviar para nós, mas tambem mandamos para quem nos acionar
    if verificar_status_servico(servico) == "RUNNING":
        try:
            resultado = subprocess.run(
                ["sc.exe", "stop", servico],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )

        except subprocess.CalledProcessError as erro:
            raise Exception(
                f"Não foi possivel parar o serviço: {servico}"
                f"Falha (código {erro.returncode}): {erro.stderr}"
            )

        except subprocess.TimeoutExpired as erro:
            raise Exception(
                f"O serviço demorou mais de 10 segundos — abortado."
            )

        inicio = time.time()
        limite = 10
        tempo = 0

        while tempo <= limite:
            status = verificar_status_servico(servico)

            if status == "STOPPED":
                return True

            time.sleep(1)
            tempo = time.time() - inicio

        return False
    else:
        return True

def parar_banco(banco_str, bancos):

    lista_erro = []

    banco_verificado = buscar_banco(banco_str, bancos)

    if banco_verificado:
        for servico in banco_verificado["evidencias"]["servicos"]:
            try:
                parar_servico(servico["name"])

            except Exception as erro:
                lista_erro.append(erro)

        if lista_erro:
            raise RuntimeError(tratando_excecoes(lista_erro))

        return "Banco parado com sucesso"

    return f"{banco_str} - Banco inexistente"

def extrair_servicos():
    try:
        resultado = subprocess.run(
            ["sc.exe", "query", "state=", "all"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )

        list_services = []

        linhas = resultado.stdout.split("\n")

        for linha in linhas:

            if linha.strip().startswith("NOME_DO"):
                partes = linha.split(":", 1)
                nome = partes[1].strip()

                config_service = obter_configuracao_servico(nome)
                displayName_service = obter_nome_display_servico(nome)

                if '"' in config_service:
                    caminho_service = config_service.split('"')
                    parte_caminho = caminho_service[1]
                else:
                    caminho_service = config_service.split()
                    parte_caminho = caminho_service[0]

                caminho_exe = parte_caminho.split('\\')

                executavel = None

                for pedacos in caminho_exe:
                    if pedacos.lower().endswith(".exe"):
                        executavel = pedacos

                list_services.append(
                    {
                        "name": nome,
                        "display": displayName_service,
                        "binary_path": config_service,
                        "executable": executavel
                    }
                )

        return list_services

    except Exception as erro:
        raise RuntimeError(f"Erro ao extrair serviços: {erro}") from erro

def obter_configuracao_servico(servico):
    try:
        resultado = subprocess.run(
            ["sc.exe", "qc", servico],
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )

        linhas = resultado.stdout.split("\n")

        for linha in linhas:
            if "NOME_DO_CAMINHO_BIN" in linha:
                partes = linha.split(":", 1)
                caminho = partes[1].strip()

                return caminho

        raise RuntimeError(
            f"Caminho binário não encontrado para o serviço '{servico}'"
        )

    except Exception as erro:
        raise RuntimeError(
            f"Erro ao obter configuração do serviço '{servico}': {erro}"
        ) from erro

def obter_nome_display_servico(servico):
    try:
        resultado = subprocess.run(
            ["sc.exe", "qc", servico],
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )

        linhas = resultado.stdout.split("\n")

        for linha in linhas:

            if linha.strip().startswith("NOME_PARA"):
                partes = linha.split(":", 1)

                return partes[1].strip()

        raise RuntimeError(
            f"Nome de exibição não encontrado para o serviço '{servico}'"
        )

    except Exception as erro:
        raise RuntimeError(
            f"Erro ao obter nome de exibição do serviço '{servico}': {erro}"
        ) from erro

def extrair_processos():
    try:
        resultado = subprocess.run(
            ["tasklist"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )

        lista = []

        for linha in resultado.stdout.splitlines()[3:]:
            partes = linha.split()

            for indice, parte in enumerate(partes):
                if parte.isdigit():
                    nome = " ".join(partes[:indice])
                    pid = int(parte)

                    lista.append({
                        "name": nome,
                        "pid": pid
                    })

                    break

        return lista

    except Exception as erro:
        raise RuntimeError(
            f"Erro ao extrair processos: {erro}"
        ) from erro

def filtrar_processos(nome):
    lista_processo = extrair_processos()

    lista_processos_filtrado = []

    for processo in lista_processo:
        if processo["name"] == nome:
            lista_processos_filtrado.append(processo)

    return lista_processos_filtrado

def obter_detalhes_processo(pid):
    try:
        if not isinstance(pid, int):
            raise ValueError("PID deve ser um número inteiro")

        comando_powershell = (
            f"Get-CimInstance Win32_Process -Filter 'ProcessId = {pid}'"
            f"|Select-Object ProcessId, Name, ExecutablePath, CommandLine, ParentProcessId "
            f"| ConvertTo-Json"
        )

        resultado = subprocess.run(
            ["powershell", "-Command", comando_powershell],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )

        dados = json.loads(resultado.stdout)

        return dados

    except Exception as erro:
        raise RuntimeError(
            f"Erro ao obter detalhes do processo PID {pid}: {erro}"
        ) from erro

def descobrir_bancos():
    try:
        servicos = extrair_servicos()
        processos = extrair_processos()

        bancos_encontrados = []

        for nome_banco, dados_banco in bancos_conhecidos.items():
            termos_servico = [
                termo.lower()
                for termo in dados_banco["servico"]
            ]

            termos_processo = [
                termo.lower()
                for termo in dados_banco["processo"]
            ]

            evidencias_servicos = []
            evidencias_processos = []

            for servico in servicos:
                campos = {
                    "name": servico["name"],
                    "display": servico["display"],
                    "binary_path": servico["binary_path"],
                    "executable": servico["executable"]
                }

                encontrado = False

                for campo, valor in campos.items():
                    if valor is None:
                        continue

                    valor = valor.lower()

                    if any(termo in valor for termo in termos_servico):
                        encontrado = True
                        break

                if encontrado:
                    evidencias_servicos.append(servico)

            for processo in processos:
                nome_processo = processo["name"].lower()

                if any(
                    termo in nome_processo
                    for termo in termos_processo
                ):
                    evidencias_processos.append(processo)

            if evidencias_servicos or evidencias_processos:
                bancos_encontrados.append({
                    "name": nome_banco,
                    "evidencias": {
                        "servicos": evidencias_servicos,
                        "processos": evidencias_processos
                    }
                })

        return bancos_encontrados

    except Exception as erro:
        raise RuntimeError(
            f"Erro ao descobrir bancos instalados: {erro}"
        ) from erro
