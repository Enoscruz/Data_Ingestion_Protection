# Matriz classe × proteção

A proteção sobe com a classe: cada linha soma à anterior.

| Classe | Proteção exigida |
| --- | --- |
| público / interno | cifra em trânsito e em repouso: o piso universal |
| confidencial | + controle de acesso fino, máscara para papéis amplos, trilha de leitura |
| pessoal | + máscara por padrão, token ou pseudônimo no pipeline, retenção executada |
| pessoal sensível | + criptografia de coluna, acesso por exceção auditada, cofre de reversão |
| em todas | varredura do que escapou do mapa; teste sempre sintético ou mascarado |

## Papéis

- **pipeline**: lê a camada bronze (onde o dado pessoal é real) e escreve a silver.
- **analista**: lê só a camada silver (pseudonimizada) e a gold (agregada).
- Garantia: pastas separadas com permissão distinta — o usuário do pipeline tem acesso à
  bronze, o usuário do analista não.

## Trajeto do CPF no pipeline

| Etapa | CPF |
| --- | --- |
| origem · clientes | real |
| log de mudanças | real, com retenção curta (24 h) — decisão do grupo |
| camada bronze | real (cópia fiel da origem) |
| camada silver | ausente (só o pseudônimo `cliente_ps`) |
| camada gold / consumo | ausente (agregado) |
| cópia de segurança | real e cifrada em repouso até expirar |

O CPF real vive só na origem e na camada bronze; o log carrega a mudança real por 24 h.
