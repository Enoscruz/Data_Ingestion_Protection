"""Missao 1 - Ingestao em lote e ELT.

Copia a origem para a camada bronze por mesclagem, lendo so o que mudou
desde a ultima marca-d'agua. Rodar de novo com a mesma entrada nao muda
o resultado (idempotencia).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import comum
from comum import DIR, CAMPOS, ler_csv, escrever_csv, anexar_csv, ler_json, salvar_json

ARQ_MARCA = os.path.join(DIR["estado"], "marca_agua.json")
TABELAS = ("clientes", "pedidos", "navegacao")


def _campos_bronze(tabela):
    return CAMPOS[tabela] + CAMPOS["controle"]


def reiniciar_origem():
    """Devolve o banco de origem ao estado do dia 1."""
    for t in TABELAS:
        escrever_csv(os.path.join(DIR["origem"], t + ".csv"), CAMPOS[t],
                     ler_csv(os.path.join(DIR["dia1"], t + ".csv")))


def limpar_bronze():
    """Camada bronze vazia: a primeira carga parte do zero."""
    for t in TABELAS:
        escrever_csv(os.path.join(DIR["bronze"], t + ".csv"), _campos_bronze(t), [])


def reiniciar_bronze_dia1():
    """Camada bronze ja com o dia 1 carregado (usado para refazer a Missao 2)."""
    for t in TABELAS:
        linhas = [dict(l, _carregado_em="2026-10-01T00:00:00", _execucao="0")
                  for l in ler_csv(os.path.join(DIR["dia1"], t + ".csv"))]
        escrever_csv(os.path.join(DIR["bronze"], t + ".csv"), _campos_bronze(t), linhas)


def limpar_marca_agua():
    salvar_json(ARQ_MARCA, {})


def _mesclar(caminho_bronze, campos, novas, execucao):
    atuais = ler_csv(caminho_bronze)
    indice = {l["id"]: i for i, l in enumerate(atuais)}
    for n in novas:
        linha = dict(n, _execucao=str(execucao))
        if n["id"] in indice:
            atuais[indice[n["id"]]] = linha
        else:
            indice[n["id"]] = len(atuais)
            atuais.append(linha)
    escrever_csv(caminho_bronze, campos, atuais)


def carga_incremental(execucao, carimbo):
    """Le so as linhas com atualizado_em maior que a marca-d'agua e mescla na bronze."""
    marca = ler_json(ARQ_MARCA, {})
    lidas = {}
    for t in ("clientes", "pedidos"):
        origem = ler_csv(os.path.join(DIR["origem"], t + ".csv"))
        novas = [dict(l, _carregado_em=carimbo) for l in origem
                 if l["atualizado_em"] > marca.get(t, "")]
        _mesclar(os.path.join(DIR["bronze"], t + ".csv"), _campos_bronze(t), novas, execucao)
        if novas:
            marca[t] = max(n["atualizado_em"] for n in novas)
        lidas[t] = {"n": len(novas), "ids": [n["id"] for n in novas]}
    salvar_json(ARQ_MARCA, marca)
    return lidas


def carga_navegacao(execucao, carimbo):
    """Anexa eventos novos, sem duplicar pela chave evento_id."""
    origem = ler_csv(os.path.join(DIR["origem"], "navegacao.csv"))
    existentes = {l["evento_id"] for l in ler_csv(os.path.join(DIR["bronze"], "navegacao.csv"))}
    novas = [dict(l, _carregado_em=carimbo, _execucao=str(execucao))
             for l in origem if l["evento_id"] not in existentes]
    anexar_csv(os.path.join(DIR["bronze"], "navegacao.csv"), _campos_bronze("navegacao"), novas)
    return len(novas)


def totais(layer="bronze"):
    cl = ler_csv(os.path.join(DIR[layer], "clientes.csv"))
    pd = ler_csv(os.path.join(DIR[layer], "pedidos.csv"))
    nv = ler_csv(os.path.join(DIR[layer], "navegacao.csv"))
    return {"clientes": len(cl), "pedidos": len(pd), "navegacao": len(nv),
            "receita": comum.receita_paga(pd)}
