# Production Bracket Swap Apply Report

Applied at: 2026-07-05T14:41:12Z
Project: BolaoRdg (`zvwvrlasmzsibjzfgolt`)
Backup: `prod-db-backups/bracket-swap-pre-change-20260705T143734Z.json`

## Changes Applied

- `M85`: `Suíça x Argélia` -> `Egito x Argélia`
- `M86`: `Austrália x Egito` -> `Austrália x Suíça`
- `M86` penalty winner: `Egito` -> `Suíça`
- `M95`: `Egito x Colômbia` -> `Suíça x Colômbia`
- `M96`: `Argentina x Suíça` -> `Argentina x Egito`
- Inserted Arthur Silva prediction for `M95`: `Suíça 1 x 2 Colômbia`

## Verification

- `M85` verified as `Egito x Argélia`, status `FT`, score `2-0`.
- `M86` verified as `Austrália x Suíça`, status `PEN`, score `1-1`, winner `Suíça`.
- `M95` verified as `Suíça x Colômbia`, status `SCHEDULED`.
- `M96` verified as `Argentina x Egito`, status `SCHEDULED`.
- Arthur Silva has one `M95` prediction: `home_goals = 1`, `away_goals = 2`.
- Prediction counts after apply:
  - `M85`: 11
  - `M86`: 11
  - `M95`: 11
  - `M96`: 12
- Audit log inserted:
  - operation: `manual_round_of_16_egypt_switzerland_swap`
  - result_code: `egypt_switzerland_swap_applied`
  - sync log id: `87785d29-6f8f-4b50-bc8d-ac06afc2ec5e`

## Notes

- No schema, backend, or frontend code changes were required.
- Existing prediction rows were preserved.
- Existing match IDs, kickoff times, scores, statuses, manual override flags, and source payload markers were preserved.
