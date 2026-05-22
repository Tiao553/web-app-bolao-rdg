# Identidade Visual — Bolão Copa RDG

> Design system completo do Bolão Copa RDG. Referência canônica para qualquer decisão de UI/UX.

---

## Visão Geral

| Atributo | Valor |
|---|---|
| **Stack de UI** | Mantine UI v7 + Next.js 15 App Router |
| **Estilo de referência** | [Archlify](https://www.archlify.com/) — dark quase preto, acento neon, split workspace, score gauge |
| **Cor primária** | `#F97316` — laranja holandês (Dutch orange) |
| **Modo** | Dark only |
| **Tipografia** | Inter (body/UI), Fira Code (monospace/badges/dados) |
| **Background** | `#09090B` — mais escuro que o Mantine dark default |

---

## Referência Visual: Padrão Archlify

O Archlify usa verde neon como acento sobre fundo dark quase preto. Adotamos a mesma linguagem visual — dark, limpo, técnico, gamificado — trocando o verde pelo **laranja holandês `#F97316`**.

### Padrões adotados do Archlify

| Padrão Archlify | No RDG | Componente |
|---|---|---|
| Top nav: logo + links + avatar | Header com badge RDG + nav links + avatar do participante | `AppShell.Header` |
| Split workspace: painel lateral + área principal | Sidebar de rodadas + MatchCards | `AppShell + Navbar` |
| Tag cloud de categorias | Tags de rodadas e fases do torneio | `TagCloud` |
| Score circular (8.5/10) | Pontuação do participante com total possível | `ScoreGauge` |
| Dimension bars (Confiabilidade · 30% · 8.5) | Breakdown por tipo de palpite (exato, resultado, bônus Brasil...) | `DimensionBars` |
| Nodes do diagrama de arquitetura | Cards de partida no bracket e na listagem de palpites | `MatchCard + BracketView` |
| Badges de avaliação (EXCELENTE) | StatusBadge (APROVADO / PENDENTE / BLOQUEADO / REJEITADO) | `StatusBadge` |

---

## Sistema de Cores

Definido via `createTheme()` do Mantine. O `primaryColor: 'rdg-orange'` injeta o laranja em todos os componentes automaticamente.

### Palette primária

```
rdg-orange[0]  #FFF7ED   ← tint mais claro
rdg-orange[1]  #FFEDD5
rdg-orange[2]  #FED7AA
rdg-orange[3]  #FDBA74
rdg-orange[4]  #FB923C
rdg-orange[5]  #F97316   ← PRIMARY — botões, ativo, pontos, acento
rdg-orange[6]  #EA580C   ← hover / pressed
rdg-orange[7]  #C2410C
rdg-orange[8]  #9A3412
rdg-orange[9]  #7C2D12   ← shade mais escuro
```

### Backgrounds (progressão de profundidade)

```
--rdg-bg:   #09090B   ← fundo da página (mais escuro que Mantine default)
--rdg-s0:   #0F0F12   ← AppShell background
--rdg-s1:   #141418   ← Cards, Navbar
--rdg-s2:   #1A1A1F   ← Card headers, Modals, inputs focus
--rdg-s3:   #222228   ← Hover states, selected items
--rdg-bd:   #27272D   ← Bordas padrão
--rdg-bd2:  #33333B   ← Bordas em hover
```

### Texto

```
--rdg-tx:   #E8E8EA   ← texto principal
--rdg-tx2:  #71717A   ← texto secundário / labels / captions
--rdg-tx3:  #3F3F47   ← texto muted / placeholders / disabled
```

### Semânticas de estado

```
Verde    #22C55E   ← APROVADO / palpite correto / janela aberta
Âmbar    #F59E0B   ← PENDENTE / atenção
Vermelho #F43F5E   ← REJEITADO / BLOQUEADO / palpite errado
```

### Semânticas de ranking

```
Ouro     #EAB308   ← 1° lugar
Prata    #94A3B8   ← 2° lugar
Bronze   #B45309   ← 3° lugar
```

---

## Tipografia

### Fontes

| Uso | Família | Peso | Observação |
|---|---|---|---|
| Corpo / UI geral | Inter | 400, 500, 600, 700 | `fontFamily` principal do Mantine |
| Dados / Badges / Labels técnicos | Fira Code | 400, 500 | Monospace para números, codes, rotas |

### Hierarquia de textos

```
h1  — 32-36px, fw 700, tracking -0.02em  → Títulos de página
h2  — 24px,    fw 600                     → Seção headers
h3  — 18px,    fw 600                     → Card titles
body — 14px,   fw 400,  lh 1.65          → Texto corrido
sm   — 13px,   fw 400                    → Captions, helpers
xs   — 12px,   fw 500, monospace         → Badges, tags, labels técnicos
```

### Regra: monospace para dados

Qualquer número que representa **dado do jogo** (pontos, placar, posição) usa Fira Code:
- Pontuação no ranking: `127 pts` → Fira Code
- Placar no MatchCard: `2 × 1` → Fira Code
- Posição: `#01` → Fira Code
- Timestamp / datas de fechamento: Fira Code

---

## Componentes

### 1. `AppShell` (layout principal)

Wrapper de layout Mantine. Presente em todas as telas autenticadas.

```
┌─────────────────────────────────────────────┐
│  TopBar: [RDG badge] [Dashboard Palpites Ranking Explore] [Avatar]  │
├─────────────────────────────────────────────┤
│  Navbar (desktop) │  Conteúdo principal      │
│  ─ Dashboard      │                          │
│  ─ Palpites       │                          │
│  ─ Ranking        │                          │
│  ─ Explore        │                          │
└─────────────────────────────────────────────┘

Mobile: Header com Burger → Drawer com os mesmos NavLink items.
```

**Arquivo:** `app/src/components/layout/app-shell.tsx`
**Mantine:** `AppShell`, `AppShell.Header`, `AppShell.Navbar`, `Burger`, `NavLink`

---

### 2. `BrandLogo`

Badge laranja com "RDG" + nome do bolão. Mesma posição do logo Archlify no canto esquerdo do header.

```
[RDG]  Copa RDG
       REI DO GADO
```

Variantes: `sm` (no header), `lg` (na tela de login).

**Arquivo:** `app/src/components/brand/brand-logo.tsx`
**Mantine:** `Group`, `Box`, `Text`

---

### 3. `StatusBadge`

Wrapper fino sobre `Badge` do Mantine. 4 variantes mapeando `accessStatus` do backend.

| Status | Cor | Label |
|---|---|---|
| `APPROVED` | green | Aprovado |
| `PENDING` | yellow | Pendente |
| `REJECTED` | red | Rejeitado |
| `BLOCKED` | gray | Bloqueado |

```tsx
<StatusBadge status={session.accessStatus} />
```

**Arquivo:** `app/src/components/ui/status-badge.tsx`
**Mantine:** `Badge` (color + variant="light")

---

### 4. `ScoreGauge`

Gauge circular SVG estilo Archlify. Mostra pontuação do participante atual.

```
    ╭───╮
   │ 127 │   Pontuação Geral
   │ /200│   2° lugar
    ╰───╯
```

- Anel SVG com `stroke-dashoffset` calculado via `score / max`
- Cor do anel: `--mantine-color-rdg-orange-5`
- Fundo do anel: `--mantine-color-dark-4`
- Client Component (SVG inline requer hidratação)

**Arquivo:** `app/src/components/ui/score-gauge.tsx`
**Mantine:** `Paper`, `Text`, `Group`

---

### 5. `DimensionBars`

Breakdown de pontos por categoria de palpite. Inspirado no painel "Detalhamento por Dimensão" do Archlify.

```
Acertos exatos    ████████░░  82
Acertos resultado █████░░░░░  24
Bônus Brasil      ███████░░░  14
Campeão           ███░░░░░░░   7
```

**Arquivo:** `app/src/components/ui/dimension-bars.tsx`
**Mantine:** `Progress`, `Group`, `Text`, `Stack`

---

### 6. `TagCloud`

Filtro interativo de rodadas e fases do torneio. Tag ativa em laranja, inativas com borda sutil.

```
[Todos ●]  [Grupo A]  [Grupo B]  [Grupo C]  [Oitavas]  [Quartas]  [Semi]  [Final]
```

- Client Component com estado de tag ativa
- `onChange` callback para filtrar MatchCards
- Tags inativas: `variant="outline"` cor `dark`
- Tag ativa: `variant="light"` cor `rdg-orange`

**Arquivo:** `app/src/components/ui/tag-cloud.tsx`
**Mantine:** `Badge` (clicável), `Group`

---

### 7. `MatchCard`

Card de partida. Usado em `/predictions` e `/explore`.

```
┌─────────────────────────────┐
│  GRUPO A · RODADA 1          │
│                              │
│  🇧🇷 Brasil  [2] × [1]  🇦🇷 Argentina  │
│                              │
│  ● Janela aberta             │
└─────────────────────────────┘
```

**Props:**
- `match` — dados da partida (times, rodada, fase)
- `prediction` — palpite atual do usuário (opcional)
- `locked` — boolean vindo do backend via `isPredictionLocked(session)`
- `result` — `'exact' | 'correct' | 'wrong' | null` (após resultado oficial)

**Bordas por resultado:**
- Sem resultado: `border-color: dark.4`
- Exato: `border-color: green`
- Resultado correto: `border-color: yellow`
- Errado: `border-color: red`

**Arquivo:** `app/src/components/match/match-card.tsx`
**Mantine:** `Card`, `NumberInput`, `Badge`, `Group`, `Text`

---

### 8. `LeaderboardTable`

Tabela de ranking estilo Archlify. Pódio top-3 com fundos coloridos.

```
  Participante          Pts
1 [JK] João K.          127   ← fundo dourado sutil
2 [MA] Mari A.          114   ← fundo prateado sutil
3 [RS] Rafa S.           98   ← fundo bronze sutil
4 [TM] Tiago M.          87   ← linha do usuário destacada em laranja
5 [AB] Ana B.            76
```

**Props:**
- `rows` — array de participantes com posição, nome, pontos
- `currentUserId` — para destacar a linha do usuário logado

**Arquivo:** `app/src/components/ranking/leaderboard-table.tsx`
**Mantine:** `Table`, `Avatar`, `Badge`, `Text`, `Group`

---

### 9. `BracketView`

Visualização do mata-mata. Slots TBD em laranja pulsante (`animate-pulse` via CSS Mantine).

**Arquivo:** `app/src/components/bracket/bracket-view.tsx`
**Mantine:** `Paper`, `Stack`, `Group`, `Text`, `Skeleton`

---

## Mapeamento de Telas

### `/login`

**Layout:** `Center` full-screen, fundo `#09090B`, `BrandLogo` tamanho lg no topo.

```
┌─────────────────────────────────────────────┐
│                                              │
│              [RDG]  Copa RDG                 │
│                                              │
│  ┌──────────────┐  ┌──────────────┐         │
│  │    Entrar     │  │ Criar conta  │         │
│  │ E-mail       │  │ Nome         │         │
│  │ Senha        │  │ E-mail       │         │
│  │ [Entrar]     │  │ Senha        │         │
│  └──────────────┘  │ [Criar conta]│         │
│                     └──────────────┘         │
└─────────────────────────────────────────────┘
```

**Mantine:** `Center`, `Stack`, `SimpleGrid cols={base:1, sm:2}`, `Card`, `TextInput`, `PasswordInput`, `Button`

---

### `/waiting`

**Layout:** `Center` full-screen. Card único centrado com StatusBadge animado.

**Variações por estado:**
- `PENDING` → badge âmbar + "Aguardando aprovação"
- `REJECTED` → badge vermelho + "Solicitação não aprovada"
- `BLOCKED` → badge cinza + "Conta bloqueada"

**Mantine:** `Center`, `Card`, `Stack`, `StatusBadge`, `Text`, `Anchor`

---

### `/dashboard`

**Layout:** AppShell + conteúdo em `Stack`.

```
┌─ Dashboard ──────────────────────────────────┐
│                                              │
│  ╭─────╮  Pontuação Geral   [Acertos exatos ████ 82]  │
│  │ 127 │  2° lugar          [Resultado     ████ 24]  │
│  │ /200│                    [Bônus Brasil  ████ 14]  │
│  ╰─────╯                    [Campeão/artil ███   7]  │
│                                              │
│  [→ Palpites]  [→ Ranking]  [→ Explore]     │
└──────────────────────────────────────────────┘
```

**Mantine:** `Stack`, `SimpleGrid`, `ScoreGauge`, `DimensionBars`, `Paper`, `Anchor`

---

### `/predictions`

**Layout:** AppShell + split workspace.

```
┌─ Sidebar ──┬─ Conteúdo ────────────────────┐
│ RODADAS    │  [Todos●] [Grupo A] [Oitavas]  │
│ ─ Grupo A  │                               │
│ ─ Grupo B  │  ┌─────────────────────────┐  │
│ ─ Grupo C  │  │ Grupo A · Rodada 1       │  │
│ ─ Oitavas  │  │ 🇧🇷 [2] × [1] 🇦🇷        │  │
│ ─ Quartas  │  └─────────────────────────┘  │
│ ESPECIAIS  │  ┌─────────────────────────┐  │
│ ─ Campeão  │  │ Grupo A · Rodada 2       │  │
│ ─ Artilh.  │  │ 🇩🇪 [1] × [0] 🇫🇷        │  │
└────────────┴──└─────────────────────────┘──┘
```

**Mantine:** `AppShell` (com Navbar estendida), `TagCloud`, `Stack`, `MatchCard`, `Select` (campeão), `TextInput` (artilheiro)

---

### `/ranking`

**Layout:** AppShell + `Stack`.

```
┌─ Ranking ────────────────────────────────────┐
│                                              │
│  ╭─────╮  Pontuação Geral   [Acertos exatos ████ 82]  │
│  │ 127 │  2° lugar          [Resultado     ████ 24]  │
│  ╰─────╯                                    │
│                                              │
│  1  [JK]  João K.          127              │
│  2  [MA]  Mari A.          114              │
│  3  [RS]  Rafa S.           98              │
│  4► [TM]  Tiago M.          87  ← você     │
└──────────────────────────────────────────────┘
```

**Mantine:** `Stack`, `ScoreGauge`, `DimensionBars`, `LeaderboardTable`

---

### `/explore`

**Layout:** igual `/ranking` com `Overlay` Mantine quando `exploreReleaseAt` ainda não chegou.

**Lock state:**
```
┌─ Explore ─────────────────────────────────┐
│                                            │
│    🔒  Explore ainda não liberado          │
│        Disponível a partir de 15/06        │
│                                            │
│  [conteúdo desfocado por trás do overlay] │
└────────────────────────────────────────────┘
```

**Mantine:** `Overlay`, `Center`, `Stack`, `Text`, `ThemeIcon`

---

## Regras de Implementação

### Server vs Client Components

> **Regra crítica:** Todas as páginas existentes são Server Components. Nunca adicionar `'use client'` em arquivos de página.

| Componente | Tipo | Motivo |
|---|---|---|
| `AppShell` | Client | `useDisclosure` para burger/navbar |
| `ScoreGauge` | Client | SVG inline com cálculo de offset |
| `TagCloud` | Client | Estado de tag ativa |
| `MatchCard` | Client | `NumberInput` requer interação |
| `LeaderboardTable` | Server | Apenas renderização de dados |
| `StatusBadge` | Server | Sem interação |
| `DimensionBars` | Server | Apenas renderização de dados |
| `BrandLogo` | Server | Sem interação |

### PostCSS (obrigatório para Mantine)

Criar `app/postcss.config.cjs`:

```js
module.exports = {
  plugins: {
    'postcss-preset-mantine': {},
    'postcss-simple-vars': {
      variables: {
        'mantine-breakpoint-xs': '36em',
        'mantine-breakpoint-sm': '48em',
        'mantine-breakpoint-md': '62em',
        'mantine-breakpoint-lg': '75em',
        'mantine-breakpoint-xl': '88em',
      },
    },
  },
};
```

### Background mais escuro que o Mantine default

O Mantine dark[9] padrão é `#141517`. O RDG usa `#09090B` (igual ao Archlify).

Forçar em `globals.css`:

```css
@import '@mantine/core/styles.css';

:root {
  --mantine-color-body: #09090B;
}

body {
  background-color: #09090B;
}
```

### MantineProvider no layout

```tsx
// app/src/app/layout.tsx
import '@mantine/core/styles.css';
import './globals.css';
import { ColorSchemeScript, MantineProvider } from '@mantine/core';
import { theme } from '../lib/theme';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <head>
        <ColorSchemeScript defaultColorScheme="dark" />
      </head>
      <body>
        <MantineProvider theme={theme} defaultColorScheme="dark">
          {children}
        </MantineProvider>
      </body>
    </html>
  );
}
```

---

## Dependências

```json
{
  "@mantine/core": "^7.x",
  "@mantine/hooks": "^7.x",
  "@mantine/form": "^7.x",
  "@mantine/notifications": "^7.x",
  "postcss": "^8.x",
  "postcss-preset-mantine": "^1.x",
  "postcss-simple-vars": "^7.x"
}
```

---

## Decisões Arquiteturais de UI

### Por que Mantine e não Tailwind/shadcn?

- Componentes ricos prontos para dados: `Table`, `NumberInput`, `Progress`, `Overlay`, `AppShell`, `Drawer`
- Dark mode nativo via CSS variables sem configuração extra
- `AppShell` cobre o split workspace do padrão Archlify out-of-the-box
- Sem necessidade de Tailwind — estilos via props Mantine e CSS Modules pontual
- Bundle menor que Ant Design, mais rico que Chakra para este caso de uso

### Por que Inter e não Barlow Condensed?

Inter é a fonte padrão do Archlify. O padrão visual de referência usa tipografia clean, sem condensed. Barlow Condensed foi descartado para manter fidelidade ao estilo de referência.

### Por que `#09090B` e não o dark default do Mantine?

O Archlify usa fundo quase preto puro. O Mantine dark[9] (`#141517`) é visualmente mais cinza. Sobrescrevemos `--mantine-color-body` para garantir o mesmo contraste e drama visual da referência.

---

*Documento criado em 2026-05-21. Referência: [archlify.com](https://www.archlify.com/)*
