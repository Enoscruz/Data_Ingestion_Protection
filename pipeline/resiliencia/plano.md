# Plano de resiliência

RPO é quanto dado se aceita perder; RTO é quanto tempo se aceita ficar fora.

| Sistema | RPO | RTO | Cópias (onde · como · por quanto) | Responsável |
| --- | --- | --- | --- | --- |
| origem | 15 min | 1 h | dump a cada 15 min · 2 locais · 30 dias | time de plataforma |
| log de mudanças | 0 | 30 min | réplicas do broker · 2 locais · 7 dias | time de plataforma |
| camada bronze | 1 h | 2 h | cópia imutável (object storage com retenção) · fora do site · 90 dias | time de dados |
| camada silver | 0 (derivada) | 10 min | reconstruída a partir da bronze | time de dados |
| chave | 0 | 15 min | cofre gerenciado · 2 locais · 1 isolado · sob guarda criptográfica | time de privacidade |

## 3-2-1-1-0

- **3** cópias: bronze, cópia imutável e a origem.
- **2** locais: dois provedores/regiões distintos.
- **1** fora: a cópia imutável fica fora do site da origem.
- **1** imutável: object storage com *object lock* — não se apaga nem se altera no prazo.
- **0** erros no teste de restauração.

## Qual cópia é imutável, qual fica isolada

- **Imutável**: a cópia da camada bronze em object storage com retenção (*object lock*).
- **Isolada**: a cópia da chave, com credencial independente do pipeline — quem opera dados não
  tem acesso à chave, e vice-versa.

## Ordem de restauração

1. chaves → 2. dados (origem/bronze) → 3. catálogo → 4. pipelines → 5. validação.
Depois, reaplicar a **lista de eliminação**: o eliminado não volta.
