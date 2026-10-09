import ctypes
import sys
from ctypes import wintypes


SEE_MASK_NOCLOSEPROCESS = 0x00000040
SW_HIDE = 0


class SHELLEXECUTEINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("fMask", wintypes.ULONG),
        ("hwnd", wintypes.HWND),
        ("lpVerb", wintypes.LPCWSTR),
        ("lpFile", wintypes.LPCWSTR),
        ("lpParameters", wintypes.LPCWSTR),
        ("lpDirectory", wintypes.LPCWSTR),
        ("nShow", ctypes.c_int),
        ("hInstApp", wintypes.HINSTANCE),
        ("lpIDList", ctypes.c_void_p),
        ("lpClass", wintypes.LPCWSTR),
        ("hkeyClass", wintypes.HKEY),
        ("dwHotKey", wintypes.DWORD),
        ("hIcon", wintypes.HANDLE),
        ("hProcess", wintypes.HANDLE),
    ]


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except AttributeError:
        return False


def executar_como_administrador(argumentos):
    """
    Executa o LDM com privilégios administrativos.

    A operação é executada em um processo elevado e oculto.
    A função aguarda o término desse processo e retorna seu
    código de saída.
    """

    parametros = " ".join(
        f'"{argumento}"' if " " in argumento else argumento
        for argumento in argumentos
    )

    informacoes = SHELLEXECUTEINFO()
    informacoes.cbSize = ctypes.sizeof(SHELLEXECUTEINFO)
    informacoes.fMask = SEE_MASK_NOCLOSEPROCESS
    informacoes.lpVerb = "runas"
    informacoes.lpFile = sys.executable
    informacoes.lpParameters = parametros
    informacoes.nShow = SW_HIDE

    resultado = ctypes.windll.shell32.ShellExecuteExW(
        ctypes.byref(informacoes)
    )

    if not resultado:
        raise RuntimeError(
            "Não foi possível solicitar privilégios administrativos."
        )

    ctypes.windll.kernel32.WaitForSingleObject(
        informacoes.hProcess,
        0xFFFFFFFF
    )

    codigo_saida = wintypes.DWORD()

    ctypes.windll.kernel32.GetExitCodeProcess(
        informacoes.hProcess,
        ctypes.byref(codigo_saida)
    )

    ctypes.windll.kernel32.CloseHandle(
        informacoes.hProcess
    )

    if codigo_saida.value == 1:
        raise RuntimeError(
            "A operação administrativa terminou com erro."
        )

    return codigo_saida.value