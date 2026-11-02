# Salvar e restaurar a mesa (arquivos/ + tokens/) como .zip em mesas/
import glob
import json
import os
import re
import shutil
import zipfile
from datetime import datetime
from rpg.paths import RAIZ as _PASTA_RAIZ, MESAS as PASTA_MESAS

_PASTA_STAGING = os.path.join(PASTA_MESAS, ".restore_tmp")

_RAIZES = ("arquivos", "tokens")
_CONFIG_LLM = os.path.join("arquivos", "config.json")  # contém a API Key: fora do backup
_PRESERVAR = (_CONFIG_LLM, os.path.join("arquivos", "limites.json"))  # configuração/uso da LLM: sobrevivem a restaurar e reiniciar
_IGNORAR_ARQUIVOS = {"fila.json"}  # a fila de requests não é restaurada: uma ação pela metade não faz sentido
_IGNORAR_PASTAS = {"__pycache__"}
_NOME_VALIDO = re.compile(r"^[\w\- ]+$", re.UNICODE)
_SUFIXO_AUTOSAVE = r"_autosave_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}"
_RE_AUTOSAVE = re.compile(_SUFIXO_AUTOSAVE + "$")


def eh_autosave(nome: str) -> bool:
    return bool(_RE_AUTOSAVE.search(nome))


def nome_valido(nome: str):
    nome = (nome or "").strip()
    if not nome or not _NOME_VALIDO.match(nome):
        return None
    return nome


def _caminho_nome_mesa() -> str:
    return os.path.join(_PASTA_RAIZ, "arquivos", "mesa.json")  # entra no backup: restaurar volta para a mesa do zip


def nome_mesa_atual() -> str:
    # "" = a mesa ainda não tem nome (não dá para iniciar rodada nem salvar backup)
    try:
        with open(_caminho_nome_mesa(), "r", encoding="utf-8") as f:
            return (json.load(f).get("nome") or "").strip()
    except (OSError, ValueError, AttributeError):
        return ""


def definir_nome_mesa(nome: str):
    limpo = nome_valido(nome)
    if not limpo:
        return False, "Nome inválido. Use apenas letras, números, espaço, '-' e '_'."
    caminho = _caminho_nome_mesa()
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump({"nome": limpo}, f, ensure_ascii=False)
    return True, limpo


def _caminho_mesa(nome: str) -> str:
    return os.path.join(PASTA_MESAS, f"{nome}.zip")


def listar_mesas() -> list[str]:
    os.makedirs(PASTA_MESAS, exist_ok=True)
    arquivos = [f for f in os.listdir(PASTA_MESAS) if f.lower().endswith(".zip")]
    arquivos.sort(key=lambda f: os.path.getmtime(os.path.join(PASTA_MESAS, f)), reverse=True)
    return [f[:-4] for f in arquivos]


def excluir_mesa(nome: str):
    # só apaga o que está listado em mesas/ (o nome vem da URL: nunca vira caminho solto)
    if nome not in listar_mesas():
        return False, "Backup não encontrado."
    if eh_autosave(nome):
        return False, "O autosave não pode ser excluído: ele é substituído a cada rodada finalizada."
    try:
        os.remove(_caminho_mesa(nome))
    except OSError as e:
        return False, f"Não foi possível excluir o backup: {e}"
    return True, f"Backup '{nome}' excluído."


def mesa_existe(nome: str) -> bool:
    return os.path.isfile(_caminho_mesa(nome))


def info_mesa(nome: str) -> tuple[float, int]:
    # (data de modificação, tamanho em bytes)
    st = os.stat(_caminho_mesa(nome))
    return st.st_mtime, st.st_size


def salvar_mesa(nome: str):
    mesa = nome_mesa_atual()
    if not mesa:
        return False, "Dê um nome à mesa antes de salvar o backup."
    limpo = nome_valido(nome)
    if not limpo:
        return False, "Nome inválido. Use apenas letras, números, espaço, '-' e '_'."
    limpo = f"{mesa}_{limpo}"  # o arquivo sempre começa pelo nome da mesa
    if eh_autosave(limpo):
        return False, "Esse nome é reservado para o autosave."
    return _gravar_zip(limpo)


