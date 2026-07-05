# Round of 32 Real Results and Points Fix

Applied at: 2026-07-05T14:51:06Z
Project: BolaoRdg (`zvwvrlasmzsibjzfgolt`)

## Correction

The previous bracket swap made `M95/M96` visually correct, but moved the finished Round of 32 match identities/results into the wrong slots. This follow-up correction restored the real finished fixtures and recalculated affected prediction points.

## Rows Corrected

- `M85`: `Suíça 2 x 0 Argélia`, status `FT`
- `M86`: `Austrália 1 x 1 Egito`, status `PEN`, winner `Egito`
- `M87`: `Argentina 3 x 2 Cabo Verde`, status `FT`
- `M88`: `Colômbia 1 x 0 Gana`, status `FT`
- `M95`: `Suíça x Colômbia`, feeders `W85 x W88`
- `M96`: `Argentina x Egito`, feeders `W87 x W86`

## Points Verification

- Recalculated prediction points for all predictions on `M85`, `M86`, `M87`, and `M88`.
- Updated prediction rows: 11.
- Verified zero mismatches between stored `points_awarded` and the active scoring rule:
  - exact score: 3
  - correct result only: 1
  - Brazil multiplier: 2
- Verified terminal matches have zero prediction rows with null points.

## Audit

- Audit log operation: `manual_round32_real_results_and_points_fix`
- Audit log id: `9ee7e46f-8884-4af7-b3c3-dfa9b502a85c`
