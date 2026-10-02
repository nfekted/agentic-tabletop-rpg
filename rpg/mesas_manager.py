# Salvar / restaurar a mesa inteira (arquivos/ + tokens/) como um .zip dentro de mesas/
import os
import re
import shutil
import zipfile
from rpg.paths import RAIZ, ARQUIVOS, TOKENS, MESAS

_PASTA_RAIZ = RAIZ
PASTA_MESAS = MESAS
PASTA_ARQUIVOS = ARQUIVOS
PASTA_TOKENS = TOKENS
_PASTA_STAGING = os.path.join(PASTA_MESAS, ".restore_tmp")

_RAIZES = ("arquivos", "tokens")
_CONFIG_LLM = os.path.join("arquivos", "config.json")  # contém a API Key: fora do backup
_IGNORAR_ARQUIVOS = {"rodada_atual_temp.txt", "sessao.json"}  # rodada não finalizada (estado da sessão)
_IGNORAR_PASTAS = {"__pycache__"}
_NOME_VALIDO = re.compile(r"^[\w\- ]+$", re.UNICODE)


def nome_valido(nome: str):
    nome = (nome or "").strip()
    if not nome or not _NOME_VALIDO.match(nome):
        return None
    return nome


def _caminho_mesa(nome: str) -> str:
    return os.path.join(PASTA_MESAS, f"{nome}.zip")


def listar_mesas() -> list[str]:
    os.makedirs(PASTA_MESAS, exist_ok=True)
    arquivos = [f for f in os.listdir(PASTA_MESAS) if f.lower().endswith(".zip")]
    arquivos.sort(key=lambda f: os.path.getmtime(os.path.join(PASTA_MESAS, f)), reverse=True)
    return [f[:-4] for f in arquivos]


def mesa_existe(nome: str) -> bool:
    return os.path.isfile(_caminho_mesa(nome))


def info_mesa(nome: str) -> tuple[float, int]:
    # (data de modificação, tamanho em bytes)
    st = os.stat(_caminho_mesa(nome))
    return st.st_mtime, st.st_size


def salvar_mesa(nome: str):
    limpo = nome_valido(nome)
    if not limpo:
        return False, "Nome inválido. Use apenas letras, números, espaço, '-' e '_'."

    os.makedirs(PASTA_MESAS, exist_ok=True)
    destino = _caminho_mesa(limpo)
    tmp = destino + ".tmp"
    try:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
            for raiz in _RAIZES:
                base = os.path.join(_PASTA_RAIZ, raiz)
                if not os.path.isdir(base):
                    continue
                zf.writestr(raiz + "/", "")
                for pasta, subpastas, arquivos in os.walk(base):
                    subpastas[:] = [d for d in subpastas if d not in _IGNORAR_PASTAS]
                    rel_pasta = os.path.relpath(pasta, _PASTA_RAIZ)
                    if rel_pasta != raiz:
                        zf.writestr(rel_pasta.replace(os.sep, "/") + "/", "")
                    for arq in arquivos:
                        rel = os.path.join(rel_pasta, arq)
                        if rel == _CONFIG_LLM or arq in _IGNORAR_ARQUIVOS:
                            continue
                        zf.write(os.path.join(pasta, arq), rel.replace(os.sep, "/"))
        os.replace(tmp, destino)
    except Exception as e:
        if os.path.exists(tmp):
            os.remove(tmp)
        return False, f"Erro ao salvar a mesa: {e}"
    return True, f"Mesa '{limpo}' salva em mesas/{limpo}.zip"


def _validar_zip(zf: zipfile.ZipFile):
    if zf.testzip() is not None:
        raise ValueError("Arquivo .zip corrompido.")
    for membro in zf.namelist():
        partes = membro.replace("\\", "/").split("/")
        if membro.startswith(("/", "\\")) or ".." in partes or partes[0] not in _RAIZES:
            raise ValueError(f"Conteúdo inválido no arquivo: '{membro}'.")


def restaurar_mesa(nome: str):
    if not nome or not mesa_existe(nome):
        return False, "Mesa não encontrada."

    # 1 e 2: valida e extrai para staging, sem tocar nos dados atuais
    shutil.rmtree(_PASTA_STAGING, ignore_errors=True)
    try:
        with zipfile.ZipFile(_caminho_mesa(nome)) as zf:
            _validar_zip(zf)
            zf.extractall(_PASTA_STAGING)
        for raiz in _RAIZES:
            os.makedirs(os.path.join(_PASTA_STAGING, raiz), exist_ok=True)

        # 3: preserva a config da LLM atual (API Key não vai no backup)
        atual_cfg = os.path.join(_PASTA_RAIZ, _CONFIG_LLM)
        if os.path.isfile(atual_cfg):
            shutil.copy2(atual_cfg, os.path.join(_PASTA_STAGING, _CONFIG_LLM))
    except Exception as e:
        shutil.rmtree(_PASTA_STAGING, ignore_errors=True)
        return False, f"Não foi possível restaurar: {e}"

    # 4: troca por rename, com rollback se algo falhar
    movidos = []
    try:
        for raiz in _RAIZES:
            atual = os.path.join(_PASTA_RAIZ, raiz)
            if os.path.exists(atual):
                os.rename(atual, atual + ".old")
                movidos.append(raiz)
        for raiz in _RAIZES:
            os.rename(os.path.join(_PASTA_STAGING, raiz), os.path.join(_PASTA_RAIZ, raiz))
    except Exception as e:
        for raiz in _RAIZES:
            novo = os.path.join(_PASTA_RAIZ, raiz)
            if raiz in movidos and os.path.exists(novo):
                shutil.rmtree(novo, ignore_errors=True)
        for raiz in movidos:
            os.rename(os.path.join(_PASTA_RAIZ, raiz + ".old"), os.path.join(_PASTA_RAIZ, raiz))
        shutil.rmtree(_PASTA_STAGING, ignore_errors=True)
        return False, f"Falha ao trocar os dados (nada foi alterado): {e}"

    for raiz in movidos:
        shutil.rmtree(os.path.join(_PASTA_RAIZ, raiz + ".old"), ignore_errors=True)
    shutil.rmtree(_PASTA_STAGING, ignore_errors=True)
    return True, f"Mesa '{nome}' restaurada."
