import ctypes
from ctypes import wintypes

import pytest

from ldm.core import windows


def criar_windll_mock(shell32, kernel32=None):
    """Cria um objeto que simula as APIs do Windows utilizadas pelo módulo."""

    atributos = {
        "shell32": shell32
    }

    if kernel32 is not None:
        atributos["kernel32"] = kernel32

    return type(
        "WindllMock",
        (),
        atributos
    )()


def preencher_codigo_saida(codigo_saida, valor):
    """Preenche o DWORD recebido através de ctypes.byref()."""

    ponteiro = ctypes.cast(
        codigo_saida,
        ctypes.POINTER(wintypes.DWORD)
    )

    ponteiro.contents.value = valor


def test_is_admin_retorna_true_quando_usuario_e_administrador(monkeypatch):
    """Deve retornar True quando o Windows informa que o usuário é administrador."""

    class Shell32Mock:
        def IsUserAnAdmin(self):
            return 1

    monkeypatch.setattr(
        windows.ctypes,
        "windll",
        criar_windll_mock(Shell32Mock())
    )

    assert windows.is_admin() is True


def test_is_admin_retorna_false_quando_usuario_nao_e_administrador(monkeypatch):
    """Deve retornar False quando o Windows informa que o usuário não é administrador."""

    class Shell32Mock:
        def IsUserAnAdmin(self):
            return 0

    monkeypatch.setattr(
        windows.ctypes,
        "windll",
        criar_windll_mock(Shell32Mock())
    )

    assert windows.is_admin() is False


def test_is_admin_retorna_false_quando_api_administrativa_nao_esta_disponivel(
    monkeypatch
):
    """Deve retornar False quando a API administrativa não está disponível."""

    class Shell32Mock:
        def IsUserAnAdmin(self):
            raise AttributeError

    monkeypatch.setattr(
        windows.ctypes,
        "windll",
        criar_windll_mock(Shell32Mock())
    )

    assert windows.is_admin() is False


def test_executar_como_administrador_solicita_elevacao(monkeypatch):
    """Deve solicitar elevação, ocultar a janela e aguardar o processo elevado."""

    chamadas = []
    handles_aguardados = []
    handles_fechados = []

    class Shell32Mock:
        def ShellExecuteExW(self, informacoes):
            ponteiro = ctypes.cast(
                informacoes,
                ctypes.POINTER(windows.SHELLEXECUTEINFO)
            )

            estrutura = ponteiro.contents

            chamadas.append({
                "verb": estrutura.lpVerb,
                "file": estrutura.lpFile,
                "parameters": estrutura.lpParameters,
                "show": estrutura.nShow,
                "mask": estrutura.fMask,
            })

            estrutura.hProcess = 1234

            return 1

    class Kernel32Mock:
        def WaitForSingleObject(self, handle, timeout):
            handles_aguardados.append((handle, timeout))
            return 0

        def GetExitCodeProcess(self, handle, codigo_saida):
            preencher_codigo_saida(codigo_saida, 0)
            return 1

        def CloseHandle(self, handle):
            handles_fechados.append(handle)
            return 1

    monkeypatch.setattr(
        windows.ctypes,
        "windll",
        criar_windll_mock(
            Shell32Mock(),
            Kernel32Mock()
        )
    )

    resultado = windows.executar_como_administrador(
        ["-m", "ldm.cli.main", "--elevated", "start", "SQL Server"]
    )

    assert resultado == 0

    assert chamadas == [{
        "verb": "runas",
        "file": windows.sys.executable,
        "parameters": '-m ldm.cli.main --elevated start "SQL Server"',
        "show": windows.SW_HIDE,
        "mask": windows.SEE_MASK_NOCLOSEPROCESS,
    }]

    assert handles_aguardados == [
        (1234, 0xFFFFFFFF)
    ]

    assert handles_fechados == [1234]
    
def test_executar_como_administrador_levanta_erro_quando_elevacao_falha(
    monkeypatch
):
    """Deve informar erro quando o Windows não consegue iniciar o processo elevado."""

    class Shell32Mock:
        def ShellExecuteExW(self, informacoes):
            return 0

    class Kernel32Mock:
        def WaitForSingleObject(self, handle, timeout):
            pytest.fail(
                "Não deveria aguardar um processo quando a elevação falhou."
            )

    monkeypatch.setattr(
        windows.ctypes,
        "windll",
        criar_windll_mock(
            Shell32Mock(),
            Kernel32Mock()
        )
    )

    with pytest.raises(
        RuntimeError,
        match="Não foi possível solicitar privilégios administrativos."
    ):
        windows.executar_como_administrador(
            ["-m", "ldm.cli.main", "--elevated", "start", "Oracle"]
        )


def test_executar_como_administrador_levanta_erro_quando_processo_elevado_termina_com_erro(
    monkeypatch
):
    """Deve informar erro quando a operação elevada termina com código diferente de zero."""

    handles_fechados = []

    class Shell32Mock:
        def ShellExecuteExW(self, informacoes):
            ponteiro = ctypes.cast(
                informacoes,
                ctypes.POINTER(windows.SHELLEXECUTEINFO)
            )

            ponteiro.contents.hProcess = 5678

            return 1

    class Kernel32Mock:
        def WaitForSingleObject(self, handle, timeout):
            assert handle == 5678
            assert timeout == 0xFFFFFFFF
            return 0

        def GetExitCodeProcess(self, handle, codigo_saida):
            assert handle == 5678

            preencher_codigo_saida(codigo_saida, 1)

            return 1

        def CloseHandle(self, handle):
            handles_fechados.append(handle)
            return 1

    monkeypatch.setattr(
        windows.ctypes,
        "windll",
        criar_windll_mock(
            Shell32Mock(),
            Kernel32Mock()
        )
    )

    with pytest.raises(
        RuntimeError,
        match="A operação administrativa terminou com erro."
    ):
        windows.executar_como_administrador(
            ["-m", "ldm.cli.main", "--elevated", "stop", "Oracle"]
        )

    assert handles_fechados == [5678]


def test_executar_como_administrador_aguarda_processo_antes_de_retornar(
    monkeypatch
):
    """Deve esperar o processo elevado terminar antes de retornar."""

    eventos = []

    class Shell32Mock:
        def ShellExecuteExW(self, informacoes):
            ponteiro = ctypes.cast(
                informacoes,
                ctypes.POINTER(windows.SHELLEXECUTEINFO)
            )

            ponteiro.contents.hProcess = 9999

            eventos.append("executou")

            return 1

    class Kernel32Mock:
        def WaitForSingleObject(self, handle, timeout):
            eventos.append("aguardou")

            assert handle == 9999
            assert timeout == 0xFFFFFFFF

            return 0

        def GetExitCodeProcess(self, handle, codigo_saida):
            eventos.append("consultou_codigo")

            preencher_codigo_saida(codigo_saida, 0)

            return 1

        def CloseHandle(self, handle):
            eventos.append("fechou")
            return 1

    monkeypatch.setattr(
        windows.ctypes,
        "windll",
        criar_windll_mock(
            Shell32Mock(),
            Kernel32Mock()
        )
    )

    windows.executar_como_administrador(
        ["-m", "ldm.cli.main", "--elevated", "start", "MySQL"]
    )

    assert eventos == [
        "executou",
        "aguardou",
        "consultou_codigo",
        "fechou"
    ]