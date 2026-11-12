"""
Option pricer: Black-Scholes vs Monte Carlo (Haq Malik)

Goal: price a European call/put on Alphabet (GOOGL) two ways, check they
agree, then compare my model price with the real market price.

Every run tries to pull live data from Yahoo Finance. If that fails (no
internet, Yahoo down, market data missing) it falls back to the numbers I
saved on 5 Nov 2026, so the script always runs.

Assumptions and limitations:
  1. Sigma (volatility) is fixed for the whole life of the option. Real
     markets have a volatility smile / surface.
  2. Sigma is estimated from the last year of daily prices, so it's
     backward-looking. The script also prints the 3-month figure and the
     market's implied volatility to compare.
  3. r is the 13-week US T-bill yield, chosen because it's close to the
     option's ~3.5-month life (not the 10-year).
  4. European exercise and no dividends. Listed GOOGL options are American
     (they can be exercised early) and GOOGL pays $0.22 a quarter, which
     lowers the stock price on each ex-dividend date. Both are ignored for now.
  5. No jumps (e.g. earnings-day gaps), no trading costs, and hedging is
     assumed to be continuous and free.

Next steps:
  - Price with implied volatility from live markets, not historical volatility.
  - Model the volatility smile (e.g. SABR or Heston).
  - Add dividends and early exercise (binomial tree).
  - Check put-call parity against live market prices, not just model prices.
  - Add a Monte Carlo standard error, Theta and Rho, and tests.
"""
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm
from scipy.optimize import brentq

# ---- 1. INPUTS -----------------------------------------------------------
TICKER = "GOOGL"
K = 290.0                    # strike: the price you can buy at
EXPIRY = date(2027, 2, 19)   # expiry date of the listed option

# Saved on 5 Nov 2026 - used if live data isn't available
FALLBACK = {
    "S": 282.57,             # GOOGL closing price
    "T": 106 / 365,          # 106 days to expiry, in years
    "r": 0.0399,             # 13-week US T-bill yield (3.99%)
    "sigma": 0.34,           # 1-year historical volatility
    "sigma_3m": 0.356,       # 3-month historical volatility
    "market_price": 20.50,   # mid of bid 20.25 / ask 20.75
    "as_of": "5 Nov 2026 (saved numbers)",
}


def get_live_inputs():
    """Pull today's numbers from Yahoo Finance. Returns None if anything fails."""
    try:
        import yfinance as yf

        T = (EXPIRY - date.today()).days / 365
        if T <= 0:
            raise ValueError(f"the {EXPIRY} option has expired - pick a later EXPIRY")

        stock = yf.Ticker(TICKER)
        closes = stock.history(period="1y")["Close"].dropna()  # pandas Series: date -> price (Yahoo sometimes leaves today blank)
        returns = np.log(closes / closes.shift(1)).dropna()    # each day's % move
        sigma = returns.std() * np.sqrt(252)                   # daily wiggle -> yearly (252 trading days)
        sigma_3m = returns[-63:].std() * np.sqrt(252)          # last ~3 months only

        r = yf.Ticker("^IRX").history(period="5d")["Close"].dropna().iloc[-1] / 100   # 13-week T-bill, 3.99 -> 0.0399

        calls = stock.option_chain(EXPIRY.isoformat()).calls
        row = calls[calls["strike"] == K].iloc[0]
        # bid/ask can show 0 when the market is shut, so use the last trade instead
        if row["bid"] > 0 and row["ask"] > 0:
            market_price = (row["bid"] + row["ask"]) / 2
        else:
            market_price = row["lastPrice"]

        return {
            "S": closes.iloc[-1], "T": T, "r": r, "sigma": sigma, "sigma_3m": sigma_3m,
            "market_price": market_price, "as_of": f"live, {closes.index[-1]:%d %b %Y}",
        }
    except Exception as e:
        print(f"Live data unavailable ({e}) - using saved numbers")
        return None


inputs = get_live_inputs() or FALLBACK
S, T, r, sigma = inputs["S"], inputs["T"], inputs["r"], inputs["sigma"]


# ---- 2. BLACK-SCHOLES (the formula) --------------------------------------
def black_scholes(S, K, T, r, sigma):
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    call = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    put = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    delta = norm.cdf(d1)                                   # call delta
    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    vega = S * norm.pdf(d1) * np.sqrt(T) / 100             # per 1 percentage point of volatility
    prob_itm = norm.cdf(d2)                                # chance the call finishes above K
    return call, put, delta, gamma, vega, prob_itm


