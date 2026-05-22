# SDD — Copa RDG Frontend · Spec vs Mock vs Implementation

> Fonte de verdade: arquivos em `mock/` e `mock/admin/`.  
> Cada seção lista elementos do mock, status de implementação e rota de backend.

---

## 1. Componentes Globais

### 1.1 Sidebar — Membro (`member-shell.tsx`)
| Elemento mock | Status | Observação |
|---|---|---|
| `.brand-logo` com mark RDG + nome + kicker | ✅ Implementado | |
| `.nav-section` "Principal" com 4 itens | ✅ | Dashboard, Palpites iniciais, Palpites por fase, Resultados |
| `.nav-section` "Competição" com 3 itens | ✅ | Ranking, Chaveamento, Explore |
| `.nav-item.active` highlight laranja | ✅ | via `usePathname` |
| `.sidebar-footer` com avatar + nome + role | ✅ | |
| `.status-pill` mostrando Approved/Pending | ✅ | |
| Botão de logout | ❌ **Falta** | Nenhum botão de logout na sidebar |

### 1.2 Sidebar — Admin (`admin-shell.tsx`)
| Elemento mock | Status | Observação |
|---|---|---|
| `.brand-logo` com kicker "Admin Console" | ✅ | |
| `.nav-section` "Admin": Dashboard, Usuários, Integração, Partidas | ✅ | |
| `.nav-section` "Operação": Resultados, Jogadores, Configurações | ✅ | |
| Avatar "AD" + "Admin RDG" + "Governança" | ✅ | |
| `.nav-item.active` dinâmico | ✅ | |
| Botão de logout | ❌ **Falta** | |

### 1.3 Botões (CSS)
| Classe mock | CSS global | Observação |
|---|---|---|
| `.primary-button` / `.btn-primary` | ✅ `.btn-primary` | Nome difere: mock usa `.primary-button`, app usa `.btn-primary` |
| `.ghost-button` / `.btn-ghost` | ✅ `.btn-ghost` | |
| `.ok-button` | ❌ **Falta** | Verde, border `rgba(34,197,94,.24)`, bg `var(--g5-g)` |
| `.danger-button` | ❌ **Falta** | Vermelho, border `rgba(244,63,94,.24)`, bg `var(--ro-g)` |
| `.secondary-button` / `.btn-light` | ✅ `.btn-light` | |

---

## 2. Páginas de Auth

### 2.1 `/login` — `mock/login-page.html`
| Elemento | Status | Observação |
|---|---|---|
| Split-screen `.auth-page` | ✅ | |
| `.brand-panel` com grid pattern + glow | ✅ | |
| `.hero-copy` com h1 + eyebrow | ✅ | |
| Ilustração `.mock-illustration` + `.person` | ✅ | |
| `.floating-card` Pontuação + Status | ✅ | |
| `.feature-cards` (3 cards) | ✅ | |
| `.form-card` com email + senha + forgot | ✅ | |
| `TypeSwitch` Participante/Administrador | ✅ Removido | Correto — separado em `/admin/login` |
| `.password-eye` toggle | ✅ | |
| Link "Esqueceu a senha?" → `/forgot-password` | ✅ | |
| Link "Criar conta" → `/create-account` | ✅ | |
| Link "Área administrativa?" → `/admin/login` | ✅ | |

### 2.2 `/admin/login` — novo
| Elemento | Status | Observação |
|---|---|---|
| Split-screen `.auth-page` | ✅ | |
| `.brand-panel.admin-brand-panel` (glow azul) | ✅ | |
| 3 `.admin-feature-row` (Dashboard, Gestão, Aprovação) | ✅ | |
| Form com `_intent=admin` hidden | ✅ | |
| Error `not_admin` tratado | ✅ | |
| Link "Voltar ao login" → `/login` | ✅ | |

### 2.3 `/create-account` — `mock/create-account.html`
| Elemento | Status | Observação |
|---|---|---|
| Layout single-panel (form esquerda, brand direita) | ❌ **Falta** | App tem split mas invertido e sem `.stats-row` |
| `.social-stack` (Apple, Google, Facebook) | ❌ **Não implementar** | Sem OAuth configurado |
| `.divider` "OR" | ❌ **Falta** | |
| `.access-type` switch Participante/Admin | ❌ **Falta** | No mock existe; só participante deve ser criado via form público |
| `.field-grid` 2 colunas (nome + email) | ❌ **Falta** | App usa coluna única |
| Ícones no input (`.input-icon`) | ❌ **Falta** | |
| Password field com eye | ✅ | |
| `.login-row` link "Login" → `/login` | ✅ | |
| `.brand-panel` direita com `.shape-field` + stats-row | ❌ **Falta** | App não tem o painel direito completo |
| Terms & conditions checkbox | ✅ | Movido do login para cá |

