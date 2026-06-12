# Tests: Sync de Resultados

## Estrategia

Cobrir o problema em tres camadas:

1. unidade de matching e merge
2. integracao da sync contra sessao/banco
3. integracao do endpoint de auto sync

## Matriz de Testes

### Unidade: Matching

1. Casa por `provider + external_id` quando ambos coincidem.
2. Casa por `external_id` quando o provider difere, mas o id coincide.
3. Casa por `bracket_slot` quando aplicavel.
4. Casa por `home_team_fifa_code + away_team_fifa_code + starts_at` quando seed local e provider nao compartilham `external_id` nem nome textual.
5. Nao casa quando apenas um codigo de time coincide.
6. Nao casa quando o horario diverge fora da normalizacao esperada.

### Unidade: Merge

1. Atualiza `status` quando o provider traz status terminal valido.
2. Atualiza gols oficiais quando ha diferenca material.
3. Atualiza `winner_team_name` quando o placar muda.
4. Retorna `noop` quando payload e estado local ja sao equivalentes.
5. Retorna `skipped_manual_override` quando `has_manual_override=True`.

### Integracao: SyncService

1. `run_scheduled_sync` atualiza `Match` seedado usando novo fallback.
2. `run_manual_match_sync` continua funcionando sem `respect_timing_window`.
3. `missing_local_match` e registrado quando o provider nao encontra correspondente local.
4. `non_terminal_status` nao aplica resultado.
5. `not_due_yet` continua respeitado quando a execucao depende de janela pos-jogo.

### Integracao: Auto Sync

1. `/api/internal/sync/auto` retorna `SKIPPED` quando `auto_sync_enabled=false`.
2. `/api/internal/sync/auto` retorna `SKIPPED` quando ainda nao esta due.
3. `/api/internal/sync/auto` retorna `SKIPPED` quando outro processo segura o lock.
4. `/api/internal/sync/auto` retorna erro de auth quando token invalido.
5. `/api/internal/sync/auto` registra log resumo de execucao.

### UI/Admin

1. O DTO de logs exposto ao admin inclui `result_code`.
2. A tela admin apresenta o motivo real do skip.
3. O fluxo de sucesso nao perde mensagem agregada de contagem.

## Evidencias Esperadas

1. Assert sobre campos do `Match` apos sync.
2. Assert sobre `SyncRunResult.success_count`, `skipped_count` e `failure_count`.
3. Assert sobre `SyncLog.result_code` e `SyncLog.message`.
4. Assert sobre payload serializado no contrato do admin.

## Gates de Validacao

- [ ] Ha teste cobrindo o fallback novo de matching.
- [ ] Ha teste cobrindo ausencia de falso positivo no fallback.
- [ ] Ha teste cobrindo `skipped_manual_override`.
- [ ] Ha teste cobrindo `missing_local_match`.
- [ ] Ha teste cobrindo o endpoint `/api/internal/sync/auto`.
- [ ] Nenhum teste existente de override/manual sync foi quebrado.
