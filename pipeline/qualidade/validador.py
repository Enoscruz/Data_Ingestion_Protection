"""Missao 4 - Contrato, validador e quarentena.

As regras vem do arquivo de contrato, nao ficam fixas no codigo. Linha
reprovada vai para a quarentena com o motivo; o resto do lote segue.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import yaml
from comum import DIR, CAMPOS, AGORA, ler_csv, escrever_csv

CAMPOS_SILVER = ["id", "cliente_id", "valor_centavos", "status", "criado_em", "_execucao"]
CAMPOS_QUAR = CAMPOS["pedidos"] + ["motivo", "_execucao"]


def carregar_contrato(conjunto):
    with open(os.path.join(DIR_CONTRATOS, conjunto + ".yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


DIR_CONTRATOS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "contratos")


def carregar_lote_dia3(execucao, carimbo):
    lote = ler_csv(os.path.join(DIR["dia3"], "pedidos_dia3.csv"))
    caminho = os.path.join(DIR["bronze"], "pedidos.csv")
    atuais = ler_csv(caminho)
    for l in lote:
        atuais.append(dict(l, _carregado_em=carimbo, _execucao=str(execucao)))
    escrever_csv(caminho, CAMPOS["pedidos"] + CAMPOS["controle"], atuais)
    return len(lote)


def _motivo(linha, contrato, vistos):
    for campo in contrato["campos"]:
        nome = campo["nome"]
        valor = (linha.get(nome) or "").strip()
        if campo.get("obrigatorio") and valor == "":
            return "cliente ausente" if nome == "cliente_id" else "campo obrigatório vazio: " + nome
        if valor == "":
            continue
        if campo.get("tipo") == "inteiro" and not re.fullmatch(r"-?\d+", valor):
            return "tipo inválido: " + nome
        if "minimo" in campo and int(valor) < campo["minimo"]:
            return "valor negativo" if nome == "valor_centavos" else "abaixo do mínimo: " + nome
        if "dominio" in campo and valor not in campo["dominio"]:
            return "status fora do domínio" if nome == "status" else "fora do domínio: " + nome
        if campo.get("maximo") == "momento da carga" and valor > AGORA:
            return "data no futuro" if nome == "criado_em" else "depois do momento da carga: " + nome
        if campo.get("unico") and valor in vistos:
            return "chave repetida" if nome == "id" else "valor repetido: " + nome
    return None


def validar(execucao):
    contrato = carregar_contrato("pedidos")
    vistos = set()
    aceitas, quarentena = [], []
    for linha in ler_csv(os.path.join(DIR["bronze"], "pedidos.csv")):
        motivo = _motivo(linha, contrato, vistos)
        if motivo:
            quarentena.append(dict(linha, motivo=motivo, _execucao=str(execucao)))
        else:
            vistos.add(linha["id"])
            aceitas.append({"id": linha["id"], "cliente_id": linha["cliente_id"],
                            "valor_centavos": linha["valor_centavos"], "status": linha["status"],
                            "criado_em": linha["criado_em"], "_execucao": str(execucao)})
    escrever_csv(os.path.join(DIR["silver"], "pedidos.csv"), CAMPOS_SILVER, aceitas)
    escrever_csv(os.path.join(DIR["quarentena"], "pedidos.csv"), CAMPOS_QUAR, quarentena)
    return {"aceitas": len(aceitas), "quarentena": len(quarentena),
            "motivos": [q["motivo"] for q in quarentena]}