### 2.4 `/forgot-password` — sem mock original
| Elemento | Status | Observação |
|---|---|---|
| Split-screen com brand panel | ✅ | |
| Campo email + botão enviar | ✅ | |
| Link voltar ao login | ✅ | |
| Backend endpoint `/api/auth/forgot-password` | ❌ **Não existe** | Funcionalidade não implementada no backend |

### 2.5 `/waiting` — `mock/aguardando-aprovacao.html`
| Elemento | Status | Observação |
|---|---|---|
| `.steps` 01/02/03 | ✅ | |
| Status card | ✅ | |
| Hero com eyebrow + h1 | ✅ | |

---

## 3. Páginas de Membro

### 3.1 `/dashboard` — `mock/dashborad.html`
| Elemento | Status | Observação |
|---|---|---|
| `.hero` com h1 personalizado (`Bem-vindo de volta, Nome`) | ✅ | |
| `.deadline-card` com countdown | ✅ | |
| Card "Sua pontuação" + `.score-gauge` | ✅ | |
| Card "Breakdown" com barras | ✅ | |
| Card "Top ranking" (mini-leaderboard 4 posições) | ✅ | |
| Card "Próximos jogos" com match list | ❌ **Falta** | Não implementado; mock tem 3 jogos com flags, horário, badge Brasil ×2 |
| `.match-row` com `.match-date`, `.teams`, `.flag`, `.match-badge` | ❌ **Falta** | Classes CSS também faltam |
| Botões topbar "Ver regras" + "Fazer palpites →" | ✅ | |
| `.match-badge.brazil` (badge laranja "Brasil ×2") | ❌ **Falta** | CSS falta |
| `.match-badge.open` (badge verde "Aberto") | ❌ **Falta** | CSS falta |

### 3.2 `/initial-predictions` — `mock/palpites-iniciais.html`
| Elemento | Status | Observação |
|---|---|---|
| `.hero` com eyebrow "Valem até 25 pontos" + deadline | ✅ | |
| Countdown no deadline-card | ✅ | |
| Card "Campeão da Copa" com select de seleção | ✅ | |
| Card "Artilheiro" com select de jogador | ✅ | |
| Botão "Salvar palpites →" | ✅ | |
| Regras de pontuação exibidas | ✅ | |
| Seleções carregadas do backend | ✅ | |
| Atacantes carregados do backend | ❌ **Parcial** | Backend `/api/member/predictions/initial` retorna jogadores mas sem artilheiros confirmados |

### 3.3 `/phase-predictions` — `mock/palpites-fase.html`
| Elemento | Status | Observação |
|---|---|---|
| `.phase-tabs` com 8 fases | ✅ | |
| `.match-card` para cada partida | ✅ | |
| `.score-input` para gols casa e fora | ✅ | |
| `.multiplier` badge Brasil ×2 | ✅ | |
| Estado locked (palpites fechados) | ✅ | |
| Partidas carregadas do backend por fase | ✅ | |

### 3.4 `/results` — `mock/resultados.html`
| Elemento | Status | Observação |
|---|---|---|
| `.result-card` por partida | ✅ | |
| `.scoreline` com placar oficial | ✅ | |
| `.comparison` palpite vs oficial | ✅ | |
| `.points-earned` badge | ✅ | |
| Filtro por fase | ❌ **Falta** | Mock tem selector de fase; app não tem |
| `.phase-tabs` para navegar por fase | ❌ **Falta** | |

### 3.5 `/ranking` — `mock/ranking.html`
| Elemento | Status | Observação |
|---|---|---|
| `.podium` (1º, 2º, 3º lugar) | ✅ | |
| `.ranking-table` completa | ✅ | |
| Coluna movimentação (↑↓ ─) | ✅ | |
| Breakdown bars por usuário | ✅ | |
| Regras de desempate (4 regras) | ✅ | |
| Destaque linha do usuário logado | ❌ **Falta** | `.rank-row.me` classe CSS e lógica |

### 3.6 `/explore` — `mock/explore.html`
| Elemento | Status | Observação |
|---|---|---|
| Estado locked com blur | ✅ | |
| Cards de palpites com `.compare-strip` | ✅ | |
| `.insight-list` | ✅ | |
| Estado desbloqueado com dados reais | ✅ | |

