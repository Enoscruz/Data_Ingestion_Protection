"""Missao 2 - CDC: o banco conta o que mudou.

A origem registra cada mudanca em um log ordenado (so anexa). O pipeline
guarda o offset e aplica so o que veio depois, em ordem, inclusive exclusoes.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from comum import DIR, CAMPOS, ler_csv, escrever_csv, anexar_csv, ler_json, salvar_json

ARQ_OFFSETS = os.path.join(DIR["estado"], "offsets.json")
LOG_MUDANCAS = os.path.join(DIR["log"], "mudancas.csv")


def _offset(chave):
    return int(ler_json(ARQ_OFFSETS, {}).get(chave, 0))


def _set_offset(chave, valor):
    o = ler_json(ARQ_OFFSETS, {})
    o[chave] = valor
    salvar_json(ARQ_OFFSETS, o)


def reiniciar_log_mudancas():
    escrever_csv(LOG_MUDANCAS, CAMPOS["mudanca"], [])
    _set_offset("mudancas", 0)


def _dados(mudanca):
    return json.loads(mudanca["dados"]) if mudanca["dados"] else {}


def aplicar_dia2(registrar_log):
    """Aplica as mudancas do dia 2 na origem (e, se pedido, registra no log)."""
    mudancas = ler_csv(os.path.join(DIR["dia2"], "mudancas.csv"))
    for m in mudancas:
        tabela, op, chave = m["tabela"], m["operacao"], m["chave"]
        campos_origem = os.path.join(DIR["origem"], tabela + ".csv")
        linhas = ler_csv(campos_origem)
        dados = _dados(m)
        if op == "EXCLUSAO":
            linhas = [l for l in linhas if l["id"] != chave]
        elif op == "INSERCAO":
            linhas.append(dict({"id": chave}, **dados))
        else:
            for l in linhas:
                if l["id"] == chave:
                    l.update(dados)
        escrever_csv(campos_origem, CAMPOS[tabela], linhas)
    if registrar_log:
        anexar_csv(LOG_MUDANCAS, CAMPOS["mudanca"], mudancas)
    return len(mudancas)


def consumir_log(execucao, carimbo):
    """Aplica na camada bronze os eventos do log ainda nao aplicados."""
    log = ler_csv(LOG_MUDANCAS)
    pos = _offset("mudancas")
    aplicados = 0
    for m in log[pos:]:
        tabela = m["tabela"]
        caminho = os.path.join(DIR["bronze"], tabela + ".csv")
        linhas = ler_csv(caminho)
        indice = {l["id"]: i for i, l in enumerate(linhas)}
        dados = _dados(m)
        if m["operacao"] == "EXCLUSAO":
            linhas = [l for l in linhas if l["id"] != m["chave"]]
        elif m["operacao"] == "INSERCAO":
            nova = dict({"id": m["chave"], "_carregado_em": carimbo,
                         "_execucao": str(execucao)}, **dados)
            if m["chave"] in indice:
                linhas[indice[m["chave"]]] = nova
            else:
                linhas.append(nova)
        else:
            for l in linhas:
                if l["id"] == m["chave"]:
                    l.update(dados)
                    l["_carregado_em"] = carimbo
                    l["_execucao"] = str(execucao)
        escrever_csv(caminho, CAMPOS[tabela] + CAMPOS["controle"], linhas)
        aplicados += 1
    _set_offset("mudancas", len(log))
    return aplicados
