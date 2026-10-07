from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.text import Text

from ldm.core.database_manager import (
    verificar_status_banco,
    iniciar_banco,
    parar_banco,
    descobrir_bancos
)


console = Console()


def mostrar_cabecalho():
    console.print(
        Panel(
            "Database Service Manager",
            title="LOCAL DATABASE MANAGER",
            border_style="cyan",
            expand=False
        )
    )


def analisar_maquina():
    try:
        with console.status(
            "[cyan]Analisando serviços e processos da máquina...[/cyan]",
            spinner="dots"
        ):
            bancos = descobrir_bancos()

        console.print(
            "[green]✓[/green] Análise da máquina concluída."
        )

        return bancos

    except Exception as erro:
        console.print(
            Panel(
                str(erro),
                title="Erro durante a análise",
                border_style="red"
            )
        )

        return []


def mostrar_menu():
    console.print()
    console.print("[bold]Menu principal[/bold]")
    console.print()
    console.print(" [cyan]1[/cyan]  Listar bancos")
    console.print(" [green]2[/green]  Iniciar banco")
    console.print(" [yellow]3[/yellow]  Parar banco")
    console.print(" [red]4[/red]  Sair")
    console.print()


def listar_bancos(bancos):
    try:
        tabela = Table(
            title="Bancos detectados",
            border_style="cyan",
            show_lines=False
        )

        tabela.add_column("Banco", style="bold")
        tabela.add_column("Status", justify="center")

        for banco in bancos:
            status = verificar_status_banco(banco)

            if status == "RUNNING":
                status_formatado = Text(
                    "● RUNNING",
                    style="green"
                )
            else:
                status_formatado = Text(
                    "● STOPPED",
                    style="red"
                )

            tabela.add_row(
                banco["name"],
                status_formatado
            )

        console.print(tabela)

    except Exception as erro:
        console.print(
            Panel(
                str(erro),
                title="Erro",
                border_style="red"
            )
        )


def iniciar_banco_menu(bancos):
    try:
        escolha_banco = Prompt.ask(
            "Digite qual banco quer iniciar"
        )

        with console.status(
            f"[green]Iniciando {escolha_banco}...[/green]",
            spinner="dots"
        ):
            resultado = iniciar_banco(
                escolha_banco,
                bancos
            )

        console.print(
            Panel(
                resultado,
                title="Sucesso",
                border_style="green"
            )
        )

    except Exception as erro:
        console.print(
            Panel(
                str(erro),
                title="Erro",
                border_style="red"
            )
        )


def parar_banco_menu(bancos):
    try:
        escolha_banco = Prompt.ask(
            "Digite qual banco quer parar"
        )

        with console.status(
            f"[yellow]Parando {escolha_banco}...[/yellow]",
            spinner="dots"
        ):
            resultado = parar_banco(
                escolha_banco,
                bancos
            )

        console.print(
            Panel(
                resultado,
                title="Resultado",
                border_style="yellow"
            )
        )

    except Exception as erro:
        console.print(
            Panel(
                str(erro),
                title="Erro",
                border_style="red"
            )
        )


def main():
    programa_ativo = True

    console.clear()

    mostrar_cabecalho()

    bancos = analisar_maquina()

    while programa_ativo:

        console.print()
        mostrar_menu()

        escolha = Prompt.ask(
            "Escolha uma opção",
            choices=["1", "2", "3", "4"]
        )

        console.print()

        match escolha:

            case "1":
                listar_bancos(bancos)

            case "2":
                iniciar_banco_menu(bancos)

            case "3":
                parar_banco_menu(bancos)

            case "4":
                console.print(
                    Panel(
                        "Até mais!",
                        title="LOCAL DATABASE MANAGER",
                        border_style="cyan"
                    )
                )

                programa_ativo = False

        if programa_ativo:
            console.input(
                "\nPressione [bold]Enter[/bold] para continuar..."
            )

            console.clear()
            mostrar_cabecalho()


if __name__ == "__main__":
    main()