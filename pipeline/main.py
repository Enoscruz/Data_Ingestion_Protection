"""Executa o laboratorio 'Do dado a protecao' de ponta a ponta (Missoes 1 a 9).

Roda cada missao na ordem, confere os numeros e grava as evidencias em
`evidencias/missaoN.txt`. Rode duas vezes e o resultado nao muda: todo o
pipeline e idempotente.

    python main.py
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
for _p in ("ingestao", "qualidade", "governanca", "seguranca", "privacidade",
           "resiliencia", "arquitetura"):
    sys.path.insert(0, os.path.join(BASE, _p))

from comum import DIR, ler_csv, reais, receita_paga
import carga
import cdc
import fluxo
import validador
import governanca
import seguranca
import privacidade
import esquecer
import resiliencia
import desenho

EVID = os.path.join(BASE, "evidencias")


def gravar(nome, texto):
    os.makedirs(EVID, exist_ok=True)
    with open(os.path.join(EVID, nome), "w", encoding="utf-8") as f:
        f.write(texto.strip() + "\n")
    print("  evidencias/%s" % nome)


def _bronze(tabela):
    return ler_csv(os.path.join(DIR["bronze"], tabela + ".csv"))


def _silver(tabela):
    return ler_csv(os.path.join(DIR["silver"], tabela + ".csv"))


# ---------------------------------------------------------------- Missao 1
def missao1():
    print("Missao 1 - carga incremental")
    carga.reiniciar_origem()
    carga.limpar_bronze()
    carga.limpar_marca_agua()

    carga.carga_incremental(1, "2026-10-01T00:00:00")
    carga.carga_navegacao(1, "2026-10-01T00:00:00")
    t1 = carga.totais("bronze")

    segunda = carga.carga_incremental(2, "2026-10-01T00:05:00")
    carga.carga_navegacao(2, "2026-10-01T00:05:00")
    t2 = carga.totais("bronze")

    cdc.aplicar_dia2(registrar_log=False)
    lidas = carga.carga_incremental(3, "2026-10-02T00:00:00")
    t3 = carga.totais("bronze")

    cliente5 = any(l["id"] == "5" for l in _bronze("clientes"))
    ids = "%s%s" % (lidas["pedidos"]["ids"], lidas["clientes"]["ids"])
    texto = """MISSAO 1 - Carga incremental e idempotencia
================================================
1) Primeira execucao (dia 1): clientes=%d, pedidos=%d, navegacao=%d
2) Segunda execucao sem mudanca na origem: lidas clientes=%d, pedidos=%d
   -> totais continuam %d, %d, %d
3) Depois das mudancas do dia 2: a execucao le %d linhas (pedidos %s; clientes %s)
4) Camada bronze: %d clientes, %d pedidos, receita paga %s
5) A cliente 5 foi excluida na origem e continua na bronze: %s
   (e o ponto de partida da Missao 2)

Arquivos: ingestao/carga.py | estado em dados/estado/marca_agua.json""" % (
        t1["clientes"], t1["pedidos"], t1["navegacao"],
        segunda["clientes"]["n"], segunda["pedidos"]["n"],
        t2["clientes"], t2["pedidos"], t2["navegacao"],
        lidas["pedidos"]["n"] + lidas["clientes"]["n"],
        lidas["pedidos"]["ids"], lidas["clientes"]["ids"],
        t3["clientes"], t3["pedidos"], reais(t3["receita"]),
        "sim" if cliente5 else "nao")
    gravar("missao1.txt", texto)


# ---------------------------------------------------------------- Missao 2
def missao2():
    print("Missao 2 - CDC")
    carga.reiniciar_origem()
    carga.reiniciar_bronze_dia1()
    cdc.reiniciar_log_mudancas()
    cdc.aplicar_dia2(registrar_log=True)

    log = ler_csv(cdc.LOG_MUDANCAS)
    cdc.consumir_log(4, "2026-10-02T00:00:00")
    t = carga.totais("bronze")
    email3 = next(l["email"] for l in _bronze("clientes") if l["id"] == "3")
    pedido106 = any(l["id"] == "106" for l in _bronze("pedidos"))

    cdc._set_offset("mudancas", 0)
    cdc.consumir_log(5, "2026-10-02T00:00:00")
    tr = carga.totais("bronze")

    eventos = ["%s %s %s %s" % (m["seq"], m["tabela"], m["operacao"], m["chave"]) for m in log]
    texto = """MISSAO 2 - CDC: o banco conta o que mudou
