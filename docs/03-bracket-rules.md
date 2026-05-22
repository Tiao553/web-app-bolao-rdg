# Regras do Chaveamento — O que a API faz vs. o que a aplicação calcula

## 1. Divisão de responsabilidades

```
┌────────────────────────────────────────┬──────────────────────────────────────────────┐
│ API-Football (dados brutos)            │ Aplicação (lógica de negócio)               │
├────────────────────────────────────────┼──────────────────────────────────────────────┤
│ Placar de cada partida                 │ Classificação final de cada grupo            │
│ Status da partida (FT, LIVE, NS…)      │ Seleção dos 8 melhores 3ºs colocados        │
│ Gols e assistências por jogador        │ Alocação dos 3ºs aos slots do bracket       │
│ Vencedor da partida (pelo placar)      │ Preenchimento dos slots TBD do chaveamento  │
│                                        │ Cálculo de pontuação dos palpites           │
│                                        │ Artilheiro oficial (gols + assistências)    │
└────────────────────────────────────────┴──────────────────────────────────────────────┘
```

---

## 2. Classificação dentro do grupo

### 2.1 Ordem de classificação (FIFA oficial)

Para cada grupo de 4 times, a classificação final é determinada pelos critérios abaixo, em ordem de prioridade:

```
1. Pontos (vitória = 3pts, empate = 1pt, derrota = 0pt)
2. Saldo de gols (gols marcados - gols sofridos na fase de grupos)
3. Gols marcados (total na fase de grupos)
4. Pontos em confrontos diretos entre os times empatados
5. Saldo de gols em confrontos diretos entre os times empatados
6. Gols marcados em confrontos diretos entre os times empatados
7. Gols fora de casa em confrontos diretos (regra FIFA para 2026)
8. Ranking FIFA à época do sorteio
```

### 2.2 Quem avança da fase de grupos

- **1º e 2º colocados** de cada grupo → avançam diretamente ao Round of 32.
- **3ºs colocados**: todos os 12 terceiros colocados são ranqueados entre si. Os 8 melhores avançam.

---

## 3. Seleção dos 8 melhores terceiros colocados

### 3.1 Critérios de ranking entre os 12 terceiros

Os 12 terceiros colocados (um por grupo) são comparados entre si pela mesma ordem de critérios da classificação intra-grupo:

```
1. Pontos (nos 3 jogos da fase de grupos)
2. Saldo de gols
3. Gols marcados
4. Ranking FIFA
```

Os 8 com melhor ranqueamento avançam. Os 4 piores são eliminados.

### 3.2 Impacto no chaveamento

Saber **quais 8 grupos** geraram os terceiros classificados é obrigatório para montar o bracket corretamente, porque o sistema garante que dois times do mesmo grupo não se encontrem antes das quartas.

---

## 4. Alocação dos 3ºs colocados no bracket — Tabela FIFA

A FIFA definiu previamente todos os 495 cenários possíveis de combinação de 8 grupos dentre os 12 (C(12,8) = 495).

Cada cenário mapeia qual 3º colocado vai para qual slot do Round of 32.

### 4.1 Slots de terceiros no Round of 32

```
Slot M74: recebe 3º de A/B/C/D/F
Slot M77: recebe 3º de C/D/F/G/H
Slot M79: recebe 3º de C/E/F/H/I
Slot M80: recebe 3º de E/H/I/J/K
Slot M81: recebe 3º de B/E/F/I/J
Slot M82: recebe 3º de A/E/H/I/J
Slot M85: recebe 3º de E/F/G/I/J
Slot M87: recebe 3º de D/E/I/J/L
```

### 4.2 Regra de exclusão mútua

Nenhum slot pode receber um 3º colocado de um grupo que já tem o 1º ou 2º colocado no mesmo slot da chave. Exemplo:

```
M74: Winner Group E vs 3º de A/B/C/D/F
  → o 3º NÃO pode ser do Grupo E (já está o 1º do Grupo E)
  → o 3º também não pode ser do Grupo F (o 2º do F está em M75)
  → logo, o 3º de M74 virá de A, B, C ou D (aplicando a tabela FIFA)
```

### 4.3 Lógica simplificada para implementação

Em vez de implementar os 495 casos, a aplicação pode seguir este algoritmo:

```
Entrada: lista dos 8 grupos que geraram os 8 melhores 3ºs colocados

Para cada slot (M74, M77, M79, M80, M81, M82, M85, M87):
  candidatos = grupos elegíveis para o slot (ver tabela acima)
    ∩ grupos dos 8 terceiros classificados
    − grupos que já estão no mesmo side do bracket naquele slot

  Se candidatos.length === 1 → alocar esse 3º ao slot
  Se candidatos.length > 1  → aplicar sub-critério: menor ranking FIFA entre os candidatos

Repetir até todos os 8 slots estarem preenchidos
```

**Alternativa mais simples:** Implementar a tabela completa de 495 linhas como um lookup estático. A FIFA publicou esse mapeamento oficialmente. Recomendado para garantir determinismo sem risco de bug na lógica de exclusão.

---

## 5. Preenchimento do bracket após cada rodada eliminatória

### 5.1 Fluxo de propagação

