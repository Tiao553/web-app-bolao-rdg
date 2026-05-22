# BRAINSTORM: Bolao Copa RDG

> Exploratory session to clarify intent and approach before requirements capture

## Metadata

| Attribute | Value |
|-----------|-------|
| **Feature** | BOLAO_COPA_RDG |
| **Date** | 2026-05-21 |
| **Author** | brainstorm-agent |
| **Status** | Ready for Define |

---

## Initial Idea

**Raw Input:** Construir a base de trabalho do projeto Bolao da Copa a partir de `docs/01-product-overview.md` e, nesta iteração, consolidar o discovery de integração em `docs/02-discovery-google-api.md`, as regras de chaveamento em `docs/03-bracket-rules.md` e os artefatos do torneio pré-carregados em `data/*`.

**Context Gathered:**
- O produto e as regras de negocio ja estao documentados em `docs/01-product-overview.md`.
- O usuario quer arquitetura e geracao de codigo, nao apenas documentacao.
- O backend foi redirecionado para PostgreSQL como banco principal, com frontend em React e camada backend dedicada a ser detalhada no design.
- O usuario pediu agentes reutilizaveis, sem prefixo do projeto, para servir em outros trabalhos.
- Foram criados agentes genericos e o roteamento foi ajustado durante esta fase.
- O discovery mostrou que nao existe Google API oficial suficiente para partidas/estatisticas da Copa; a melhor fonte automatica para o MVP passa a ser API-Football via RapidAPI.
- `Google Sheets API` passa a fazer mais sentido como fallback operacional/controlado pelo admin do que como fonte primaria de resultados.
- O chaveamento da Copa 2026 nao vem pronto da API: a aplicacao precisa calcular classificacao de grupos, ranking dos 12 terceiros, selecao dos 8 melhores e preenchimento do Round of 32.
- O repositorio ja possui carga-base do torneio em `data/teams-groups.json`, `data/group-stage-matches.json` e `data/bracket-knockout.json`.

**Technical Context Observed (for Define):**

| Aspect | Observation | Implication |
|--------|-------------|-------------|
| Likely Location | `docs/`, `specs/`, `~/.config/opencode/agents/`, `~/.config/opencode/config/` | O projeto mistura produto, workflow SDD e customizacao global do opencode |
| Relevant KB Domains | workflow, architecture, frontend, integration, qa | O DEFINE deve separar requisitos de produto, integracao, persistencia PostgreSQL e validacao de regras |
| Seed Assets | `data/teams-groups.json`, `data/group-stage-matches.json`, `data/bracket-knockout.json` | O design pode partir de dados canonicos locais antes da sincronizacao automatica |
| IaC Patterns | Vercel + jobs agendados + PostgreSQL + backend dedicado | A fase seguinte deve prever cron/sync, persistencia transacional e servicos de aplicacao |

---

## Discovery Questions & Answers

| # | Question | Answer | Impact |
|---|----------|--------|--------|
| 1 | What is the primary use case? | Customer-facing product. O app e um bolao web para participantes e admin. | Confirma necessidade de UX clara, auth, regras de acesso e area administrativa. |
| 2 | What is the current pain point this feature solves? | O escopo do produto e amplo e faltava um conjunto de agentes adequado para conduzir arquitetura, implementacao e validacao com consistencia. | A Atividade 0 passa a ser fundacional: preparar agentes e direcao antes do DEFINE. |
| 3 | Who are the primary users and at what scale? | Participantes do bolao e um administrador. A escala exata nao foi confirmada, mas o overview sugere um grupo controlado, nao um produto massivo. | Permite priorizar simplicidade operacional no MVP, sem foco inicial em hiperescala. |
| 4 | How will success be recognized? | Sucesso nesta fase significa sair com agentes prontos, roteamento ajustado e direcao suficiente para entrar em DEFINE sem bloqueio estrutural. | Define um criterio claro de encerramento do brainstorm. |
| 5 | What are the hard constraints? | Deve usar stack web moderna, com React no frontend; o usuario trocou o backend para PostgreSQL como banco principal; os agentes devem ser reutilizaveis globalmente; a integracao deve usar uma fonte automatica viavel e preservar fallback/manual override. | Restringe as decisoes da fase e evita criar artefatos presos ao projeto. |
| 6 | Are there existing tools or partial solutions? | Sim: existe um product overview detalhado e havia agentes genericos no ambiente, mas faltavam especialistas adequados para este tipo de projeto. | Permite reaproveitar a base do opencode e complementar apenas as lacunas reais. |
| 7 | What systems must this integrate with? | Multiple. O produto depende de auth, banco, painel admin, API-Football como fonte automatica recomendada e possivel fallback por Google Sheets. | Justifica separar integracao externa, governanca de overrides e seeds locais. |
| 8 | What is the production risk if this fails? | Se a base de arquitetura e agentes estiver errada, o projeto entra em execucao com alta chance de retrabalho, regras inconsistentes e integracoes mal definidas. | Reforca a necessidade de sequenciar arquitetura, backend, integracao e QA antes de construir tudo. |
| 9 | How might this evolve in 6-12 months? | O usuario quer uma estrutura reutilizavel que sirva a este projeto e a futuros projetos, com agentes generalistas e routing evolutivo. | A fase precisa produzir ativos globais, nao apenas especificos do Bolao. |

