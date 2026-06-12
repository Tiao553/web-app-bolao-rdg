# Task 03: Observabilidade no admin

## Objetivo

Fazer o console admin mostrar o motivo real do resultado de sync, em vez de apenas um agregado generico.

## Descricao

Hoje a operacao pode parecer bem-sucedida do ponto de vista de HTTP, mas o operador nao enxerga facilmente se houve `missing_local_match`, `not_due_yet` ou `skipped_manual_override`.

## Arquivos-Alvo

1. `backend/app/services/frontend_contract_service.py`
2. `app/src/lib/contracts.ts`
3. `app/src/components/admin/integration-controls.tsx`

## Atividades

1. Expandir o DTO de logs para incluir `result_code`.
2. Ajustar o contrato frontend correspondente.
3. Renderizar o motivo de forma legivel no admin.
4. Preservar o resumo agregado atual da operacao.

## Gates de Validacao

- [ ] O admin mostra `result_code` sem exigir inspeção de banco.
- [ ] A listagem continua funcional para logs antigos.
- [ ] O resumo agregado da sync continua visivel.
