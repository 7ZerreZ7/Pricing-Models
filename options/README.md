# Options Pricer: Black-Scholes vs Monte Carlo

Prices a European call and put on Alphabet (GOOGL) two ways, checks they agree,
then compares the model's price with the **real market price** to see what
volatility the market is actually pricing in.

Built as a learning project while studying for CFA Level I and learning Python.

## What it does

1. **Pulls live data** from Yahoo Finance: the stock price, a year of daily
   prices (to estimate volatility), the 13-week US T-bill rate, and the market
   price of a real listed option (strike $290, expiring 19 Feb 2027).
2. **Prices the option with the Black-Scholes formula**, plus the Greeks
   Delta, Gamma and Vega.
3. **Prices it again with a Monte Carlo simulation**: 200,000 random futures
   for the stock, averaging the option's payoff across them.
4. **Works out implied volatility** by running Black-Scholes backwards until
   it matches the market price.
5. **Sanity checks**: put-call parity, and the chance the call pays out
   calculated two ways (formula vs counting simulations).
6. **Falls back to saved numbers** if live data isn't available, so it always runs.

## Example result (5 Nov 2026)

| | Call | Put |
| --- | --- | --- |
| Black-Scholes | 18.79 | 22.88 |
| Monte Carlo | 18.67 | 22.90 |
| Market (mid) | 20.50 | |

| Volatility | |
| --- | --- |
| 1-year historical (used by the model) | 34.0% |
| 3-month historical | 35.6% |
| **Implied by the market price** | **36.8%** |

Put-call parity holds (both sides −4.09), and the chance the call finishes
above the strike is 43.2% by both the formula and the simulation.

**What it shows:** the two methods agree, which checks the code. But the market
charges about $1.70 more than the model, because traders expect more volatility
ahead (36.8%) than the past year showed (34%). One likely reason is that
Alphabet usually reports earnings in early February, before this option expires.

The numbers change every run, because the data is live.

![Charts: call value vs stock price, simulated prices at expiry, and time decay](Alphabet%20Options%20Pricer%20BS%20and%20MC%20Graphs.png)

- **Left:** the option's value today vs its payoff at expiry. The gap is time value.
- **Middle:** 200,000 simulated prices at expiry. Orange = the call pays out.
- **Right:** the option losing value as expiry approaches (Theta, time decay).

## How to run

From the repository's top folder:

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt   # Windows
.venv\Scripts\python.exe options\option_pricer.py
```

To price a different option, change `TICKER`, `K` (strike) and `EXPIRY` at the
top of `option_pricer.py`. The expiry must be a date that has listed options.

## Assumptions and limitations

- **Volatility is fixed** for the option's whole life. Real markets have a
  volatility smile, where each strike trades at a different implied volatility.
- **Historical volatility is backward-looking.** Desks price with implied
  volatility instead.
- **European exercise, no dividends.** Listed GOOGL options are American and
  GOOGL pays a small dividend. Both are ignored.
- **No price jumps** (e.g. on earnings day), no trading costs, and hedging is
  assumed to be continuous and free.
- Monte Carlo uses the same assumptions as Black-Scholes, so their agreement
  checks the code, not whether the model matches reality.

## Next steps

- Show a standard error on the Monte Carlo price.
- Add Theta and Rho, and unit tests (put-call parity, textbook values).
- Model the volatility smile (SABR or Heston).
- Add dividends and early exercise (binomial tree).

## What I learned

Almost all of this was new to me when I started.

### Options and pricing

- What a call and a put are, the difference between the strike and the
  premium, and how an option's value splits into intrinsic value and time value.
- The fair premium is the **average payoff across all possible futures,
  discounted to today**. Black-Scholes does that with a formula; Monte Carlo
  does it by brute force.
- What the parts of Black-Scholes mean, not just how to type them:
  - `ln(S/K)`: how far the stock is from the strike.
  - `σ√T`: the typical move over the option's life. Uncertainty grows with
    the *square root* of time.
  - `N(d2)`: the chance the option pays out. It's an **area** under the bell
    curve (CDF), not a height (PDF). I mixed these up at first.
  - The **drift** term and **volatility drag** (−½σ²): +10% then −10% leaves
    you with 99, not 100.
- Why the discount rate is the risk-free rate (what cash could earn), not
  inflation, and why it should match the option's life.

### The Greeks

- Delta, Gamma, Vega, Theta and Rho, each checked with real numbers. For example,
  raising volatility from 34% to 35% adds about $0.61 to the call (Vega).
- I first confused Vega with volatility itself. Sigma is the input; Vega is
  how sensitive the price is to it.
- Delta hedging: one US contract covers 100 shares, so selling 10 contracts
  with Delta 0.505 means buying 505 shares to be delta-neutral.
- The trade-off between Gamma and Theta, and what negative Vega means for
  whoever sold the option.

### Markets

- Historical vs implied volatility, the volatility smile, and why more
  advanced models (SABR, Heston) exist.
- Put-call parity, and why arbitrage still happens in practice even though
  everyone checks for it: speed, inconsistent models, bad inputs.

### Python

- NumPy for fast maths on arrays vs pandas for tables of data, and why
  vectorised code can simulate 200,000 futures without a loop.
- Virtual environments, `try`/`except` fallbacks, f-strings, random seeds,
  and using a root-finder (`brentq`) to solve for implied volatility.
- Debugging real data: Yahoo once returned a blank closing price, which broke
  every calculation until the code dropped empty rows.

### Approach

- Start with a problem and learn the maths it needs, rather than picking a
  model first and looking for somewhere to use it.

## Notes

Built with help from an AI assistant (Claude) as a learning tool. I worked
through every line until I could explain it.

For learning purposes only. Not investment advice.
