# Task 01: Matching e identidade

## Objetivo

Adicionar uma estrategia de matching estavel entre payload do provider e partidas locais seedadas.

## Descricao

O problema principal nao e a chamada HTTP, e a identidade da partida. O sistema precisa reconhecer o mesmo jogo mesmo quando provider, id externo e nome textual divergem entre seed local e provider.

## Entradas

1. `ProviderMatchRecord`
2. colecao local de `Match`
3. normalizacao UTC existente no servico

## Arquivos-Alvo

1. `backend/app/services/sync_service.py`
2. `backend/tests/integration/test_admin_sync.py`

## Atividades

1. Revisar a ordem atual de `_match_local_record(...)`.
2. Inserir fallback por `home_team_fifa_code + away_team_fifa_code + starts_at` apos os criterios mais fortes.
3. Garantir que o horario seja comparado no mesmo formato UTC ja usado por `_identity_key(...)` e `_as_utc(...)`.
4. Escrever teste que reproduz seed local + payload do provider com ids divergentes e merge valido.
5. Escrever teste negativo para evitar casamento indevido.

## Dependencias

1. Nao depende de alteracao de schema.
2. Pode ser implementada antes das mudancas de admin/log.

## Gates de Validacao

- [ ] O novo fallback nao substitui os criterios mais fortes.
- [ ] O novo fallback depende de ambos os codigos FIFA e do horario.
- [ ] Existe teste positivo do novo fallback.
- [ ] Existe teste negativo para falso positivo.
