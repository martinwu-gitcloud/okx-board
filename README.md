# OKX Perpetual Swap Board / OKX 永续合约看板

A single-file, no-login dashboard for watching **OKX USDT perpetual swaps** in one page: live prices, mini candles, large-trade alerts, market overview, and a local 24–48h rule-based outlook.

单文件、免登录的 OKX **USDT 永续合约**看板：同一页看实时价格、迷你 K 线、大单异动、市场总览，以及本地 24–48 小时规则研判。

**Disclaimer / 声明：** This is a market-watching tool, not trading advice and not an official OKX product.  
这是看盘工具，不是投资建议，也不是欧易官方产品。

---

## What it does / 这是干什么的

Open `index.html` (or the GitHub Pages URL) and the browser talks directly to OKX public WebSocket / REST. No API key.

打开页面后，浏览器直接连 OKX 公共行情接口，不需要 API Key。

| EN | 中文 |
| --- | --- |
| Default watchlist: BTC and ETH perpetuals, always pinned first | 默认盯 BTC、ETH 永续，并且永远排在最前 |
| Add / remove other SWAP symbols yourself | 自行添加、删除其他合约 |
| Price card + mini candlestick | 价格卡片 + 迷你 K 线 |
| Change % vs **08:00 UTC+8** session open | 涨跌幅按 **北京时间早上 8 点** 开盘价 |
| Large buy/sell prints and average of those alerts | 大单异动，以及异动单均价 / 均量 / 金额 |
| Market snapshot: Fear & Greed, altseason estimate, cap, OKX OI | 市场总览：恐慌贪婪、山寨季估算、总市值、OKX 持仓 |
| 24–48h multi-rule bias (not an LLM) | 24–48 小时多策略投票研判（不是大模型预测） |
| Paper win-rate log after 24h / 48h | 到期后统计该决策的本地胜率 |

---

## Features / 功能说明

### Watchlist / 自选

- Type `BTC` or `BTC-USDT-SWAP` and click **添加合约**.
- BTC / ETH cannot be removed and stay on the left.
- Timeframes: 1m / 5m / 15m / 1H / 4H / 1D.
- Sort: watch order, change, volume.

输入 `BTC` 或完整 `BTC-USDT-SWAP` 即可添加。BTC、ETH 不能删，始终置顶。周期和支持排序见上。

### Session change / 早8点涨跌

Percent change uses the OKX daily bar that opens at **08:00 Beijing time** (UTC+8). Before 08:00 it still compares to the previous 08:00 open.

涨跌幅对照 UTC+8 当日 08:00 开盘。当天 8 点前仍对比前一天 8 点。

### Alerts / 异动

Trades that look unusually large versus recent prints are listed on each card, with separate buy/sell average price, size, and notional.

相对近期成交偏大的单会记在卡片里，并分买卖统计均价、均量、金额。

### Outlook & win rate / 研判和胜率

Strategies averaged into a 0–100 **direction score**:

- **≥ 60** → logged as long  
- **≤ 40** → logged as short  
- **41–59** → flat, not counted  

Same coin + same side is logged at most once every 8 hours. After 24h and 48h the stored entry is compared with the live price (±0.1% buffer). Sample size matters; a handful of trades is not a real edge.

多策略投票合成方向分：≥60 记开多，≤40 记开空，中间观望不计入。同币同向 8 小时最多一笔。满 24/48 小时后对比入场价结算。样本少时胜率没有统计意义。

---

## Run locally / 本地打开

1. Download `okx-swap-board.html` and rename it to `index.html` if you want.
2. Double-click it, or serve the folder:

```bash
python3 -m http.server 8080
```

Then open `http://127.0.0.1:8080/`.

手机和电脑若只是本地文件，自选名单不会自动同步。

---

## GitHub Pages / 放到网站上

1. Create a public repo.  
2. Upload this file as **`index.html`**.  
3. Settings → Pages → Deploy from branch `main` / root.  
4. Open `https://<user>.github.io/<repo>/`.

Use **复制同步链接** so phone and desktop share the same hash watchlist:

`https://<user>.github.io/<repo>/#BTC-USDT-SWAP,ETH-USDT-SWAP,SOL-USDT-SWAP`

---

## Data sources / 数据来源

- Prices, funding, trades, candles, open interest: **OKX public API**
- Fear & Greed: alternative.me  
- Market cap / dominance: CoinGecko (may fail if CORS blocks the browser)  
- Icons: OKX CDN, with CoinCap / letter fallback  

Some overview widgets can stay on `--` if a third-party API blocks the browser. Swap cards should still work.

总览个别接口可能被浏览器跨域拦住，合约卡片一般不受影响。

---

## Privacy / 隐私

Watchlist and win-rate log stay in **this browser’s localStorage**. Nothing is sent to a backend of this project.

自选和战绩只存在当前浏览器，本项目没有自己的服务器收数据。

---

## Not included / 做不到的

- Place orders or read your OKX account  
- Guaranteed forecasts  
- Instant sync between devices without sharing the URL  
- Official CoinMarketCap widgets cloned 1:1  

不能下单、不能保证涨跌、不复制链接就不会跨设备同步。
