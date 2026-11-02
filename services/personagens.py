# Exclusão total de um personagem: lista, ficha, memória/avatar, turno e estado da mesa.
import glob
import os
import shutil

from rpg.config import carregar_dados_jogadores, definir_morto, salvar_dados_jogadores
from rpg.fichas import PASTA_FICHAS
from services import sessao
from rpg.turno import carregar_turno, salvar_turno
from rpg.paths import ARQUIVOS


def _tirar_da_cena(nome: str):
    # Sai do modo por turnos, da lista de envolvidos e das chamadas pendentes (morte ou exclusão).
    with sessao.LOCK_TURNO:
        turno = carregar_turno()
        if turno:
            pid = f"p_{nome}"
            turno["personagens"] = [p for p in turno["personagens"] if p["id"] != pid]
            for a in turno["areas"]:
                a["participantes"] = [x for x in a["participantes"] if x != pid]
            salvar_turno(turno)

    s = sessao.obter()
    s["envolvidos"] = [e for e in s["envolvidos"] if e != nome]
    s["pending_chamadas"] = [
        c for c in s["pending_chamadas"] if nome not in (c["origem"], c["destino"])
    ]
    sessao.salvar()


def marcar_morto(nome: str, morto: bool):
    # Morto: a ficha e a memória ficam (para consulta e passagem de itens), mas ele sai da cena e das mensagens.
    definir_morto(nome, morto)
    if morto:
        _tirar_da_cena(nome)


def excluir_personagem(nome: str) -> bool:
    dados = carregar_dados_jogadores()
    nova = [j for j in dados if j.get("nome", "").lower() != nome.lower()]
    if len(nova) == len(dados):
        return False
    salvar_dados_jogadores(nova)

    shutil.rmtree(os.path.join(ARQUIVOS, f"memoria_{nome}"), ignore_errors=True)
    for arq in glob.glob(os.path.join(PASTA_FICHAS, f"{nome.lower()}_*")):
        try:
            os.remove(arq)
        except OSError:
            pass

    _tirar_da_cena(nome)
    s = sessao.obter()
    s["ultima_fala"].pop(nome, None)
    s["compressao_perguntada"].pop(nome, None)
    sessao.salvar()
    return True
