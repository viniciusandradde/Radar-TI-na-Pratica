# Infraestrutura base — VSA Radar

Este diretório contém somente a fundação de dados para staging/produção. Não publica portas de PostgreSQL ou Redis e não inicia ainda a API. A API e os workers serão adicionados após a confirmação do ambiente e a implementação do contrato de dados.

## Pré-requisitos

- Docker Engine e Docker Compose plugin atualizados.
- Host Linux suportado e firewall administrado.
- Volume persistente e backup externo configurados.
- Arquivo `.env` criado a partir de `.env.example`, com permissões `0600`.

## Inicialização

```bash
cp .env.example .env
# Edite POSTGRES_PASSWORD com segredo aleatório forte.
docker compose up -d
docker compose ps
```

## Segurança

- Não versionar o arquivo `.env`.
- PostgreSQL e Redis ficam apenas na rede interna `radar-internal`.
- Não mapear portas do banco/cache no host.
- O volume nomeado não é backup. Configure backup criptografado off-site e teste restore.
- Use usuário de aplicação com privilégios mínimos; não conectar API como superuser.

## Encerramento

```bash
docker compose down
```

Não usar `down -v` em ambiente com dados persistentes.