### 3.7 `/bracket` — `mock/chaveamento.html`
| Elemento | Status | Observação |
|---|---|---|
| `.bracket-wrapper` | ✅ | |
| Chaveamento visual com times | Parcial | Layout básico presente |

---

## 4. Páginas de Admin

### 4.1 `/admin/dashboard` — `mock/admin/AdminDashboard.html`
| Elemento mock | Status | Rota backend |
|---|---|---|
| `.hero` com "Controle do Bolão da Copa" | ✅ | |
| `.health-card` "Tudo saudável" com ícone ✓ | ❌ **Falta** | App tem card genérico sem estilo correto |
| 4 `.metric` cards (span 3) no grid 12 colunas | ❌ **Falta** | App usa `.metric-card` fora de grid-12 |
| Card "Fila de governança" (`.task-list`) | ❌ **Falta** | Layout e CSS ausentes |
| `.task-row` com icon + título + texto + pill | ❌ **Falta** | |
| Card "Atividade recente" (`.activity-list`) | ❌ **Falta** | App tem "Últimas sincronizações" mas diferente |
| `.activity-row` com avatar + título + texto + pill | ❌ **Falta** | |
| Sidebar "Progresso do torneio" (`.progress-list`) | ❌ **Falta** | |
| Sidebar "Atalhos" com 3 `.task-row` | ❌ **Falta** | |
| Grid 12 colunas (`.metric` span 3, `.main-card` span 8, `.side-card` span 4) | ❌ **Falta** | CSS de grid admin |
| Backend: `GET /api/admin/dashboard` | ✅ | `AdminDashboardContract` |

### 4.2 `/admin/users` — `mock/admin/AdminUsers.html`
| Elemento mock | Status | Rota backend |
|---|---|---|
| `.hero` com stats pendentes/aprovados | ✅ | |
| Barra de filtros (search + status) | ❌ **Falta** | Client-side filtering |
| Cards de usuário (`.table-row`) estilizados | ❌ **Falta** | App usa HTML `<table>` |
| Avatar com iniciais por usuário | ❌ **Falta** | |
| `.badge` por status (approved/pending/risk) | ❌ **Falta** | App usa `.pill` mas sem visual correto |
| Ações: Aprovar / Rejeitar / Bloquear | Parcial | Approve/Reject OK, Block falta |
| Linha auditoria por usuário | ❌ **Falta** | |
| Backend: `GET /api/admin/users` | ✅ | |
| Backend: `POST /api/admin/users/:id/approve` | ✅ | Via form POST do Next.js |
| Backend: `POST /api/admin/users/:id/reject` | ✅ | |

### 4.3 `/admin/matches` — `mock/admin/AdminMatches.html`
| Elemento mock | Status | Rota backend |
|---|---|---|
| `.hero` "Corrija jogos" + `.match-health` card | ❌ **Falta** | App tem hero simples sem `.match-health` |
| Barra de filtros (search + fase + status + fonte) | ❌ **Falta** | |
| Grid 2 colunas (lista + sidebar) | ❌ **Falta** | App usa tabela única |
| `.match-list` com `.match-row` card-style | ❌ **Falta** | App usa HTML `<table>` |
| Colunas: Código, Partida (flags), Data, Fonte, Ações | ❌ **Falta** | |
| Botões por row: Editar + Validar/Remover/Publicar | ❌ **Falta** | |
| Sidebar: `.stat-grid` (total, API, manuais, pendentes) | ❌ **Falta** | |
| Sidebar: "Editor rápido" com fields + save | ❌ **Falta** | |
| Sidebar: `.warning` card operacional | ❌ **Falta** | |
| Botões topbar: "Importar da API" + "Criar partida manual →" | ❌ **Falta** | |
| Backend: `GET /api/admin/matches` | ✅ | `AdminMatchesContract` |
| Backend: `POST /api/admin/matches` (criar) | ❌ **Falta** | |
| Backend: `PUT /api/admin/matches/:id` (editar) | ❌ **Falta** | |

