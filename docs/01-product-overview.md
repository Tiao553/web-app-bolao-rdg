# Bolão da Copa — Visão Geral do Produto

## 1. Objetivo

O objetivo do **Bolão da Copa** é criar uma aplicação web pessoal para bolão da Copa do Mundo, onde os usuários possam registrar palpites, acompanhar seus pontos, visualizar rankings e explorar os palpites dos demais participantes após o fechamento oficial dos palpites.

A aplicação deverá ser publicada na **Vercel** e terá integração automática via **Google API** para importar ou atualizar dados da competição, como partidas, datas, seleções, fases, resultados, jogadores, artilheiros e assistências, conforme a fonte configurada.

Além da integração automática, o sistema deverá permitir que o administrador corrija manualmente partidas, horários, seleções, jogadores, resultados oficiais, gols, assistências, campeão e artilheiro oficial caso algum dado importado esteja incorreto.

---

## 2. Premissas principais

- A aplicação será uma web app.
- O frontend será desenvolvido com **React**.
- A interface deverá utilizar componentes de um **UI Kit**, evitando componentes visuais feitos do zero.
- A aplicação será publicada na **Vercel**.
- A aplicação deverá ter autenticação de usuários.
- Qualquer pessoa poderá se cadastrar.
- Todo novo usuário deverá iniciar com status **pendente de aprovação**.
- Somente usuários aprovados pelo administrador poderão acessar o bolão, registrar palpites, aparecer no ranking e visualizar a área Explore.
- A aplicação deverá ter acesso administrativo.
- A Copa deverá considerar fase de **16 avos de final**, quando aplicável.
- O sistema deverá importar dados automaticamente via Google API.
- O administrador deverá conseguir alterar manualmente qualquer partida, horário, jogador, gol, assistência ou resultado incorreto.
- Jogos que envolvem o **Brasil** terão pontuação dobrada quando o usuário acertar o placar exato ou o resultado.
- Acertar o campeão da Copa vale **10 pontos**.
- Acertar o artilheiro da Copa vale **15 pontos**.
- Caso exista empate entre artilheiros, o critério de desempate será o número de assistências.
- Após o fechamento dos palpites, os usuários aprovados poderão visualizar os palpites dos outros participantes na área **Explore**.
- A liberação da área Explore será controlada por uma data e hora configurada pelo administrador.
- Usuários pendentes, rejeitados ou bloqueados não deverão influenciar pontuação, ranking ou estatísticas.

---

## 3. Público-alvo

## 3.1 Usuário comum

O usuário comum é o participante do bolão.

Ele poderá:

- Criar uma conta na aplicação.
- Aguardar aprovação do administrador.
- Acessar o bolão somente após aprovação.
- Registrar palpite de campeão.
- Registrar palpite de artilheiro.
- Registrar placares dos jogos.
- Visualizar seus próprios palpites.
- Visualizar seus pontos.
- Visualizar ranking geral.
- Visualizar resultados oficiais.
- Acompanhar o chaveamento da competição.
- Acessar a área Explore após o horário de liberação configurado pelo administrador.
- Ver os palpites dos outros usuários somente depois que os palpites estiverem fechados e o Explore estiver liberado.

---

## 3.2 Usuário pendente

O usuário pendente é aquele que criou conta, mas ainda não foi aprovado pelo administrador.

Ele poderá:

- Fazer login.
- Visualizar uma tela de aguardando aprovação.

Ele não poderá:

- Registrar palpites.
- Visualizar ranking.
- Acessar Explore.
- Ver palpites de outros usuários.
- Participar da pontuação.
- Influenciar estatísticas do bolão.

---

## 3.3 Administrador

O administrador é responsável por controlar a competição dentro da aplicação.

Ele poderá:

- Gerenciar usuários.
- Visualizar usuários pendentes.
- Aprovar usuários.
- Rejeitar usuários.
- Bloquear usuários.
- Reativar usuários bloqueados, se necessário.
- Gerenciar seleções.
- Gerenciar jogadores.
- Gerenciar fases.
- Gerenciar partidas.
- Importar partidas automaticamente via Google API.
- Atualizar resultados automaticamente via Google API.
- Corrigir manualmente partidas importadas incorretamente.
- Corrigir manualmente horários de jogos.
- Corrigir manualmente seleções de uma partida.
- Corrigir manualmente resultados oficiais.
- Corrigir manualmente gols de jogadores.
- Corrigir manualmente assistências de jogadores.
- Abrir ou fechar fases para palpites.
- Definir a data e hora de fechamento dos palpites.
- Definir a data e hora de liberação da área Explore.
- Recalcular pontuação.
- Definir campeão oficial.
- Definir artilheiro oficial.
- Configurar regras de pontuação.
- Configurar quais seleções possuem multiplicador especial de pontos.
- Visualizar logs de sincronização.

