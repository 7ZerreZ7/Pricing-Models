# Pricing Models

Financial pricing models I'm building in Python while studying for CFA Level I
and learning quantitative finance. Each model has its own folder and write-up.

| Model | Folder | Status |
|---|---|---|
| Options pricer: Black-Scholes vs Monte Carlo, with live data and implied volatility | [`options/`](options/) | Done |
| FICC (fixed income, currencies and commodities) models | `ficc/` | Planned |

## How to run

From this folder:

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt   # Windows
.venv\Scripts\python.exe options\option_pricer.py
```

## Notes

Built with help from an AI assistant (Claude) as a learning tool. I work
through every line until I can explain it.

For learning purposes only. Not investment advice.
