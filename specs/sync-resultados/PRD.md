# PRD: Sync de Resultados

## Metadata

| Campo | Valor |
|---|---|
| Feature | `sync-resultados` |
| Status | Draft |
| Tipo | Correcao funcional + observabilidade |
| Prioridade | Alta |
| Donos provaveis | Backend + QA |

## Objetivo

Corrigir o fluxo de sincronizacao de resultados para que a resposta valida do TheSportsDB produza atualizacao real nos registros locais de `Match`, preserve o comportamento de `manual override`, e torne o motivo de `SKIPPED` auditavel no admin e no endpoint de auto sync.

## Problema

Hoje o provider pode responder com `200 OK`, mas isso nao garante merge bem-sucedido no banco local. O problema principal e a incompatibilidade entre a identidade dos jogos seedados localmente e a identidade retornada pelo provider.

## Evidencia Atual

1. O seed local cria partidas com `external_provider=SEED`, `external_id` interno e nomes/codigos derivados do dataset local.
   Fonte: `backend/app/seed/seeder.py:128-146`
2. O TheSportsDB retorna `idEvent`, nomes normalizados e status/gols do provider.
   Fonte: `backend/app/integrations/the_sports_db.py:153-205`
3. O matching atual tenta casar por:
   - `provider + external_id`
   - `external_id`
   - `bracket_slot`
   - `home_team_name + away_team_name + starts_at`
   Fonte: `backend/app/services/sync_service.py:269-292`
4. Como o seed local nao compartilha necessariamente provider, external id nem nome textual com o provider, ha casos em que o provider responde, mas nenhum `Match` local e encontrado.
5. A rota de auto sync ainda pode responder `SKIPPED` por token, disabled flag, janela de intervalo ou lock concorrente.
   Fonte: `backend/app/api/routes/internal.py:106-210`

## Causa Provavel

O sistema esta acoplado demais a chaves de identidade que nao sao estaveis entre seed local e provider externo. O fallback textual por nome/horario nao e suficiente quando o dataset local usa codigos FIFA e o provider usa nomes localizados.

## Resultado Esperado

1. Quando o provider trouxer um jogo que corresponde a uma partida local seedada, o sistema deve conseguir casar esse jogo por uma chave estavel.
2. O merge deve atualizar `status`, `official_home_goals`, `official_away_goals`, `winner_team_name`, `synced_at` e dados complementares quando houver diferenca material.
3. Se houver `manual override`, o sync automatico/manual do provider deve preservar o dado local e registrar claramente o motivo.
4. Se nao houver `Match` local compativel, o sistema deve registrar o evento com `result_code` rastreavel.
5. O admin deve conseguir distinguir claramente sucesso, skip por override, skip por falta de match local, skip por status nao terminal e skip por janela do cron.

## Escopo

Incluido:

1. Ajuste da estrategia de matching no `SyncService`.
2. Exposicao de motivos reais de skip no admin.
3. Revisao do caminho do auto sync externo para diagnostico mais claro.
4. Testes unitarios e de integracao cobrindo o novo fallback e os estados operacionais.

Excluido:

1. Troca de provider.
2. Reescrita do pipeline de recalculo.
3. Redesenho da tela admin alem do necessario para observabilidade.
4. Expansao do suporte a knockout no provider, exceto se descoberta como bloqueador direto da correcao de grupos.

## Mudanca Proposta

### 1. Matching resiliente

Adicionar fallback de matching por:

1. `home_team_fifa_code`
2. `away_team_fifa_code`
3. `starts_at` normalizado em UTC

Esse fallback entra somente depois dos criterios ja existentes, para manter a mudanca cirurgica.

### 2. Observabilidade

Padronizar e expor `result_code` para os cenarios:

1. `updated`
2. `noop`
3. `missing_local_match`
4. `skipped_manual_override`
5. `non_terminal_status`
6. `not_due_yet`

### 3. Diagnostico operacional do cron

Preservar a logica atual de `SYNC_ADMIN_TOKEN`, `auto_sync_enabled`, intervalo e advisory lock, mas garantir que os estados sejam testados e documentados.

## Arquivos Mais Provaveis de Impacto

1. `backend/app/services/sync_service.py`
2. `backend/app/integrations/the_sports_db.py`
3. `backend/app/api/routes/internal.py`
4. `backend/app/services/frontend_contract_service.py`
5. `app/src/lib/contracts.ts`
6. `app/src/components/admin/integration-controls.tsx`
7. `backend/tests/integration/test_admin_sync.py`
8. `backend/tests/integration/test_auto_sync_internal.py`
9. `backend/tests/unit/test_the_sports_db.py`

## Riscos

1. Casar partidas erradas se o fallback por codigos + horario for permissivo demais.
2. Alterar excessivamente o contrato do admin ao expor log detalhado.
3. Mascarar erro de parsing do provider se o foco ficar so no matching.

## Mitigacoes

1. O novo fallback so entra depois das chaves fortes existentes.
2. O horario deve ser comparado em UTC e com normalizacao identica ao restante do servico.
3. Testes devem cobrir match correto e ausencia de falso positivo.

## Criticos de Aceitacao

1. Um jogo seedado localmente precisa ser atualizado com payload valido do TheSportsDB sem depender de `external_id` compartilhado.
2. `manual override` nao pode ser sobrescrito.
3. O admin precisa visualizar o motivo de skip sem ler log bruto do banco.
4. O endpoint `/api/internal/sync/auto` precisa continuar respondendo corretamente nos cenarios `disabled`, `waiting`, `locked` e `success`.

## Gates de Validacao

- [ ] Existe evidencia automatizada de merge bem-sucedido com seed local + payload TheSportsDB.
- [ ] Existe evidencia automatizada de preservacao de `manual override`.
- [ ] Existe evidencia automatizada de `missing_local_match`.
- [ ] O admin recebe um campo legivel para diferenciar motivos de skip.
- [ ] O fluxo de auto sync nao regrediu em autenticacao ou gating por intervalo.
