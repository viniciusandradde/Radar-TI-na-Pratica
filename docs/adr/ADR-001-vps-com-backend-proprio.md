# ADR-001 — VPS e backend próprio para o VSA Radar

- **Status:** Aceito
- **Data:** 2026-11-11
- **Decisores:** VSA Tecnologia
- **Contexto:** o Radar atual é um frontend estático com persistência local, integração preparada para Supabase e coletor RSS em GitHub Actions. A evolução requer CRM compartilhado, identidade central, auditoria e execução de tarefas sem depender de serviços gerenciados.
- **Decisão:** hospedar os serviços de backend na VPS da VSA, usando FastAPI, PostgreSQL, Redis e workers em Docker Compose. Preservar a interface e os fluxos atuais e migrar módulo a módulo.
- **Alternativas consideradas:**
  1. Supabase como backend gerenciado — reduz operação, mas mantém dependência externa e não corresponde à decisão de hospedagem própria.
  2. VPS com backend próprio — escolhida; maior controle, exige responsabilidade por segurança, backup e atualização.
  3. Arquitetura híbrida — não escolhida como destino; pode ser usada transitoriamente para compatibilidade durante a migração.
- **Consequências positivas:** controle de dados e integrações, custos previsíveis, autonomia de evolução e possibilidade de integração com infraestrutura da VSA.
- **Consequências/risco:** equipe passa a operar banco, autenticação, patching, backup, restore, monitoramento e resposta a incidentes.
- **Mitigações:** Compose, redes privadas, least privilege, backup off-site testado, staging, healthchecks, logs e runbooks.
- **Reversibilidade:** alta enquanto a interface usar adaptadores de API e os dados forem exportáveis. A remoção do Supabase só ocorrerá após reconciliação e aceite formal.
