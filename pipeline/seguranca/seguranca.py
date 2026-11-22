"""Missao 6 - Seguranca: cada classe com a sua tranca.

Pseudonimo HMAC-SHA-256 do id do cliente (chave fora do repositorio) e a
camada silver sem nome, email, cpf, observacao nem ip.
"""
import hashlib
import hmac
import os
import secrets
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from comum import DIR, ler_csv, escrever_csv

CHAVE_DIR = os.path.join(os.path.expanduser("~"), ".lab-di")
ARQ_CHAVE = os.path.join(CHAVE_DIR, "chave_pseudonimo")

CAMPOS_CLIENTES = ["cliente_ps", "nascimento", "cidade"]
CAMPOS_PEDIDOS = ["id", "cliente_ps", "valor_centavos", "status", "criado_em"]
CAMPOS_NAVEGACAO = ["evento_id", "cliente_ps", "pagina", "quando"]


def chave():
    """Le a chave da variavel de ambiente ou de um arquivo fora do repositorio."""
    v = os.environ.get("CHAVE_PSEUDONIMO")
    if v:
        return v
    if os.path.exists(ARQ_CHAVE):
        with open(ARQ_CHAVE, encoding="utf-8") as f:
            return f.read().strip()
    v = secrets.token_hex(32)
    os.makedirs(CHAVE_DIR, exist_ok=True)
    with open(ARQ_CHAVE, "w", encoding="utf-8") as f:
        f.write(v)
    return v


def pseudonimo(id_cliente, chave_usada=None):
    if id_cliente in (None, ""):
        return ""
    k = (chave_usada or chave()).encode("utf-8")
    return hmac.new(k, str(id_cliente).encode("utf-8"), hashlib.sha256).hexdigest()[:32]


def construir_silver(chave_usada=None):
    """Monta clientes, pedidos e navegacao da camada silver, pseudonimizados."""
    k = chave_usada or chave()
    clientes = [{"cliente_ps": pseudonimo(l["id"], k), "nascimento": l["nascimento"],
                 "cidade": l["cidade"]} for l in ler_csv(os.path.join(DIR["bronze"], "clientes.csv"))]
    escrever_csv(os.path.join(DIR["silver"], "clientes.csv"), CAMPOS_CLIENTES, clientes)

    pedidos = []
    validos = {l["id"] for l in ler_csv(os.path.join(DIR["bronze"], "clientes.csv"))}
    for l in ler_csv(os.path.join(DIR["silver"], "pedidos.csv")):
        if l.get("cliente_ps"):
            ps = l["cliente_ps"]
        else:
            cid = l.get("cliente_id", "")
            ps = pseudonimo(cid, k) if cid in validos else ""   # cliente eliminado: pedido fica orfao
        pedidos.append({"id": l["id"], "cliente_ps": ps, "valor_centavos": l["valor_centavos"],
                        "status": l["status"], "criado_em": l["criado_em"]})
    escrever_csv(os.path.join(DIR["silver"], "pedidos.csv"), CAMPOS_PEDIDOS, pedidos)

    navegacao = [{"evento_id": l["evento_id"], "cliente_ps": pseudonimo(l["cliente_id"], k),
                  "pagina": l["pagina"], "quando": l["quando"]}
                 for l in ler_csv(os.path.join(DIR["bronze"], "navegacao.csv"))]
    escrever_csv(os.path.join(DIR["silver"], "navegacao.csv"), CAMPOS_NAVEGACAO, navegacao)

    return {"clientes": len(clientes), "pedidos": len(pedidos), "navegacao": len(navegacao)}


def gerar_sintetico(destino=None):
    """EXTRA: conjunto sintetico com a mesma forma e nenhuma pessoa real."""
    destino = destino or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                      "dados", "sintetico")
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dados", "dia1")
    mapa = {}
    clientes, pedidos = [], []
    for i, l in enumerate(ler_csv(os.path.join(base, "clientes.csv")), start=1):
        novo_id = 900 + i
        mapa[l["id"]] = str(novo_id)
        clientes.append({"id": str(novo_id), "nome": "Pessoa Sintetica %d" % i,
                         "email": "pessoa%d@exemplo.invalido" % i,
                         "cpf": "%03d.%03d.%03d-%02d" % (i, i, i, i),
                         "nascimento": l["nascimento"], "cidade": l["cidade"],
                         "atualizado_em": l["atualizado_em"]})
    for l in ler_csv(os.path.join(base, "pedidos.csv")):
        pedidos.append(dict(l, id=str(2000 + int(l["id"])), cliente_id=mapa.get(l["cliente_id"], "")))
    escrever_csv(os.path.join(destino, "clientes.csv"),
                 ["id", "nome", "email", "cpf", "nascimento", "cidade", "atualizado_em"], clientes)
    escrever_csv(os.path.join(destino, "pedidos.csv"),
                 ["id", "cliente_id", "valor_centavos", "status", "criado_em", "atualizado_em", "observacao"],
                 pedidos)
    navegacao = [dict(l, cliente_id=mapa.get(l["cliente_id"], ""))
                 for l in ler_csv(os.path.join(base, "navegacao.csv"))]
    escrever_csv(os.path.join(destino, "navegacao.csv"),
                 ["evento_id", "cliente_id", "ip", "pagina", "quando"], navegacao)
    return destino