### 4.4 `/admin/results` — `mock/admin/AdminResults.html`
| Elemento mock | Status | Rota backend |
|---|---|---|
| `.hero` "Altere placares com rastreabilidade" + `.score-card` | ❌ **Falta** | App tem hero simples |
| Barra de filtros (search + fase + fonte + status) | ❌ **Falta** | |
| Grid 2 colunas (lista + sidebar) | ❌ **Falta** | App usa tabela única |
| `.result-list` com `.result-row` card-style | ❌ **Falta** | App usa HTML `<table>` |
| Colunas: Código, Partida, Placar, Fonte, Ações | ❌ **Falta** | |
| Botões por row: Editar + Recalcular/Override/Finalizar | ❌ **Falta** | |
| Sidebar: `.stat-grid` (finalizados, manual, rankings, erros) | ❌ **Falta** | |
| Sidebar: "Editor rápido" com `.score-editor` inputs | ❌ **Falta** | |
| Sidebar: `.warning` "Impacto automático" | ❌ **Falta** | |
| Botões topbar: "Auditoria" + "Recalcular ranking →" | ❌ **Falta** | |
| Backend: `POST /api/admin/results/:matchId` | ❌ **Falta** | |
| Backend: `POST /api/admin/recalculate` | ❌ **Falta** | |

### 4.5 `/admin/players` — `mock/admin/AdminPlayers.html`
| Elemento mock | Status | Rota backend |
|---|---|---|
| `.hero` "Controle o desempate de artilheiros" + `.top-scorer-card` (gold) | ❌ **Falta** | App tem hero simples |
| Barra de filtros (search + seleção + ordenação) | ❌ **Falta** | |
| Grid 2 colunas (lista + sidebar) | ❌ **Falta** | App usa 2 cards simples |
| `.player-list` com `.player-row` card-style | ❌ **Falta** | App usa `.table-list` |
| Colunas: #/avatar, Jogador + detalhe, Gols, Assist., Status pill, Ações | ❌ **Falta** | |
| `.num.gold` para artilheiro líder | ❌ **Falta** | |
| Sidebar: `.stat-grid` (jogadores, gols, assist., empatados) | ❌ **Falta** | |
| Sidebar: `.rule-box` regra de desempate | ❌ **Falta** | |
| Sidebar: "Editor rápido" com inputs de gols/assist. | ❌ **Falta** | |
| Botões topbar: "Importar estatísticas" + "Recalcular artilharia →" | ❌ **Falta** | |
| Backend: `GET /api/admin/players` | ✅ | `AdminPlayersContract` |
| Backend: `PUT /api/admin/players/:id` (gols+assist.) | ❌ **Falta** | |

### 4.6 `/admin/integration` — `mock/admin/AdminIntegration.html`
| Elemento mock | Status | Rota backend |
|---|---|---|
| `.hero` "Integração com v3.football.api-sports.io" + `.connection-card` | ❌ **Falta** | App tem hero diferente |
| Card "Configuração da integração" com `.config-grid` 6 campos | ❌ **Falta** | App tem card simplificado |
| Sidebar "Cobertura" com `.stat-grid` | ❌ **Falta** | |
| Card "Fluxo de sincronização" com `.timeline` 4 steps | ❌ **Falta** | |
| Sidebar "Ações rápidas" com `.sync-list` | ❌ **Falta** | |
| Card "Logs recentes" com `.log-list` | ❌ **Falta** | App tem lista de syncs mas sem estilo |
| Grid 2 colunas intercaladas | ❌ **Falta** | App usa grid-2 simples |
| Backend: `GET /api/admin/integration` | ✅ | `AdminIntegrationContract` |
| Backend: `POST /api/admin/sync` | ❌ **Falta** | |

### 4.7 `/admin/settings` — `mock/admin/AdminSettings.html`
| Elemento mock | Status | Rota backend |
|---|---|---|
| `.hero` "Defina prazos, bloqueios e pontuação" + `.lock-card` | ❌ **Falta** | App tem hero simples com hero-content em grid-2 |
| Card "Configurações principais" com `.settings-grid` (9 campos) | ❌ **Falta** | App tem form mas sem grid correto |
| Campos extras: timezone, modo pontuação, pontos campeão/artilheiro, msg bloqueio | ❌ **Falta** | App tem só nome, fecha, libera |
| Sidebar "Chaves rápidas" com 3 `.toggle-row` + `.switch` | ❌ **Falta** | |
| Sidebar "Zona crítica" / `.danger-zone` | ❌ **Falta** | |
| Card "Regras aplicadas" com 4 `.rule-card` | ❌ **Falta** | App não tem este card |
| Sidebar "Auditoria" com `.audit-list` | ❌ **Falta** | |
| Backend: `POST /api/admin/settings/window` | ✅ | Salva janela |
| Backend: `POST /api/admin/settings/scoring` | ❌ **Falta** | |

---

## 5. Rotas Backend — Lacunas

