# Canva e padrões visuais do VSA Radar

## Fluxo inicial sem custo adicional de API

1. O editor define pauta, headline e formato.
2. O Estúdio Visual monta um prompt de briefing alinhado à identidade VSA.
3. O usuário copia o prompt e abre o Canva.
4. No Canva, cria ou duplica um template mestre, ajusta textos/elementos e exporta PNG/JPG.
5. O arquivo exportado é anexado à publicação no canal desejado.

## Direção de arte

- Paleta: azul-marinho `#0C1420`, azul tecnológico `#159DBB`, laranja `#F29B38`, branco gelo `#EDF3FA`.
- Tipografia: Manrope para títulos; DM Sans para textos.
- Linguagem: editorial tecnológico premium, minimalista, alto contraste, sem excesso de ícones.
- Assinatura: `VSA RADAR_` e `VSA TECNOLOGIA`.
- Evitar: clichês de robôs, imagens genéricas de banco sem relação com a pauta, logos de terceiros, títulos longos e texto miúdo.

## Formatos recomendados

| Uso | Dimensão de referência |
|---|---:|
| LinkedIn link/post horizontal | 1200 × 627 |
| Instagram feed quadrado | 1080 × 1080 |
| Instagram feed retrato / carrossel | 1080 × 1350 |
| Story / Reels | 1080 × 1920 |

## API Canva: avaliação

A Canva oferece APIs REST para designs, assets, exportações, Brand Templates e Autofill. O fluxo Autofill exige template/design preparado com campos de dados e OAuth. A documentação atual indica disponibilidade de Autofill quando a aplicação atua em nome de usuário Canva Pro, Teams ou Enterprise. Assim, não considerar essa automação uma integração gratuita garantida.

**Decisão:** usar integração manual pelo editor Canva agora; deixar a arquitetura preparada para OAuth/Autofill apenas se a conta e o custo forem aprovados. Não guardar access token ou client secret no frontend.

## Pré-requisito de identidade

A consulta ao Canva não encontrou Brand Kit da VSA disponível para a integração conectada. Antes de automatizar, criar um Brand Kit com logo oficial, paleta, fontes e pelo menos três Brand Templates: notícia única, carrossel de análise e alerta de segurança.
