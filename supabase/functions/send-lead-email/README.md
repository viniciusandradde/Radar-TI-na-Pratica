# Resend — envio individual revisado

Configure secrets na Supabase Edge Function:
- RESEND_API_KEY
- RESEND_FROM_EMAIL (ex.: VSA Radar <contato@seudominio.com>)

Deploy:
```bash
supabase functions deploy send-lead-email
supabase secrets set RESEND_API_KEY=re_xxx RESEND_FROM_EMAIL="VSA Tecnologia <contato@seudominio.com>"
```

O remetente precisa pertencer a um domínio verificado no Resend. A função exige usuário autenticado, lead pertencente ao usuário e consent_status igual a opted_in ou legitimate_interest_reviewed. Bloqueia opted_out e do_not_contact. O endpoint envia somente um e-mail por chamada e registra o retorno. Não há endpoint de disparo em massa.
