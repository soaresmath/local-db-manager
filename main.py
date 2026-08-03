import subprocess

def verificar_status_banco(banco):
    for servico in banco["services"]:
        status = verificar_status_servico(servico)
        if status == "STOPPED":
            return "STOPPED"
    return "RUNNING"
        
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
        print(f"Falha (código {erro.returncode}): {erro.stderr}")
    except subprocess.TimeoutExpired as erro:
        print("O serviço demorou mais de 10 segundos — abortado.")

    if "STOPPED" in resultado.stdout:
        status = "STOPPED"
        return status
                        
    return "RUNNING"
    
def iniciar_servico(servico):
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
        if banco["name"] == banco_st:
            for servico in banco["services"]:
                    status = iniciar_servico(servico)
            
                    if status is False:
                        return "Erro ao subir banco"
            return "Banco ok"

programa_ativo = True

bancos = [
    {
        "name": "MySQL",
        "services": [
            "MySQL80"
        ]
    },
    {
        "name": "SQL Server",
        "services": [
            "MSSQL$SQLEXPRESS"
        ]
    },
    {
        "name": "Oracle",
        "services": [
            "OracleServiceFREE",
            "OracleOraDB23Home1TNSListener"
        ]
    }
]

while programa_ativo:

    print("=============================")
    print("    LOCAL DATABASE MANAGER")
    print("=============================")

    print()
    print("1. Listar bancos")
    print("2. Iniciar banco")
    print("3. Parar banco")
    print("4. Sair")

    escolha = input("Escolha uma opção: ")

    match escolha:
        case "1":
            print("Banco disponíveis: ")
            print()
            for banco in bancos:

                status = verificar_status_banco(banco)
                print(" - ", banco["name"], "Status:", status)

        case "2":
            print("Você escolheu Iniciar banco")
            print()
            escolha_banco = input("Digite qual banco quer iniciar: ")

            status = iniciar_banco(escolha_banco)
            print(status)
    

        case "3":
            print("Você escolheu Parar banco")
        case "4":
            print("Saiu")
            programa_ativo = False
        case _:
            print("Opção inválida")