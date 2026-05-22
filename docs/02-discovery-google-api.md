# Discovery — Integração com Google API para Jogos e Resultados

## 1. Objetivo

Investigar como consumir dados de jogos e resultados da Copa do Mundo via **Google API**, identificar a melhor fonte de dados disponível, mapear os campos necessários para o bolão e definir a estratégia de sincronização.

---

## 2. Contexto

O produto exige que a aplicação importe automaticamente:

- Partidas (datas, horários, seleções, fases)
- Resultados oficiais
- Gols por jogador
- Assistências por jogador
- Ranking de artilheiros

A integração deve ser automática (via job agendado), mas o administrador sempre poderá corrigir manualmente qualquer dado importado incorretamente.

---

## 3. Opções de API identificadas

### 3.1 Google Cloud — Structured Data (Knowledge Graph / Search)

**O Google não oferece uma API oficial de futebol** com dados estruturados e atualizados em tempo real, como placar de partidas e artilheiros.

O que existe no ecossistema Google:
- **Google Knowledge Graph API** — retorna entidades (times, competições), mas **não inclui placar, resultados ou estatísticas de jogadores**.
- **Google Custom Search API** — busca em texto, não serve para dados estruturados.
- **Google Sheets API** — pode servir como camada intermediária se os dados forem mantidos numa planilha.

**Conclusão:** Google não tem API nativa e gratuita para dados de partidas de futebol ao vivo ou históricos.

---

### 3.2 Alternativa principal recomendada — API-Football (via RapidAPI)

A fonte mais robusta disponível hoje para dados de Copa do Mundo é a **API-Football**, acessível via RapidAPI.

**Endpoint base:**
```
https://api-football-v1.p.rapidapi.com/v3/
```

**Plano gratuito:** 100 requisições/dia (suficiente para MVP em fase de testes).

**Campos disponíveis:**

| Recurso          | Endpoint                            | Dados retornados                                               |
| ---------------- | ----------------------------------- | -------------------------------------------------------------- |
| Competições      | `/leagues?name=World+Cup`           | id, nome, temporada, rodadas                                   |
| Times/Seleções   | `/teams?league=1&season=2026`       | id, nome, código, bandeira                                     |
| Jogos            | `/fixtures?league=1&season=2026`    | id, data, horário, times, placar, status, fase                 |
| Resultado ao vivo| `/fixtures?live=all`                | placar atual, minuto, status                                   |
| Jogadores/Gols   | `/players/topscorers?league=1&season=2026` | jogador, time, gols, assistências                    |
| Rodadas          | `/fixtures/rounds?league=1&season=2026`    | lista de fases/rodadas                               |

**Headers obrigatórios:**
```http
X-RapidAPI-Key: {API_KEY}
X-RapidAPI-Host: api-football-v1.p.rapidapi.com
```

---

### 3.3 Alternativa 2 — TheSportsDB

**Endpoint base:**
```
https://www.thesportsdb.com/api/v1/json/{API_KEY}/
```

**Plano gratuito:** disponível com limitações.

| Recurso          | Endpoint                                              |
| ---------------- | ----------------------------------------------------- |
| Liga              | `/search_all_leagues.php?s=Soccer`                   |
| Eventos (jogos)   | `/eventsseason.php?id={league_id}&s={season}`        |
| Resultado ao vivo | `/eventslive.php?l={league_id}` (plano pago)         |
| Jogadores         | `/searchplayers.php?t={team_name}`                   |

**Limitação:** artilheiros e assistências **não estão disponíveis** no plano gratuito.

---

### 3.4 Alternativa 3 — OpenLigaDB

**Endpoint base:**
```
https://api.openligadb.de/
```

Focado em ligas europeias. Suporte à Copa do Mundo é limitado e sem garantia de dados de artilheiros.

**Não recomendado** para este projeto.

---

### 3.5 Integração via Google Sheets (abordagem híbrida)

Caso nenhuma API externa satisfaça, o administrador pode manter os dados em uma **Google Planilha**, e o sistema consome via **Google Sheets API v4**.

**Casos de uso:**
- Admin importa dados oficiais manualmente numa planilha.
- Sistema lê a planilha via job agendado.
- Dados são sincronizados para o banco da aplicação.

