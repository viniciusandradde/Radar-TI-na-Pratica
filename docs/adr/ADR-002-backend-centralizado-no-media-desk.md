# ADR-002 — Backend centralizado no VSA Media Desk

- **Status:** Aceito
- **Data:** 2026-11-13
- **Decisores:** VSA Tecnologia (Vinicius Andrade)
- **Complementa / substitui em parte:** ADR-001 (branch `feat/vps-evolution-architecture`)

## Contexto

O ADR-001 previa um backend próprio do Radar (FastAPI, PostgreSQL, Redis, workers, editorial, aprovação, distribuição, RBAC e auditoria). O repositório `vsa-media-desk` foi criado com exatamente esse escopo para todo o ecossistema TI na Prática. Manter dois backends criaria duplicidade de regras editoriais, aprovações e publicação.

## Decisão

1. **O VSA Media Desk é o único backend de aplicação:** API, autenticação, RBAC, editorial, aprovações, distribuição, analytics e auditoria.
2. **O Radar mantém a responsabilidade de descoberta e captura de fontes:**
   - coletor RSS/Atom (`collector/`);
   - registro curado de fontes (`collector/sources.json`, `sources/external-sources.md`);
   - princípios editoriais de verificação.
3. **Persistência do Radar:** PostgreSQL próprio (`postgres/schema.sql`), banco `vsa_radar`, no lugar do Supabase. O Media Desk lê esse banco por um papel **somente leitura** (`md_radar_ro`). Esse é o contrato de integração.
4. **O que permanece no Supabase:** o dashboard estático (`site/`) e a Edge Function de e-mail seguem funcionando como legado até serem substituídos por telas e serviços do Media Desk. O CRM de leads não faz parte do escopo do Media Desk e só será migrado com decisão própria (LGPD).
5. **O que deixa de ser implementado no Radar:** os itens do ADR-001 que se sobrepõem ao Media Desk (API própria, RBAC, editorial, distribuição). A fundação de infraestrutura do ADR-001 (PostgreSQL e Redis em Docker com rede interna) fica atendida pelo compose do Media Desk.

## Consequências

- Uma única trilha de aprovação e auditoria para todo conteúdo.
- O Radar continua independente: pode coletar sem o Media Desk no ar, e o Media Desk tolera o Radar indisponível.
- Mudanças no schema `news_items` passam a ser **mudança de contrato**, com aviso e teste de contrato no Media Desk.

## Reversibilidade

Alta. O coletor ainda suporta o Supabase quando `RADAR_DATABASE_URL` não está definida.
