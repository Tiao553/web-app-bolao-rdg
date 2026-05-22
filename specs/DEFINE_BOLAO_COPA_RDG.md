# DEFINE: Bolao Copa RDG

> Aplicação web de bolão da Copa com autenticação, aprovação administrativa, frontend novo guiado por `mock/*`, contratos backend→frontend explícitos, ranking, Explore controlado por data, seed oficial do torneio 2026 e sincronização pós-jogo com override manual seguro.

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | BOLAO_COPA_RDG |
| **Date** | 2026-05-21 |
| **Author** | define-agent |
| **Status** | Built |
| **Clarity Score** | 15/15 |

---

## Problem Statement

O projeto Bolao da Copa precisa transformar um product overview amplo em um MVP executável e governável, garantindo que apenas usuários aprovados participem, que a pontuação siga regras determinísticas e que dados oficiais da Copa 2026 sejam carregados de uma base local canônica e sincronizados por uma fonte automatizada viável, com correção manual sem corromper ranking, Explore, classificação de grupos ou chaveamento mata-mata. Além disso, o backend precisa expor contratos claros para o novo frontend, e o frontend deve seguir como referência obrigatória todos os mocks em `mock/*` e `mock/admin/*`.

---

## Target Users

| User | Role | Pain Point |
|------|------|------------|
| Participante aprovado | Usuário comum do bolão | Precisa registrar palpites e acompanhar pontuação, ranking e Explore sem acesso prematuro aos palpites dos outros. |
| Participante pendente | Usuário aguardando aprovação | Precisa entender claramente que pode autenticar, mas ainda não pode participar do bolão. |
| Administrador | Operador do bolão | Precisa aprovar usuários, corrigir dados oficiais, controlar janelas de palpites/Explore e recalcular resultados sem inconsistências. |
| Dono do projeto | Builder/maintainer | Precisa de requisitos fechados para seguir para design sem retrabalho estrutural entre frontend, backend, integração e QA. |

---

## Goals

What success looks like (prioritized):

| Priority | Goal |
|----------|------|
| **MUST** | Permitir cadastro aberto com autenticação e fazer todo novo usuário iniciar com `accessStatus = PENDING`. |
| **MUST** | Garantir que apenas usuários `APPROVED` possam registrar palpites, aparecer no ranking, pontuar e acessar Explore. |
| **MUST** | Permitir que usuários aprovados registrem palpites de campeão, artilheiro e placares por partida até o horário de fechamento configurado. |
| **MUST** | Fazer o backend expor contratos HTTP/JSON estáveis e orientados às telas do novo frontend para login, criação de conta, dashboard, palpites iniciais, palpites por fase, resultados, ranking, chaveamento, Explore e console admin. |
| **MUST** | Calcular pontuação de forma determinística: 3 pontos para placar exato, 1 para resultado correto, multiplicador 2 em jogos do Brasil, 10 pontos para campeão e 15 para artilheiro. |
| **MUST** | Implementar painel administrativo para aprovar/rejeitar/bloquear usuários, configurar janelas do bolão, importar dados externos e aplicar correções manuais com precedência sobre sincronização automática. |
| **MUST** | Implementar o frontend novo aderente aos fluxos, navegação, hierarquia visual e estados exibidos nos mocks em `mock/*` e `mock/admin/*`, tratando esses artefatos como baseline canônica de UX do MVP. |
| **MUST** | Recalcular automaticamente pontuação, ranking e artilheiro oficial quando resultados, gols ou assistências forem importados ou corrigidos. |
| **MUST** | Carregar os seeds oficiais do torneio a partir de `data/teams-groups.json`, `data/group-stage-matches.json` e `data/bracket-knockout.json`, preservando 48 seleções, 12 grupos, 72 jogos de fase de grupos e 32 jogos de mata-mata. |
| **MUST** | Adotar API-Football via RapidAPI como fonte automática recomendada para fixtures, resultados, eventos e artilharia, com Google Sheets API como fallback operacional e painel admin como fallback final. |
| **MUST** | Calcular na aplicação a classificação final de grupos, o ranking dos 12 terceiros colocados, a seleção dos 8 melhores terceiros, a alocação dos slots TBD do Round of 32 e a propagação dos vencedores no bracket. |
| **SHOULD** | Exibir área Explore somente após `exploreReleaseAt` e somente para usuários aprovados. |
| **SHOULD** | Exibir ranking geral com desempates transparentes e excluir totalmente usuários não aprovados de ranking, estatísticas e desempates. |
| **SHOULD** | Manter logs básicos de sincronização para auditoria operacional do MVP, incluindo skips por override manual e partidas ainda não finalizadas. |
| **SHOULD** | Executar sincronização pós-jogo em agenda compatível com o plano gratuito da RapidAPI, usando o critério `startsAt + ~115 min` e processando apenas status `FT`, `AET` ou `PEN`. |
| **COULD** | Permitir ativar Google Sheets como camada de fallback já no MVP, sem depender dela para a operação normal. |

