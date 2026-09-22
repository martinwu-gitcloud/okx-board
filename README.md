# OKX Perpetual Swap Board / OKX 永续合约看板

Single-file OKX USDT-perp dashboard with a **local 1,000 USDT / 50x paper book that opens and closes by itself** from the 24–48h rule engine.

单文件看板。模拟盘本金 1000U、50 倍，**按 24–48 小时研判和推荐点位自动开平仓**，不用手点。

**Disclaimer / 声明：** Not live trading. Not investment advice.

---

## Auto paper / 自动模拟

1. Direction score ≥60 → look for **long** at the suggested 开多 price (EMA / mid pullback).  
2. Score ≤40 → look for **short** at the suggested 开空 price.  
3. 41–59 → stay flat.  
4. If price reaches the **加仓** level once, the system may add margin (still ≤ cash and ≤ 1000).  
5. Close when: opposite signal, take-profit at the other side’s open level, **24h** timeout, or **liquidation** (~2% adverse at 50x).  
6. Each close stores price, USDT PnL, return on margin. Loss or liq = 输.  
7. If the book is wiped, bank resets to **1000U** and it hunts again.  
8. 24h / 48h boxes show the **coin with the best close win-rate**.  
9. Same coin waits **8 hours** after a close before a new auto entry.

顶栏「自动保证金 U」只决定每笔自动开仓用多少钱，默认 100。

---

## Also on the page / 其它

- Session % vs 08:00 UTC+8, mini candles with prices  
- Funding, heatmap, recent liquidations, vs-BTC  
- TradingView **TA + events only** (no big chart)  
- Four cards per row on a wide screen  
- BTC / ETH pinned  

---

## Run

Upload as `index.html` + this `README.md` on GitHub Pages, or:

```bash
python3 -m http.server 8080
```

Watchlist syncs via URL hash. The 1000U book stays in this browser only.
