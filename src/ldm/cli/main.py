from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.text import Text

import logging
import tempfile
import sys
from pathlib import Path

from ldm.core.database_manager import (
    verificar_status_banco,
    iniciar_banco,
    parar_banco,
    descobrir_bancos
)

from ldm.core.windows import (
    is_admin,
    executar_como_administrador
)


console = Console()

CODIGO_SUCESSO = 0
CODIGO_ERRO = 1
CODIGO_BANCO_INEXISTENTE = 2
CODIGO_JA_NO_ESTADO_DESEJADO = 3


def executar_operacao_elevada(argumentos):
    caminho_resultado = None
    comando = "desconhecido"
    banco = "não identificado"
    if "--result-file" in argumentos:
        indice_resultado = argumentos.index("--result-file")
        if indice_resultado + 1 < len(argumentos):
            caminho_resultado = Path(argumentos[indice_resultado + 1])

    try:
        _, comando, banco = argumentos[:3]
        bancos = descobrir_bancos()

        match comando:
            case "start":
                resultado = iniciar_banco(banco, bancos)
                mensagem_estado = "O banco já estava em execução"

            case "stop":
                resultado = parar_banco(banco, bancos)
                mensagem_estado = "O banco já estava parado"

            case _:
                raise ValueError(
                    f"Comando elevado desconhecido: {comando}"
                )

        if resultado == "Banco inexistente":
            return CODIGO_BANCO_INEXISTENTE

        if resultado == mensagem_estado:
            return CODIGO_JA_NO_ESTADO_DESEJADO

        return CODIGO_SUCESSO

    except Exception as erro:
        logging.exception("Falha na operação elevada de %s para %s", comando, banco)
        if caminho_resultado is not None:
            caminho_resultado.write_text(
                f"{type(erro).__name__}: {erro}",
                encoding="utf-8"
            )
        return CODIGO_ERRO


def interpretar_codigo_operacao(codigo_saida, acao, detalhe=None):
    match codigo_saida:
        case 0:
            return f"Banco {acao} com sucesso"

        case 2:
            return "Banco inexistente"

        case 3:
            if acao == "iniciado":
                return "O banco já estava em execução"
            return "O banco já estava parado"

        case _:
            if detalhe:
                raise RuntimeError(
                    f"Não foi possível {acao} o banco: {detalhe}"
                )
            raise RuntimeError(
                f"Não foi possível {acao} o banco."
            )


def executar_operacao_com_elevacao(comando, banco, acao):
    with tempfile.NamedTemporaryFile(
        prefix="ldm-result-",
        suffix=".txt",
        delete=False
    ) as arquivo_resultado:
        caminho_resultado = Path(arquivo_resultado.name)

    try:
        try:
            codigo_saida = executar_como_administrador(
                [
                    "-m",
                    "ldm.cli.main",
                    "--elevated",
                    comando,
                    banco,
                    "--result-file",
                    str(caminho_resultado)
                ]
            )
        except RuntimeError as erro:
            detalhe = caminho_resultado.read_text(encoding="utf-8").strip()
            if not detalhe:
                raise
            raise RuntimeError(
                f"Não foi possível {acao} o banco: {detalhe}"
            ) from erro

        detalhe = caminho_resultado.read_text(encoding="utf-8").strip()
        return interpretar_codigo_operacao(
            codigo_saida,
            acao,
            detalhe or None
        )
    finally:
        caminho_resultado.unlink(missing_ok=True)


def mostrar_resultado(resultado):
    if resultado == "Banco inexistente":
        titulo = "Aviso"
        cor = "yellow"

    elif resultado in (
        "O banco já estava em execução",
        "O banco já estava parado"
    ):
        titulo = "Informação"
        cor = "cyan"

    else:
        titulo = "Sucesso"
        cor = "green"

    console.print(
        Panel(
            resultado,
            title=titulo,
            border_style=cor
        )
    )


def mensagem_operacao_em_andamento(erro):
    texto = str(erro).upper()

    if "START_PENDING" in texto:
        return "Em processo de iniciar"
    if "STOP_PENDING" in texto:
        return "Em processo de parar"
    if "PAUSE_PENDING" in texto:
        return "Em processo de pausar"
    if "CONTINUE_PENDING" in texto:
        return "Em processo de continuar"

    return None


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
            elif status == "STOPPED":
                status_formatado = Text(
                    "● STOPPED",
                    style="red"
                )
            else:
                status_formatado = Text(
                    "● EM ANDAMENTO",
                    style="yellow"
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

        if not is_admin():
            with console.status(
                f"[green]Iniciando {escolha_banco}...[/green]",
                spinner="dots"
            ):
                resultado = executar_operacao_com_elevacao(
                    "start",
                    escolha_banco,
                    "iniciado"
                )

        else:
            with console.status(
                f"[green]Iniciando {escolha_banco}...[/green]",
                spinner="dots"
            ):
                resultado = iniciar_banco(
                    escolha_banco,
                    bancos
                )

        mostrar_resultado(resultado)

    except Exception as erro:
        mensagem = mensagem_operacao_em_andamento(erro)

        if mensagem:
            console.print(
                Panel(
                    mensagem,
                    title="Informação",
                    border_style="cyan"
                )
            )
            return

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

        if not is_admin():
            with console.status(
                f"[yellow]Parando {escolha_banco}...[/yellow]",
                spinner="dots"
            ):
                resultado = executar_operacao_com_elevacao(
                    "stop",
                    escolha_banco,
                    "parado"
                )

        else:
            with console.status(
                f"[yellow]Parando {escolha_banco}...[/yellow]",
                spinner="dots"
            ):
                resultado = parar_banco(
                    escolha_banco,
                    bancos
                )

        mostrar_resultado(resultado)

    except Exception as erro:
        mensagem = mensagem_operacao_em_andamento(erro)

        if mensagem:
            console.print(
                Panel(
                    mensagem,
                    title="Informação",
                    border_style="cyan"
                )
            )
            return

        console.print(
            Panel(
                str(erro),
                title="Erro",
                border_style="red"
            )
        )


def main():
    argumentos = sys.argv[1:]

    if argumentos and argumentos[0] == "--elevated":
        codigo_saida = executar_operacao_elevada(argumentos)
        sys.exit(codigo_saida)

    console.clear()
    mostrar_cabecalho()

    bancos = analisar_maquina()
    programa_ativo = True

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
