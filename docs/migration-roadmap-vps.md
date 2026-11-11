# VSA Radar — plano de migração incremental para VPS

## Estratégia de corte

Migração por *strangler pattern*: a aplicação atual permanece como sistema operacional até que cada módulo novo seja validado. Não realizar big-bang migration. O frontend continua usando os serviços atuais até o adaptador equivalente da API estar testado.

## Fase 0 — inventário e proteção

- [ ] Congelar alterações estruturais na camada de dados.
- [ ] Inventariar telas, eventos, chaves LocalStorage, tabelas Supabase, Edge Functions, secrets, workflows e integrações.
- [ ] Exportar dados Supabase e workspace local; gerar checksums e registrar contagens.
- [ ] Criar ambiente staging isolado.
- [ ] Confirmar capacidade da VPS, DNS, proxy, TLS, firewall e backup off-site.
- **Gate:** inventário aprovado, backup restaurável e plano de rollback validado.

## Fase 1 — fundação de infraestrutura

- [ ] Provisionar rede Docker privada, PostgreSQL e Redis.
- [ ] Criar API FastAPI mínima com live/ready healthchecks e OpenAPI.
- [ ] Criar migrations versionadas e usuário de banco com privilégios mínimos.
- [ ] Configurar logs, limites de recursos, secrets e backups.
- [ ] Pipeline CI: lint, testes, build de imagem e scan de dependências.
- **Gate:** staging saudável, banco restaurado de backup e endpoints protegidos.

## Fase 2 — identidade, fontes e radar

- [ ] Implementar autenticação e RBAC.
- [ ] Migrar fontes e itens de notícias com import idempotente.
- [ ] Adaptar coletor RSS para publicar na API (mantendo o collector atual como fallback temporário).
- [ ] Validar deduplicação, timestamps e status.
- [ ] Executar reconciliação por contagem e amostragem.
- **Gate:** duas coletas consecutivas sem duplicidade e usuários com permissões corretas.

## Fase 3 — editorial

- [ ] Migrar rascunhos, versões, calendário e estados de aprovação.
- [ ] Criar trilha de auditoria de revisão/aprovação.
- [ ] Integrar frontend à API por um adapter; manter fallback de leitura enquanto durar a homologação.
- [ ] Validar criação, edição, revisão, aprovação, exportação e recuperação.
- **Gate:** editor e revisor completam o fluxo em staging sem perda de dados.

## Fase 4 — CRM e Resend

- [ ] Migrar leads com origem, finalidade, base legal e histórico disponíveis.
- [ ] Implementar opt-out, supressão e trilha de consentimento quando aplicável.
- [ ] Integrar Resend somente pelo backend/worker.
- [ ] Testar envio para endereço interno autorizado, webhooks e idempotência.
- [ ] Não importar leads sem proveniência ou enviar campanhas até validação jurídica/operacional.
- **Gate:** bloqueio de supressão validado; segredos não expostos; teste de envio aprovado.

## Fase 5 — distribuição e produção

- [ ] Implementar filas de publicação e conectores por canal.
- [ ] Exigir aprovação humana e registrar resultado de cada publicação.
- [ ] Fazer cutover DNS/proxy em janela controlada.
- [ ] Monitorar erros, latência, fila, entregabilidade e integridade por período acordado.
- [ ] Desativar serviços antigos somente após período de estabilidade e aceite.
- **Gate:** checklist de produção assinado e rollback disponível.

## Plano de rollback

1. Interromper workers e tarefas agendadas no novo ambiente.
2. Reverter DNS/roteamento para o frontend e backend anterior.
3. Preservar o banco novo em modo somente leitura para investigação.
4. Reprocessar apenas operações idempotentes; não reenviar campanhas/publicações automaticamente.
5. Reconciliar registros criados durante a janela de corte antes de nova tentativa.

## Critérios gerais de conclusão

- 100% dos registros elegíveis reconciliados ou com exceção documentada.
- Nenhuma credencial em código-fonte ou bundle frontend.
- Backup e restore testados.
- Fluxos de coleta, edição, aprovação, CRM e auditoria homologados.
- Nenhum autopublish sem aprovação humana.
- Documentação operacional e responsáveis definidos.