def salvar_autosave():
    # Backup automático depois de finalizar a rodada: um por mesa. O anterior só é apagado depois que o novo existe.
    mesa = nome_mesa_atual()
    if not mesa:
        return False, "a mesa não tem nome"
    novo = f"{mesa}_autosave_{datetime.now():%Y-%m-%d_%H-%M-%S}"
    ok, msg = _gravar_zip(novo)
    if not ok:
        return False, msg
    anteriores = re.compile("^" + re.escape(mesa) + _SUFIXO_AUTOSAVE + "$")
    for antigo in listar_mesas():
        if antigo != novo and anteriores.match(antigo):
            try:
                os.remove(_caminho_mesa(antigo))
            except OSError:
                pass
    return True, novo


def _gravar_zip(limpo: str):
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
                        if rel in _PRESERVAR or arq in _IGNORAR_ARQUIVOS or arq.endswith(".tmp"):
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

    # valida e extrai para staging, sem tocar nos dados atuais
    shutil.rmtree(_PASTA_STAGING, ignore_errors=True)
    try:
        with zipfile.ZipFile(_caminho_mesa(nome)) as zf:
            _validar_zip(zf)
            zf.extractall(_PASTA_STAGING)
        for raiz in _RAIZES:
            os.makedirs(os.path.join(_PASTA_STAGING, raiz), exist_ok=True)

        # a config da LLM atual é mantida (a API Key não vai no backup)
        for rel in _PRESERVAR:
            atual = os.path.join(_PASTA_RAIZ, rel)
            if os.path.isfile(atual):
                shutil.copy2(atual, os.path.join(_PASTA_STAGING, rel))
    except Exception as e:
        shutil.rmtree(_PASTA_STAGING, ignore_errors=True)
        return False, f"Não foi possível restaurar: {e}"

    # troca por rename, com rollback se algo falhar
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


def resetar_mesa():
    # Apaga tudo de arquivos/ e tokens/, mantendo só a config/uso da LLM e os default.txt/base.txt (placeholders versionados)
    manter = {os.path.join(_PASTA_RAIZ, rel) for rel in _PRESERVAR}
    try:
        for raiz in _RAIZES:
            base = os.path.join(_PASTA_RAIZ, raiz)
            for pasta, _, arquivos in os.walk(base, topdown=False):
                for arq in arquivos:
                    caminho = os.path.join(pasta, arq)
                    if arq not in ("default.txt", "base.txt") and caminho not in manter:
                        os.remove(caminho)
                if pasta != base:
                    try:
                        os.rmdir(pasta)  # só remove se ficou vazia
                    except OSError:
                        pass
    except Exception as e:
        return False, f"Erro ao resetar a mesa: {e}"
    return True, "Mesa resetada."


# Partes de um backup que "Importar base" sabe trazer para uma mesa nova (personagens tem tratamento próprio).
CATEGORIAS_BASE = {
    "regras": "arquivos/regras/",
    "padrao": "arquivos/padrao_ficha.json",
    "anotacoes": "arquivos/anotacoes_mestre.txt",
    "inimigos": "tokens/inimigo/",
    "npcs": "tokens/npc/",
    "itens": "tokens/item/",
}


def _vivos_do_backup(zf: zipfile.ZipFile) -> list[str]:
    try:
        dados = json.loads(zf.read("arquivos/jogadores.json").decode("utf-8"))
    except (KeyError, ValueError):
        return []
    return [j["nome"] for j in dados if isinstance(j, dict) and j.get("nome") and not j.get("morto")]


def _membro_da_base(rel: str, categorias: set, vivos: list[str]) -> bool:
    for cat, alvo in CATEGORIAS_BASE.items():
        if cat in categorias and (rel == alvo or (alvo.endswith("/") and rel.startswith(alvo))):
            return True
    if "personagens" not in categorias:
        return False
    if rel == "arquivos/jogadores.json":
        return True
    for nome in vivos:
        if rel.startswith(f"arquivos/fichas/{nome.lower()}_") or re.fullmatch(rf"arquivos/memoria_{re.escape(nome)}/avatar\.[^/]+", rel):
            return True
    return False