---

## Sample Data Inventory

> Samples improve LLM accuracy through in-context learning and few-shot prompting.

| Type | Location | Count | Notes |
|------|----------|-------|-------|
| Input files | `docs/01-product-overview.md`, `docs/02-discovery-google-api.md`, `docs/03-bracket-rules.md` | 3 | Produto, estrategia de integracao e regras de chaveamento do torneio |
| Output examples | `data/*.json` | 3 | Seeds canonicos para grupos, calendario da fase de grupos e chaveamento mata-mata |
| Ground truth | `data/teams-groups.json`, `data/group-stage-matches.json`, `data/bracket-knockout.json` | 3 | Base inicial verificavel para 48 selecoes, 72 jogos de grupos e 32 jogos de mata-mata |
| Related code | `~/.config/opencode/agents/*.agent.md`, `~/.config/opencode/config/routing.json` | 7+ | Base criada na Atividade 0 para orientar fases futuras |

**How samples will be used:**

- O product overview continua como ancora de produto para o DEFINE.
- O discovery da integracao reduz a incerteza: API-Football vira fonte automatica recomendada; Google Sheets vira fallback/manual assistido.
- Os JSONs pre-carregados servem como carga inicial, fixture de validacao e referencia para modelagem de seeds/importers.
- `docs/03-bracket-rules.md` transforma a logica de chaveamento em requisito explicito da aplicacao, nao da API.

---

## Approaches Explored

### Approach A: Foundation-first with reusable specialists ⭐ Recommended

**Description:** Antes de detalhar requisitos e arquitetura, criar um conjunto pequeno de agentes reutilizaveis para system design, frontend React, UX/design system, backend baseado em PostgreSQL, integracoes externas e validacao de regras.

**Pros:**
- Reduz retrabalho nas proximas fases.
- Cria uma base reaproveitavel para este e outros projetos.
- Separa melhor responsabilidades entre arquitetura, implementacao e validacao.
- Explicita o discovery da integracao externa sem bloquear o projeto inteiro.

**Cons:**
- Consome um passo inicial antes de entrar no DEFINE.
- Exige ajuste de roteamento e manutencao desses agentes globais.

**Why Recommended:** Resolve a dor principal apontada pelo usuario, melhora a qualidade das fases seguintes e evita acoplamento excessivo a um unico projeto.

---

### Approach B: Project-specific agents for the Bolao only

**Description:** Criar agentes com identidade e instrucoes especificas do Bolao da Copa.

**Pros:**
- Mais contexto de dominio embutido logo no nome e no prompt.
- Menor ambiguidade dentro deste projeto especifico.

**Cons:**
- Baixa reutilizacao em futuros projetos.
- Aumenta manutencao e duplicacao desnecessaria.
- Vai contra a preferencia explicita do usuario.

---

### Approach C: Skip agent foundation and jump directly into DEFINE/implementation

**Description:** Aceitar a estrutura generica existente e partir direto para requisitos e construcao.

**Pros:**
- Menor esforco inicial.
- Mais rapido para comecar a produzir artefatos de produto.

