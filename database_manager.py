import subprocess
from config import bancos

def buscar_banco(nome):
    nome_tratado = nome.upper()

    for banco in bancos:
        
        banco_tratado = banco["name"].upper()
          
        if banco_tratado == nome_tratado:
            return banco
        
    return False
            
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

        lista_erro = []

        banco_encontrado = buscar_banco(banco_st)

        if banco_encontrado:

            for servico in banco_encontrado["services"]:
                    try:
                        iniciar_servico(servico)
                        
                    except Exception as erro:
                        lista_erro.append(erro)

            if lista_erro:
                mensagem_erro = ""

                for erro in lista_erro:
                     mensagem_erro = mensagem_erro + "\n" + str(erro)
                raise Exception(mensagem_erro)
            
            else:
                return " Banco iniciado com sucesso "
            
        return ' Banco inexistente '

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

    lista_erro = []

    banco_verificado = buscar_banco(banco_str)

    if banco_verificado:
            
        for servicos in banco_verificado["services"]:
            
            try:
                parar_servico(servicos)

            except Exception as erro:
                lista_erro.append(erro)

        if lista_erro:
            mensagem_erro = ""

            for erro in lista_erro:
                mensagem_erro = mensagem_erro + "\n" + str(erro)

            raise Exception(mensagem_erro) 
        else: 
            return "Banco parado com sucesso"
         
    return f'{banco_str} - Banco inexistente'