---

# 4. Funcionalidades principais

## 4.1 Cadastro e aprovação de usuários

Como medida de segurança e governança, qualquer pessoa poderá se cadastrar na aplicação, porém o acesso ao bolão não será liberado automaticamente.

Após o cadastro, o usuário ficará com status **pendente de aprovação** até que um administrador aprove sua participação.

Essa regra evita:

- Criação de múltiplas contas pela mesma pessoa.
- Entrada de usuários não autorizados.
- Participação de pessoas fora do grupo combinado.
- Problemas de governança no ranking.
- Manipulação indevida de palpites.

Fluxo esperado:

```text
Usuário realiza cadastro
  ↓
Conta fica pendente de aprovação
  ↓
Administrador revisa o cadastro
  ↓
Administrador aprova ou rejeita o usuário
  ↓
Somente usuários aprovados podem acessar o bolão e registrar palpites
````

Regras:

```text
Se o usuário estiver com status PENDING:
  pode fazer login, mas verá apenas uma tela de aguardando aprovação

Se o usuário estiver com status APPROVED:
  pode acessar o bolão normalmente

Se o usuário estiver com status REJECTED:
  não pode acessar o bolão

Se o usuário estiver com status BLOCKED:
  não pode acessar o bolão, mesmo que já tenha sido aprovado antes
```

---

## 4.2 Palpites iniciais

Antes dos palpites por partida, cada usuário aprovado deverá registrar:

* Campeão da Copa.
* Artilheiro da Copa.

Esses palpites deverão respeitar uma data e hora limite configurada pelo administrador.

Regra:

```text
Após o horário de fechamento dos palpites iniciais, o usuário não poderá mais alterar campeão nem artilheiro.
```

Pontuação:

| Palpite                      | Pontos |
| ---------------------------- | -----: |
| Acertar o campeão da Copa    |     10 |
| Acertar o artilheiro da Copa |     15 |

---

## 4.3 Regra do artilheiro com critério de assistências

O sistema deverá considerar o artilheiro oficial da Copa com base na quantidade de gols marcados.

Caso exista empate entre dois ou mais jogadores no número de gols, o sistema deverá usar o número de assistências como critério de desempate.

Regra:

```text
O artilheiro oficial será o jogador com mais gols na Copa.

Se dois ou mais jogadores tiverem o mesmo número de gols:
  vence como artilheiro o jogador com mais assistências entre os empatados.

Se ainda houver empate em gols e assistências:
  todos os jogadores ainda empatados serão considerados artilheiros válidos.
```

Exemplo:

| Jogador   | Gols | Assistências | Situação                          |
| --------- | ---: | -----------: | --------------------------------- |
| Jogador A |    6 |            2 | Artilheiro oficial                |
| Jogador B |    6 |            1 | Perde no critério de assistências |
| Jogador C |    5 |            4 | Não entra no empate de gols       |

Neste caso, apenas o **Jogador A** será considerado acerto para o palpite de artilheiro.

Exemplo com empate mantido:

| Jogador   | Gols | Assistências | Situação                          |
| --------- | ---: | -----------: | --------------------------------- |
| Jogador A |    6 |            2 | Artilheiro válido                 |
| Jogador B |    6 |            2 | Artilheiro válido                 |
| Jogador C |    6 |            1 | Perde no critério de assistências |

Neste caso, palpites no **Jogador A** ou no **Jogador B** deverão receber os pontos de artilheiro.

Pontuação:

```text
Se o usuário acertar o artilheiro oficial após aplicar o critério de assistências:
  recebe 15 pontos

Senão:
  recebe 0 pontos
