# Task 04: Auto sync externo

## Objetivo

Validar e endurecer o caminho operacional do cron externo.

## Descricao

O endpoint interno tem gates corretos, mas a confiabilidade da operacao depende de testes claros para cada estado de execucao.

## Arquivos-Alvo

1. `backend/app/api/routes/internal.py`
2. `backend/tests/integration/test_auto_sync_internal.py`

## Atividades

1. Revisar os estados `sync_admin_token_missing`, token invalido, disabled, not due yet e advisory lock.
2. Garantir cobertura de testes para cada estado.
3. Confirmar que sucesso continua registrando `automatic_sync_completed`.

## Gates de Validacao

- [ ] Token invalido falha com auth claro.
- [ ] Disabled retorna `SKIPPED`.
- [ ] Intervalo nao vencido retorna `SKIPPED`.
- [ ] Execucao elegivel gera log resumo.