**Vantagens:**
- Total controle sobre os dados.
- Admin pode corrigir diretamente na planilha.
- Fácil integração com Next.js via Google Sheets API.

**Desvantagens:**
- Dados não são atualizados automaticamente.
- Depende de intervenção humana para inserir resultados.

---

## 4. Decisão recomendada

```
Fonte primária:     API-Football (RapidAPI) para dados automáticos
Fonte secundária:   Google Sheets API para override manual do admin
Fallback:           Cadastro manual direto no painel admin da aplicação
```

---

## 5. Mapeamento de campos — API-Football → Modelo de dados

### 5.1 Partidas (`/fixtures`)

**Resposta da API:**
```json
{
  "fixture": {
    "id": 867946,
    "date": "2026-06-12T15:00:00+00:00",
    "status": { "short": "FT", "long": "Match Finished" }
  },
  "league": {
    "id": 1,
    "name": "World Cup",
    "round": "Group Stage - 1"
  },
  "teams": {
    "home": { "id": 9, "name": "Spain", "logo": "..." },
    "away": { "id": 21, "name": "Germany", "logo": "..." }
  },
  "goals": {
    "home": 2,
    "away": 1
  }
}
```

**Mapeamento para `Match`:**

| Campo API                        | Campo Match              | Observação                              |
| -------------------------------- | ------------------------ | --------------------------------------- |
| `fixture.id`                     | `externalId`             | id externo para deduplicação            |
| `fixture.date`                   | `startsAt`               | converter para UTC                      |
| `fixture.status.short`           | `status`                 | `NS→SCHEDULED`, `FT→FINISHED`, etc.     |
| `league.round`                   | `phaseId`                | mapear para Phase via `round` string    |
| `teams.home.id`                  | `homeTeamId`             | id externo → id interno via lookup      |
| `teams.away.id`                  | `awayTeamId`             | id externo → id interno via lookup      |
| `goals.home`                     | `homeScore`              | null se não iniciou                     |
| `goals.away`                     | `awayScore`              | null se não iniciou                     |

**Status mapping:**

| API status | Match.status  |
| ---------- | ------------- |
| `NS`       | `SCHEDULED`   |
| `1H`, `HT`, `2H`, `ET`, `P` | `LIVE` |
| `FT`, `AET`, `PEN` | `FINISHED` |
| `PST`, `CANC`, `ABD` | `CANCELLED` |

---

### 5.2 Artilheiros (`/players/topscorers`)

**Resposta da API:**
```json
{
  "player": {
    "id": 276,
    "name": "K. Mbappe",
    "nationality": "France"
  },
  "statistics": [{
    "team": { "id": 2, "name": "France" },
    "goals": { "total": 8, "assists": 3 },
    "games": { "appearences": 7 }
  }]
}
```

**Mapeamento para `PlayerTournamentStats`:**

| Campo API                          | Campo PlayerTournamentStats | Observação                     |
| ---------------------------------- | --------------------------- | ------------------------------ |
| `player.id`                        | `player.externalId`         | lookup/upsert em Player        |
| `player.name`                      | `player.name`               |                                |
| `statistics[0].team.id`            | `player.teamId`             | lookup/upsert em Team          |
| `statistics[0].goals.total`        | `goals`                     |                                |
| `statistics[0].goals.assists`      | `assists`                   |                                |

---

### 5.3 Times/Seleções (`/teams`)

**Resposta da API:**
```json
{
  "team": {
    "id": 6,
    "name": "Brazil",
    "code": "BRA",
    "logo": "https://media.api-sports.io/football/teams/6.png"
  },
  "venue": { ... }
}
```

**Mapeamento para `Team`:**

| Campo API     | Campo Team              | Observação                             |
| ------------- | ----------------------- | -------------------------------------- |
| `team.id`     | `externalId`            | para deduplicação                      |
| `team.name`   | `name`                  |                                        |
| `team.code`   | `code`                  |                                        |
| `team.logo`   | `flagUrl`               |                                        |
| —             | `isSpecialMultiplierTeam` | `true` se `team.name === "Brazil"`   |
| —             | `multiplierValue`       | `2` se Brazil, `1` caso contrário      |

---

## 6. Estratégia de sincronização

### 6.1 Estratégia de sincronização — trigger pós-jogo

