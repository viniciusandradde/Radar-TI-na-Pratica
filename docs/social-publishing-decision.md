# Publicação social: decisão técnica e financeira

## Recomendação VSA: começar com copiar e colar

Na primeira fase, o Radar prepara três versões independentes do texto e deixa o usuário copiar e publicar manualmente. Essa abordagem é mais simples, tem custo incremental próximo de zero e evita que uma integração com permissões pendentes bloqueie o calendário editorial.

| Canal | Automação oficial possível? | Requisitos / limitações | Decisão inicial |
|---|---|---|---|
| LinkedIn | Sim, especialmente para páginas de organização via Posts / Community Management APIs | Aplicativo, OAuth, permissões, aprovação e níveis Development/Standard. Acesso de produção não deve ser presumido. | Manual |
| Facebook | Sim, para Páginas administradas | Meta App, Page Access Token, permissões como pages_manage_posts, revisão de permissões quando exigida. Não publicar em perfis pessoais por API. | Manual |
| Instagram | Sim, para contas profissionais compatíveis | Conta Business/Creator, ligação a uma Página, app Meta, token e permissões de publicação; limitações por formato. | Manual |

## Custos

- **API das plataformas:** não assumir tarifa por publicação. O custo direto pode ser zero para uso elegível, mas aprovação, operação, manutenção, hospedagem e suporte têm custo de engenharia. Confirmar termos e limites vigentes antes de ativar.
- **Agendadores de terceiros:** frequentemente cobram por canal, usuário ou volume; não contratar na fase inicial.
- **Infraestrutura:** GitHub Actions tem limites incluídos conforme plano; Supabase tem plano gratuito com limites e condições próprias. Monitorar uso.
- **Risco operacional:** tokens expiram/revogam, permissões mudam e APIs versionam/depreciam. Uma falha pode deixar publicação pendente.

## LinkedIn

A documentação oficial descreve a Posts API e o programa Community Management. O programa tem Development e Standard tiers; Standard requer solicitação e demonstração de casos de uso. Portanto, mesmo que a API suporte publicar em páginas, não há garantia de aprovação imediata para produção. Não implementar automação por scraping, extensão de navegador ou robô que simule cliques.

## Meta: Facebook e Instagram

A API de Instagram é direcionada a contas profissionais; a conta precisa estar conectada ao ecossistema de Página/Meta e conceder permissões. Facebook Pages API exige permissões de gerenciamento de Página e token de Página. Implementar apenas após confirmar se a VSA possui Página, conta Instagram profissional e acesso de administrador.

## Gate de aprovação para automação

Antes de ativar qualquer botão "Publicar":
1. confirmar propriedade/administração dos perfis;
2. criar app oficial do fornecedor;
3. solicitar permissões mínimas;
4. concluir App Review / aprovação necessária;
5. guardar tokens criptografados no backend, nunca no GitHub Pages;
6. implementar prévia, confirmação explícita, log de retorno e prevenção de postagem duplicada;
7. testar em ambiente controlado;
8. manter publicação manual como fallback.

## Conclusão

Para a VSA, o retorno maior neste momento está em produzir com consistência e qualidade. Recomendo operar manualmente por 30–60 dias, medir frequência, engajamento e conversão, e só então investir na automação dos canais que realmente gerarem volume suficiente para justificar manutenção.