---

## Success Criteria

Measurable outcomes (must include numbers):

- [ ] 100% dos novos cadastros entram com `accessStatus = PENDING`.
- [ ] 100% dos usuários com status diferente de `APPROVED` ficam impedidos de registrar palpites, acessar Explore, aparecer no ranking e influenciar estatísticas.
- [ ] 100% dos palpites de campeão, artilheiro e partidas ficam bloqueados quando `dataHoraAtual >= predictionCloseAt`.
- [ ] 100% dos acessos ao Explore por usuários aprovados seguem a regra `dataHoraAtual >= exploreReleaseAt`; antes disso, o sistema mostra apenas os próprios palpites.
- [ ] 100% das telas representadas em `mock/*.html` e `mock/admin/*.html` possuem rota ou composição equivalente no frontend implementado.
- [ ] 100% das telas do novo frontend consomem payloads do backend alinhados ao fluxo da tela, sem depender de regra canônica executada no cliente.
- [ ] 100% dos cálculos de pontuação seguem a fórmula oficial: exato=3, vencedor/empate=1, erro=0, multiplicador Brasil=2, campeão=10, artilheiro=15.
- [ ] 100% das alterações em resultados oficiais, gols ou assistências disparam recálculo de pontuação, ranking e artilheiro oficial afetados.
- [ ] 100% da carga inicial reflete os 48 times distribuídos em 12 grupos definidos em `data/teams-groups.json`.
- [ ] 100% dos 72 jogos de fase de grupos em `data/group-stage-matches.json` podem ser importados sem perda de grupo, rodada, horário, venue ou multiplicador do Brasil.
- [ ] 100% dos 32 jogos de mata-mata em `data/bracket-knockout.json` podem ser persistidos com feeders/slots suficientes para propagação automática.
- [ ] 100% dos 12 terceiros colocados são ranqueados pela aplicação e apenas os 8 melhores avançam ao Round of 32 conforme as regras documentadas.
- [ ] 100% dos slots TBD de terceiros no Round of 32 são preenchidos deterministicamente sem confronto precoce inválido entre times do mesmo grupo.
- [ ] O MVP atende um grupo inicial de até 100 usuários autenticados com uma única competição ativa.
- [ ] A aplicação fica publicável na Vercel com frontend React, backend dedicado e banco PostgreSQL operacionais para o MVP.

---

## Acceptance Tests