**Cons:**
- Maior risco de usar especialistas errados ou insuficientes.
- Mais chance de retrabalho em arquitetura, frontend, backend e QA.
- Mantem a dor principal sem tratamento.

---

## Data Engineering Context (if applicable)

### Source Systems
| Source | Type | Volume Estimate | Current Freshness |
|--------|------|-----------------|-------------------|
| API-Football via RapidAPI | API externa | Baixo no MVP; ate 100 req/dia no plano free | Pos-jogo / agendado |
| Google Sheets API (fallback) | Planilha/API | Baixo | Sob demanda / agendado |
| Seed JSON local | Arquivos versionados | 48 selecoes, 72 jogos de grupos, 32 jogos de mata-mata | Estatica / bootstrap |
| PostgreSQL | Banco transacional principal + camada backend dedicada | Ate 100 usuarios no MVP | Transacional |

### Data Flow Sketch
```text
[API-Football seed/sync] -> [Normalized official data in PostgreSQL] -> [Manual admin override or Google Sheets fallback] -> [Group standings + top 8 third-place ranking + bracket fill] -> [Score recalculation] -> [Ranking / Explore / Reports]
```

### Key Data Questions Explored
| # | Question | Answer | Impact |
|---|----------|--------|--------|
| 1 | Existe Google API oficial suficiente para este caso? | Nao. | O projeto nao deve depender de uma API Google nativa para placares/estatisticas oficiais. |
| 2 | Qual a melhor fonte automatica para o MVP? | API-Football via RapidAPI. | O DEFINE pode tratar essa escolha como baseline da integracao. |
| 3 | O sistema depende de correcao manual? | Sim, explicitamente. | A arquitetura deve preservar precedence de override manual. |
| 4 | O chaveamento vem pronto da API? | Nao. | A aplicacao precisa calcular classificacao, terceiros colocados, slots TBD e propagacao do mata-mata. |
| 5 | Ha base local suficiente para bootstrap? | Sim, em `data/*`. | O design pode prever carga inicial canonica antes dos jobs externos. |

---

## Selected Approach

| Attribute | Value |
|-----------|-------|
| **Chosen** | Approach A |
| **User Confirmation** | 2026-05-21 |
| **Reasoning** | O usuario definiu a Atividade 0 como montagem dos agentes necessarios, pediu que eles fossem genericos e solicitou ajuste do routing para uso futuro em qualquer projeto. |

---

## Key Decisions Made

| # | Decision | Rationale | Alternative Rejected |
|---|----------|-----------|----------------------|
| 1 | Tratar a Atividade 0 como fundacao do projeto | A principal dor atual era falta de agentes adequados para tocar o trabalho com seguranca | Pular direto para implementacao |
| 2 | Criar agentes reutilizaveis e sem prefixo do projeto | O usuario quer reaproveitamento em trabalhos futuros | Agentes especificos do Bolao |
| 3 | Adotar PostgreSQL como direcao do backend | Foi a nova escolha explicita do usuario para esta iniciativa | Manter dependencia de Supabase |
| 4 | Separar React e UX em agentes diferentes | O usuario pediu um agente para cada responsabilidade | Um unico agente frontend amplo |
| 5 | Tratar a integracao externa como discovery inicial | Antes desta iteracao a fonte ainda nao estava consolidada | Congelar prematuramente uma fonte especifica |
| 6 | Ajustar `routing.json` ja no brainstorm | Garante que os agentes criados sejam acionados de forma consistente nas proximas fases | Deixar roteamento para depois |
| 7 | Adotar API-Football como fonte automatica recomendada e Google Sheets como fallback | O discovery mostrou ausencia de API Google oficial adequada e uma opcao viavel com baixo consumo | Permanecer com integracao abstrata demais |
| 8 | Tratar `data/*` como seed canonico do torneio 2026 | Ja existe material pronto para grupos, calendario e bracket | Esperar a integracao externa para iniciar modelagem |
| 9 | Fazer a aplicacao ser dona da logica do chaveamento | A API entrega dados brutos, nao a regra FIFA de terceiros colocados e propagacao do bracket | Pressupor que o provedor externo resolvera o bracket |

---

## Features Removed (YAGNI)

