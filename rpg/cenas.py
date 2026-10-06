# Cenas do mestre (arquivos/cenas/*.txt)
import re
from pathlib import Path
from rpg.paths import ARQUIVOS

PASTA_CENAS = Path(ARQUIVOS) / "cenas"


def nome_seguro(nome: str) -> str:
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
    arquivo = PASTA_CENAS / f"{nome}.txt"
    if arquivo.exists():
        arquivo.unlink()
        return True
    return False
