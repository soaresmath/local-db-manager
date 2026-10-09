from pathlib import Path
from io import StringIO

import pytest

from ldm.cli import main


def test_listar_bancos_exibe_mixed_como_operacao_em_andamento(
    monkeypatch,
    capsys
):
    bancos = [{"name": "BancoTeste", "evidencias": {"servicos": []}}]

    monkeypatch.setattr(main, "verificar_status_banco", lambda banco: "MIXED")

    main.listar_bancos(bancos)

    saida = capsys.readouterr().out
    assert "EM ANDAMENTO" in saida


def test_mensagem_operacao_em_andamento_ignora_transicao_genérica():
    erro = RuntimeError(
        "O serviço 'BancoTeste' não atingiu RUNNING. Estado atual: START_PENDING."
    )

    assert main.mensagem_operacao_em_andamento(erro) == "Em processo de iniciar"


def test_operacao_elevada_preserva_detalhe_da_excecao(tmp_path, monkeypatch):
    # verifica se a operação elevada grava a causa original da falha
    arquivo_resultado = tmp_path / "resultado.txt"

    monkeypatch.setattr(
        main,
        "descobrir_bancos",
        lambda: [{"name": "Oracle", "evidencias": {"servicos": []}}]
    )

    def falhar_inicio(banco, bancos):
        raise RuntimeError("Falha no serviço OracleServiceFREE")

    monkeypatch.setattr(main, "iniciar_banco", falhar_inicio)

    codigo = main.executar_operacao_elevada([
        "--elevated",
        "start",
        "Oracle",
        "--result-file",
        str(arquivo_resultado)
    ])

    assert codigo == main.CODIGO_ERRO
    assert arquivo_resultado.read_text(encoding="utf-8") == (
        "RuntimeError: Falha no serviço OracleServiceFREE"
    )


def test_operacao_elevada_apresenta_detalhe_retornado_pelo_processo(monkeypatch):
    # verifica se a CLI apresenta o detalhe enviado pelo processo elevado
    def executar_como_admin(argumentos):
        caminho_resultado = Path(argumentos[-1])
        caminho_resultado.write_text(
            "RuntimeError: Falha no serviço OracleServiceFREE",
            encoding="utf-8"
        )
        return main.CODIGO_ERRO

    monkeypatch.setattr(main, "executar_como_administrador", executar_como_admin)

    with pytest.raises(
        RuntimeError,
        match="Falha no serviço OracleServiceFREE"
    ):
        main.executar_operacao_com_elevacao("start", "Oracle", "iniciado")