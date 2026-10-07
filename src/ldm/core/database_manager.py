import subprocess
from ldm.config.databases import bancos_conhecidos
import time
import json
import re


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
        raise Exception(
            f"\nNão foi possível consultar o status do serviço: {servico}\n"
            f"Falha (código {erro.returncode}): {erro.stderr}"
        )
    except subprocess.TimeoutExpired:
        raise Exception(
            "O serviço demorou mais de 10 segundos — abortado."
        )

    padrao = r"(?:STATE|ESTADO)\s*:\s*(\d+)\s+(\w+)"

    for linha in resultado.stdout.splitlines():
        correspondencia = re.search(padrao, linha)

        if correspondencia:
            return correspondencia.group(2)

    raise RuntimeError(
        f"Não foi possível identificar o estado do serviço: {servico}"
    )

def verificar_status_banco(banco):
    for servico in banco["evidencias"]["servicos"]:
        # não tratamos o erro se verificar_status_servico explodir erro e enviar para nós
        status = verificar_status_servico(servico["name"])

        if status == "STOPPED":
            return "STOPPED"

    return "RUNNING"

def aguardar_transicao_servico(servico, estados_transitorios, limite=10):
    inicio = time.time()
    tempo = 0

    status = verificar_status_servico(servico)

    while status in estados_transitorios and tempo < limite:
        time.sleep(1)
        tempo = time.time() - inicio
        status = verificar_status_servico(servico)

    return status

def iniciar_servico(servico):

    status = verificar_status_servico(servico)

    if status == "RUNNING":
        return True

    if status == "PAUSED":
        raise RuntimeError(
            f"O serviço '{servico}' está pausado e não pode ser iniciado pelo LDM."
        )

    if status == "STOPPED":
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
                f"Não foi possível iniciar o serviço: {servico}"
                f"Falha (código {erro.returncode}): {erro.stderr}"
            )
        except subprocess.TimeoutExpired:
            raise Exception(
                "O serviço demorou mais de 10 segundos — abortado."
            )

        if "START_PENDING" in resultado.stdout:
            status = aguardar_transicao_servico(servico,{"START_PENDING"})

            if status == "RUNNING":
                return True

            if status == "PAUSED":
                raise RuntimeError(
                    f"O serviço '{servico}' foi pausado durante a inicialização."
                )

            return False

        raise RuntimeError(
            "Erro interno na verificação do status do serviço."
        )

    if status == "START_PENDING":
        status = aguardar_transicao_servico(servico,{"START_PENDING"})

        if status == "RUNNING":
            return True

        if status == "PAUSED":
            raise RuntimeError(
                f"O serviço '{servico}' está pausado e não pode ser iniciado pelo LDM."
            )

        return False

    if status == "STOP_PENDING":
        status = aguardar_transicao_servico(servico,{"STOP_PENDING"})

        if status == "STOPPED":
            return iniciar_servico(servico)

        return False

    if status in ["PAUSE_PENDING", "CONTINUE_PENDING"]:
        status = aguardar_transicao_servico(servico,{status})

        if status == "RUNNING":
            return True

        if status == "PAUSED":
            raise RuntimeError(
                f"O serviço '{servico}' está pausado e não pode ser iniciado pelo LDM."
            )

        return False

    raise RuntimeError(
        f"Estado do serviço não suportado pelo LDM: {status}"
    )

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

    status = verificar_status_servico(servico)

    if status == "STOPPED":
        return True

    if status == "PAUSED":
        raise RuntimeError(
            f"O serviço '{servico}' está pausado e não pode ser parado pelo LDM."
        )

    if status == "RUNNING":
        try:
            subprocess.run(
                ["sc.exe", "stop", servico],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
        except subprocess.CalledProcessError as erro:
            raise Exception(
                f"Não foi possível parar o serviço: {servico}"
                f"Falha (código {erro.returncode}): {erro.stderr}"
            )
        except subprocess.TimeoutExpired:
            raise Exception(
                "O serviço demorou mais de 10 segundos — abortado."
            )

        status = aguardar_transicao_servico(servico,{"RUNNING", "STOP_PENDING"})

        return status == "STOPPED"

    if status == "STOP_PENDING":
        status = aguardar_transicao_servico(
            servico,
            {"STOP_PENDING"}
        )

        return status == "STOPPED"

    if status == "START_PENDING":
        status = aguardar_transicao_servico(servico,{"START_PENDING"})

        if status == "RUNNING":
            return parar_servico(servico)

        if status == "STOPPED":
            return True

        if status == "PAUSED":
            raise RuntimeError(
                f"O serviço '{servico}' está pausado e não pode ser parado pelo LDM."
            )

        return False

    if status == "CONTINUE_PENDING":
        status = aguardar_transicao_servico(servico,{"CONTINUE_PENDING"})

        if status == "RUNNING":
            return parar_servico(servico)

        if status == "STOPPED":
            return True

        if status == "PAUSED":
            raise RuntimeError(
                f"O serviço '{servico}' está pausado e não pode ser parado pelo LDM."
            )

        return False

    if status == "PAUSE_PENDING":
        status = aguardar_transicao_servico(servico,{"PAUSE_PENDING"})

        if status == "PAUSED":
            raise RuntimeError(
                f"O serviço '{servico}' está pausado e não pode ser parado pelo LDM."
            )

        if status == "STOPPED":
            return True

        if status == "RUNNING":
            return parar_servico(servico)

        return False

    raise RuntimeError(
        f"Estado do serviço não suportado pelo LDM: {status}"
    )

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

            if evidencias_servicos:
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