| ID | Scenario | Given | When | Then |
|----|----------|-------|------|------|
| AT-001 | Cadastro inicia pendente | Um visitante sem conta acessa a aplicação | Ele cria uma conta | O usuário é criado com `accessStatus = PENDING` e não recebe acesso ao bolão. |
| AT-002 | Usuário pendente vê somente espera | Um usuário autenticado com status `PENDING` | Ele tenta acessar dashboard, ranking ou palpites | O sistema mostra a tela de aguardando aprovação e bloqueia as demais áreas. |
| AT-003 | Aprovação libera participação | Um usuário autenticado com status `APPROVED` e janela de palpites aberta | Ele salva palpite de campeão, artilheiro e partida | Os palpites são persistidos com sucesso. |
| AT-004 | Fechamento bloqueia edição | Um usuário `APPROVED` possui palpites salvos | O horário atual alcança `predictionCloseAt` e ele tenta editar ou criar palpite | O sistema bloqueia criação e edição e preserva os palpites existentes. |
| AT-004A | Frontend público segue mocks de autenticação | Um visitante acessa login e criação de conta | Ele navega entre autenticação e cadastro | O frontend apresenta estrutura e estados equivalentes a `mock/login-page.html` e `mock/create-account.html`, consumindo contratos do backend. |
| AT-005 | Explore respeita liberação | Um usuário `APPROVED` possui acesso normal | Ele abre Explore antes e depois de `exploreReleaseAt` | Antes vê apenas os próprios palpites; depois vê os palpites dos demais aprovados. |
| AT-005A | Frontend membro cobre todos os mocks principais | Um usuário `APPROVED` autenticado acessa a aplicação | Ele navega por dashboard, palpites iniciais, palpites por fase, resultados, ranking, chaveamento e Explore | Cada área possui rota/composição equivalente aos mocks correspondentes em `mock/*` e obtém dados do backend sem recalcular regras canônicas no cliente. |
| AT-006 | Usuário não aprovado não influencia ranking | Existem usuários `PENDING`, `REJECTED`, `BLOCKED` e `APPROVED` | O sistema recalcula ranking e estatísticas | Apenas usuários `APPROVED` aparecem e influenciam desempates e agregações. |
| AT-007 | Pontuação exata não acumula | Existe uma partida finalizada com placar oficial conhecido | Um palpite acerta o placar exato | O sistema atribui 3 pontos base, sem somar ponto adicional por vencedor. |
| AT-008 | Multiplicador do Brasil é aplicado | Existe uma partida envolvendo o Brasil | Um palpite acerta o placar exato ou apenas o resultado | O sistema atribui respectivamente 6 ou 2 pontos. |
| AT-009 | Override manual tem precedência | Um dado importado já recebeu correção manual do admin | Uma sincronização automática posterior tenta sobrescrever o mesmo campo | O sistema preserva o override manual, salvo autorização explícita do admin. |
| AT-010 | Mudança de estatística recalcula artilheiro | Há empate de gols entre jogadores e assistências relevantes | O admin ou a integração altera gols ou assistências | O sistema recalcula a lista oficial de artilheiros e os pontos de artilheiro dos usuários. |
| AT-011 | Seed inicial do torneio é carregado | O sistema recebe os arquivos `data/*` do projeto | O processo de bootstrap roda | São persistidos 48 times, 72 partidas de grupos e 32 partidas de mata-mata com metadados coerentes. |
| AT-012 | Ranking dos terceiros é calculado | Todos os grupos concluíram a 3a rodada | O job consolida a fase de grupos | Os 12 terceiros são ordenados por pontos, saldo, gols e ranking FIFA; apenas os 8 melhores avançam. |
| AT-013 | Slots TBD do Round of 32 são preenchidos | Os 8 melhores terceiros já são conhecidos | A aplicação monta o bracket | Cada slot M74/M77/M79/M80/M81/M82/M85/M87 recebe um terceiro elegível sem conflito de grupo. |
| AT-014 | Vencedor propaga no mata-mata | Uma partida de mata-mata finalizou com status `FT`, `AET` ou `PEN` | O sync processa o resultado | O vencedor preenche o feeder do próximo jogo e, em semifinal, o perdedor alimenta a disputa de 3o lugar. |
| AT-015 | Sync não processa jogo ainda aberto | O cron dispara antes do encerramento real de uma partida | O status da fixture ainda não é `FT`, `AET` ou `PEN` | O sistema registra o evento no `SyncLog` e não recalcula bracket nem ranking. |
| AT-016 | Console admin segue todos os mocks administrativos | Um administrador autenticado acessa o console | Ele navega por dashboard, usuários, integração, partidas, resultados, jogadores e configurações | O frontend apresenta telas equivalentes a `mock/admin/*` e o backend oferece endpoints/DTOs adequados para cada fluxo. |