```

---

## 4.4 Palpites por fase

O usuário aprovado deverá registrar os placares dos jogos por fase.

Fases previstas:

| Ordem | Fase                             |
| ----: | -------------------------------- |
|     1 | Palpites iniciais                |
|     2 | Fase de grupos — Primeira rodada |
|     3 | Fase de grupos — Segunda rodada  |
|     4 | Fase de grupos — Terceira rodada |
|     5 | 16 avos de final                 |
|     6 | Oitavas de final                 |
|     7 | Quartas de final                 |
|     8 | Semifinais                       |
|     9 | Disputa de terceiro lugar        |
|    10 | Final                            |

Para cada jogo, o usuário deverá informar:

* Gols do time A.
* Gols do time B.

O sistema deverá calcular automaticamente o resultado previsto:

* Vitória do time A.
* Vitória do time B.
* Empate.

---

## 4.5 Regra de pontuação por partida

Após o resultado oficial ser cadastrado ou importado, o sistema deverá calcular a pontuação dos usuários.

Pontuação padrão:

| Condição                            | Pontos |
| ----------------------------------- | -----: |
| Acertar o placar exato              |      3 |
| Acertar apenas o vencedor ou empate |      1 |
| Errar o resultado                   |      0 |

Regra importante:

```text
Se o usuário acertar o placar exato, ele recebe 3 pontos no total.
Não deve receber 1 + 3.
```

Exemplo:

Resultado oficial:

```text
Brasil 2 x 1 Alemanha
```

| Palpite               | Resultado              | Pontos base |
| --------------------- | ---------------------- | ----------: |
| Brasil 2 x 1 Alemanha | Acertou o placar exato |           3 |
| Brasil 1 x 0 Alemanha | Acertou o vencedor     |           1 |
| Brasil 1 x 1 Alemanha | Errou o resultado      |           0 |
| Alemanha 2 x 1 Brasil | Errou o resultado      |           0 |

---

## 4.6 Regra especial para jogos do Brasil

Jogos que envolvem o **Brasil** terão pontuação dobrada quando o usuário acertar o placar exato ou acertar o resultado da partida.

Essa regra vale para qualquer partida em que o Brasil seja um dos times, seja como mandante ou visitante.

Pontuação em jogos do Brasil:

| Condição                            | Pontos padrão | Pontos em jogos do Brasil |
| ----------------------------------- | ------------: | ------------------------: |
| Acertar o placar exato              |             3 |                         6 |
| Acertar apenas o vencedor ou empate |             1 |                         2 |
| Errar o resultado                   |             0 |                         0 |

Regra:

```text
Se a partida envolver o Brasil e o usuário acertar o placar exato:
  usuário recebe 6 pontos

Senão, se a partida envolver o Brasil e o usuário acertar apenas o vencedor ou empate:
  usuário recebe 2 pontos

Senão, se acertar o placar exato em jogo sem Brasil:
  usuário recebe 3 pontos

Senão, se acertar apenas o vencedor ou empate em jogo sem Brasil:
  usuário recebe 1 ponto

Senão:
  usuário recebe 0 pontos
```

Exemplo com jogo do Brasil:

Resultado oficial:

```text
Brasil 2 x 1 Alemanha
```

| Palpite               | Resultado                                | Pontos |
| --------------------- | ---------------------------------------- | -----: |
| Brasil 2 x 1 Alemanha | Acertou o placar exato em jogo do Brasil |      6 |
| Brasil 1 x 0 Alemanha | Acertou o vencedor em jogo do Brasil     |      2 |
| Brasil 1 x 1 Alemanha | Errou o resultado                        |      0 |
| Alemanha 2 x 1 Brasil | Errou o resultado                        |      0 |

Exemplo com empate em jogo do Brasil:

Resultado oficial:

```text
Brasil 1 x 1 Espanha
```

| Palpite              | Resultado                                | Pontos |
| -------------------- | ---------------------------------------- | -----: |
| Brasil 1 x 1 Espanha | Acertou o placar exato em jogo do Brasil |      6 |
| Brasil 0 x 0 Espanha | Acertou o empate em jogo do Brasil       |      2 |
| Brasil 2 x 1 Espanha | Errou o resultado                        |      0 |
| Espanha 2 x 1 Brasil | Errou o resultado                        |      0 |

---

## 4.7 Integração automática via Google API

A aplicação deverá possuir uma integração automática via Google API para buscar ou sincronizar dados da Copa.

A integração poderá ser usada para:

* Importar partidas.
* Importar datas e horários.
* Importar fases.
* Importar seleções.
* Importar jogadores.
* Atualizar resultados oficiais.
* Atualizar status dos jogos.
* Atualizar gols dos jogadores.
* Atualizar assistências dos jogadores.
* Atualizar ranking de artilheiros.
* Atualizar ranking de assistências.

A integração deverá ser executada de forma automática, preferencialmente por job agendado.

Fluxo esperado:

```text
Google API
  ↓
Job agendado
  ↓
Importação ou atualização dos jogos, jogadores, gols e assistências
  ↓
Validação dos dados
  ↓
Atualização do banco de dados
  ↓
Recalcular pontuação, se houver mudança em resultado oficial, artilheiro ou assistência
```

Regra obrigatória:

```text
Mesmo com integração automática, o administrador sempre poderá editar manualmente qualquer dado incorreto.
```

---

## 4.8 Correção manual pelo administrador

O sistema deverá permitir override manual dos dados importados automaticamente.

O administrador poderá corrigir:

* Nome da seleção.
* Jogador.
* Fase.
* Data e horário da partida.
* Status da partida.
* Placar oficial.
* Time vencedor.
* Gols de jogadores.
* Assistências de jogadores.
* Dados do artilheiro.
* Dados do campeão.
* Regra de multiplicador de pontos para jogos especiais.

Quando o administrador fizer uma alteração manual, o sistema deverá registrar que aquele campo foi alterado manualmente.

Regras recomendadas:

```text
Se um resultado for corrigido manualmente pelo admin:
  o sistema deverá recalcular os pontos afetados.

