"""Missao 3 - Streaming: um log, varios leitores.

A navegacao corre por um topico. Cada leitor guarda o proprio offset e
le no seu ritmo; um leitor novo comeca do zero e assiste a historia.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from comum import DIR, CAMPOS, ler_csv, escrever_csv, anexar_csv, ler_json, salvar_json

ARQ_OFFSETS = os.path.join(DIR["estado"], "offsets.json")
TOPICO = os.path.join(DIR["log"], "navegacao.csv")
BRONZE = os.path.join(DIR["bronze"], "navegacao.csv")
CARIMBO = "2026-10-02T00:00:00"


def _offset(chave):
    return int(ler_json(ARQ_OFFSETS, {}).get(chave, 0))


def _set_offset(chave, valor):
    o = ler_json(ARQ_OFFSETS, {})
    o[chave] = valor
    salvar_json(ARQ_OFFSETS, o)


def reiniciar_topico():
    """Topico vazio e bronze de navegacao zerada: a carga em lote sai de cena."""
    escrever_csv(TOPICO, CAMPOS["navegacao"], [])
    escrever_csv(BRONZE, CAMPOS["navegacao"] + CAMPOS["controle"], [])
    for k in ("visitas", "bronze_navegacao", "por_cliente"):
        _set_offset(k, 0)


def publicar():
    """O produtor publica os eventos do dia 1 e nao sabe quem vai ler."""
    eventos = ler_csv(os.path.join(DIR["origem"], "navegacao.csv"))
    anexar_csv(TOPICO, CAMPOS["navegacao"], eventos)
    return len(eventos)


def _eventos():
    return ler_csv(TOPICO)


def leitor_visitas(parar_apos=None):
    """Leitor rapido: conta visitas por pagina. `parar_apos` simula uma queda."""
    eventos = _eventos()
    pos = _offset("visitas")
    limite = len(eventos) if parar_apos is None else min(len(eventos), pos + parar_apos)
    _set_offset("visitas", limite)
    contagem = {}
    for e in eventos[:limite]:
        contagem[e["pagina"]] = contagem.get(e["pagina"], 0) + 1
    return contagem


def leitor_bronze():
    """Leitor lento: grava o que chegou desde o seu offset, sem duplicar."""
    eventos = _eventos()
    pos = _offset("bronze_navegacao")
    novos = [dict(e, _carregado_em=CARIMBO, _execucao="fluxo") for e in eventos[pos:]]
    anexar_csv(BRONZE, CAMPOS["navegacao"] + CAMPOS["controle"], novos)
    _set_offset("bronze_navegacao", len(eventos))
    return len(novos)


def leitor_por_cliente():
    """Leitor novo, ligado depois de tudo: le desde o offset 0."""
    eventos = _eventos()
    pos = _offset("por_cliente")
    contagem = {}
    for e in eventos[pos:]:
        chave = e["cliente_id"] or "(sem cadastro)"
        contagem[chave] = contagem.get(chave, 0) + 1
    _set_offset("por_cliente", len(eventos))
    return contagem
