# OKX Perpetual Swap Board / OKX 永续合约看板

Single-file page for watching **OKX USDT-margined perpetual swaps** (`*-USDT-SWAP`). Open the HTML, no login, no API key, no live orders.

单文件页面，盯 OKX USDT 永续合约。打开即用，无需登录和 API Key，**不会下单**。

**Disclaimer / 声明：** For market watching only. The 24–48h block is a local rule model, not a bank, broker, or official OKX / TradingView product. Not investment advice.

仅供看盘。底部研判是浏览器里的规则模型，不是券商、不是官方产品，不构成投资建议。

---

## Open / 打开

```bash
python3 -m http.server 8080
```

Then visit `http://localhost:8080/okx-swap-board.html`.

GitHub Pages: upload this file as `index.html` together with this `README.md`. Use `https://`, not `file://`, so OKX WebSocket and the calendar iframe can load.

用 GitHub Pages 时请把看板存成 `index.html`，和本说明一起上传。请走 https，不要用 `file://`。

---

## Toolbar / 顶栏

| Control / 控件 | What it does / 作用 |
| --- | --- |
| Symbol box / 输入框 | Type `BTC` or `BTC-USDT-SWAP` |
| 添加合约 | Add a USDT perp to the watchlist |
| Timeframe / 周期 | Mini candles: 1m, 5m, 15m, 1H, 4H, 1D |
| Sort / 排序 | Watchlist order, % change, volume |
| 只留默认 | Reset to BTC + ETH + BNB |
| 复制同步链接 | Copy URL with `#BTC-USDT-SWAP,ETH-USDT-SWAP,...` so another device can open the same list |
| 财经日历 | Toggle TradingView economic calendar (hidden until opened) |
| Status dots / 状态灯 | Public ticker WS and business candle WS |

Default list is **BTC-USDT-SWAP, ETH-USDT-SWAP, BNB-USDT-SWAP**. Those three stay pinned first and cannot be removed. Other coins you add sit after them.

默认自选是 BTC / ETH / BNB，永远排在最前且不能删除。其它合约自己添加，排在这三个后面。

The watchlist is stored in `localStorage` and in the URL hash when the page is allowed to write history (not inside `about:srcdoc` previews).

自选存在浏览器本地。能改地址栏时也会写进网址 `#` 段，方便电脑改、手机打开同一条链接。

---

## Market overview / 市场总览

Four boxes under the toolbar:

1. **Fear & Greed / 恐慌贪婪指数** — alternative.me style 0–100 gauge  
2. **Altseason estimate / 山寨季估算** — rough 0–100 from BTC vs alt share  
3. **Crypto cap & 24h volume / 总市值与成交额**  
4. **Dominance + OKX OI / 市值占比与 OKX 永续持仓** — BTC / ETH / other, plus BTC and ETH open interest on OKX  

These refresh on a timer from public endpoints. If a source is blocked, the box stays `--`.

这些盒子定时拉公共数据。接口被拦时显示 `--`。

---

## Intel row / 情报栏

1. **Funding / 资金费率** — watchlist ranked by funding, plus countdown to next funding  
2. **Session heatmap / 涨跌热力图** — change vs **08:00 Beijing time (UTC+8)**  
   - Row 1: default coins BTC, ETH, BNB  
   - Row 2+: coins you added  
3. **Liquidation heat / 爆仓热力** — recent OKX force-closes, long vs short notional  
4. **Vs BTC + LS ratio / 相对 BTC 与多空人数比** — session out/underperformance vs BTC, plus long/short account ratio when the public endpoint is reachable  

爆仓和人数比依赖公共接口，偶发跨域失败时该格会空。

---

## Contract card / 合约卡片

Wide screens show **three cards per row** (two below ~1100px, one on phones). Each card, top to bottom:

宽屏一行三张（窄屏两张，手机一张）。卡片从上到下：