Se gols ou assistências forem corrigidos manualmente pelo admin:
  o sistema deverá recalcular o artilheiro oficial e os pontos de artilheiro.

Se uma partida, resultado, gol ou assistência tiver override manual:
  a próxima sincronização automática não deverá sobrescrever esse campo sem permissão do admin.
```

---

## 4.9 Fechamento dos palpites

O administrador deverá configurar uma data e hora limite para o fechamento dos palpites.

Após esse horário:

* Usuários aprovados não poderão mais criar palpites.
* Usuários aprovados não poderão mais alterar palpites existentes.
* O sistema deverá preservar os palpites enviados.
* A área Explore poderá ser liberada, caso o horário de liberação também tenha sido atingido.

Regra:

```text
Se dataHoraAtual >= dataHoraFechamentoPalpites:
  bloquear criação e edição de palpites
```

---

## 4.10 Área Explore

A área **Explore** permitirá que os usuários aprovados vejam os palpites dos outros participantes.

Essa área só poderá ser acessada depois do horário configurado pelo administrador.

Objetivo:

* Dar transparência ao bolão.
* Permitir comparação entre palpites.
* Evitar que usuários copiem palpites antes do fechamento.
* Mostrar os palpites dos participantes após o prazo oficial.

A área Explore deverá permitir visualizar:

* Palpite de campeão dos usuários.
* Palpite de artilheiro dos usuários.
* Palpites por partida.
* Palpites por fase.
* Comparação entre usuários.
* Pontos conquistados após os resultados oficiais.

Regra obrigatória:

```text
Antes do horário de liberação do Explore:
  o usuário aprovado só pode ver os próprios palpites.

Após o horário de liberação do Explore:
  o usuário aprovado pode ver os palpites dos outros usuários.

Usuários pendentes, rejeitados ou bloqueados não podem acessar o Explore.
```

O administrador deverá configurar:

```text
dataHoraFechamentoPalpites
dataHoraLiberacaoExplore
```

Por padrão, recomenda-se que:

```text
dataHoraLiberacaoExplore >= dataHoraFechamentoPalpites
```

---

# 5. Ranking

A página de ranking deverá mostrar a classificação geral dos usuários aprovados.

A pontuação total será:

```text
Pontuação total = Pontos dos jogos + Pontos do campeão + Pontos do artilheiro
```

O ranking deverá exibir:

| Campo             | Descrição                                                           |
| ----------------- | ------------------------------------------------------------------- |
| Posição           | Colocação do usuário                                                |
| Usuário           | Nome do participante aprovado                                       |
| Pontos dos jogos  | Pontos obtidos nos palpites das partidas, incluindo multiplicadores |
| Pontos campeão    | Pontos pelo acerto do campeão                                       |
| Pontos artilheiro | Pontos pelo acerto do artilheiro                                    |
| Pontuação total   | Soma geral                                                          |

Critérios de desempate sugeridos:

1. Maior número de placares exatos.
2. Maior número de acertos de vencedor ou empate.
3. Maior pontuação em jogos do Brasil.
4. Maior pontuação em mata-mata.
5. Palpite inicial enviado primeiro.
6. Ordem alfabética.

Regras de governança:

```text
Somente usuários com accessStatus = APPROVED devem aparecer no ranking.

Usuários pendentes, rejeitados ou bloqueados não devem aparecer no ranking.

