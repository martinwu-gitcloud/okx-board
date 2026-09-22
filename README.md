# OKX Perpetual Swap Board / OKX 永续合约看板

Single-file dashboard for watching **OKX USDT-margined perpetual swaps**. The browser talks to public APIs only. No login, no API key, no backend of our own.

单文件看盘页，盯 **OKX USDT 永续合约**。浏览器直连公共接口，无需登录、无需 API Key、没有自建服务器。

**Disclaimer / 声明：** Market-watching tool only. Not trading advice, not an official OKX or TradingView product.  
只用于看盘，不构成投资建议，也不是欧易或 TradingView 官方产品。

---

## What you see / 页面结构

Top to bottom:

1. Toolbar — add symbol, timeframe, sort, reset to BTC/ETH, copy sync URL, expand/collapse charts  
2. **TradingView dock (collapsed by default)** — ticker tape, advanced chart, technical analysis, economic calendar  
3. Market overview — Fear & Greed, altseason estimate, total cap, BTC/ETH dominance + OKX OI  
4. Paper win-rate of the local 24–48h rules  
5. Intel row — funding ranks, session heatmap, liquidation bars, strength vs BTC + long/short ratio  
6. **Four compact contract cards per row** on a wide screen  

从上到下：工具栏 → 默认收起的 TradingView → 市场总览 → 研判战绩 → 费率/热力/爆仓/相对BTC → 一行最多四张合约卡片。

---

## Contract cards / 合约卡片

Each card is a compact desk for one SWAP:

- Live last price  
- Change vs **08:00 Beijing time (UTC+8)** session open, not rolling 24h  
- 24h high / low / volume, funding rate  
- Strength vs BTC (session change minus BTC session change)  
- Open interest and 1h OI change  
- Account long/short ratio, countdown to next funding  
- Mini candlestick (1m / 5m / 15m / 1H / 4H / 1D)  
- Top-of-book 3 bids / 3 asks (`books5`)  
- Aggressive buy/sell flow in the last minute  
- Large-print alerts + average price / size / notional  
- Rule-based 24–48h bias, logged entry side and average entry  

BTC-USDT-SWAP and ETH-USDT-SWAP stay pinned first and cannot be removed. Other symbols you add yourself (`SOL` or `SOL-USDT-SWAP`).

默认只有 BTC、ETH，且永远排在最前、不能删除。其他合约自己添加。宽屏一行固定四卡，不会自动排出第五张。

Click a card to select it for TradingView (`OKX:BTCUSDT.P` style). Expand the chart dock to actually load the widget.

点击卡片只切换当前品种；点「展开图表」后才会加载 TradingView。

---

## Intel row / 情报四宫格

| Panel | EN | 中文 |
| --- | --- | --- |
| Funding | Watchlist sorted by funding + time to next settlement | 自选费率排序 + 下次结算倒计时 |
| Heatmap | Color tiles of session change vs 08:00 UTC+8 | 相对早8点涨跌热力 |
| Liquidations | Approx. last-hour long vs short liq (OKX rubik stats) | 近1小时多空爆仓粗分 |
| vs BTC | Session relative strength and long/short account ratio | 相对大饼强弱 + 多空人数比 |

These stats are polled on a slow timer because OKX trading-data endpoints are rate-limited. Empty `--` usually means CORS or a cold symbol, not a crash.

统计接口有频次限制，第一次可能要十几秒才齐。个别格子一直 `--` 多为跨域或该币没有该项数据。

---

## 24–48h outlook / 本地研判

Not an LLM. Votes from EMA trend, RSI, channel, session momentum, funding, and taker flow are averaged into a **0–100 direction score**:

- **≥ 60** → paper long  
- **≤ 40** → paper short  
- **41–59** → flat, not counted  

Same coin + same side at most once every 8 hours. After 24h and 48h the stored entry is compared with live price (±0.1%). Win rate is localStorage only. Small samples mean nothing.

不是人工智能预测。方向分、开仓均价、浮盈写在卡片底部；总胜率在战绩栏。

---

## Sync / 同步

Watchlist lives in `localStorage` and in the URL hash:

```text
https://<user>.github.io/<repo>/#BTC-USDT-SWAP,ETH-USDT-SWAP,SOL-USDT-SWAP
```

**复制同步链接** copies that URL. Phone and desktop stay in sync only if they open the same hash. There is no cloud account.

自选和战绩只存在当前浏览器。跨设备靠同一条带 `#` 的网址。

---

## Run / 怎么打开

### Local

Rename the board file to `index.html` if you want, then:

```bash
python3 -m http.server 8080
```

Open `http://127.0.0.1:8080/`. Double-clicking the file works for OKX sockets; TradingView widgets are more reliable over `http://` or `https://`.

本地双击也能看 OKX 行情；TradingView 组件更建议用本地服务器或网站。

### GitHub Pages

1. Public repo  
2. Upload board as **`index.html`**, this file as **`README.md`**  
3. Settings → Pages → branch `main`, folder `/ (root)`  
4. Wait a minute for `https://<user>.github.io/<repo>/`

---

## Data sources / 数据来源

- OKX public WS/REST: tickers, funding, trades, books5, candles, OI, rubik long/short and liquidation history  
- TradingView widgets: tape, advanced chart, technical analysis, events calendar  
- alternative.me Fear & Greed  
- CoinGecko global cap / dominance (may be blocked by CORS)  
- Icons: OKX CDN, then CoinCap, then a letter tile  

---

## Layout notes / 排版

- Wide desktop: 4 cards per row, no more  
- ~1280px: 2 cards  
- Phone: 1 card  
- TradingView dock stays collapsed so four cards can share the first screen  

---

## Not included / 做不到

- Place orders or read your OKX account  
- Coinglass-grade liquidation maps  
- Instant two-device sync without sharing the URL  
- Guaranteed forecasts  

不能下单、不能保证涨跌、不复制链接就不会跨设备同步。
