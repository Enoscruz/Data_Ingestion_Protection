# Inventário de moradas da titular (cliente 5)

Onde a cliente 5 ainda vive, a técnica escolhida e o porquê.

| Morada | O que há da titular | Técnica | Por quê |
| --- | --- | --- | --- |
| origem · clientes | cadastro completo (nome, email, cpf) | DELETE propagado | é a fonte; some na origem e o log transporta |
| origem · pedidos.observacao | telefone no pedido 106 | limpar o campo | texto livre esconde dado pessoal |
| origem · navegacao | 2 eventos dela | DELETE propagado | atividade ligada ao titular |
| log · tópico mudancas | evento de exclusão dela | marcador de exclusão (tombstone) + retenção curta | o log não se edita; vira evidência |
| log · tópico navegacao | 2 eventos dela | DELETE (eventos de atividade) | não há o que preservar |
| estado dos leitores do log | contagens por cliente | reposição das contagens | não guarda dado pessoal, só agregado |
| camada bronze | cadastro e eventos | DELETE + limpar observacao | cópia fiel que precisa acompanhar a origem |
| camada silver | pseudônimo `cliente_ps` | apagar a linha; `cliente_ps` vazio no pedido 106 | pseudônimo ainda é dado pessoal (LGPD art. 13, § 4º) |
| cópia de segurança | cópia do dia 1 contém a titular | deixar expirar e não restaurar o eliminado | o passado não pode ressuscitar |
| saídas e evidências do pipeline | nada além de números | lista de eliminação sem dado pessoal | prova o pedido sem expor a pessoa |

## Resultado

- 6 eventos de navegação, 11 pedidos, receita paga de R$ 844,90.
- O pedido 106 fica sem pessoa: `cliente_ps` vazio e observação limpa; o valor continua na receita.
- A lista de eliminação tem 1 registro, sem nome, CPF, e-mail ou telefone.
