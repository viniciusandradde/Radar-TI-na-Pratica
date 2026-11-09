# Integração Resend

O projeto não possui conector direto para ler a configuração da conta Resend conectada no painel. A integração foi preparada via API oficial do Resend a partir de uma Supabase Edge Function.

## Segredos
Cadastre `RESEND_API_KEY` e `RESEND_FROM_EMAIL` nos secrets da Supabase Edge Function. Nunca insira API key no GitHub Pages, no JavaScript, no CSV ou no repositório.

## Preparação
1. Confirmar domínio verificado no Resend.
2. Escolher remetente no domínio validado.
3. Configurar os dois secrets no Supabase.
4. Fazer deploy de `supabase/functions/send-lead-email`.
5. Habilitar o botão de envio no painel somente depois de validar autenticação, consentimento e remetente.

## Política do MVP
O painel prepara mensagens individualizadas. Envio via Resend é individual, com confirmação humana. Leads com consentimento desconhecido não podem ser enviados pela Edge Function. Não existe envio em massa, nem sequência automática para leads frios. Para campanhas, usar somente contatos com opt-in ou base legal documentada e revisada, identificação clara da VSA e mecanismo simples de descadastro. Respeitar supressão global e pedidos de oposição.