A sincronização **não é contínua**. Ela é disparada **3 vezes por dia**, sempre logo após o término previsto de cada jogo.

A Copa do Mundo 2026 terá no máximo 4 jogos por dia na fase de grupos. Cada disparo consome 4 requisições (placar, eventos, artilheiros, classificação).

**Consumo calculado:**

| Cenário              | Jogos/dia | Req/disparo | Total req/dia |
| -------------------- | --------: | ----------: | ------------: |
| Dia típico (3 jogos) |         3 |           4 |            12 |
| Dia cheio (4 jogos)  |         4 |           4 |            16 |
| Mata-mata (2 jogos)  |         2 |           4 |             8 |
| **Limite free plan** |         — |           — |       **100** |

**Conclusão: o plano gratuito (100 req/dia) é suficiente com folga de ~84 req no pior dia.**

```
┌─────────────────────────┬──────────────────────────────┬─────────────────────────────────┐
│ Job                     │ Quando dispara               │ Ação                            │
├─────────────────────────┼──────────────────────────────┼─────────────────────────────────┤
│ sync-after-match        │ Cron ~30min após startsAt    │ GET /fixtures?id={id}           │
│                         │ de cada partida*             │ GET /fixtures/events?fixture={} │
│                         │                              │ GET /players/topscorers         │
│                         │                              │ GET /standings                  │
│                         │                              │ → recalcular pontos e ranking   │
├─────────────────────────┼──────────────────────────────┼─────────────────────────────────┤
│ sync-teams (seed only)  │ 1x manual (carga inicial)    │ Upsert times/seleções           │
│ sync-fixtures (seed)    │ 1x manual (carga inicial)    │ Upsert calendário de jogos      │
└─────────────────────────┴──────────────────────────────┴─────────────────────────────────┘

* O cron é calculado como: startsAt + 115 minutos (90min de jogo + 25min de acréscimos/intervalo).
  Se a partida entrar em prorrogação (mata-mata), o admin pode disparar manualmente.
  O job verifica se fixture.status.short === "FT" | "AET" | "PEN" antes de processar.
  Se ainda não finalizado, registra no SyncLog e aguarda o próximo ciclo.
```

### 6.2 Fluxo de upsert com proteção de override manual

```
Para cada registro recebido da API:
  ↓
  Buscar no banco pelo externalId
  ↓
  Se não existe → inserir com source = "GOOGLE_API"
  ↓
  Se existe e hasManualOverride = false → atualizar campos com dados da API
  ↓
  Se existe e hasManualOverride = true → NÃO sobrescrever
    → Registrar no SyncLog que o campo foi ignorado por override manual
```

---

## 7. Autenticação e configuração

### 7.1 Variáveis de ambiente necessárias

```env
# API-Football via RapidAPI
RAPIDAPI_KEY=your_key_here
RAPIDAPI_HOST=api-football-v1.p.rapidapi.com

# IDs da competição
WORLD_CUP_LEAGUE_ID=1
WORLD_CUP_SEASON=2026

# Google Sheets (opcional, para fallback manual)
GOOGLE_SHEETS_CLIENT_EMAIL=...
GOOGLE_SHEETS_PRIVATE_KEY=...
GOOGLE_SPREADSHEET_ID=...
```

### 7.2 Obter chave da API-Football

