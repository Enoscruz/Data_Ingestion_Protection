"""Missao 9 - Resiliencia: copia, reconstrucao e ensaio com cronometro."""
import os
import shutil
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
for _p in ("ingestao", "qualidade", "seguranca", "privacidade"):
    sys.path.insert(0, os.path.join(BASE, _p))

from comum import DIR, CAMPOS, ler_csv, escrever_csv, ler_json, salvar_json
import cdc
import validador
import seguranca
import privacidade
import esquecer

BACKUP_BRONZE = os.path.join(DIR["backup"], "bronze_dia1")


def fazer_copia(carimbo="2026-10-01T00:00:00"):
    """Copia da camada bronze no estado do dia 1, o offset do log e a chave."""
    for t in ("clientes", "pedidos", "navegacao"):
        linhas = [dict(l, _carregado_em=carimbo, _execucao="0")
                  for l in ler_csv(os.path.join(DIR["dia1"], t + ".csv"))]
        escrever_csv(os.path.join(BACKUP_BRONZE, t + ".csv"), CAMPOS[t] + CAMPOS["controle"], linhas)
    salvar_json(os.path.join(DIR["backup"], "offsets.json"), {"mudancas": 0})
    chave_dir = os.path.dirname(seguranca.ARQ_CHAVE)
    dest = os.path.join(chave_dir, "backup")   # a copia da chave fica fora do repositorio
    os.makedirs(dest, exist_ok=True)
    shutil.copy(seguranca.ARQ_CHAVE, dest)
    return BACKUP_BRONZE


def reconstruir(execucao="rebuild", carimbo="2026-10-04T01:00:00"):
    """Apaga a silver e a gold e as recria do zero a partir da bronze."""
    for camada in ("silver", "gold"):
        if os.path.exists(DIR[camada]):
            shutil.rmtree(DIR[camada])
    os.makedirs(DIR["silver"], exist_ok=True)
    os.makedirs(DIR["gold"], exist_ok=True)
    validador.validar(execucao)
    seguranca.construir_silver()
    privacidade.generalizar_nascimento()
    privacidade.visao_consumo()
    return True


def _restaurar():
    if os.path.exists(DIR["bronze"]):
        shutil.rmtree(DIR["bronze"])
    shutil.copytree(BACKUP_BRONZE, DIR["bronze"])


def ensaio():
    """Apaga a bronze, restaura a copia, reaplica o log e a eliminacao,
    carrega o lote do dia 3 e reconstroi. Cronometra o RTO."""
    inicio = time.perf_counter()
    _restaurar()
    cdc._set_offset("mudancas", 0)
    cdc.consumir_log("restore", "2026-10-04T01:00:00")
    for chave in {l["chave"] for l in ler_csv(esquecer.LISTA)}:
        esquecer.esquecer(chave)
    validador.carregar_lote_dia3("restore", "2026-10-04T01:00:00")
    reconstruir()
    return time.perf_counter() - inicio