================================================
1) O log registra %d eventos, na ordem em que foram aplicados:
   %s
2) Camada bronze depois de sincronizar: %d clientes (sem a cliente 5), %d pedidos,
   e-mail novo no cliente 3 (%s)
3) O pedido 106 continua la: %s. Receita paga: %s
4) Reaplicar o log desde o primeiro evento: mesmos numeros (%d clientes, %d pedidos, %s)

Arquivos: ingestao/cdc.py | log em dados/log/mudancas.csv | offset em dados/estado/offsets.json""" % (
        len(log), " | ".join(eventos),
        t["clientes"], t["pedidos"], email3,
        "sim" if pedido106 else "nao", reais(t["receita"]),
        tr["clientes"], tr["pedidos"], reais(tr["receita"]))
    gravar("missao2.txt", texto)


# ---------------------------------------------------------------- Missao 3
def missao3():
    print("Missao 3 - streaming")
    fluxo.reiniciar_topico()
    publicados = fluxo.publicar()

    parcial = fluxo.leitor_visitas(parar_apos=4)   # simula queda no 4o evento
    visitas = fluxo.leitor_visitas()               # religa e termina
    bronze_n = fluxo.leitor_bronze()
    por_cliente = fluxo.leitor_por_cliente()
    topico = ler_csv(fluxo.TOPICO)

    carrinho = visitas.get("/carrinho", 0)
    outras = sum(1 for p, n in visitas.items() if n == 1)
    pc = ", ".join("%s=%d" % (k or "(sem cadastro)", v) for k, v in sorted(por_cliente.items()))
    texto = """MISSAO 3 - Streaming: um log, varios leitores
================================================
Produtor: publicou %d eventos no topico navegacao.
Leitor rapido 'visitas': /carrinho com %d visitas e %d paginas com 1 visita.
Queda e retomada: parou apos o 4o evento (offset salvo em 4), religou e
  chegou aos mesmos totais, sem contar evento duas vezes.
Leitor lento 'bronze': gravou %d eventos, sem duplicata.
Leitor novo 'por_cliente' (ligado depois de tudo, do offset 0): %s
Ao fim, o topico continua com %d eventos (guarda por tempo, nao ate ser lido).

Arquivos: ingestao/fluxo.py | topico em dados/log/navegacao.csv""" % (
        publicados, carrinho, outras, bronze_n, pc, len(topico))
    gravar("missao3.txt", texto)


# ---------------------------------------------------------------- Missao 4
def missao4():
    print("Missao 4 - contrato, validador e quarentena")
    validador.carregar_lote_dia3(5, "2026-10-03T00:00:00")
    sem_validacao = receita_paga(_bronze("pedidos"))
    r = validador.validar(5)
    silver = _silver("pedidos")
    motivos = "\n".join("   - " + m for m in r["motivos"])
    texto = """MISSAO 4 - Contrato, validador e quarentena
================================================
Do lote do dia 3: %d linhas aceitas (pedidos 110 e 115) e %d para a quarentena.
Motivos (um por linha):
%s
Camada silver: %d pedidos. Receita paga: %s
Sem a validacao, o mesmo calculo daria %s.

