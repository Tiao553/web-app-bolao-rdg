# Task 02: Merge e codigos de resultado

## Objetivo

Padronizar os cenarios de sucesso, noop e skip para que o comportamento seja verificavel e auditavel.

## Descricao

Mesmo apos casar a partida corretamente, o fluxo precisa deixar explicito se houve update material, preservacao por override ou ausencia de alteracao real.

## Arquivos-Alvo

1. `backend/app/services/sync_service.py`
2. `backend/tests/integration/test_admin_sync.py`

## Atividades

1. Revisar os caminhos de `MatchEligibility` e `_merge_provider_match(...)`.
2. Garantir consistencia entre `eligible`, `noop`, `updated` e `skipped_manual_override`.
3. Garantir que `missing_local_match` seja registrado tambem na execucao agendada quando relevante.
4. Confirmar que `changed_fields` continue coerente para disparo de recalculo.

## Gates de Validacao

- [ ] `updated` so ocorre quando houve diferenca material.
- [ ] `noop` continua disponivel quando payload e estado local sao equivalentes.
- [ ] `skipped_manual_override` preserva os dados locais.
- [ ] `missing_local_match` gera log observavel.