def implied_vol(price, S, K, T, r):
    """Run Black-Scholes backwards: which sigma makes the model match the market price?"""
    # brentq keeps guessing sigma between 1% and 300% until model - market = 0
    return brentq(lambda s: black_scholes(S, K, T, r, s)[0] - price, 0.01, 3.0)


# ---- 3. MONTE CARLO (simulate lots of futures) ---------------------------
# Uses the same assumptions as Black-Scholes (fixed sigma, drift r),
# so agreement checks the code, not whether the model is realistic.
def monte_carlo(S, K, T, r, sigma, n=200_000, seed=1):
    rng = np.random.default_rng(seed)
    z = rng.standard_normal(n)
    # stock price at expiry in each simulated future
    ST = S * np.exp((r - 0.5 * sigma**2) * T + sigma * np.sqrt(T) * z)
    disc = np.exp(-r * T)
    call = disc * np.maximum(ST - K, 0).mean()   # average payoff, discounted
    put = disc * np.maximum(K - ST, 0).mean()
    return call, put, ST


call, put, delta, gamma, vega, prob_itm = black_scholes(S, K, T, r, sigma)
mc_call, mc_put, ST = monte_carlo(S, K, T, r, sigma)
iv = implied_vol(inputs["market_price"], S, K, T, r)

print(f"{TICKER} ${S:.2f} | strike ${K:.0f} | {T * 365:.0f} days | r {r:.2%} | data: {inputs['as_of']}")
print(f"Volatility: 1-year {sigma:.1%} (used) | 3-month {inputs['sigma_3m']:.1%} | market implied {iv:.1%}")
print()
results = pd.DataFrame(
    {"Call": [call, mc_call, inputs["market_price"]], "Put": [put, mc_put, None]},
    index=["Black-Scholes", "Monte Carlo", "Market (mid)"],
)
print(results.round(3))
print()
print(f"Delta {delta:.3f} | Gamma {gamma:.4f} | Vega {vega:.3f}")
# Put-call parity: call - put should equal S - K*e^(-rT)
print(f"Parity check: {call - put:.3f} vs {S - K * np.exp(-r * T):.3f}")
# Same 43%-style number two ways: the formula's area vs counting simulated futures
print(f"Chance call pays out: formula N(d2) {prob_itm:.1%} | simulation {(ST > K).mean():.1%}")

# ---- 4. CHARTS -----------------------------------------------------------
fig = plt.figure(figsize=(16, 5))

ax1 = fig.add_subplot(1, 3, 1)
spots = np.linspace(0.7 * S, 1.3 * S, 100)
ax1.plot(spots, [black_scholes(s, K, T, r, sigma)[0] for s in spots], label="Value today")
ax1.plot(spots, np.maximum(spots - K, 0), "--", label="Payoff at expiry")
ax1.set(title="Call value vs stock price", xlabel="Stock price", ylabel="Option value")
ax1.legend()

# Histogram split at the strike: the orange share of futures is the N(d2) probability
ax2 = fig.add_subplot(1, 3, 2)
bins = np.linspace(0.4 * S, 1.8 * S, 80)
ax2.hist(ST[ST <= K], bins=bins, color="steelblue", label="Call expires worthless")
ax2.hist(ST[ST > K], bins=bins, color="darkorange", label=f"Call pays out ({(ST > K).mean():.0%})")
ax2.axvline(K, color="red", label="Strike")
ax2.set(title=f"{len(ST):,} simulated prices at expiry", xlabel="Stock price", ylabel="Number of futures")
ax2.legend()

# Time decay (Theta): one line per "days left" - each line sinks towards the payoff as expiry nears
ax3 = fig.add_subplot(1, 3, 3)
for days, colour in zip([round(T * 365), 60, 30, 7], ["#08306b", "#2171b5", "#6baed6", "#c6dbef"]):
    if days <= round(T * 365):
        ax3.plot(spots, black_scholes(spots, K, days / 365, r, sigma)[0], color=colour, label=f"{days} days left")
ax3.plot(spots, np.maximum(spots - K, 0), "--", color="darkorange", label="At expiry (0 days)")
ax3.axvline(S, color="grey", linestyle=":", label="Price today")
ax3.set(title="Call value as time runs out", xlabel="Stock price", ylabel="Option value")
ax3.legend()

plt.tight_layout()
plt.savefig(Path(__file__).parent / "Alphabet Options Pricer BS and MC Graphs.png", dpi=120)   # next to this script
plt.show()
