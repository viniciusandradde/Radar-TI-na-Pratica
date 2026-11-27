# VSA Radar — arquitetura técnica alvo (VPS)

**Status:** proposta aprovada para implementação incremental  
**Decisão:** VPS própria da VSA + evolução do sistema atual  
**Branch:** feat/vps-evolution-architecture

## 1. Objetivos e restrições

- Preservar o dashboard estático em `site/`, o fluxo editorial, o cadastro de fontes e o coletor RSS existentes.
- Eliminar dependência obrigatória do Supabase, sem remover o suporte atual antes da migração.
- Centralizar autenticação, persistência e integrações em serviços sob controle da VSA.
- Manter aprovação humana antes de qualquer publicação externa.
- Não migrar dados de produção sem backup, inventário e teste de restauração.
- Não armazenar segredos no frontend, Git ou logs.

## 2. Topologia lógica

```text
Equipe VSA / navegador
        |
     HTTPS :443
        |
 Reverse proxy (Traefik ou Nginx Proxy Manager já adotado pela VSA)
        |-----------------------------|
        |                             |
 radar.vsa...                    api.radar.vsa...
 Frontend atual                  FastAPI
 (site/)                         |
                                 |---- PostgreSQL (persistência)
                                 |---- Redis (cache/fila)
                                 |---- Worker (RSS, e-mail, tarefas)
                                 |
                                 |---- Resend / provedores IA / Canva
```

PostgreSQL e Redis não terão portas publicadas na internet. Somente o proxy publica 80/443. Os serviços internos ficam em rede Docker privada.

## 3. Componentes

| Componente | Responsabilidade | Tecnologia |
|---|---|---|
| Web | Interface editorial, radar, CRM, calendário e relatórios | Manter HTML/CSS/JS atual na primeira etapa; avaliar React/Vite somente se houver benefício comprovado |
| API | Contratos HTTP, autenticação, autorização, validação e auditoria | Python + FastAPI |
| Banco | Dados transacionais e histórico | PostgreSQL |
| Fila/cache | Agendamento, retentativas, cache e locks | Redis |
| Worker | RSS, normalização, deduplicação, e-mail e tarefas demoradas | Python; RQ ou Celery será escolhido na implementação |
| Proxy | TLS, roteamento e cabeçalhos de segurança | Proxy já operado pela VSA |
| Observabilidade | Logs estruturados, healthchecks e métricas | Docker logs inicialmente; integrar ao stack Zabbix/Grafana da VSA |

## 4. Domínios funcionais e módulos

1. **Identidade e acesso:** usuários, papéis (admin, editor, revisor), sessões, recuperação e trilha de auditoria.
2. **Radar:** fontes, execuções de coleta, itens, URL canônica, hash, datas e evidências.
3. **Editorial:** pautas, rascunhos, versões, revisão, aprovação, calendário e histórico.
4. **CRM:** leads, empresa, origem, finalidade, base legal registrada, consentimento quando aplicável, opt-out, supressão e histórico de contato.
5. **Distribuição:** conectores por canal, fila, agendamento, resultado e identificador externo. Nenhum autopublish sem aprovação explícita.
6. **Integrações:** Resend, IA e Canva por adaptadores isolados; credenciais somente no backend/worker.
7. **Administração:** configurações, permissões, saúde dos serviços, auditoria e exportação.

## 5. Modelo de dados inicial

Entidades propostas (nomes lógicos; migrations definirão os nomes físicos):

- `users`, `roles`, `user_roles`, `sessions`
- `sources`, `collector_runs`, `news_items`
- `editorial_items`, `draft_versions`, `editorial_reviews`
- `content_assets`, `content_channels`, `publication_jobs`, `publication_events`
- `leads`, `lead_consents`, `lead_suppressions`, `lead_activities`
- `integration_accounts` (metadados; segredos fora do banco ou criptografados), `audit_events`

Requisitos: UUIDs, timestamps UTC, índices para status/data/owner, constraints de unicidade para URL canônica e idempotency keys. Toda tabela de negócio terá política de autorização no serviço; não confiar em filtros enviados pelo browser.

## 6. Contratos da API

Prefixo versionado: `/api/v1`.

- `GET /health/live` e `GET /health/ready`
- `GET/POST /sources`
- `POST /collector/runs` e `GET /collector/runs/{id}`
- `GET/PATCH /news` e `GET /news/{id}`
- `GET/POST/PATCH /editorial-items`
- `POST /editorial-items/{id}/submit-review`, `/approve`, `/reject`
- `GET/POST/PATCH /leads`, `POST /leads/{id}/opt-out`
- `GET/POST /publication-jobs`
- `GET /audit-events` (restrito a administradores)

Paginação por cursor, filtros allowlisted, validação Pydantic, erros padronizados e OpenAPI gerado. Operações de escrita devem ser idempotentes quando houver retentativa de worker.

## 7. Segurança e LGPD

- HTTPS obrigatório; HSTS após validar domínio e TLS.
- Senhas com Argon2id; tokens curtos e refresh rotativo em cookies HttpOnly, Secure e SameSite.
- RBAC no backend; menor privilégio; MFA para administradores quando disponível.
- Rate limit em login, formulários públicos e endpoints sensíveis.
- CORS restrito aos domínios do Radar.
- Segredos por environment/secret store, nunca em `site/config.js`.
- PostgreSQL/Redis sem exposição pública; firewall permitindo apenas SSH administrativo e 80/443.
- Backups criptografados, off-site, retenção definida e teste periódico de restore.
- Leads: registrar origem, finalidade e base legal; consentimento não deve ser presumido. Respeitar opt-out e lista de supressão antes de qualquer campanha.
- Coletar somente dados necessários; definir retenção, canal de atendimento ao titular e processo de incidente.
- Não inserir dados pessoais/sensíveis de clientes, hospitais ou pacientes no Radar editorial.

## 8. Operação na VPS

- Docker Compose; volumes persistentes separados para PostgreSQL e uploads.
- Containers sem privilégios, filesystem read-only quando viável, limites de CPU/memória e healthchecks.
- Deploy por tag/commit imutável; migrations antes da troca de versão; rollback documentado.
- Backup diário + WAL/PITR conforme RPO/RTO aprovados.
- Monitorar disco, memória, CPU, certificados, containers, banco, fila, falhas de coleta e envio.
- Ambiente `staging` separado de `production`; credenciais e bancos distintos.

## 9. Decisões ainda condicionadas à infraestrutura

Antes do deploy: confirmar distro/versão, CPU/RAM/disco, domínio/subdomínios, proxy/TLS existente, política de backup off-site, monitoramento e capacidade de restauração. Não assumir que a VPS está pronta apenas por existir.

## 10. Critérios de aceite

- Site atual continua acessível e funcional durante a migração.
- Nenhum dado é descartado; totais e amostras são reconciliados.
- Login e permissões são testados com pelo menos dois papéis.
- Coleta é idempotente e não duplica URLs.
- CRM bloqueia contatos com opt-out/supressão.
- Publicação externa exige estado aprovado.
- Backup restaurado em ambiente isolado com evidência.
- Healthchecks, logs e alertas operacionais disponíveis.