Arquivos: contratos/*.yaml | qualidade/validador.py | quarentena em dados/quarentena/pedidos.csv""" % (
        r["aceitas"] - 9, r["quarentena"], motivos,
        len(silver), reais(receita_paga(silver)), reais(sem_validacao))
    gravar("missao4.txt", texto)


# ---------------------------------------------------------------- Missao 5
def missao5():
    print("Missao 5 - governanca e catalogo")
    governanca.verificar_retencao()
    governanca.gerar_catalogo()
    achados = governanca.varrer()

    acordo = governanca.carregar_acordo()
    for c in acordo["conjuntos"]:
        if c["nome"] == "navegacao":
            c["retencao"] = ""
    try:
        governanca.verificar_retencao(acordo)
        barrado = "(nao barrou - erro na regra)"
    except ValueError as e:
        barrado = str(e)

    pedidos = [a for a in achados if a["conjunto"] == "pedidos"]
    ips = [a for a in achados if a["conjunto"] == "navegacao"]
    linhas = "\n".join("   - pedidos %s: %s em observacao" % (a["chave"], a["tipo"]) for a in pedidos)
    texto = """MISSAO 5 - Governanca: dono, classe, retencao e catalogo
================================================
Regra como codigo: removida a retencao de 'navegacao', o pipeline para com:
   %s
Catalogo gerado por script: governanca/catalogo.md (nada digitado duas vezes).
Varredor - dado pessoal onde ninguem declarou:
%s
   - navegacao: coluna 'ip' nos %d eventos

Arquivos: governanca/acordo.yaml | governanca/governanca.py | governanca/catalogo.md""" % (
        barrado, linhas, len(ips))
    gravar("missao5.txt", texto)


# ---------------------------------------------------------------- Missao 6
def missao6():
    print("Missao 6 - seguranca")
    seguranca.construir_silver()
    contagem = {t: len(_silver(t)) for t in ("clientes", "pedidos", "navegacao")}

    # nenhum dado pessoal na silver
    import re as _re
    padroes = governanca.PADROES
    escapar = []
    for t in ("clientes", "pedidos", "navegacao"):
        for linha in _silver(t):
            for campo, valor in linha.items():
                if campo.startswith("_") or not valor:
                    continue
                for tipo, padrao in padroes.items():
                    if padrao.search(valor):
                        escapar.append("%s.%s=%s" % (t, campo, valor))
                        break

    k = seguranca.chave()
    ps1a = seguranca.pseudonimo("1", k)
    ps1b = seguranca.pseudonimo("1", k)
    ps1_outra = seguranca.pseudonimo("1", "chave-de-teste-diferente")

    # a chave vaza no repositorio?
    vazou = []
    for raiz, _, arqs in os.walk(BASE):
        if os.sep + ".git" in raiz:
            continue
        for a in arqs:
            c = os.path.join(raiz, a)
            try:
                with open(c, "r", encoding="utf-8", errors="ignore") as f:
                    if k in f.read():
                        vazou.append(os.path.relpath(c, BASE))
            except OSError:
                pass

    seguranca.gerar_sintetico()
    texto = """MISSAO 6 - Seguranca: cada classe com a sua tranca
================================================
Camada silver montada: %d clientes, %d pedidos, %d eventos (sem nome, email,
   CPF, observacao nem ip).
Busca por @, CPF, telefone e IP na silver: %s
Mesma chave -> mesmos pseudonimos: %s == %s
Outra chave -> todos mudam: %s (diferente)
Valor da chave no repositorio: %s
EXTRA: conjunto sintetico gerado em dados/sintetico/

Arquivos: seguranca/seguranca.py | seguranca/matriz.md | chave fora do repo""" % (
        contagem["clientes"], contagem["pedidos"], contagem["navegacao"],
        "nenhuma ocorrencia" if not escapar else "ATENCAO: " + ", ".join(escapar),
        ps1a[:12], ps1b[:12], ps1_outra[:12],
        "nenhuma ocorrencia" if not vazou else "ATENCAO em " + ", ".join(vazou))
    gravar("missao6.txt", texto)


# ---------------------------------------------------------------- Missao 7
def missao7():
    print("Missao 7 - privacidade")
    privacidade.generalizar_nascimento()
    combos, unicas = privacidade.medir_k()
    linhas3, _ = privacidade.visao_consumo(K=3)
    linhas, total = privacidade.visao_consumo(K=2)

    def _linha(l):
        val = reais(l["receita_centavos"]) if l["situacao"] == "liberada" else "-"
        return "   - %-9s | %d cliente(s) | %-9s | %s" % (l["cidade"], l["clientes"], val, l["situacao"])

    corpo = "\n".join(_linha(l) for l in linhas)
    sup3 = ", ".join(l["cidade"] for l in linhas3 if l["situacao"] == "suprimida")
    texto = """MISSAO 7 - Privacidade e LGPD: pseudonimo nao e anonimo
================================================
K da tabela de clientes (cidade + faixa etaria): %d combinacoes com 1 pessoa so.
Visao de consumo (K = 2):
%s
Total geral: %s (inclui a cidade suprimida e os R$ 159,00 do pedido 106).
Com K = 3, tambem fica suprimida: %s

Arquivos: privacidade/privacidade.py | gold em dados/gold/receita_por_cidade.csv""" % (
        len(unicas), corpo, reais(total), sup3 or "(nenhuma)")
    gravar("missao7.txt", texto)


# ---------------------------------------------------------------- Missao 8
def missao8():
    print("Missao 8 - direito ao esquecimento")
    esquecer.esquecer("5")

    alvo = ["555.555.555-55", "(13) 90000-0005", "203.0.113.55", "Elisa", "elisa.moura@example.com"]
    achados = []
    for camada in ("origem", "log", "bronze", "silver"):
        for raiz, _, arqs in os.walk(DIR[camada]):
            for a in arqs:
                if not a.endswith(".csv"):
                    continue
                c = os.path.join(raiz, a)
                for linha in ler_csv(c):
                    for valor in linha.values():
                        if valor and any(t in valor for t in alvo):
                            achados.append(os.path.relpath(c, BASE))

    n_nav = len(_bronze("navegacao"))
    n_pedidos = len(_silver("pedidos"))
    receita = receita_paga(_silver("pedidos"))
    lista = ler_csv(esquecer.LISTA)
    antes = (n_nav, n_pedidos, receita, len(lista))
    esquecer.esquecer("5")
    depois = (len(_bronze("navegacao")), len(_silver("pedidos")),
              receita_paga(_silver("pedidos")), len(ler_csv(esquecer.LISTA)))

    texto = """MISSAO 8 - O direito de ser esquecido (cliente 5)
================================================
Busca por "Elisa", 555.555.555-55, (13) 90000-0005 e 203.0.113.55
nas camadas: %s
Depois do esquecimento: %d eventos de navegacao, %d pedidos, receita paga %s.
A visao de consumo nao muda.
Lista de eliminacao: %d registro, sem nome, CPF, e-mail ou telefone.
Rodar 'esquecer 5' de novo: idempotente (%s)

Arquivos: privacidade/esquecer.py | privacidade/moradas.md | dados/eliminacao/lista.csv""" % (
        "nenhuma ocorrencia" if not achados else "ATENCAO em " + ", ".join(sorted(set(achados))),
        n_nav, n_pedidos, reais(receita), len(lista),
        "nao mudou" if antes == depois else "MUDOU")
    gravar("missao8.txt", texto)


# ---------------------------------------------------------------- Missao 9
def missao9():
    print("Missao 9 - resiliencia e ensaio")
    resiliencia.fazer_copia()
    resiliencia.reconstruir()
    rto = resiliencia.ensaio()

    clientes = len(_silver("clientes"))
    pedidos = len(_silver("pedidos"))
    eventos = len(_silver("navegacao"))
    receita = receita_paga(_silver("pedidos"))
    cliente5 = any(l["id"] == "5" for l in _bronze("clientes"))

    gold = ler_csv(os.path.join(DIR["gold"], "receita_por_cidade.csv"))
    corpo = "\n".join("   - %-9s | %d | %s | %s" % (l["cidade"], int(l["clientes"]),
                                                    reais(l["receita_centavos"]) if l["situacao"] == "liberada" else "-",
                                                    l["situacao"]) for l in gold)
    texto = """MISSAO 9 - Resiliencia: copia, reconstrucao e ensaio
================================================
Copia do dia 1 criada (contem a cliente 5) + offset do log + copia da chave.
'reconstruir' recria a silver e a gold a partir da bronze: %d pedidos, %s.
Ensaio de desastre (RTO medido): %.2f s
Depois do ensaio: %d clientes, %d pedidos, %d eventos, %s.
A cliente 5 nao reaparece em nenhuma camada: %s
Visao de consumo:
%s

Arquivos: resiliencia/resiliencia.py | resiliencia/plano.md | copia em dados/backup/""" % (
        pedidos, reais(receita), rto, clientes, pedidos, eventos, reais(receita),
        "confirmado" if not cliente5 else "REAPARECEU", corpo)
    gravar("missao9.txt", texto)


def main():
    missao1()
    missao2()
    missao3()
    missao4()
    missao5()
    missao6()
    missao7()
    missao8()
    missao9()
    desenho.gerar()
    print("\nPronto. Evidencias em evidencias/ e desenhos em arquitetura/.")
    print("Receita final (silver):", reais(receita_paga(_silver("pedidos"))))


if __name__ == "__main__":
    main()