---

## Out of Scope

Explicitly NOT included in this feature:

- App mobile nativo.
- Pagamentos, prêmios financeiros ou monetização do bolão.
- Chat, comentários ou funcionalidades sociais avançadas.
- WebSocket ou atualização em tempo real como requisito de MVP.
- Múltiplos torneios na mesma instância.
- Sistema avançado de permissões além de participante/admin.
- Auditoria completa além de logs básicos de sincronização.
- Tempo real contínuo ou live polling de alta frequência durante partidas.
- Scraping/web scraping como dependência principal de dados oficiais.

---

## Constraints

| Type | Constraint | Impact |
|------|------------|--------|
| Product | O MVP deve cobrir autenticação, aprovação, palpites, ranking, Explore, chaveamento e administração básica. | Restringe cortes de escopo nas funcionalidades centrais do bolão. |
| Technical | Frontend em React com uso de UI Kit, evitando construção visual totalmente custom. | Direciona o design para composição sobre biblioteca pronta. |
| UX | Os arquivos em `mock/*` e `mock/admin/*` são a referência obrigatória para navegação, estados e composição do novo frontend. | O design precisa mapear cada mock para rota, componente e contrato backend correspondente. |
| Platform | A aplicação deve ser publicável na Vercel. | Influencia escolhas de deploy, frontend e jobs agendados. |
| Backend | O backend desta iniciativa usará PostgreSQL como banco principal, com auth, autorização e regras server-side em camada backend dedicada. | Direciona modelagem de banco, serviços de aplicação e controles de acesso fora do Supabase. |
| API Contract | O backend deve entregar DTOs/view models orientados às telas do frontend, evitando acoplamento direto do cliente ao schema relacional. | Exige camada explícita de contratos e testes de integração/contrato. |
| Integration | A fonte automática recomendada do MVP é API-Football via RapidAPI; Google Sheets é fallback operacional opcional. | O design deve prever adaptador externo, credenciais seguras e caminho alternativo simples. |
| Data | Os arquivos `data/teams-groups.json`, `data/group-stage-matches.json` e `data/bracket-knockout.json` são a base canônica inicial da competição. | O design precisa prever seed/import idempotente e versionado. |
| Sync | O job pós-jogo deve respeitar o plano gratuito de 100 req/dia e a janela `startsAt + ~115 min`. | O design deve evitar polling contínuo e controlar consumo. |
| Rules | O chaveamento do Round of 32 e a propagação do mata-mata são responsabilidade da aplicação, não da API externa. | O design precisa de módulo determinístico de standings/bracket. |
| Governance | Overrides manuais do admin não podem ser sobrescritos automaticamente por sincronizações futuras. | Requer rastreamento de precedência e reconciliação. |
| Scope | O grupo inicial do MVP é de até 100 usuários. | Permite priorizar simplicidade operacional em vez de hiperescala. |

---

## Technical Context

> Essential context for Design phase - prevents misplaced files and missed infrastructure needs.