Usuários pendentes, rejeitados ou bloqueados não devem influenciar estatísticas, pontuação ou desempates.
```

---

# 6. Chaveamento

A aplicação deverá montar automaticamente o chaveamento da Copa com base nos dados oficiais.

O chaveamento deverá considerar:

* 16 avos de final.
* Oitavas de final.
* Quartas de final.
* Semifinais.
* Disputa de terceiro lugar.
* Final.
* Campeão.

Regra obrigatória:

```text
O chaveamento oficial será baseado nos resultados oficiais importados ou cadastrados pelo administrador.
Os palpites dos usuários nunca devem alterar o chaveamento oficial.
```

---

# 7. Painel administrativo

O painel administrativo deverá ser uma parte essencial da aplicação.

Funcionalidades obrigatórias:

* Visualizar usuários pendentes.
* Aprovar usuários.
* Rejeitar usuários.
* Bloquear usuários aprovados.
* Reativar usuários bloqueados, se necessário.
* Consultar usuários por nome, e-mail e status.
* Ver data de cadastro do usuário.
* Ver quem aprovou o usuário.
* Ver data de aprovação.
* Gerenciar usuários.
* Gerenciar seleções.
* Gerenciar jogadores.
* Gerenciar fases.
* Gerenciar partidas.
* Importar dados via Google API.
* Atualizar dados via Google API.
* Editar manualmente dados importados.
* Registrar resultados oficiais.
* Corrigir resultados oficiais.
* Corrigir gols e assistências.
* Configurar fechamento dos palpites.
* Configurar liberação da área Explore.
* Abrir ou fechar fases.
* Bloquear palpites.
* Recalcular pontuação.
* Definir campeão oficial.
* Definir artilheiro oficial.
* Configurar multiplicador especial para jogos do Brasil.
* Visualizar logs de sincronização.

---

# 8. Stack recomendada

## 8.1 Frontend

* React.
* Componentes de UI Kit.
* Preferência por bibliotecas de componentes prontas.
* Evitar criar toda a camada visual manualmente do zero.

Possíveis UI Kits:

* Material UI.
* Ant Design.
* Chakra UI.
* Mantine.
* shadcn/ui, caso o projeto aceite composição com componentes prontos.

---

## 8.2 Backend e infraestrutura

* Next.js.
* TypeScript.
* PostgreSQL.
* Prisma.
* Auth.js / NextAuth.
* Vercel.
* Vercel Cron Jobs.
* Google API para importação ou sincronização automática.

Observação:

Mesmo usando React, o projeto pode ser estruturado com Next.js para facilitar deploy na Vercel, autenticação, rotas de API, server actions e jobs agendados.

---

# 9. Modelo de dados sugerido

## 9.1 User

```ts
type User = {
  id: string
  name: string
  email: string
  role: "USER" | "ADMIN"
  accessStatus: "PENDING" | "APPROVED" | "REJECTED" | "BLOCKED"
  approvedByUserId?: string
  approvedAt?: Date
  rejectedAt?: Date
  blockedAt?: Date
  createdAt: Date
  updatedAt: Date
}
```

Observações:

```text
Todo usuário novo deve iniciar com accessStatus = PENDING.

Somente usuários com accessStatus = APPROVED podem participar do bolão.

Usuários com accessStatus = PENDING, REJECTED ou BLOCKED não podem registrar palpites, acessar Explore ou aparecer no ranking.
```

---

## 9.2 Team

```ts
type Team = {
  id: string
  name: string
  code: string
  flagUrl?: string
  group?: string
  isSpecialMultiplierTeam?: boolean
  multiplierValue?: number
  createdAt: Date
  updatedAt: Date
}
```

Observação:

```text
Para o MVP, o Brasil deverá ser marcado como isSpecialMultiplierTeam = true e multiplierValue = 2.
```

---

## 9.3 Player

```ts
type Player = {
  id: string
  name: string
  teamId: string
  createdAt: Date
  updatedAt: Date
}
```

---

## 9.4 PlayerTournamentStats

```ts
type PlayerTournamentStats = {
  id: string
  playerId: string
  tournamentId?: string
  goals: number
  assists: number
  source: "MANUAL" | "GOOGLE_API"
  hasManualOverride: boolean
  createdAt: Date
  updatedAt: Date
}
```

Observação:

```text
Esta entidade será usada para calcular o artilheiro oficial.
O critério principal é gols.
Em caso de empate em gols, o desempate será assistências.
```

---

## 9.5 Phase

```ts
type Phase = {
  id: string
  name: string
  order: number
  type:
    | "INITIAL"
    | "GROUP"
    | "ROUND_OF_32"
    | "ROUND_OF_16"
    | "QUARTER_FINAL"
    | "SEMI_FINAL"
    | "THIRD_PLACE"
    | "FINAL"
  isOpen: boolean
  predictionDeadline: Date
  exploreReleaseAt?: Date
  createdAt: Date
  updatedAt: Date
}
```

Observação:

```text
ROUND_OF_32 representa os 16 avos de final.
```

---

## 9.6 Match

```ts
type Match = {
  id: string
  phaseId: string
  homeTeamId: string
  awayTeamId: string
  homeScore?: number
  awayScore?: number
  status: "SCHEDULED" | "LIVE" | "FINISHED" | "CANCELLED"
  startsAt: Date
  winnerTeamId?: string
  source: "MANUAL" | "GOOGLE_API"
  hasManualOverride: boolean
  hasSpecialMultiplier: boolean
  multiplierValue: number
  createdAt: Date
  updatedAt: Date
}
```

Observação:

```text
hasSpecialMultiplier deverá ser true quando a partida envolver o Brasil.
multiplierValue deverá ser 2 para jogos do Brasil.
```

---

## 9.7 MatchPrediction

```ts
type MatchPrediction = {
  id: string
  userId: string
  matchId: string
  predictedHomeScore: number
  predictedAwayScore: number
  predictedWinnerTeamId?: string
  predictedDraw: boolean
  basePoints: number
  multiplierApplied: number
  points: number
  createdAt: Date
  updatedAt: Date
}
```

Observação:

```text
basePoints representa a pontuação antes do multiplicador.
multiplierApplied representa o multiplicador usado na partida.
points representa a pontuação final após o multiplicador.
```

---

## 9.8 TournamentPrediction

```ts
type TournamentPrediction = {
  id: string
  userId: string
  championTeamId: string
  topScorerPlayerId: string
  championPoints: number
  topScorerPoints: number
  createdAt: Date
  updatedAt: Date
}
```

Regra:

```text
Somente usuários aprovados podem criar ou alterar TournamentPrediction.

