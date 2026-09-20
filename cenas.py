# Persistência das cenas do Mestre (arquivos .txt em arquivos/cenas).
import re
from pathlib import Path

PASTA_CENAS = Path("arquivos") / "cenas"


def nome_seguro(nome: str) -> str:
    # Remove caracteres inválidos para nome de arquivo.
    return re.sub(r'[\\/:*?"<>|]', "", nome).strip()


def listar_cenas() -> list[str]:
    PASTA_CENAS.mkdir(parents=True, exist_ok=True)
    return sorted(p.stem for p in PASTA_CENAS.glob("*.txt"))


def ler_cena(nome: str) -> str:
    arquivo = PASTA_CENAS / f"{nome}.txt"
    if not arquivo.exists():
        return ""
    return arquivo.read_text(encoding="utf-8")


def salvar_cena(nome: str, conteudo: str) -> None:
    PASTA_CENAS.mkdir(parents=True, exist_ok=True)
    (PASTA_CENAS / f"{nome}.txt").write_text(conteudo, encoding="utf-8")


def deletar_cena(nome: str) -> bool:
    # Deleta o arquivo da cena se ele existir no disco.
    arquivo = PASTA_CENAS / f"{nome}.txt"
    if arquivo.exists():
        arquivo.unlink()
        return True
    return False
