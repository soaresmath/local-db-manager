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
    parar_banco,
    obter_configuracao_servico,
    descobrir_bancos
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
def test_verificar_status_servico_start_pending(mock_run):
    # simulamos a resposta do Windows para testar um serviço em processo de inicialização
    mock_resultado = Mock()
    mock_resultado.stdout = "STATE : 2 START_PENDING"
    mock_run.return_value = mock_resultado

    resultado = verificar_status_servico("MySQL80")

    assert resultado == "START_PENDING"

@patch("ldm.core.database_manager.subprocess.run")
def test_verificar_status_servico_stop_pending(mock_run):
    # simulamos a resposta do Windows para testar um serviço em processo de parada
    mock_resultado = Mock()
    mock_resultado.stdout = "STATE : 3 STOP_PENDING"
    mock_run.return_value = mock_resultado

    resultado = verificar_status_servico("MySQL80")

    assert resultado == "STOP_PENDING"

@patch("ldm.core.database_manager.subprocess.run")
def test_verificar_status_servico_paused(mock_run):
    # simulamos a resposta do Windows para testar um serviço pausado
    mock_resultado = Mock()
    mock_resultado.stdout = "STATE : 7 PAUSED"
    mock_run.return_value = mock_resultado

    resultado = verificar_status_servico("MySQL80")

    assert resultado == "PAUSED"

@patch("ldm.core.database_manager.subprocess.run")
def test_verificar_status_servico_pause_pending(mock_run):
    # simulamos a resposta do Windows para testar um serviço entrando em pausa
    mock_resultado = Mock()
    mock_resultado.stdout = "STATE : 6 PAUSE_PENDING"
    mock_run.return_value = mock_resultado

    resultado = verificar_status_servico("MySQL80")

    assert resultado == "PAUSE_PENDING"

@patch("ldm.core.database_manager.subprocess.run")
def test_verificar_status_servico_continue_pending(mock_run):
    # simulamos a resposta do Windows para testar um serviço retomando sua execução
    mock_resultado = Mock()
    mock_resultado.stdout = "STATE : 5 CONTINUE_PENDING"
    mock_run.return_value = mock_resultado

    resultado = verificar_status_servico("MySQL80")

    assert resultado == "CONTINUE_PENDING"


@patch("ldm.core.database_manager.subprocess.run")
def test_verificar_status_servico_estado_nao_identificado(mock_run):
    # simulamos uma resposta sem informação de estado para testar o tratamento do erro
    mock_resultado = Mock()
    mock_resultado.stdout = "SERVICE_NAME: MySQL80"
    mock_run.return_value = mock_resultado

    with pytest.raises(RuntimeError):
        verificar_status_servico("MySQL80")

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

@patch("ldm.core.database_manager.verificar_status_servico")
def test_iniciar_servico_quando_esta_rodando(mock_status):
    # simulamos um serviço que já está em execução para verificar se o LDM evita iniciar novamente
    mock_status.return_value = "RUNNING"

    resultado = iniciar_servico("MySQL80")

    assert resultado is True
    mock_status.assert_called_once_with("MySQL80")

@patch("ldm.core.database_manager.verificar_status_servico")
def test_iniciar_servico_quando_esta_pausado(mock_status):
    # simulamos um serviço pausado para verificar se o LDM impede a tentativa de inicialização
    mock_status.return_value = "PAUSED"

    with pytest.raises(RuntimeError):
        iniciar_servico("MySQL80")

@patch("ldm.core.database_manager.verificar_status_servico")
def test_iniciar_servico_start_pending(mock_status):
    # simulamos um serviço iniciando até atingir o estado RUNNING
    mock_status.side_effect = [
        "START_PENDING",
        "START_PENDING",
        "RUNNING"
    ]

    resultado = iniciar_servico("MySQL80")

    assert resultado is True

@patch("ldm.core.database_manager.verificar_status_servico")
@patch("ldm.core.database_manager.subprocess.run")
def test_iniciar_servico_stop_pending(mock_run, mock_status):
    # simulamos um serviço parando até chegar em STOPPED e depois sendo iniciado novamente
    mock_status.side_effect = [
        "STOP_PENDING",
        "STOPPED",
        "STOPPED",
        "START_PENDING",
        "RUNNING"
    ]

    mock_resultado = Mock()
    mock_resultado.stdout = "START_PENDING"
    mock_run.return_value = mock_resultado

    resultado = iniciar_servico("MySQL80")

    assert resultado is True

