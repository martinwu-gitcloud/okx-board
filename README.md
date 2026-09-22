# OKX Perpetual Swap Board / OKX 永续合约看板

Single-file dashboard for OKX **USDT perpetual swaps**, plus a local **1,000 USDT / 50x paper account**. No login, no API key.

单文件看盘页：OKX USDT 永续行情 + 本地 **1000U / 50x 模拟盘**。无需登录和 API Key。

**Disclaimer / 声明：** Not trading advice. Not official OKX or TradingView. Paper PnL is an estimate.  
看盘与模拟，不构成投资建议。

---

## Layout / 页面

1. Toolbar — add symbol, timeframe, sort, sync URL, **margin input (USDT)**
2. TradingView **technical analysis + economic calendar** (no big chart)
3. Market overview
4. Paper account: equity, free cash, used margin, realized PnL, 24h/48h best coin
5. Funding / heatmap / liquidations / vs-BTC
6. Four compact cards per row on desktop

TradingView 大图和滚动胶带已去掉，只留技术分析与财经事件。点卡片只切换分析品种。

---

## Paper account / 模拟盘规则

| Rule | EN | 中文 |
| --- | --- | --- |
| Bank | Starts at **1,000 USDT** | 本金 1000U |
| Leverage | 50x linear, isolated-style | 50 倍 |
| Actions | You click **开多 / 开空 / 平仓 / 加保证金** | 自行决策，不是自动下单 |
| Margin cap | Each add ≤ remaining cash, and ≤ 1,000 | 不能超过可用资金，单次不超过本金 |
| Close | Records close price, PnL (USDT), return on margin | 自动记平仓价、收益额、收益率 |
| Loss | Close in red **or liquidation** counts as 输 | 亏损平仓或打到参考强平记输 |
| Wipe | Equity gone → bank resets to 1,000 and you can open again | 本金亏完自动回 1000U 再找机会 |
| Best coin | Highest win rate among closes in last 24h / 48h | 每 24/48 小时展示胜率最高的币 |

Liquidation line ≈ entry × (1 ± 1/50). Fees and OKX MMR are ignored.

顶部「保证金 U」是下一笔开仓或加仓要用的金额。卡片底部四个按钮执行。

Data lives in `localStorage` (`okx_paper_v1`).

---

## Cards / 卡片

- Session change vs **08:00 UTC+8**
- Mini candles with last / high / low / suggested long-short levels
- Books, flow, large prints
- Rule-based 24–48h bias (EMA, RSI, channel, momentum, funding, flow) — **not an LLM**
- Paper position line: side, margin, entry time, UPL, liq

BTC and ETH stay pinned first.

---

## Run / 打开

```bash
python3 -m http.server 8080
```

GitHub Pages: upload this board as `index.html` and this file as `README.md`.

Sync watchlist with the hash URL from **复制同步链接**. Paper account does **not** sync across devices.

---

## Data / 数据

OKX public WS/REST, TradingView widgets (TA + events only), alternative.me, CoinGecko (CORS may block overview).

---

## Not included / 做不到

Live orders on your OKX account, guaranteed forecasts, cloud sync of the 1,000U book.