Usuários pendentes, rejeitados ou bloqueados não podem registrar palpite de campeão ou artilheiro.
```

---

## 9.9 OfficialTournamentResult

```ts
type OfficialTournamentResult = {
  id: string
  championTeamId?: string
  topScorerPlayerIds: string[]
  topScorerResolutionRule: "GOALS_ONLY" | "GOALS_THEN_ASSISTS"
  topScorerPoints: number
  championPoints: number
  source: "MANUAL" | "GOOGLE_API"
  hasManualOverride: boolean
  createdAt: Date
  updatedAt: Date
}
```

Observação:

```text
topScorerPlayerIds pode conter mais de um jogador caso o empate continue após aplicar gols e assistências.
```

---

## 9.10 AppSettings

```ts
type AppSettings = {
  id: string
  predictionCloseAt: Date
  exploreReleaseAt: Date
  championPoints: number
  topScorerPoints: number
  exactScorePoints: number
  correctOutcomePoints: number
  brazilMatchMultiplier: number
  topScorerTieBreaker: "GOALS_ONLY" | "GOALS_THEN_ASSISTS"
  requireAdminApprovalForUsers: boolean
  createdAt: Date
  updatedAt: Date
}
```

---

## 9.11 SyncLog

```ts
type SyncLog = {
  id: string
  provider: "GOOGLE_API"
  status: "SUCCESS" | "ERROR"
  message?: string
  executedAt: Date
}
```

---

# 10. Principais páginas

| Página               | Objetivo                                                                        |
| -------------------- | ------------------------------------------------------------------------------- |
| Login                | Acesso de usuários e administradores                                            |
| Cadastro             | Permitir que qualquer pessoa crie uma conta                                     |
| Aguardando aprovação | Informar que o usuário ainda precisa ser aprovado pelo admin                    |
| Dashboard            | Mostrar pontos, ranking, fases abertas e próximos jogos para usuários aprovados |
| Palpites iniciais    | Palpite de campeão e artilheiro                                                 |
| Palpites por fase    | Cadastro dos placares por fase                                                  |
| Resultados           | Resultados oficiais, palpites e pontuação                                       |
| Ranking              | Classificação geral apenas com usuários aprovados                               |
| Chaveamento          | Visualização da fase eliminatória, incluindo 16 avos                            |
| Explore              | Visualizar palpites dos outros usuários após liberação                          |
| Admin Dashboard      | Visão geral administrativa                                                      |
| Admin Usuários       | Aprovação, rejeição, bloqueio e gestão de participantes                         |
| Admin Integração     | Sincronização com Google API                                                    |
| Admin Partidas       | Gestão e correção manual de partidas                                            |
| Admin Resultados     | Cadastro e correção de resultados                                               |
| Admin Jogadores      | Gestão de jogadores, gols e assistências                                        |
| Admin Configurações  | Fechamento de palpites, liberação do Explore e multiplicadores                  |

---

# 11. Regras críticas

## Regra 1 — Todo usuário novo começa pendente

```text
Quando um novo usuário se cadastrar:
  criar usuário com accessStatus = PENDING
```

---

## Regra 2 — Somente usuários aprovados participam

```text
Se accessStatus = APPROVED:
  permitir acesso ao bolão

Se accessStatus diferente de APPROVED:
  bloquear acesso ao bolão
```

---

## Regra 3 — Usuário pendente vê apenas aguardando aprovação

```text
Se accessStatus = PENDING:
  permitir login
  exibir tela de aguardando aprovação
  bloquear cadastro de palpites
  bloquear ranking
  bloquear Explore
```

---

## Regra 4 — Usuários rejeitados ou bloqueados não acessam

```text
Se accessStatus = REJECTED ou BLOCKED:
  bloquear acesso ao bolão
  não permitir palpites
  não exibir no ranking
  não permitir Explore
