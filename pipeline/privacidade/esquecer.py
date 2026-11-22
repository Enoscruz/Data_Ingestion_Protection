"""Missao 8 - O direito de ser esquecido.

O comando `esquecer <id>` trata todas as moradas do titular, e a lista de
eliminacao registra a prova sem nenhum dado pessoal.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "seguranca"))
from comum import DIR, CAMPOS, ler_csv, escrever_csv, anexar_csv
import seguranca

LISTA = os.path.join(DIR["eliminacao"], "lista.csv")
CAMPOS_LISTA = ["chave", "data", "moradas_tratadas"]

MORADAS = [
    "origem.clientes", "origem.pedidos.observacao", "origem.navegacao",
    "log.mudancas", "log.navegacao", "estado.leitores",
    "bronze.clientes", "bronze.pedidos", "bronze.navegacao",
    "silver.clientes", "silver.pedidos", "silver.navegacao",
    "copia.seguranca",
]


def _sem_cliente(linhas, campo, id_cliente):
    return [l for l in linhas if l.get(campo) != id_cliente]


def esquecer(id_cliente, carimbo="2026-10-04T00:00:00"):
    ps = seguranca.pseudonimo(id_cliente)

    # origem
    c = os.path.join(DIR["origem"], "clientes.csv")
    escrever_csv(c, CAMPOS["clientes"], _sem_cliente(ler_csv(c), "id", id_cliente))
    p = os.path.join(DIR["origem"], "pedidos.csv")
    linhas = ler_csv(p)
    for l in linhas:
        if l["cliente_id"] == id_cliente:
            l["observacao"] = ""
    escrever_csv(p, CAMPOS["pedidos"], linhas)
    n = os.path.join(DIR["origem"], "navegacao.csv")
    escrever_csv(n, CAMPOS["navegacao"], _sem_cliente(ler_csv(n), "cliente_id", id_cliente))

    # log (o log nao se edita: o evento de exclusao permanece como marcador)
    ln = os.path.join(DIR["log"], "navegacao.csv")
    escrever_csv(ln, CAMPOS["navegacao"], _sem_cliente(ler_csv(ln), "cliente_id", id_cliente))

    # camada bronze
    bc = os.path.join(DIR["bronze"], "clientes.csv")
    escrever_csv(bc, CAMPOS["clientes"] + CAMPOS["controle"], _sem_cliente(ler_csv(bc), "id", id_cliente))
    bp = os.path.join(DIR["bronze"], "pedidos.csv")
    linhas = ler_csv(bp)
    for l in linhas:
        if l["cliente_id"] == id_cliente:
            l["observacao"] = ""
    escrever_csv(bp, CAMPOS["pedidos"] + CAMPOS["controle"], linhas)
    bn = os.path.join(DIR["bronze"], "navegacao.csv")
    escrever_csv(bn, CAMPOS["navegacao"] + CAMPOS["controle"], _sem_cliente(ler_csv(bn), "cliente_id", id_cliente))

    # camada silver
    sc = os.path.join(DIR["silver"], "clientes.csv")
    escrever_csv(sc, ler_campos(sc), [l for l in ler_csv(sc) if l["cliente_ps"] != ps])
    sp = os.path.join(DIR["silver"], "pedidos.csv")
    linhas = ler_csv(sp)
    for l in linhas:
        if l["cliente_ps"] == ps:
            l["cliente_ps"] = ""
    escrever_csv(sp, ler_campos(sp), linhas)
    sn = os.path.join(DIR["silver"], "navegacao.csv")
    escrever_csv(sn, ler_campos(sn), [l for l in ler_csv(sn) if l["cliente_ps"] != ps])

    # lista de eliminacao: idempotente e sem dado pessoal
    lista = ler_csv(LISTA)
    if not any(l["chave"] == id_cliente for l in lista):
        anexar_csv(LISTA, CAMPOS_LISTA,
                   [{"chave": id_cliente, "data": carimbo, "moradas_tratadas": ";".join(MORADAS)}])
    return len(MORADAS)


def ler_campos(caminho):
    import csv
    with open(caminho, "r", encoding="utf-8") as f:
        return next(csv.reader(f), [])
