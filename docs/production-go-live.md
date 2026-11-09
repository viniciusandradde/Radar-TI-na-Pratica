# VSA Radar — checklist de entrada em produção

Este documento diferencia o que está versionado do que exige configuração nos painéis externos. Não colocar segredos em commits, Issues, prints ou no frontend.

## Estado verificado em 09/11/2026

- [x] PR #1 integrado à `main`.
- [x] Identidade visual derivada aplicada no dashboard.
- [x] Lockup secundário SVG criado em `site/assets/brand/vsa-radar-lockup.svg`.
- [x] Coletor RSS/Atom e workflow diário versionados.
- [x] Pré-validação estática e `node --check` incluídos no workflow Pages.
- [ ] GitHub Pages ainda não habilitado/configurado. A primeira execução falhou na etapa `actions/configure-pages@v5`, antes de gerar o artefato.
- [ ] Supabase URL e chave pública ainda não configuradas em `site/config.js`.
- [ ] Segredos de Actions e Supabase ainda precisam ser cadastrados pelo proprietário.
- [ ] Função Edge Resend ainda precisa ser implantada e testada.
- [ ] Arquivo JPEG mestre da logomarca ainda não foi copiado para `site/assets/brand`; o lockup SVG é uma assinatura de produto e não substitui a logomarca oficial.

## 1. GitHub Pages

1. Abra o repositório no GitHub.
2. Entre em **Settings → Pages**.
3. Em **Build and deployment → Source**, selecione **GitHub Actions**.
4. Salve.
5. Confira em **Settings → Environments** se o ambiente `github-pages` foi criado pelo workflow.
6. Execute novamente **Actions → Deploy VSA Radar dashboard → Run workflow**.
7. Confirme que as etapas Configure Pages, Upload Pages artifact e Deploy to GitHub Pages concluíram com sucesso.

**Atenção à visibilidade:** o repositório está privado. A disponibilidade de GitHub Pages para repositórios privados depende do plano GitHub. Mesmo quando o repositório é privado, o site publicado pode ser acessível publicamente. Não publique dados de leads, clientes, hospitais ou informações internas no frontend estático.

Se o plano não permitir Pages no repositório privado, mantenha o código privado e publique somente o diretório `site/` em uma hospedagem estática compatível, por exemplo Cloudflare Pages, após configurar a conta e o domínio.

## 2. Supabase

1. Crie/seleciona um projeto Supabase dedicado ao VSA Radar.
2. No SQL Editor, execute `supabase/schema.sql` integralmente.
3. Em Authentication, crie o usuário editor.
4. Copie o UUID do usuário editor; esse valor é o `VSA_OWNER_ID`.
5. Em Project Settings → API, copie Project URL e a chave publishable/anon. Somente esses dois valores públicos entram no frontend.
6. Atualize `site/config.js`:
   - `SUPABASE_URL`: Project URL.
   - `SUPABASE_ANON_KEY`: publishable/anon key.
7. Faça commit da configuração pública. Nunca colocar `service_role` no `site/config.js`.

### GitHub Actions secrets

Em **Settings → Secrets and variables → Actions → New repository secret**, cadastrar:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY` — somente para o coletor RSS no Actions.
- `VSA_OWNER_ID` — UUID do usuário editor.

O coletor diário está programado para 10:15 no horário de Campo Grande (UTC−4). Execute-o manualmente uma vez após cadastrar os três secrets e confira os logs do workflow.

## 3. Supabase Edge Function + Resend

Instale/atualize o Supabase CLI, autentique-se e vincule o projeto correto. No terminal, dentro do repositório:

```bash
supabase login
supabase link --project-ref SEU_PROJECT_REF
supabase secrets set RESEND_API_KEY=SEU_TOKEN_RESEND
supabase secrets set RESEND_FROM_EMAIL="VSA Radar <radar@SEU_DOMINIO_VERIFICADO>"
supabase functions deploy send-lead-email
```

Ajuste o remetente para um endereço de domínio verificado no Resend. Não enviar a chave em chat, issue ou commit. A função exige usuário autenticado e bloqueia leads sem base legal revisada, com opt-out ou em não contatar.

Antes do primeiro envio:
- validar SPF, DKIM e domínio no Resend;
- testar com um endereço interno autorizado;
- conferir registro em `lead_email_log`;
- testar opt-out e bloqueio de lead sem base legal;
- disponibilizar mecanismo de descadastro e política de privacidade;
- não importar listas sem origem, finalidade e base legal documentadas.

O status “quente” não representa consentimento nem autorização de envio. A decisão de legítimo interesse exige avaliação documentada e compatibilidade com a LGPD.

## 4. Marca

- `site/assets/brand/vsa-radar-lockup.svg`: assinatura secundária VSA Radar.
- A logomarca original VSA deve ser usada sem distorção ou recoloração. A imagem de referência recebida no chat ainda precisa ser adicionada como arquivo mestre em formato adequado.
- Conferir a aplicação da marca em desktop e celular antes de divulgar.

## 5. Testes de aceite

- [ ] Site abre por HTTPS e layout responsivo funciona.
- [ ] Login Supabase funciona e logout encerra a sessão.
- [ ] Usuário não acessa dados de outro owner (teste RLS com duas contas).
- [ ] Coletor executa e faz upsert idempotente.
- [ ] Notícias exibem fonte, link e data.
- [ ] CSV importa com validação e deduplicação.
- [ ] Leads opt-out/não contatar são bloqueados.
- [ ] E-mail de teste chega e é registrado na auditoria.
- [ ] Não há chaves secretas em arquivos servidos pelo browser.
- [ ] Não existem dados reais de pacientes ou informações hospitalares confidenciais no sistema.

## Limitações operacionais atuais

O dashboard é uma aplicação estática com backend Supabase opcional. A integração social e a geração de imagens via Canva não estão automatizadas. Publicações continuam exigindo aprovação humana. O modo local armazena dados no navegador e não deve ser tratado como banco compartilhado ou backup.