```

---

## Regra 5 — Palpites não podem ser alterados após fechamento

```text
Se dataHoraAtual >= dataHoraFechamentoPalpites:
  bloquear criação e edição de palpites
```

---

## Regra 6 — Explore só abre após horário definido pelo admin

```text
Se dataHoraAtual >= dataHoraLiberacaoExplore e usuário estiver APPROVED:
  liberar visualização dos palpites de outros usuários

Senão:
  permitir apenas visualização dos próprios palpites, se o usuário estiver APPROVED
```

---

## Regra 7 — Resultado manual do admin tem prioridade

```text
Se uma partida ou resultado tiver alteração manual:
  não sobrescrever automaticamente na próxima sincronização
  exceto se o admin autorizar
```

---

## Regra 8 — Mudança de resultado recalcula pontuação

```text
Se resultado oficial for criado ou alterado:
  recalcular pontos das previsões relacionadas
  atualizar ranking
```

---

## Regra 9 — Placar exato não acumula com vencedor

```text
Se acertou placar exato:
  pontos base = 3
Senão, se acertou vencedor ou empate:
  pontos base = 1
Senão:
  pontos base = 0
```

---

## Regra 10 — Jogos do Brasil têm pontuação dobrada

```text
Se a partida envolver o Brasil:
  aplicar multiplicador 2 sobre os pontos base

Exemplos:
  placar exato em jogo do Brasil = 3 x 2 = 6 pontos
  vencedor ou empate em jogo do Brasil = 1 x 2 = 2 pontos
  erro em jogo do Brasil = 0 x 2 = 0 pontos
```

---

## Regra 11 — Artilheiro usa assistências como desempate

```text
Para definir o artilheiro oficial:
  ordenar jogadores por gols em ordem decrescente

Se houver apenas um jogador com mais gols:
  esse jogador é o artilheiro oficial

Se houver empate em gols:
  entre os empatados, ordenar por assistências em ordem decrescente

Se houver apenas um jogador com mais assistências entre os empatados:
  esse jogador é o artilheiro oficial

Se ainda houver empate em gols e assistências:
  todos os jogadores empatados serão considerados artilheiros válidos
```

---

## Regra 12 — Alteração de gols ou assistências recalcula artilheiro

```text
Se gols ou assistências de jogadores forem criados, importados ou alterados:
  recalcular artilheiro oficial
  recalcular pontos de artilheiro dos usuários
  atualizar ranking
```

---

## Regra 13 — Usuários não aprovados não influenciam o bolão

```text
Usuários com accessStatus diferente de APPROVED:
  não aparecem no ranking
  não entram nas estatísticas
  não são considerados em desempates
  não têm pontuação ativa
```

---

# 12. MVP atualizado

## 12.1 Obrigatório no MVP

* Cadastro aberto de usuários.
* Status de aprovação de usuários.
* Tela de aguardando aprovação.
* Aprovação manual pelo administrador.
* Rejeição manual pelo administrador.
* Bloqueio de usuários pelo administrador.
* Bloqueio de acesso para usuários não aprovados.
* Ranking considerando apenas usuários aprovados.
* Explore disponível apenas para usuários aprovados.
* Autenticação.
* Perfis de usuário e administrador.
* React com UI Kit.
* Cadastro de seleções.
* Cadastro de jogadores.
* Cadastro de fases.
* Suporte a 16 avos de final.
* Cadastro de partidas.
* Importação automática via Google API.
* Importação ou cadastro de gols dos jogadores.
* Importação ou cadastro de assistências dos jogadores.
* Definição de artilheiro usando gols e assistências.
* Correção manual pelo admin.
* Palpite de campeão.
* Palpite de artilheiro.
* Palpites por partida.
* Regra de pontuação dobrada para jogos do Brasil.
* Fechamento de palpites por data e hora.
* Liberação do Explore por data e hora.
* Visualização dos palpites de outros usuários após liberação.
* Cálculo automático de pontos.
* Ranking.
* Chaveamento.
* Logs básicos de sincronização.

---

## 12.2 Fora do MVP

Para evitar excesso de complexidade na primeira versão, ficam fora do MVP:

* App mobile nativo.
* Pagamentos.
* Prêmios financeiros.
* WebSocket em tempo real.
* Chat entre usuários.
* Comentários.
* Múltiplos torneios.
* Sistema avançado de permissões.
* Auditoria completa.
* Notificações push.

---

# 13. Fluxo principal da aplicação

```text
Usuário se cadastra
  ↓
Conta fica pendente de aprovação
  ↓
Admin aprova ou rejeita o usuário
  ↓
Usuário aprovado acessa o bolão
  ↓
Admin configura competição
  ↓
Sistema importa partidas via Google API
  ↓