| Endpoint necessário | Existe? | Prioridade |
|---|---|---|
| `GET /api/admin/dashboard` | ✅ | — |
| `GET /api/admin/users` | ✅ | — |
| `POST /api/admin/users/:id/approve` | ✅ | — |
| `POST /api/admin/users/:id/reject` | ✅ | — |
| `POST /api/admin/users/:id/block` | ❌ | Alta |
| `GET /api/admin/matches` | ✅ | — |
| `POST /api/admin/matches` | ❌ | Alta |
| `PUT /api/admin/matches/:id` | ❌ | Alta |
| `POST /api/admin/results/:matchId` | ❌ | Alta |
| `POST /api/admin/recalculate` | ❌ | Alta |
| `GET /api/admin/players` | ✅ | — |
| `PUT /api/admin/players/:key/stats` | ❌ | Alta |
| `GET /api/admin/integration` | ✅ | — |
| `POST /api/admin/sync` | ❌ | Alta |
| `POST /api/admin/settings/scoring` | ❌ | Média |
| `GET /api/member/dashboard` | ✅ | — |
| `GET /api/member/next-matches` | ❌ | Alta |

---

## 6. Dados Iniciais — Seed

| Arquivo | Existe? | Tabela destino |
|---|---|---|
| `data/teams-groups.json` | ✅ | `matches.home_team_fifa_code` |
| `data/group-stage-matches.json` | ✅ | `matches` |
| `data/bracket-knockout.json` | ✅ | `matches` |
| `data/players-attackers.json` | 🔄 Em criação | `competition_predictions` (TOP_SCORER pool) |

### Rotina de Seed (a criar)
- `backend/app/seed/seeder.py`: checa se dados já existem → ignora; se não → insere
- Chamada no `app_lifespan` do `main.py` (startup)
- Ordem: times → partidas grupo → partidas knockout → jogadores

---

## 7. CSS Faltante em `globals.css`

### Botões admin
```css
.btn-ok    /* verde: border rgba(34,197,94,.24), bg var(--g5-g), color var(--g5) */
.btn-danger /* vermelho: border rgba(244,63,94,.24), bg var(--ro-g), color var(--ro) */
```

### Admin dashboard
```css
.health-card, .health-icon, .health-title, .health-text
.task-list, .task-row, .task-icon, .task-title, .task-text
.activity-list, .activity-row
.progress-list (admin variant)
.grid-12, .col-span-3, .col-span-8, .col-span-4
```

### Admin matches / results
```css
.filters (grid layout search + selects)
.match-list, .match-row (card-style com grid-template-columns)
.result-list, .result-row
.stat-grid, .stat, .stat-value, .stat-label
.edit-panel, .field, .field-label, .field-value
.warning, .warning-title, .warning-text
.match-health, .health-num
.score-card (admin), .score-num, .score-label
.score-editor, .score-box, .score-team, .score-input, .score-sep
```

### Admin players
```css
.top-scorer-card, .top-name, .top-meta
.player-list (admin), .player-row (admin grid)
.player-name, .player-detail
.num, .num.gold
.rule-box, .rule-title, .rule-text (admin variant)
.editor, .editor-summary, .editor-title, .editor-sub
.stat-editor, .stat-input-box, .stat-input-title, .stat-input
.source-box, .source-text
.editor-actions
```

### Admin integration
```css
.connection-card, .conn-label, .conn-title, .conn-text
.config-grid
.timeline (integration), .step, .step-num, .step-title, .step-text
.sync-list, .sync-row
.log-list, .log-row
```

### Admin settings
```css
.lock-card, .lock-title, .lock-meta
.settings-grid
.toggle-row, .toggle-title, .toggle-text, .switch
.danger-zone, .danger-title, .danger-text
.rule-card (settings), .rule-icon
.audit-list, .audit-row, .audit-title, .audit-text
```

### Member dashboard
```css
.match-row (member), .match-date, .match-badge, .match-badge.brazil, .match-badge.open
```

---

## 8. Prioridade de Implementação

1. **CSS faltante** — bloqueia todo o resto
2. **Admin Dashboard** — primeira visão do admin
3. **Admin Users** — aprovação é fluxo crítico
4. **Admin Matches** — gestão de partidas
5. **Admin Results** — registrar resultados
6. **Admin Players** — artilharia
7. **Admin Integration** — sync automático
8. **Admin Settings** — configurações
9. **Member Dashboard** — card "próximos jogos"
10. **Seed routine** — dados iniciais
