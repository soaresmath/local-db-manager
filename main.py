from database_manager import verificar_status_banco, iniciar_banco, parar_banco
from config import bancos

programa_ativo = True

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
            try:
                for banco in bancos:

                    status = verificar_status_banco(banco)
                    print(" - ", banco["name"], "Status:", status)
                    
            except Exception as erro:
                print(f"Erro: {erro}")         

        case "2":
            print("Você escolheu Iniciar banco")
            print()
            escolha_banco = input("Digite qual banco quer iniciar: ")

            status = iniciar_banco(escolha_banco)
            print(status)
    

        case "3":  
            print("Você escolheu Parar banco:")
            print()

            escolha_banco = input("Digite qual banco quer parar: ")

            status = parar_banco(escolha_banco)
            print(status)

        case "4":
            print("Saiu")
            programa_ativo = False
        case _:
            print("Opção inválida")