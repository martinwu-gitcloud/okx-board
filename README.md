# OKX Perpetual Swap Board / OKX 永续合约看板

Single-file dashboard for watching **OKX USDT perpetual swaps**. No login, no API key, no live orders.

单文件看盘页，盯 OKX USDT 永续。无需登录和 API Key，不会下单。

**Disclaimer / 声明：** Market-watching only. Not trading advice. Not official OKX or TradingView.

---

## What is on the page / 页面有什么

1. Toolbar — add/remove symbols, timeframe, sort, reset to BTC/ETH, copy sync URL  
2. TradingView TA widget inside each card; economic calendar is collapsed until you open it  
3. Market overview — Fear & Greed, altseason estimate, cap, dominance, OKX OI  
4. Rule-based 24–48h outlook stats (not a 1000U paper account)  
5. Funding ranks, session heatmap, recent liquidations, strength vs BTC  
6. Four compact contract cards per row on a wide screen  

BTC-USDT-SWAP and ETH-USDT-SWAP stay pinned first.

---

## Cards / 卡片

- Last price and change vs **08:00 Beijing time (UTC+8)**  
- 24h high / low / volume, funding, OI, OI change, long/short ratio  
- Mini candles with last / high / low and suggested long-short levels  
- Top-of-book, taker flow, large-print alerts  
- Rule vote: EMA, RSI, channel, momentum, funding, flow, plus ADX regime weights, OI vs price, strength vs BTC, 4H structure  
- Direction score: ≥60 lean long, ≤40 lean short, otherwise flat  

There is **no** 1,000 USDT / 50x auto paper book anymore.

---

## Run / 打开

```bash
python3 -m http.server 8080
```

GitHub Pages: upload as `index.html` plus this `README.md`.

Watchlist syncs through the URL hash from **复制同步链接**.