| Aspect | Value | Notes |
|--------|-------|-------|
| **Deployment Location** | `app/` + `backend/` + `database/` | `app/` para frontend React/web app, `backend/` para auth/APIs/jobs e `database/` para schema/migrations do PostgreSQL. |
| **UX Reference** | `mock/` + `mock/admin/` + `docs/04-visual-identity.md` | Fonte canônica para o novo frontend em conjunto com os requisitos do MVP. |
| **Data Assets** | `data/` | Seeds versionados para grupos, fixtures e bracket do torneio 2026. |
| **KB Domains** | None currently applicable from `~/.config/opencode/kb/_index.yaml` | O índice disponível no ambiente lista apenas `containers`, que não é o domínio principal deste MVP. |
| **IaC Impact** | New resources | Espera-se provisionar PostgreSQL, backend dedicado, deploy na Vercel e automação agendada para sincronização. |

---

## Data Contract (if applicable)

> Include this section when the feature involves data pipelines, ETL, or analytics.

### Source Inventory
| Source | Type | Volume | Freshness | Owner |
|--------|------|--------|-----------|-------|
| API-Football via RapidAPI | API HTTP externa | Baixo no MVP; <= 100 req/dia no plano free | Pós-jogo / agendado | Projeto / admin |
| Google Sheets API (fallback) | API de planilha | Baixo | Sob demanda / agendado | Admin / projeto |
| Seed JSON local | Arquivo versionado | 48 times + 72 jogos grupos + 32 jogos mata-mata | Bootstrap/manual | Repositório |
| PostgreSQL transactional store | PostgreSQL | Até 100 usuários no MVP | Near-real-time transacional | Application backend |
| Manual admin overrides | Operação administrativa | Baixo volume, alta criticidade | On-demand | Administrador |

### Schema Contract
| Column | Type | Constraints | PII? |
|--------|------|-------------|------|
| `users.access_status` | ENUM | `PENDING`, `APPROVED`, `REJECTED`, `BLOCKED`; default `PENDING` | No |
| `matches.has_manual_override` | BOOLEAN | Default `false`; impede overwrite automático sem permissão | No |
| `matches.external_id` | TEXT | Obrigatório para fixtures sincronizadas; único por provedor | No |
| `matches.phase` | ENUM | Deve cobrir `GROUP_STAGE`, `ROUND_OF_32`, `ROUND_OF_16`, `QUARTER_FINAL`, `SEMI_FINAL`, `THIRD_PLACE`, `FINAL` | No |
| `matches.bracket_slot` | TEXT | Slots como `M74`, `M89`, `W101` para feeders e propagação | No |
| `sync_logs.provider` | ENUM | `API_FOOTBALL`, `GOOGLE_SHEETS`, `ADMIN`, `SEED` | No |
| `official_results.top_scorer_player_ids` | ARRAY<UUID> | Aceita 1..N jogadores empatados após critério oficial | No |
| `predictions.user_id` | UUID | Obrigatório; deve referenciar usuário `APPROVED` para participação ativa | No |
| `users.email` | TEXT | Único por usuário | Yes |

### Freshness SLAs
| Layer | Target | Measurement |
|-------|--------|-------------|
| External sync | Até 3 execuções/dia após jogos previstos | Timestamp do último `SyncLog` bem-sucedido por fixture/job |
| Manual override propagation | Recalcular imediatamente após alteração salva | Timestamp de atualização versus conclusão do recálculo |
| Ranking/app views | Refletir resultados recalculados após processamento | Comparação entre `updatedAt` dos dados oficiais e materialização/consulta exibida |
| Seed bootstrap | Carga completa antes da abertura do bolão | Contagem persistida vs. contagem esperada dos arquivos `data/*` |

### Completeness Metrics
- 100% dos usuários exibidos no ranking devem ter `accessStatus = APPROVED`.
- 0 sobrescritas automáticas indevidas em campos marcados com override manual.
- 100% das partidas finalizadas usadas no ranking devem ter pontuação derivada da fórmula oficial.
- 100% dos seeds carregados devem preservar os totais esperados: 48 seleções, 72 jogos de grupos, 32 jogos de mata-mata.
- 0 slots TBD do Round of 32 podem permanecer vazios depois que os 8 melhores terceiros forem conhecidos.

