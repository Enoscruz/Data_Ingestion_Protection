"""Missao 7 - Privacidade e LGPD: minimizacao, K-anonimato e agregado."""
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from comum import DIR, ler_csv, escrever_csv

REF = "2026-10-04"
FAIXAS = [(25, 34, "25–34"), (35, 44, "35–44"), (45, 54, "45–54")]


def idade(nascimento, ref=REF):
    n = date.fromisoformat(nascimento)
    r = date.fromisoformat(ref)
    return r.year - n.year - ((r.month, r.day) < (n.month, n.day))


def faixa_etaria(nascimento, ref=REF):
    i = idade(nascimento, ref)
    for lo, hi, rotulo in FAIXAS:
        if lo <= i <= hi:
            return rotulo
    return "%d–%d" % ((i // 10) * 10, (i // 10) * 10 + 9)


def generalizar_nascimento():
    """Troca o nascimento pela faixa etaria na camada silver."""
    linhas = ler_csv(os.path.join(DIR["silver"], "clientes.csv"))
    for l in linhas:
        l["faixa_etaria"] = faixa_etaria(l["nascimento"])
    out = [{"cliente_ps": l["cliente_ps"], "faixa_etaria": l["faixa_etaria"], "cidade": l["cidade"]}
           for l in linhas]
    escrever_csv(os.path.join(DIR["silver"], "clientes.csv"),
                 ["cliente_ps", "faixa_etaria", "cidade"], out)
    return out


def medir_k():
    """Combina cidade + faixa etaria: quantas combinacoes tem uma pessoa so."""
    combinacoes = {}
    for l in ler_csv(os.path.join(DIR["silver"], "clientes.csv")):
        chave = (l["cidade"], l["faixa_etaria"])
        combinacoes[chave] = combinacoes.get(chave, 0) + 1
    unicas = {c: n for c, n in combinacoes.items() if n == 1}
    return combinacoes, unicas


def visao_consumo(K=2):
    """Agregado receita_por_cidade com limiar minimo K."""
    clientes = ler_csv(os.path.join(DIR["silver"], "clientes.csv"))
    pedidos = ler_csv(os.path.join(DIR["silver"], "pedidos.csv"))
    ps_cidade = {c["cliente_ps"]: c["cidade"] for c in clientes}
    contagem, receita = {}, {}
    for c in clientes:
        contagem[c["cidade"]] = contagem.get(c["cidade"], 0) + 1
    for p in pedidos:
        cid = ps_cidade.get(p["cliente_ps"])
        if p["status"] == "pago" and cid:
            receita[cid] = receita.get(cid, 0) + int(p["valor_centavos"])
    linhas = []
    for cid in sorted(contagem):
        n = contagem[cid]
        if n >= K:
            linhas.append({"cidade": cid, "clientes": n,
                           "receita_centavos": receita.get(cid, 0), "situacao": "liberada"})
        else:
            linhas.append({"cidade": cid, "clientes": n,
                           "receita_centavos": 0, "situacao": "suprimida"})
    escrever_csv(os.path.join(DIR["gold"], "receita_por_cidade.csv"),
                 ["cidade", "clientes", "receita_centavos", "situacao"], linhas)
    total = sum(int(p["valor_centavos"]) for p in pedidos if p["status"] == "pago")
    return linhas, total
