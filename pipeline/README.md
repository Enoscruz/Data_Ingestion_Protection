# Do dado à proteção — pipeline

Laboratório da FIAP: o ciclo de vida de um dado pessoal, do `INSERT` na origem
até um destino governado, protegido e restaurável. Cada missão deixa uma peça
pronta; este repositório é um projeto só, que cresce.

## Integrantes

- Enos de Barros Cruz — RM 561926

## Escolhas

- **Linguagem:** Python 3.12.
- **Trilha:** A, sem infraestrutura. A origem, a camada bronze e a silver são
  arquivos CSV; o log de mudanças e o tópico de navegação são arquivos que só
  se anexam; o estado (marca-d'água e offsets) vive em `dados/estado/`; os
  contratos e o acordo de governança são YAML. Não há banco nem broker: o
  grupo não tinha como provisionar infraestrutura, e o laboratório existe para
  mostrar os conceitos, não o produto.
- **Dependências:** `PyYAML` (leitura dos contratos). O resto é biblioteca padrão.

## Como rodar do zero

```bash
cd pipeline
pip install pyyaml
python main.py
```

`python main.py` executa as Missões 1 a 9 na ordem, do zero (reinicia origem,
bronze, log e tópico), grava as evidências em `evidencias/missao1.txt` …
`missao9.txt` e gera os desenhos em `arquitetura/`. Rodar de novo dá o mesmo
resultado: o pipeline é idempotente.

A chave do pseudônimo é lida de `CHAVE_PSEUDONIMO` ou criada em
`~/.lab-di/chave_pseudonimo` — **fora do repositório**.

## Estrutura

```
pipeline/
├── dados/          dia 1, mudanças do dia 2, lote do dia 3, sintético, origem, log, camadas
├── contratos/      pedidos.yaml, clientes.yaml, navegacao.yaml
├── ingestao/       carga incremental, CDC, produtor e leitores
├── qualidade/      validação e quarentena
├── governanca/     acordo.yaml, catálogo gerado, regra como código
├── seguranca/      matriz.md, pseudonimização, camada silver
├── privacidade/    visão de consumo, moradas.md, esquecer
├── resiliencia/    plano.md, cópia de segurança, reconstruir
├── arquitetura/    estrutura.svg e vida-do-dado.svg
├── evidencias/     números de cada missão
├── main.py         executa as 9 missões
└── README.md
```

## Decisões do grupo

- **Trilha de captura (Missão 2):** Trilha A. O próprio programa que altera a
  origem registra cada mudança em `dados/log/mudancas.csv` (só anexa), com
  sequência, tabela, operação, chave e dados. Sem broker e sem leitura do log
  do banco, o conceito de CDC fica visível e o resultado é reprodutível.
- **Offset (Missão 3):** cada leitor grava o offset **depois** de processar.
  Assim vale "pelo menos uma vez": ao voltar de uma queda o leitor pode repetir
  um evento, e quem repete sem estragar é o processamento idempotente (a chave
  do evento evita a duplicata). Preferimos repetir a perder.
- **Dono mais difícil (Missão 5):** `navegacao`. O dado de atividade é
  produzido por vários times e em volume alto, e ninguém o "possui" por
  natureza. Escolhemos o **time de plataforma** como dono porque é quem opera o
  tópico e responde pela entrega; os times de produto são consumidores, não
  donos.
- **Dois papéis (Missão 6):** o pipeline lê a camada bronze (onde o dado pessoal
  é real) e o analista lê só a silver (pseudonimizada) e a gold (agregada).
  Garantimos isso com **pastas e usuários separados**: o usuário do pipeline tem
  permissão na bronze, o usuário do analista não. O dado real nunca cruza para
  a pasta que o analista enxerga.

## As peças da entrega

Cada semana fechou uma entrega; cada missão deixou uma peça, e um número a
comprova. Peça sem evidência não conta.

| Missão | Peça | Onde | Número que comprova |
| --- | --- | --- | --- |
| 1 · Carga | Carga incremental idempotente | `ingestao/carga.py` | Lê 4 linhas no dia 2; bronze com 7 clientes, 9 pedidos, R$ 750,90 |
| 2 · CDC | Log de mudanças e offset | `ingestao/cdc.py` | 5 eventos; 6 clientes, 9 pedidos, R$ 750,90 |
| 3 · Fluxo | Tópico de navegação e leitores | `ingestao/fluxo.py` | `/carrinho` com 2 visitas; 8 eventos |
| 4 · Contrato | Contrato, validador e quarentena | `contratos/*.yaml`, `qualidade/validador.py` | 2 aceitas, 5 na quarentena; silver com 11 pedidos, R$ 844,90 |
| 5 · Governança | Acordo, catálogo e varredor | `governanca/` | 2 pedidos e 8 IPs achados onde ninguém declarou |
| 6 · Segurança | Matriz, pseudônimo e camada silver | `seguranca/` | Silver sem nenhum `@`, CPF, telefone ou IP |
| 7 · Privacidade | Visão de consumo com K-anonimato | `privacidade/privacidade.py` | K = 2; Santos R$ 545,00, Sorocaba R$ 95,90, Campinas suprimida |
| 8 · Esquecer | Comando `esquecer` e lista de eliminação | `privacidade/esquecer.py` | 6 eventos, 11 pedidos, R$ 844,90; lista com 1 registro |
| 9 · Resiliência | `reconstruir`, cópia e ensaio | `resiliencia/resiliencia.py` | Mesmos números da Missão 8 após o desastre |

Desenho da arquitetura: `arquitetura/estrutura.svg` (estrutura) e
`arquitetura/vida-do-dado.svg` (a vida de um dado pessoal, do cadastro à
eliminação).

## Números de referência

- Receita paga da origem no dia 1: **R$ 655,00**.
- Depois do dia 2 e do CDC: **R$ 750,90**.
- Depois do contrato e da quarentena: **R$ 844,90** (sem validação, R$ 932,90).
- Depois do esquecimento da cliente 5: continua **R$ 844,90**.
- Depois do ensaio de restauração: continua **R$ 844,90**.
