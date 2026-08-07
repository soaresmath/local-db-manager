import subprocess
from config import bancos

def verificar_status_servico(servico):
    resultado = False

    try:
        resultado = subprocess.run(
            ["sc", "query", servico],
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )
    except subprocess.CalledProcessError as erro:
        print(f"Falha (código {erro.returncode}): {erro.stderr}")
        return False
    except subprocess.TimeoutExpired as erro:
        print("O serviço demorou mais de 10 segundos — abortado.")
        return False

    if resultado:
        if "STOPPED" in resultado.stdout:
            status = "STOPPED"
            return status
                            
        return "RUNNING"

def verificar_status_banco(banco):
    for servico in banco["services"]:
        status = verificar_status_servico(servico)

        if status == "STOPPED":
            return "STOPPED"
        elif status is False:
            return "Erro na verificação de servico"
        
    return "RUNNING"

def iniciar_servico(servico):

    if verificar_status_servico(servico) == "STOPPED":
        try:
            resultado = subprocess.run(
                ["sc", "start", servico],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
        except subprocess.CalledProcessError as erro:
            print(f"Falha (código {erro.returncode}): {erro.stderr}")
            resultado = False
        except subprocess.TimeoutExpired as erro:
            print("O serviço demorou mais de 10 segundos — abortado.")
            resultado = False
    else:
        return True # minha logica é economizar processmento, se um serviço já está ligado, não precisa rodar as camadas abaixa do if

    if resultado:
        if "START_PENDING" in resultado.stdout:
            status = verificar_status_servico(servico)
            if status == "RUNNING":
                return True
        else:
            return False
    else:
        return "Erro no try e execption - serviço"

def iniciar_banco(banco_st):

    for banco in bancos:

        banco_st = banco_st.upper()
        banco_dic = banco["name"].upper()

        if banco_dic == banco_st:
            for servico in banco["services"]:
                    status = iniciar_servico(servico)
            
                    if status is False:
                        return "Erro ao subir banco"
            return "Banco ok"

    return 'Banco inexistente'

def parar_servico(servico):

    if verificar_status_servico(servico) == "RUNNING":
        try:
            resultado = subprocess.run(
                    ["sc", "stop", servico],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=10
            )

        except subprocess.CalledProcessError as erro:
            print(f"Falha (código {erro.returncode}): {erro.stderr}")
            return False
        except subprocess.TimeoutExpired as erro:
            print("O serviço demorou mais de 10 segundos — abortado.")
            return False

        return True
    else:
        return False

def parar_banco(banco_str):
    lista_retorno = []

    for banco in bancos:
        algum_servico_parado = False

        banco_dic = banco["name"].upper()
        banco_str = banco_str.upper()

        """print(f"{banco_dic} - {banco_str}")"""

        if banco_dic == banco_str:
           for servicos in banco["services"]:
                retorno = parar_servico(servicos) 

                if retorno == False:
                    algum_servico_parado = True

           if algum_servico_parado:
                return "Banco já estava parado" 
           else: 
                return "Banco parado"
    
    return 'Banco inexistente' # isso matava a operação, ele conseguia PARA O LOOP DO FOR QUANDO ERA UM ELSE NO IF Da comparação das palavras digitadas e dicionario.
