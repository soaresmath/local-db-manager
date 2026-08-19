import subprocess
from config import bancos

def verificar_status_servico(servico):
    try:
        resultado = subprocess.run(
            ["sc", "query", servico],
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )
    except subprocess.CalledProcessError as erro:
        # o raise interrompe a execução e propaga a exceção para quem chamou.
        # Quem chamou pode tratar o erro com except ou deixar a exceção continuar subindo, como verificar status banco, inicar serviço, parar serviço - nenhum faz isso e deixa com o main

        raise Exception(
            f"Não foi possivel consultar o status do serviço: {servico}"
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
    for servico in banco["services"]:

        # não tratamos o erro se verificar_status_servico explodir erro e enviar para nós
        status = verificar_status_servico(servico)
        
        if status == "STOPPED":
            return "STOPPED"
    
    return "RUNNING"

def iniciar_servico(servico):

    # não tratamos o erro se por acaso o verificar status servico explodir erro se enviar para nós, mas tambem mandamos para quem nos acionar 
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
                raise Exception(
                    f"Não foi possivel iniciar o serviço: {servico}"
                    f"Falha (código {erro.returncode}): {erro.stderr}"
                )
            
        except subprocess.TimeoutExpired as erro:
                raise Exception(
                    f"O serviço demorou mais de 10 segundos — abortado."
                )
                
    else:
        return True # minha logica é economizar processmento, se um serviço já está ligado, não precisa rodar as camadas abaixa do if
    
    if "START_PENDING" in resultado.stdout:
        status = verificar_status_servico(servico)
        if status == "RUNNING":
            return True
        else:
            return False
    else:
        return False

def iniciar_banco(banco_st):

    for banco in bancos:

        banco_st = banco_st.upper()
        banco_dic = banco["name"].upper()

        if banco_dic == banco_st:
            for servico in banco["services"]:
                    # se o iniciar servico explodir não estamos tratando
                    status = iniciar_servico(servico)
                    
                    if status is False:
                        return "Erro ao subir banco"
                            
            return "Banco ok"
        else:
            ...
    return 'Banco inexistente'

def parar_servico(servico):

    # não tratamos o erro se por acaso o verificar status servico explodir erro se enviar para nós, mas tambem mandamos para quem nos acionar
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
                raise Exception(
                    f"Não foi possivel parar o serviço: {servico}"
                    f"Falha (código {erro.returncode}): {erro.stderr}"
                )
            
        except subprocess.TimeoutExpired as erro:
                raise Exception(
                    f"O serviço demorou mais de 10 segundos — abortado."
                )

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
                # se algum erro do parar servico fundamental nos enviar nçao estamos tratando
                retorno = parar_servico(servicos) 

                if retorno == False:
                    algum_servico_parado = True

           if algum_servico_parado:
                return "Banco já estava parado" 
           else: 
                return "Banco parado"
    
    return 'Banco inexistente'
