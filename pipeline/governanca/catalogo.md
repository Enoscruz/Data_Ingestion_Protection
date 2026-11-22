# Catalogo de dados

Gerado por `governanca/governanca.py` a partir dos contratos e do acordo.

## clientes

- **Dono:** time de cadastro
- **Classe:** pessoal sensível
- **Retencao:** 5 anos após o fim da relação (obrigação fiscal) e o cadastro enquanto durar a relação
- **Frescor:** até 24 horas depois da mudança na origem
- **Acesso:** analistas pedem, o time de privacidade aprova, toda leitura e auditada

| campo | tipo | classe |
| --- | --- | --- |
| id | inteiro | interno |
| nome | texto | pessoal |
| email | texto | pessoal |
| cpf | texto | pessoal sensível |
| nascimento | data | pessoal |
| cidade | texto | interno |
| atualizado_em | data_hora | interno |

## pedidos

- **Dono:** time de pedidos
- **Classe:** pessoal
- **Retencao:** 5 anos (obrigação fiscal)
- **Frescor:** até 24 horas depois da mudança na origem
- **Acesso:** analistas de receita pedem, o dono do dado aprova, leitura auditada

| campo | tipo | classe |
| --- | --- | --- |
| id | inteiro | interno |
| cliente_id | inteiro | interno |
| valor_centavos | inteiro | interno |
| status | texto | interno |
| criado_em | data_hora | interno |
| observacao | texto | interno |

## navegacao

- **Dono:** time de plataforma
- **Classe:** pessoal
- **Retencao:** 90 dias (volume alto, uso curto de analytics)
- **Frescor:** até 5 segundos depois do evento
- **Acesso:** time de produto pede, a plataforma aprova, leitura agregada auditada

| campo | tipo | classe |
| --- | --- | --- |
| evento_id | inteiro | interno |
| cliente_id | inteiro | interno |
| ip | texto | interno |
| pagina | texto | interno |
| quando | data_hora | interno |
