import pytest
import subprocess
from unittest.mock import patch, Mock

from ldm.core.database_manager import (
    buscar_banco,
    tratando_excecoes,
    verificar_status_servico,
    iniciar_servico,
    parar_servico,
    iniciar_banco,
    parar_banco
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

@patch("ldm.core.database_manager.subprocess.run")
@patch("ldm.core.database_manager.verificar_status_servico")
def test_parar_servico(mock_status, mock_run):
    # simulamos que o serviço está rodando e depois para
    mock_status.side_effect = ["RUNNING", "STOPPED"]

    mock_resultado = Mock()
    mock_run.return_value = mock_resultado

    resultado = parar_servico("MySQL80")

    assert resultado is True

    mock_run.assert_called_with(
        ["sc.exe", "stop", "MySQL80"],
        capture_output=True,
        text=True,
        check=True,
        timeout=10
    )

@patch("ldm.core.database_manager.subprocess.run")
@patch("ldm.core.database_manager.verificar_status_servico")
def test_parar_servico_quando_ja_esta_parado(mock_status, mock_run):
    # simulamos que o serviço já está parado
    mock_status.return_value = "STOPPED"

    resultado = parar_servico("MySQL80")

    assert resultado is True

    mock_run.assert_not_called()

@patch("ldm.core.database_manager.subprocess.run")
@patch("ldm.core.database_manager.verificar_status_servico")
def test_iniciar_servico_quando_ja_esta_rodando(mock_status, mock_run):
    # simulamos que o serviço já está rodando
    mock_status.return_value = "RUNNING"

    resultado = iniciar_servico("MySQL80")

    assert resultado is True

    mock_run.assert_not_called()

@patch("ldm.core.database_manager.subprocess.run")
@patch("ldm.core.database_manager.verificar_status_servico")
def test_iniciar_servico_erro(mock_status, mock_run):
    # simulamos que o Windows falhou ao iniciar o serviço
    mock_status.return_value = "STOPPED"
    mock_run.side_effect = subprocess.CalledProcessError(
        1,
        ["sc.exe", "start", "MySQL80"],
        stderr="Erro ao iniciar serviço"
    )

    with pytest.raises(Exception):
        iniciar_servico("MySQL80")

@patch("ldm.core.database_manager.subprocess.run")
@patch("ldm.core.database_manager.verificar_status_servico")
def test_parar_servico_erro(mock_status, mock_run):
    # simulamos que o Windows falhou ao parar o serviço
    mock_status.return_value = "RUNNING"
    mock_run.side_effect = subprocess.CalledProcessError(
        1,
        ["sc.exe", "stop", "MySQL80"],
        stderr="Erro ao parar serviço"
    )

    with pytest.raises(Exception):
        parar_servico("MySQL80")

@patch("ldm.core.database_manager.iniciar_servico")
def test_iniciar_banco(mock_iniciar):
    # simulamos os serviços de um banco e verificamos se todos são iniciados
    bancos = [
        {
            "name": "MySQL",
            "evidencias": {
                "servicos": [
                    {"name": "MySQL80"},
                    {"name": "MySQLBackup"}
                ]
            }
        }
    ]

    resultado = iniciar_banco("MySQL", bancos)

    assert resultado == "Banco iniciado com sucesso"

    assert mock_iniciar.call_count == 2
    mock_iniciar.assert_any_call("MySQL80")
    mock_iniciar.assert_any_call("MySQLBackup")
    
def test_iniciar_banco_inexistente():
    # simulamos uma tentativa de iniciar um banco que não foi encontrado
    bancos = [
        {
            "name": "MySQL",
            "evidencias": {
                "servicos": [
                    {"name": "MySQL80"}
                ]
            }
        }
    ]

    resultado = iniciar_banco("PostgreSQL", bancos)

    assert resultado == "Banco inexistente"

@patch("ldm.core.database_manager.parar_servico")
def test_parar_banco(mock_parar):
    # simulamos os serviços de um banco e verificamos se todos são parados
    bancos = [
        {
            "name": "MySQL",
            "evidencias": {
                "servicos": [
                    {"name": "MySQL80"},
                    {"name": "MySQLBackup"}
                ]
            }
        }
    ]

    resultado = parar_banco("MySQL", bancos)

    assert resultado == "Banco parado com sucesso"

    assert mock_parar.call_count == 2
    mock_parar.assert_any_call("MySQL80")
    mock_parar.assert_any_call("MySQLBackup")

def test_parar_banco_inexistente():
    # simulamos uma tentativa de parar um banco que não foi encontrado
    bancos = [
        {
            "name": "MySQL",
            "evidencias": {
                "servicos": [
                    {"name": "MySQL80"}
                ]
            }
        }
    ]

    resultado = parar_banco("PostgreSQL", bancos)

    assert resultado == "PostgreSQL - Banco inexistente"