def importar_base(backup: str, categorias: list[str], nome_nova: str):
    # Começa uma mesa NOVA: apaga tudo e traz do backup só as partes escolhidas (nada é mesclado).
    # Personagens: só os vivos, com ficha e foto; a memória deles começa vazia.
    escolhidas = set(categorias)
    if not escolhidas or not escolhidas <= {*CATEGORIAS_BASE, "personagens"}:
        return False, "Escolha ao menos uma parte da base para importar."
    nome = nome_valido(nome_nova)
    if not nome:
        return False, "Nome da nova mesa inválido. Use apenas letras, números, espaço, '-' e '_'."
    if not backup or not mesa_existe(backup):
        return False, "Backup não encontrado."

    # extrai só o escolhido para staging, antes de apagar qualquer coisa
    shutil.rmtree(_PASTA_STAGING, ignore_errors=True)
    try:
        with zipfile.ZipFile(_caminho_mesa(backup)) as zf:
            _validar_zip(zf)
            vivos = _vivos_do_backup(zf) if "personagens" in escolhidas else []
            for membro in zf.namelist():
                rel = membro.replace("\\", "/")
                if not rel.endswith("/") and _membro_da_base(rel, escolhidas, vivos):
                    zf.extract(membro, _PASTA_STAGING)
        jogadores = os.path.join(_PASTA_STAGING, "arquivos", "jogadores.json")
        if "personagens" in escolhidas and os.path.isfile(jogadores):
            with open(jogadores, "r", encoding="utf-8") as f:
                lista = [j for j in json.load(f) if isinstance(j, dict) and j.get("nome") and not j.get("morto")]
            with open(jogadores, "w", encoding="utf-8") as f:
                json.dump(lista, f, ensure_ascii=False)
            for j in lista:
                os.makedirs(os.path.join(_PASTA_STAGING, "arquivos", f"memoria_{j['nome']}"), exist_ok=True)
    except Exception as e:
        shutil.rmtree(_PASTA_STAGING, ignore_errors=True)
        return False, f"Não foi possível importar: {e}"

    ok, msg = resetar_mesa()
    if not ok:
        shutil.rmtree(_PASTA_STAGING, ignore_errors=True)
        return False, msg
    try:
        for raiz in _RAIZES:
            base = os.path.join(_PASTA_STAGING, raiz)
            for pasta, _, arquivos in os.walk(base):
                destino = os.path.join(_PASTA_RAIZ, os.path.relpath(pasta, _PASTA_STAGING))
                os.makedirs(destino, exist_ok=True)
                for arq in arquivos:
                    shutil.copy2(os.path.join(pasta, arq), os.path.join(destino, arq))
    except Exception as e:
        return False, f"A importação falhou no meio (a mesa foi limpa): {e}"
    finally:
        shutil.rmtree(_PASTA_STAGING, ignore_errors=True)
    definir_nome_mesa(nome)
    return True, f"Nova mesa '{nome}' criada com a base de '{backup}'."


def reiniciar_mesa():
    # Recomeça a campanha do zero mantendo o cenário: só apaga a memória dos personagens (rodadas, cenas, mesa,
    # rascunho da rodada e métricas); avatares, fichas, regras, cenas, tokens e configuração da LLM ficam.
    try:
        for pasta in glob.glob(os.path.join(_PASTA_RAIZ, "arquivos", "memoria_*")):
            if not os.path.isdir(pasta):
                continue
            for arq in os.listdir(pasta):
                caminho = os.path.join(pasta, arq)
                if os.path.isfile(caminho) and not arq.startswith("avatar."):
                    os.remove(caminho)
    except Exception as e:
        return False, f"Erro ao reiniciar a mesa: {e}"
    return True, "Mesa reiniciada: personagens, fichas, cenas e tokens mantidos; memórias apagadas."
