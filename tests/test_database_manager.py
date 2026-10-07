import pytest
import inspect
from unittest.mock import patch, Mock

from ldm.core.database_manager import (
    buscar_banco,
    tratando_excecoes,
    verificar_status_servico,
    iniciar_servico
)


def test_buscar_banco_encontra_banco():
    # testa se conseguimos encontrar o banco pelo nome
    bancos = [
        {"name": "MySQL"},
        {"name": "PostgreSQL"}
    ]

    resultado = buscar_banco("mysql", bancos)

    assert resultado == {"name": "MySQL"}


def test_buscar_banco_retorna_false_quando_nao_encontra():
    # testa o comportamento quando o banco não existe na lista
    bancos = [
        {"name": "MySQL"},
        {"name": "PostgreSQL"}
    ]

    resultado = buscar_banco("Oracle", bancos)

    assert resultado is False


def test_tratando_excecoes():
    # testa se conseguimos juntar as mensagens das exceções
    erros = [
        Exception("Erro 1"),
        Exception("Erro 2")
    ]

    resultado = tratando_excecoes(erros)

    assert resultado == "\nErro 1\nErro 2"


@patch("ldm.core.database_manager.subprocess.run")
def test_verificar_status_servico_running(mock_run):
    # simulamos a resposta do Windows para testar nossa lógica
    mock_resultado = Mock()
    mock_resultado.stdout = "STATE : 4  RUNNING"
    mock_run.return_value = mock_resultado

    resultado = verificar_status_servico("MySQL80")

    assert resultado == "RUNNING"

@patch("ldm.core.database_manager.subprocess.run")
def test_verificar_status_servico_stopped(mock_run):
    # simulamos a resposta do Windows para testar nossa lógica
    mock_resultado = Mock()
    mock_resultado.stdout = "STATE: 4 STOPPED"
    mock_run.return_value = mock_resultado

    resultado = verificar_status_servico("MySQL80")

    assert resultado == "STOPPED"

@patch("ldm.core.database_manager.subprocess.run")
def test_verificar_status_servico_erro(mock_run):
    # simulamos um erro do Windows
    mock_essecao = Mock()
    mock_essecao = Exception("Erro")
    mock_run.side_effect = mock_essecao

    with pytest.raises(Exception):
        verificar_status_servico("MySQL80") 

@patch("ldm.core.database_manager.subprocess.run")
@patch("ldm.core.database_manager.verificar_status_servico")
def test_iniciar_servico(mock_status, mock_run):
    # simulamos que o serviço está parado e depois inicia
    mock_status.side_effect = ["STOPPED", "RUNNING"]

    mock_resultado = Mock()
    mock_resultado.stdout = "START_PENDING"
    mock_run.return_value = mock_resultado

    resultado = iniciar_servico("MySQL80")

    assert resultado is True

    mock_run.assert_called_once_with(
        ["sc.exe", "start", "MySQL80"],
        capture_output=True,
        text=True,
        check=True,
        timeout=10
    )