@patch("ldm.core.database_manager.verificar_status_servico")
def test_iniciar_servico_pause_pending(mock_status):
    # simulamos um serviço entrando em pausa até atingir o estado PAUSED
    mock_status.side_effect = [
        "PAUSE_PENDING",
        "PAUSED"
    ]

    with pytest.raises(RuntimeError):
        iniciar_servico("MySQL80")

@patch("ldm.core.database_manager.verificar_status_servico")
def test_iniciar_servico_continue_pending(mock_status):
    # simulamos um serviço retomando a execução até atingir o estado RUNNING
    mock_status.side_effect = [
        "CONTINUE_PENDING",
        "CONTINUE_PENDING",
        "RUNNING"
    ]

    resultado = iniciar_servico("MySQL80")

    assert resultado is True

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

@patch("ldm.core.database_manager.verificar_status_servico")
def test_parar_servico_quando_esta_parado(mock_status):
    # simulamos um serviço que já está parado para verificar se nenhuma parada é necessária
    mock_status.return_value = "STOPPED"

    resultado = parar_servico("MySQL80")

    assert resultado is True
    mock_status.assert_called_once_with("MySQL80")

@patch("ldm.core.database_manager.verificar_status_servico")
@patch("ldm.core.database_manager.subprocess.run")
def test_parar_servico_quando_esta_rodando(mock_run, mock_status):
    # simulamos um serviço em execução que é parado com sucesso
    mock_status.side_effect = [
        "RUNNING",
        "RUNNING",
        "STOPPED"
    ]

    mock_resultado = Mock()
    mock_run.return_value = mock_resultado

    resultado = parar_servico("MySQL80")

    assert resultado is True
    mock_run.assert_called_once()

@patch("ldm.core.database_manager.verificar_status_servico")
def test_parar_servico_stop_pending(mock_status):
    # simulamos um serviço que já está sendo parado até atingir STOPPED
    mock_status.side_effect = [
        "STOP_PENDING",
        "STOP_PENDING",
        "STOPPED"
    ]

    resultado = parar_servico("MySQL80")

    assert resultado is True

@patch("ldm.core.database_manager.verificar_status_servico")
@patch("ldm.core.database_manager.subprocess.run")
def test_parar_servico_start_pending(mock_run, mock_status):
    # simulamos um serviço iniciando até chegar em RUNNING e depois sendo parado
    mock_status.side_effect = [
        "START_PENDING",
        "RUNNING",
        "RUNNING",
        "STOPPED"
    ]

    mock_resultado = Mock()
    mock_run.return_value = mock_resultado

    resultado = parar_servico("MySQL80")

    assert resultado is True
    mock_run.assert_called_once()

@patch("ldm.core.database_manager.verificar_status_servico")
def test_parar_servico_quando_esta_pausado(mock_status):
    # simulamos um serviço pausado para verificar se o LDM impede a parada automática
    mock_status.return_value = "PAUSED"

    with pytest.raises(RuntimeError):
        parar_servico("MySQL80")

@patch("ldm.core.database_manager.verificar_status_servico")
def test_parar_servico_pause_pending(mock_status):
    # simulamos um serviço entrando em pausa até atingir PAUSED
    mock_status.side_effect = [
        "PAUSE_PENDING",
        "PAUSED"
    ]

    with pytest.raises(RuntimeError):
        parar_servico("MySQL80")

@patch("ldm.core.database_manager.verificar_status_servico")
@patch("ldm.core.database_manager.subprocess.run")
def test_parar_servico_continue_pending(mock_run, mock_status):
    # simulamos um serviço retomando a execução até RUNNING e depois sendo parado
    mock_status.side_effect = [
        "CONTINUE_PENDING",
        "RUNNING",
        "RUNNING",
        "STOPPED"
    ]

    mock_resultado = Mock()
    mock_run.return_value = mock_resultado

    resultado = parar_servico("MySQL80")

    assert resultado is True
    mock_run.assert_called_once()

@patch("ldm.core.database_manager.verificar_status_servico")
def test_parar_servico_estado_nao_suportado(mock_status):
    # simulamos um estado desconhecido para verificar se o LDM rejeita a operação
    mock_status.return_value = "UNKNOWN"

    with pytest.raises(RuntimeError):
        parar_servico("MySQL80")

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