### Lineage Requirements
- Cada sincronização deve registrar origem, status e horário em `SyncLog`.
- Alterações manuais precisam manter sinalização de override para reconciliar futuras sincronizações.
- Mudanças em resultados, gols ou assistências devem ser rastreáveis até o recálculo de ranking e artilheiro.
- O seed inicial deve registrar que veio do repositório local para diferenciar bootstrap de sincronização externa.
- O preenchimento de slots do bracket deve ser rastreável até a combinação de grupos dos terceiros classificados.

---

## Assumptions

Assumptions that if wrong could invalidate the design:

| ID | Assumption | If Wrong, Impact | Validated? |
|----|------------|------------------|------------|
| A-001 | O MVP operará com uma única competição ativa e até 100 usuários. | O design pode precisar de otimizações de escala e multi-tenant mais cedo. | [ ] |
| A-002 | PostgreSQL com uma camada backend dedicada atenderá auth, persistência e regras server-side deste MVP sem complexidade excessiva. | Pode ser necessário rever a stack backend, os boundaries de arquitetura ou os controles de acesso. | [ ] |
| A-003 | API-Football no plano gratuito continuará suficiente para a estratégia pós-jogo do MVP. | Pode ser necessário rever frequência, custos ou provedor externo. | [ ] |
| A-004 | Uma tabela estática/lookup determinístico será suficiente para alocar os 8 melhores terceiros aos slots do Round of 32 sem ambiguidade operacional. | O design pode precisar embutir a tabela FIFA completa ou regras extras. | [ ] |
| A-005 | Overrides manuais por campo/registro são suficientes para preservar a precedência operacional. | Pode ser necessário modelo mais sofisticado de reconciliação e versionamento. | [ ] |
| A-006 | Logs básicos de sincronização atendem o MVP. | Pode ser necessário ampliar auditoria e trilhas de decisão administrativas. | [ ] |

---

## Clarity Score Breakdown

| Element | Score (0-3) | Notes |
|---------|-------------|-------|
| Problem | 3 | Dor, impacto e necessidade de governança estão claros e acionáveis. |
| Users | 3 | Personas principais e dores foram explicitadas, incluindo admin e builder. |
| Goals | 3 | Metas estão priorizadas em MoSCoW e conectadas ao MVP. |
| Success | 3 | Critérios agora incluem seed, sincronização pós-jogo e comportamento do bracket de forma mensurável. |
| Scope | 3 | Limites do MVP e exclusões estão explícitos. |
| **Total** | **15/15** | |

**Minimum to proceed: 12/15**

---

## Open Questions

- O design vai embutir a tabela FIFA completa de combinações dos 8 terceiros colocados ou um algoritmo determinístico equivalente com testes de exaustão?
- Google Sheets fallback entra já no MVP inicial ou fica apenas preparado por interface/adapter?
- O deploy web será React puro ou React estruturado com Next.js na Vercel para simplificar rotas protegidas e operações server-side?
- Os contratos frontend→backend serão mantidos por schemas compartilhados gerados ou por DTOs versionados manualmente no backend com tipos espelhados no frontend?

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-21 | define-agent | Initial version |
| 1.1 | 2026-05-21 | iterate-agent | Added integration strategy, bracket-calculation requirements, and tournament seed constraints from discovery docs/data |
| 1.2 | 2026-05-21 | iterate-agent | Replaced Supabase with PostgreSQL plus a dedicated backend layer across constraints, context, and assumptions |
| 1.3 | 2026-05-21 | design-agent | Design phase completed; status updated to Designed |
| 1.4 | 2026-05-22 | iterate-agent | Added mock-driven frontend and explicit backend-to-frontend contract requirements, with admin/member screen coverage expectations |

---

## Next Step

**Ready for:** `/workflow:build ~/.config/opencode/sdd/features/bolao-copa-rdg/DESIGN_BOLAO_COPA_RDG.md`