1. Acessar [https://rapidapi.com/api-sports/api/api-football](https://rapidapi.com/api-sports/api/api-football)
2. Criar conta gratuita.
3. Subscrever ao plano Basic (gratuito: 100 req/dia).
4. Copiar `X-RapidAPI-Key` do dashboard.

---

## 8. Implementação — esboço de código

### 8.1 Serviço base

```ts
// src/services/google-api/football-client.ts

const BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"

async function apiFetch<T>(path: string, params: Record<string, string>): Promise<T> {
  const url = new URL(`${BASE_URL}${path}`)
  Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v))

  const res = await fetch(url.toString(), {
    headers: {
      "X-RapidAPI-Key": process.env.RAPIDAPI_KEY!,
      "X-RapidAPI-Host": process.env.RAPIDAPI_HOST!,
    },
    next: { revalidate: 0 }, // sem cache — dados ao vivo
  })

  if (!res.ok) throw new Error(`API-Football error: ${res.status} ${res.statusText}`)

  const json = await res.json()
  return json.response as T
}

export const footballApi = {
  getFixtures: (leagueId: string, season: string) =>
    apiFetch("/fixtures", { league: leagueId, season }),

  getLiveFixtures: () =>
    apiFetch("/fixtures", { live: "all" }),

  getTeams: (leagueId: string, season: string) =>
    apiFetch("/teams", { league: leagueId, season }),

  getTopScorers: (leagueId: string, season: string) =>
    apiFetch("/players/topscorers", { league: leagueId, season }),

  getRounds: (leagueId: string, season: string) =>
    apiFetch("/fixtures/rounds", { league: leagueId, season }),
}
```

### 8.2 Serviço de sincronização de partidas

```ts
// src/services/sync/sync-fixtures.ts

import { footballApi } from "@/services/google-api/football-client"
import { prisma } from "@/lib/prisma"
import { mapFixtureStatus } from "@/services/sync/mappers"

export async function syncFixtures() {
  const leagueId = process.env.WORLD_CUP_LEAGUE_ID!
  const season = process.env.WORLD_CUP_SEASON!

  const fixtures = await footballApi.getFixtures(leagueId, season)

  for (const item of fixtures) {
    const externalId = String(item.fixture.id)

    const existing = await prisma.match.findUnique({ where: { externalId } })

    if (existing?.hasManualOverride) {
      await prisma.syncLog.create({
        data: {
          provider: "GOOGLE_API",
          status: "SUCCESS",
          message: `Match ${externalId} skipped — manual override active`,
          executedAt: new Date(),
        },
      })
      continue
    }

    const homeTeam = await prisma.team.findUnique({
      where: { externalId: String(item.teams.home.id) },
    })
    const awayTeam = await prisma.team.findUnique({
      where: { externalId: String(item.teams.away.id) },
    })

    if (!homeTeam || !awayTeam) continue // times ainda não sincronizados

    await prisma.match.upsert({
      where: { externalId },
      update: {
        homeScore: item.goals.home,
        awayScore: item.goals.away,
        status: mapFixtureStatus(item.fixture.status.short),
        startsAt: new Date(item.fixture.date),
        source: "GOOGLE_API",
      },
      create: {
        externalId,
        homeTeamId: homeTeam.id,
        awayTeamId: awayTeam.id,
        homeScore: item.goals.home,
        awayScore: item.goals.away,
        status: mapFixtureStatus(item.fixture.status.short),
        startsAt: new Date(item.fixture.date),
        source: "GOOGLE_API",
        hasManualOverride: false,
        hasSpecialMultiplier: homeTeam.isSpecialMultiplierTeam || awayTeam.isSpecialMultiplierTeam,
        multiplierValue: homeTeam.isSpecialMultiplierTeam || awayTeam.isSpecialMultiplierTeam ? 2 : 1,
        phaseId: await resolvePhaseId(item.league.round),
      },
    })
  }
}

function mapFixtureStatus(short: string): "SCHEDULED" | "LIVE" | "FINISHED" | "CANCELLED" {
  if (["NS"].includes(short)) return "SCHEDULED"
  if (["1H", "HT", "2H", "ET", "P", "BT"].includes(short)) return "LIVE"
  if (["FT", "AET", "PEN"].includes(short)) return "FINISHED"
  return "CANCELLED"
}
```

### 8.3 Rota de API para trigger manual

```ts
// src/app/api/admin/sync/route.ts

import { syncFixtures } from "@/services/sync/sync-fixtures"
import { syncTopScorers } from "@/services/sync/sync-topscorers"
import { syncTeams } from "@/services/sync/sync-teams"
import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth"

export async function POST(req: Request) {
  const session = await getServerSession(authOptions)

  if (!session || session.user.role !== "ADMIN") {
    return Response.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { type } = await req.json()

  try {
    if (type === "teams")      await syncTeams()
    if (type === "fixtures")   await syncFixtures()
    if (type === "topscorers") await syncTopScorers()

    return Response.json({ success: true })
  } catch (error) {
    return Response.json({ error: String(error) }, { status: 500 })
  }
}
```

### 8.4 Vercel Cron Jobs — trigger pós-jogo

Os jogos começam em horários variados (ver `group-stage-matches.json`). A estratégia é
agendar um cron ~115 minutos após o horário de início de cada jogo. O job verifica se
o status da partida já é `FT | AET | PEN` antes de processar — se ainda não, registra
no SyncLog e encerra sem consumir requisições desnecessárias.

Como a Copa tem no máximo 4 jogos/dia e cada disparo usa 4 requisições, o consumo máximo
é de **16 req/dia**, dentro do plano gratuito (100 req/dia) com folga de 84 req.

```json
// vercel.json
{
  "crons": [
    {
      "path": "/api/cron/sync-after-match",
      "schedule": "45 21 * * *",
      "_comment": "Jogo 1 do dia: início ~20:00 UTC + 105min = 21:45 UTC"
    },
    {
      "path": "/api/cron/sync-after-match",
      "schedule": "45 0 * * *",
      "_comment": "Jogo 2 do dia: início ~23:00 UTC + 105min = 00:45 UTC"
    },
    {
      "path": "/api/cron/sync-after-match",
      "schedule": "45 3 * * *",
      "_comment": "Jogo 3 do dia: início ~02:00 UTC + 105min = 03:45 UTC"
    }
  ]
}
```

> **Nota:** Os horários acima são aproximados para a fase de grupos. O admin pode
> ajustar os crons no painel da Vercel conforme o calendário real avançar. No mata-mata,
> onde pode haver prorrogação, o admin dispara o sync manualmente via POST `/api/admin/sync`.

```ts
// src/app/api/cron/sync-after-match/route.ts

import { syncAfterMatch } from "@/services/sync/sync-after-match"

export async function GET(req: Request) {
  const authHeader = req.headers.get("authorization")
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return Response.json({ error: "Unauthorized" }, { status: 401 })
  }

  // Busca no banco todas as partidas cujo startsAt <= agora - 105min e status !== FINISHED
  await syncAfterMatch()
  return Response.json({ success: true })
}
```

---

## 9. Tratamento de erros e resiliência

```
Cenário                              Ação
────────────────────────────────────────────────────────────
API retorna 429 (rate limit)      → Registrar no SyncLog com status ERROR, tentar no próximo ciclo
API retorna 5xx                   → Registrar no SyncLog, não interromper outros jobs
Time não encontrado no banco      → Skip da partida, registrar aviso no SyncLog
Campo com override manual         → Skip do campo, registrar no SyncLog
Prisma error                      → Rollback, registrar no SyncLog com stack trace
```

---

## 10. Plano de evolução pós-MVP

| Fase        | Melhoria                                                                 |
| ----------- | ------------------------------------------------------------------------ |
| MVP         | 3 syncs/dia pós-jogo, trigger manual pelo admin, override protegido      |
| V1.1        | Google Sheets como fallback editorial gerenciado pelo admin              |
| V2          | Migrar para API oficial FIFA se disponível, multi-torneio                |

---

## 11. Estimativa de custos (API-Football)

| Plano    | Requisições/dia | Preço/mês | Consumo real (max 4 jogos/dia × 4 req) | Viável? |
| -------- | --------------- | --------- | --------------------------------------- | ------- |
| Free     | 100             | $0        | 16 req/dia (84 de folga)                | **Sim** |
| Basic    | 7.500           | $10       | —                                       | Sim     |
| Standard | 30.000          | $30       | —                                       | Não necessário |

Com a estratégia de 3 syncs/dia pós-jogo (4 req cada), o **plano Free cobre todo o torneio**
sem precisar de upgrade. O único momento que exigiria atenção seria se a Copa tivesse mais
de 25 jogos num único dia — o que não acontece no formato de 2026.

---

## 12. Resumo de decisões

| Decisão                            | Escolha                                     |
| ---------------------------------- | ------------------------------------------- |
| Fonte de dados primária            | API-Football via RapidAPI                   |
| Fonte de dados secundária/fallback | Google Sheets API (manual pelo admin)       |
| Frequência de sync padrão          | A cada 6 horas (Vercel Cron Job)            |
| Proteção de override manual        | `hasManualOverride = true` bloqueia o campo |
| Registro de auditoria              | SyncLog para cada execução                  |
| Trigger manual                     | POST `/api/admin/sync` com role ADMIN       |
| Autenticação do cron               | `CRON_SECRET` no header Authorization      |
