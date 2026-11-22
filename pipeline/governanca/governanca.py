"""Missao 5 - Governanca e catalogo.

Regra como codigo (falha o pipeline), catalogo gerado por script e um
varredor que acha dado pessoal escondido onde ninguem declarou.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import yaml
from comum import DIR, ler_csv

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTRATOS = os.path.join(RAIZ, "contratos")
ACORDO = os.path.join(RAIZ, "governanca", "acordo.yaml")
CATALOGO = os.path.join(RAIZ, "governanca", "catalogo.md")

CLASSES_PESSOAIS = ("pessoal", "pessoal sensível")
CONJUNTOS = ("clientes", "pedidos", "navegacao")

PADROES = {
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "telefone": re.compile(r"\(\d{2}\)\s*\d{4,5}-\d{4}"),
    "cpf": re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}"),
    "ip": re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
}


def carregar_acordo():
    with open(ACORDO, encoding="utf-8") as f:
        return yaml.safe_load(f)


def carregar_contrato(conjunto):
    with open(os.path.join(CONTRATOS, conjunto + ".yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def verificar_retencao(acordo=None):
    """Regra como codigo: conjunto pessoal sem retencao barra o pipeline."""
    acordo = acordo or carregar_acordo()
    for c in acordo["conjuntos"]:
        if c["classe"] in CLASSES_PESSOAIS and not str(c.get("retencao") or "").strip():
            raise ValueError(
                "PIPELINE BARRADO: o conjunto '%s' e de classe '%s' e nao tem retencao "
                "definida. Defina o prazo no acordo de governanca." % (c["nome"], c["classe"]))


def gerar_catalogo():
    """Gera governanca/catalogo.md a partir dos contratos e do acordo. Nada digitado duas vezes."""
    por_nome = {c["nome"]: c for c in carregar_acordo()["conjuntos"]}
    linhas = ["# Catalogo de dados", "",
              "Gerado por `governanca/governanca.py` a partir dos contratos e do acordo.", ""]
    for conjunto in CONJUNTOS:
        ct = carregar_contrato(conjunto)
        ac = por_nome[conjunto]
        linhas += ["## " + conjunto, "",
                   "- **Dono:** " + ac["dono"],
                   "- **Classe:** " + ac["classe"],
                   "- **Retencao:** " + str(ac["retencao"]),
                   "- **Frescor:** " + ct["frescor"],
                   "- **Acesso:** " + str(ac["acesso"]), "",
                   "| campo | tipo | classe |", "| --- | --- | --- |"]
        for campo in ct["campos"]:
            linhas.append("| %s | %s | %s |" % (campo["nome"], campo["tipo"], campo.get("classe", "-")))
        linhas.append("")
    with open(CATALOGO, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))
    return CATALOGO


def varrer():
    """Procura email, telefone, CPF e IP nas colunas da bronze, inclusive texto livre,
    ignorando os campos ja declarados pessoais no contrato."""
    chave_de = {"clientes": "id", "pedidos": "id", "navegacao": "evento_id"}
    achados = []
    for conjunto in CONJUNTOS:
        declarado = {c["nome"] for c in carregar_contrato(conjunto)["campos"]
                     if c.get("classe") in CLASSES_PESSOAIS}
        for linha in ler_csv(os.path.join(DIR["bronze"], conjunto + ".csv")):
            for campo, valor in linha.items():
                if campo.startswith("_") or campo in declarado or not valor:
                    continue
                for tipo, padrao in PADROES.items():
                    if padrao.search(valor):
                        achados.append({"conjunto": conjunto, "chave": linha[chave_de[conjunto]],
                                        "campo": campo, "tipo": tipo})
                        break
    return achados
