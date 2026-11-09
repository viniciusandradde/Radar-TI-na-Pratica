# Implementação do VSA Radar

## O que foi implementado nesta branch

- Dashboard web responsivo em `site/`: visão geral, inbox, filtros, revisão/aprovação/descarte, editor, versões de texto para LinkedIn/Facebook/Instagram, calendário, briefing visual e gestão local de fontes.
- Modo local com armazenamento no navegador e exportação/importação JSON.
- Integração opcional com Supabase Auth + tabelas privadas, usando somente URL e anon/publishable key no navegador.
- Esquema SQL com Row Level Security.
- Coletor RSS/Atom Python: descoberta de feeds por link `rel=alternate`, fallback conservador para caminhos RSS comuns, normalização de URL, deduplicação e upsert.
- Workflow GitHub Actions para coleta diária e execução manual.
- Workflow de deploy GitHub Pages.

## Arquitetura

```
Fontes RSS/Atom
    │
    ▼
GitHub Actions (diário / manual)
    │  secrets do repositório
    ▼
collector/collect.py ──► Supabase news_items
                              │ RLS + Supabase Auth
                              ▼
                      site/ (GitHub Pages)
                       ├─ Radar / aprovação
                       ├─ Editor / rascunhos
                       ├─ versões por rede
                       └─ briefing visual Canva
```

O GitHub Pages serve apenas arquivos estáticos. O coletor roda no GitHub Actions; os dados privados ficam no Supabase. Nunca publicar service_role, tokens sociais ou segredos em `site/config.js`.

## Configuração inicial

1. Criar um projeto Supabase.
2. Executar `supabase/schema.sql` no SQL Editor.
3. Em Supabase Auth, criar o usuário editor (e habilitar o método de autenticação escolhido).
4. Copiar o UUID do usuário criado.
5. Em Settings → Secrets and variables → Actions do GitHub, adicionar:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY` (somente GitHub Actions; nunca no browser)
   - `VSA_OWNER_ID` (UUID do usuário editor)
6. Editar `site/config.js` com `SUPABASE_URL` e a chave anon/publishable pública. A proteção real dos dados é RLS + Auth.
7. Confirmar as permissões de Pages e o workflow de deploy.
8. Abrir Actions → VSA Radar RSS Collector → Run workflow para primeira coleta.
9. Abrir o Pages após o deploy e entrar no workspace.

## Limitações conhecidas do MVP

- O painel funciona em modo local sem Supabase, mas nesse modo os dados ficam apenas naquele navegador/dispositivo.
- A persistência Supabase está preparada para notícias e rascunhos; a gestão de fontes no painel ainda é local. A fonte oficial do coletor é `collector/sources.json`.
- O botão "Coletar agora" orienta a executar o workflow; o acionamento direto via API do GitHub ainda não foi ligado ao frontend para evitar expor um token GitHub.
- A geração de texto com IA ainda é assistida por prompts copiáveis; nenhum provedor LLM foi conectado e, portanto, não há consumo automático de créditos.
- O estúdio visual cria um briefing/prompt e abre o Canva. A exportação automática por API depende de permissões e plano Canva elegível.
- A publicação nas redes é manual nesta primeira entrega. O painel gera textos por canal e permite copiar; não guarda tokens nem publica sozinho.
- A interface foi implementada, mas a publicação Pages só pode ser validada depois de habilitar Pages nas configurações do repositório. Como o repositório está privado, confirme que o plano GitHub permite Pages em repositórios privados; o site publicado é público.
- Não armazene dados de clientes, hospitais, pacientes ou conteúdo confidencial no dashboard.

## Publicação GitHub Pages

O workflow `.github/workflows/pages.yml` publica o diretório `site/` quando alterações chegam à `main`. Para manter a branch atual em revisão, o deploy só ocorrerá após merge e ativação do Pages nas configurações. Se o plano não permitir Pages no repositório privado, use uma hospedagem estática apropriada ou um repositório público separado somente para o frontend.

## Próximas etapas

1. Configurar projeto Supabase e segredos.
2. Validar feeds descobertos e adicionar URLs RSS específicas quando necessário.
3. Ajustar UI para gravar/editar status de notícias no Supabase (o MVP lê notícias e salva rascunhos).
4. Criar templates visuais Canva e definir Brand Kit.
5. Só depois de aprovação e validação dos perfis, avaliar conectores oficiais de publicação social.
