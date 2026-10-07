from unittest.mock import patch, Mock

from ldm.core.database_manager import (
    verificar_status_servico,
    obter_configuracao_servico,
    descobrir_bancos
)


def test_verificar_status_servico_integracao():
    # testa a comunicação real com o Windows
    resultado = verificar_status_servico("MySQL80")

    assert resultado in ["RUNNING", "STOPPED"]

def test_obter_configuracao_servico_integracao():
    # testa se conseguimos obter a configuração de um serviço real
    resultado = obter_configuracao_servico("MySQL80")

    assert resultado

def test_descobrir_bancos_integracao():
    # testa a descoberta de bancos usando os serviços reais da máquina
    resultado = descobrir_bancos()

    assert isinstance(resultado, list)
    assert resultado