| Feature Suggested | Reason Removed | Can Add Later? |
|-------------------|----------------|----------------|
| Agentes especificos do Bolao com prefixo do projeto | Baixa reutilizacao e preferencia explicita contra isso | Yes |
| Buscar uma Google API nativa de futebol como fonte primaria | O discovery mostrou que ela nao existe de forma adequada para o MVP | No |
| Tratar deploy/DevOps como frente principal da Atividade 0 | Nao reduz o maior risco atual do projeto | Yes |
| Expandir para mobile nativo ou features sociais nesta fase | Fora do MVP do overview e sem relacao com a dor principal | Yes |
| Resolver em tempo real/live score no MVP | O plano free e o fluxo pos-jogo cobrem a necessidade atual com menor complexidade | Yes |

---

## Incremental Validations

| Section | Presented | User Feedback | Adjusted? |
|---------|-----------|---------------|-----------|
| Prioridade do MVP | ✅ | O foco deveria ser montar os agentes necessarios para o projeto | Yes |
| Escopo dos agentes | ✅ | Backend com PostgreSQL, integracao externa para discovery, React e UX separados | Yes |
| Naming dos agentes | ✅ | O usuario rejeitou prefixo `bolao` e pediu agentes genericos | Yes |
| Roteamento | ✅ | O usuario pediu ajuste do routing e ele foi aplicado | Yes |

---

## Suggested Requirements for /workflow:define

Based on this brainstorm session, the following should be captured in the DEFINE phase:

### Problem Statement (Draft)
Estruturar o projeto Bolao da Copa de forma que a definicao, o desenho tecnico e a implementacao ocorram com agentes adequados, arquitetura coerente, uma estrategia concreta de integracao oficial (API-Football + fallback operacional) e regras claras para classificacao de grupos, terceiros colocados e chaveamento do mata-mata.

### Target Users (Draft)
| User | Pain Point |
|------|------------|
| Dono do projeto / builder | Precisa transformar um overview amplo em um plano executavel sem retrabalho estrutural |
| Administrador do bolao | Dependera de auth, aprovacao, override manual e gestao confiavel da competicao |
| Participante do bolao | Dependera de fluxos claros de cadastro, palpites, ranking e Explore |

### Success Criteria (Draft)
- [ ] O projeto tem requisitos consolidados para auth, status de usuario, palpites, ranking, Explore e administracao.
- [ ] O papel da integracao externa fica fechado no nivel de estrategia: API-Football como fonte automatica recomendada, Google Sheets como fallback e admin panel como correcao final.
- [ ] A separacao entre frontend, UX, backend, integracao e QA fica clara no plano.
- [ ] A fase DEFINE produz um escopo viavel para o MVP descrito no overview.
- [ ] O DEFINE captura que o app e responsavel por calcular grupos, melhores terceiros, preenchimento do bracket e propagacao dos vencedores.

### Constraints Identified
- React no frontend com uso de UI Kit.
- Backend direcionado para PostgreSQL nesta iniciativa.
- Integracao externa obrigatoria com baseline em API-Football via RapidAPI e fallback opcional por Google Sheets.
- Agentes e roteamento devem continuar genericos e reaproveitaveis.
- Seeds locais em `data/*` devem ser considerados fonte canonica inicial da competicao 2026.

### Out of Scope (Confirmed)
- Tornar os agentes especificos do Bolao.
- Procurar uma API Google nativa de futebol como dependencia central do MVP.
- Tratar mobile nativo, pagamentos, notificacoes push ou features sociais antes do MVP principal.

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-05-21 | brainstorm-agent | Initial version |
| 1.1 | 2026-05-21 | iterate-agent | Consolidated Google/API discovery, bracket rules, and tournament seed files into the brainstorm |
| 1.2 | 2026-05-21 | iterate-agent | Replaced Supabase direction with PostgreSQL and a dedicated backend layer in the discovery narrative |

---

## Session Summary

| Metric | Value |
|--------|-------|
| Questions Asked | 9 |
| Approaches Explored | 3 |
| Features Removed (YAGNI) | 5 |
| Validations Completed | 4 |
| Duration | Approx. one collaborative setup session |

---

## Next Step

**Ready for:** `/workflow:define ~/.config/opencode/sdd/features/bolao-copa-rdg/BRAINSTORM_BOLAO_COPA_RDG.md`