Sistema importa jogadores, gols e assistências
  ↓
Admin revisa e corrige dados, se necessário
  ↓
Usuários aprovados cadastram palpites
  ↓
Horário de fechamento bloqueia alterações
  ↓
Horário de liberação ativa o Explore
  ↓
Usuários aprovados visualizam palpites dos outros participantes
  ↓
Resultados oficiais são importados ou corrigidos pelo admin
  ↓
Gols e assistências são importados ou corrigidos pelo admin
  ↓
Sistema define campeão e artilheiro oficial
  ↓
Sistema recalcula pontos aplicando multiplicador dos jogos do Brasil
  ↓
Sistema recalcula pontos de campeão e artilheiro
  ↓
Ranking é atualizado apenas com usuários aprovados
  ↓
Chaveamento é atualizado
```

---

# 14. Critérios de sucesso

A primeira versão será considerada bem-sucedida quando:

* Qualquer pessoa conseguir se cadastrar.
* O usuário novo ficar pendente por padrão.
* O administrador conseguir aprovar ou rejeitar usuários.
* O administrador conseguir bloquear usuários.
* Apenas usuários aprovados conseguirem participar do bolão.
* Usuários não aprovados não conseguirem registrar palpites.
* Usuários não aprovados não aparecerem no ranking.
* Usuários não aprovados não acessarem o Explore.
* O usuário aprovado conseguir cadastrar campeão e artilheiro.
* O usuário aprovado conseguir cadastrar placares dos jogos.
* O sistema bloquear alterações após o fechamento.
* O Explore liberar os palpites dos outros usuários somente após o horário configurado.
* O admin conseguir importar partidas via Google API.
* O admin conseguir importar ou cadastrar gols e assistências.
* O admin conseguir corrigir manualmente partidas, resultados, gols e assistências.
* O sistema calcular pontos corretamente.
* O sistema dobrar corretamente os pontos em jogos do Brasil.
* O sistema definir o artilheiro usando gols e assistências.
* O sistema aceitar múltiplos artilheiros caso o empate continue após gols e assistências.
* O ranking atualizar automaticamente.
* O chaveamento considerar 16 avos de final.
* A aplicação estiver publicada na Vercel.

---

# 15. Fórmula final de pontuação

```text
pontosBase =
  3, se acertou o placar exato
  1, se acertou vencedor ou empate
  0, se errou o resultado

multiplicador =
  2, se a partida envolver o Brasil
  1, para os demais jogos

pontosDaPartida = pontosBase * multiplicador

pontosCampeao =
  10, se acertou o campeão
  0, se errou o campeão

pontosArtilheiro =
  15, se acertou o artilheiro oficial após aplicar critério de gols e assistências
  0, se errou o artilheiro

pontuacaoTotal =
  pontosDasPartidas
  + pontosCampeao
  + pontosArtilheiro
```

Exemplos finais:

| Cenário                                                 | Pontos |
| ------------------------------------------------------- | -----: |
| Acertou placar exato em jogo comum                      |      3 |
| Acertou vencedor ou empate em jogo comum                |      1 |
| Acertou placar exato em jogo do Brasil                  |      6 |
| Acertou vencedor ou empate em jogo do Brasil            |      2 |
| Acertou campeão                                         |     10 |
| Acertou artilheiro após critério de gols e assistências |     15 |

---

# 16. Regra final do artilheiro

```text
O palpite de artilheiro será considerado correto se o jogador escolhido pelo usuário estiver na lista final de artilheiros oficiais calculada pelo sistema.

A lista final será calculada assim:

1. Selecionar o maior número de gols da competição.
2. Filtrar todos os jogadores com esse número de gols.
3. Se houver apenas um jogador, ele será o artilheiro oficial.
4. Se houver mais de um jogador, aplicar desempate por assistências.
5. Selecionar o maior número de assistências entre os jogadores empatados em gols.
6. Se houver apenas um jogador com mais assistências, ele será o artilheiro oficial.
7. Se ainda houver empate, todos os jogadores empatados em gols e assistências serão considerados artilheiros oficiais válidos.
```

---

# 17. Regra final de governança de acesso

```text
Todo usuário pode se cadastrar.

Por padrão, todo novo usuário começa com:
  accessStatus = PENDING

Somente o administrador pode alterar o status do usuário para:
  APPROVED
  REJECTED
  BLOCKED

Somente usuários APPROVED podem:
  acessar o bolão
  registrar palpites
  aparecer no ranking
  acessar Explore
  participar das estatísticas
  pontuar

Usuários PENDING, REJECTED ou BLOCKED:
  não podem registrar palpites
  não aparecem no ranking
  não acessam Explore
  não influenciam pontuação
  não influenciam critérios de desempate
```

