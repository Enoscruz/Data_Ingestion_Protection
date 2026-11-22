"""Utilitarios compartilhados: caminhos, CSV, JSON e formatacao."""
import csv
import json
import os

RAIZ = os.path.dirname(os.path.abspath(__file__))

# Momento de referencia da carga (Missao 4: regra "data no futuro").
AGORA = "2026-10-04T00:00:00"


def caminho(*partes):
    return os.path.join(RAIZ, *partes)


def ler_csv(c):
    if not os.path.exists(c):
        return []
    with open(c, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def escrever_csv(c, campos, linhas):
    os.makedirs(os.path.dirname(c), exist_ok=True)
    with open(c, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(linhas)


def anexar_csv(c, campos, linhas):
    if not linhas:
        return
    novo = not os.path.exists(c)
    os.makedirs(os.path.dirname(c), exist_ok=True)
    with open(c, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        if novo:
            w.writeheader()
        w.writerows(linhas)


def ler_json(c, padrao=None):
    if not os.path.exists(c):
        return {} if padrao is None else padrao
    with open(c, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_json(c, obj):
    os.makedirs(os.path.dirname(c), exist_ok=True)
    with open(c, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def reais(centavos):
    return "R$ " + ("%.2f" % (int(centavos) / 100)).replace(".", ",")


def receita_paga(linhas_pedido):
    return sum(int(p["valor_centavos"]) for p in linhas_pedido if p["status"] == "pago")


DIR = {
    "dia1": caminho("dados", "dia1"),
    "dia2": caminho("dados", "dia2"),
    "dia3": caminho("dados", "dia3"),
    "origem": caminho("dados", "origem"),
    "log": caminho("dados", "log"),
    "bronze": caminho("dados", "bronze"),
    "silver": caminho("dados", "silver"),
    "gold": caminho("dados", "gold"),
    "quarentena": caminho("dados", "quarentena"),
    "eliminacao": caminho("dados", "eliminacao"),
    "estado": caminho("dados", "estado"),
    "backup": caminho("dados", "backup"),
}

CAMPOS = {
    "clientes": ["id", "nome", "email", "cpf", "nascimento", "cidade", "atualizado_em"],
    "pedidos": ["id", "cliente_id", "valor_centavos", "status", "criado_em", "atualizado_em", "observacao"],
    "navegacao": ["evento_id", "cliente_id", "ip", "pagina", "quando"],
    "controle": ["_carregado_em", "_execucao"],
    "mudanca": ["seq", "tabela", "operacao", "chave", "dados"],
}