1. Icon, name, instId; extra coins have ×  
2. Last price and **session change vs 08:00 UTC+8**  
3. 24h high / low / volume, funding, strength vs BTC, open interest  
4. OI change, long/short ratio, next funding countdown  
5. Mini candlesticks for the selected timeframe, with last / high / low labels and long-short guide lines  
6. Suggested levels: open-long, add-long, open-short, add-short (EMA pullback + 20-bar channel + ATR)  
7. Top-of-book, 3 bids and 3 asks  
8. Taker buy vs sell bar (about the last minute)  
9. Unusual prints + a small average table  
10. 24–48h rule block  

Icons try several public CDN paths; if all fail, a letter badge is used.

图标会依次试几个公共源，都失败则显示字母。

---

## Unusual prints / 大单异动

Trades that are large versus the recent book mid are listed with time, side, price and size.

相对盘口明显偏大的成交会记入列表。

| Class / 类型 | Color / 颜色 |
| --- | --- |
| Large buy / 大额买单 | Light green / 浅绿 |
| Large sell / 大额卖单 | Light red / 浅红 |
| Huge buy / 超大买单扫货 | Dark green / 深绿 |
| Huge sell / 超大卖单砸盘 | Dark red / 深红 |

Under the list, a table shows **count, VWAP, average size, and notional** for buy prints vs sell prints in the current buffer.

列表下方表格给出当前缓冲里买单 / 卖单的笔数、均价、均量、金额。

---

## 24–48h outlook / 综合研判

Local rules only. Votes are **weighted**, not a simple count.

只在本地算，按权重合成，不是每条规则一票到底。

Base votes:

- EMA 12 / 26  
- RSI 14  
- 20-bar channel (breakout vs mean-reversion)  
- 24h / session momentum  
- Funding crowding  
- Taker flow  

Extra votes:

- **ADX regime / ADX 环境** — ADX ≥ 25 treats the tape as trend (EMA, momentum, 4H structure get more weight; RSI and mean-reversion get less). ADX ＜ 20 is the opposite.  
- **OI vs price / 持仓验证** — price up + OI up leans long; price down + OI up leans short; price up + OI down weakens the long vote  
- **Vs BTC / 相对 BTC** — skipped on BTC itself  
- **4H structure / 4小时结构** — last six 4H bars vs the six before (HH+HL vs LH+LL)  

Direction score is 0–100:

- **≥ 60** → lean long / 开多  
- **≤ 40** → lean short / 开空  
- **41–59** → flat / 观望  

The card also stores a local “decision” (side, time, entry, average) and, after 24h / 48h, marks win/loss if price moved more than 0.1% the right way. Same coin, same side, waits 8 hours before another stored decision. Small samples mean nothing.

卡片会记下方向、时间、开仓价。满 24 / 48 小时后按价格涨跌结算；同币同向 8 小时内不重复记账。样本少时胜率没有意义。

The one-line **技术分析 · 1小时** label (强烈买入 / 买入 / 中性 / 卖出 / 强烈卖出) is the same score, not a live TradingView gauge.

最底下那行「技术分析」只是同一套方向分的文字档，不是 TradingView 实时仪表。

There is **no** 1,000 USDT / 50x paper account in this build.

当前版本**没有** 1000U / 50 倍模拟盘。

---

## Data / 数据

- OKX public WebSocket: tickers, trades, funding, books5, liquidations, candles  
- OKX public REST on first load (ticker, candles 1H / 4H / 1D, funding)  
- Overview extras from public market APIs when CORS allows  

Reconnect and ping/pong are handled in the page. No private account endpoints.

页面自己重连和心跳。不碰任何需要登录的接口。

---

## What this is not / 不是什么

- Not an exchange, broker, or signal service  
- Does not place, cancel, or copy trades on OKX  
- Does not promise that the rule score will win  
- Calendar and some ratios need a normal https origin  

---

## Files / 文件

- `okx-swap-board.html` — the whole app  
- `README.md` — this note  

Keep both when you publish a new version.