```
Resultado de M73 (W ou L) → preenche homeTeam de M89
Resultado de M74 (W ou L) → preenche awayTeam de M89
...
Resultado de M101 (L) → preenche homeTeam de M103 (3º lugar)
Resultado de M102 (L) → preenche awayTeam de M103 (3º lugar)
Resultado de M101 (W) → preenche homeTeam de M104 (Final)
Resultado de M102 (W) → preenche awayTeam de M104 (Final)
```

### 5.2 Regra de desempate em mata-mata

A partir do Round of 32, não há empate. Em caso de placar igual após 90 minutos:

```
1. Prorrogação (2× 15 minutos)
2. Se ainda empatado: pênaltis
```

A API retorna `fixture.status.short` como:
- `"AET"` (After Extra Time) — vitória na prorrogação
- `"PEN"` (Penalties) — vitória nos pênaltis

O campo `winnerTeamId` da partida deve ser preenchido pelo resultado real, independente de como a vitória foi obtida.

**Para fins de palpite do bolão:** o palpite é apenas o placar ao final dos 90 minutos. A prorrogação e os pênaltis não afetam a pontuação do bolão — apenas determinam quem avança.

---

## 6. Regras de pontuação no mata-mata

As mesmas regras da fase de grupos se aplicam ao mata-mata:

```
Placar exato (90min)        → 3 pts (6 pts se envolver o Brasil)
Resultado certo (90min)     → 1 pt  (2 pts se envolver o Brasil)
Resultado errado            → 0 pts
```

**Atenção:** No mata-mata não há empate após 90 minutos (o jogo pode continuar com prorrogação/pênaltis). Para o palpite do bolão:

```
Se o usuário palpitou 1x1 e o placar foi 1x1 aos 90min → resultado correto (1pt)
Se o usuário palpitou 2x1 e o placar foi 1x1 → resultado errado (0pt)
Quem avançou (pênaltis/prorrogação) NÃO afeta a pontuação do bolão
```

---

## 7. O que a API-Football entrega para cada fase

| Dado necessário                          | Endpoint API-Football             | Disponível? |
| ---------------------------------------- | --------------------------------- | ----------- |
| Placar ao fim de 90 min                  | `/fixtures?id={id}`               | Sim         |
| Status da partida (FT, AET, PEN)         | `fixture.status.short`            | Sim         |
| Vencedor após prorrogação / pênaltis     | `teams.home/away.winner`          | Sim         |
| Gols e assistências por jogador          | `/fixtures/events?fixture={id}`   | Sim         |
| Ranking de artilheiros                   | `/players/topscorers?league=1`    | Sim         |
| Classificação do grupo (pontos, saldo)   | `/standings?league=1&season=2026` | Sim         |
| Qual 3º colocado vai para qual slot      | — não disponível —                | **NÃO**     |
| Preenchimento automático do chaveamento  | — não disponível —                | **NÃO**     |

**Conclusão:** A API entrega resultados brutos. Todo o chaveamento, classificações, seleção de terceiros e propagação de bracket deve ser calculado pela própria aplicação.

---

## 8. Quando e como o recálculo é disparado

O chaveamento e a pontuação são recalculados pelo job `sync-after-match`, que roda
~115 minutos após o início de cada partida (3 vezes ao dia, via Vercel Cron Jobs).

O job só processa se `fixture.status.short === "FT" | "AET" | "PEN"`. Caso contrário,
registra no SyncLog e encerra sem fazer nada.

Sequência de recálculo após cada jogo finalizado:

```
1. Upsert do placar na tabela Match
2. Se fase de grupos:
     → recalcular classificação do grupo (pontos, saldo, gols)
     → se for o 3º jogo do grupo: consolidar posições finais (1º, 2º, 3º)
     → se todos os 12 grupos tiverem o 3º jogo concluído:
         → rankear os 12 terceiros colocados
         → selecionar os 8 melhores
         → aplicar tabela de alocação FIFA → preencher slots TBD do Round of 32
3. Se fase eliminatória (Round of 32 em diante):
     → preencher slot do próximo jogo com o vencedor
     → se semifinal: preencher Final (W) e 3º lugar (L)
4. Recalcular pontos dos palpites afetados pelo jogo concluído
5. Atualizar ranking (somente usuários APPROVED)
6. Registrar execução no SyncLog
```

No mata-mata com prorrogação/pênaltis, o admin pode disparar o sync manualmente via
`POST /api/admin/sync` com `{ "type": "match", "fixtureId": "..." }` caso o cron
já tenha executado antes do jogo terminar.

---

## 9. Referências

- [Wikipedia — 2026 FIFA World Cup knockout stage](https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_knockout_stage)
- [ESPN — 2026 World Cup format & tiebreakers](https://www.espn.com/soccer/story/_/id/47108758/2026-fifa-world-cup-format-tiebreakers-fixtures-schedule)
- [FIFA — Knockout stage bracket schedule](https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/knockout-stage-match-schedule-bracket)
- [Sportmonks — Round of 32 bracket builder](https://www.sportmonks.com/blogs/world-cup-2026-round-of-32-and-knockouts-how-to-build-world-cup-brackets/)
