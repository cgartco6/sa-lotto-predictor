# SA Lotto Predictor – Separate Predictors for Each Game

This repository contains **five independent predictors**, one for each lottery machine:

- Lotto (main)
- Lotto Plus 1
- Lotto Plus 2
- Powerball (main)
- Powerball Plus

Each script:
- Fetches its own historical draws from the official National Lottery API.
- Analyses the most common **group distribution** (G1=1‑10, G2=11‑20, G3=21‑30, G4=31‑58 for Lotto; G4=31‑50 for Powerball).
- Generates tickets that match that distribution (not forced to include your numbers).
- Suggests a bonus ball based on the most common group from history.
- Backtests on the last 50 draws to estimate win rate.

## Requirements

- Python 3.8+
- `requests` library

Install: `pip install -r requirements.txt`

## How to run

Run the script for the game you want to play **before** its draw:

```bash
python lotto.py          # for Lotto
python lotto_plus1.py    # for Lotto Plus 1
python lotto_plus2.py    # for Lotto Plus 2
python powerball.py      # for Powerball main
python powerball_plus.py # for Powerball Plus
