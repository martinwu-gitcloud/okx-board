# OKX 永续合约看板

自建看盘站：OKX USDT 永续行情 + 本地规则研判 + 多用户登录门。  
适合放在 Google Cloud 虚拟机上，用公网 IP 访问，不必买域名。

只看盘，不交易，不是官方产品，不构成投资建议。

---

## 文件

| 文件 | 作用 |
| --- | --- |
| `server.py` | 登录门、代理 OKX、账号与自选、运行时长 |
| `login.html` | 登录页 |
| `okx-swap-board.html` | 看板主页 |
| `admin.html` | 账号管理（管理员 / SVIP） |
| `data/` | 运行后自动生成，**不要覆盖** |

`data/` 里常见内容：

- `users.json` 账号、角色、有效期、最后登录
- `watchlists/<账号>.json` 每人本自选
- `site_born.txt` 本站首次启动时间（运行时长用，重启不清零）
- `login_guard.json` 登录失败锁定
- `ip_geo.json` 登录 IP 归属地缓存

---

## 启动

```bash
cd ~/okx-board
python3 server.py >> board.log 2>&1
```

默认监听 `0.0.0.0:8080`。建议放在 tmux 里：

```bash
tmux new -s board
cd ~/okx-board
python3 server.py >> board.log 2>&1
# Ctrl+B 再 D 脱离
```

访问：

- 登录 `http://虚拟机公网IP:8080/login`
- 看板 `/board`
- 账号管理 `/admin`

更新 HTML / `server.py` 后把文件拷进 `~/okx-board/`。改了 `server.py` 必须停掉再启动；只改 HTML 强制刷新浏览器即可。

---

## 页面功能

### 看板

- 默认置顶 BTC / ETH / BNB，一行三张卡片（手机改为单列）
- 自选、周期（1m～1D）、排序
- 卡片含：价格与早 8 点涨跌、24h 高低量、资金费率及含义（多头偏多 / 空头偏多 / 均衡）、相对 BTC、持仓 OI、点位、盘口、主动买卖、大单、24–48h 研判
- 技术分析两行四个周期：15 分钟、1 小时、4 小时、1 天
- 顶部保留：恐慌贪婪、山寨季、总市值、市值占比、自选热力图、爆仓热力、相对 BTC 强弱（全站资金费率总表已去掉，费率看每张卡片）
- 财经日历、赞助通道
- 顶栏：本站已稳定运行、最后修改时间、登录账号、角色、有效期、修改密码

### 登录与账号

| 角色 | 权限 |
| --- | --- |
| 管理员 | 全部，永久；可改角色、续期、看密码、批量删除 |
| SVIP | 看看板 + 添加账号，不能改有效期 |
| VIP | 只看看板 |

- 新账号默认 1 天有效期，过期提示「账户已到期」，账号不会自动删除
- 可续 +1 / +15 / +30 天或永久，也可清空有效期
- 主管理员 `13517601192` 角色锁死，不能改角色、不能删除
- 每个登录号自选独立，互不串
- 「记住登录 30 天」只延长 Cookie，不把密码写进浏览器

管理员在账号管理可见：角色、状态、开启时间、有效期、最后登录、IP、归属地、当前密码（旧号若只有哈希，重置一次后才显示明文）。

---

## 防护（已接上的）

1. 登录 10 分钟内失败 5 次，锁定 15 分钟（按 IP + 账号）
2. 失败写入 `board.log`，可用 fail2ban 封 IP（jail `okx-board`，封 1 小时）
3. GCP 防火墙：只把 **tcp:22** 来源改成你的 `公网IP/32`；**tcp:8080 必须保持 `0.0.0.0/0`**，否则外人打不开网站
4. 建议尽快改掉默认管理员密码

fail2ban 状态：

```bash
sudo fail2ban-client status okx-board
```

---

## 接口（给维护用）

| 路径 | 说明 |
| --- | --- |
| `POST /api/login` | 登录 |
| `GET /api/me` | 当前用户 |
| `POST /api/me/password` | 自己改密 |
| `GET/PUT /api/watchlist` | 自选 |
| `GET/POST/PATCH /api/users` | 账号管理 |
| `POST /api/users/batch-delete` | 批量删除 |
| `GET /api/uptime` | 运行时长与最后修改时间 |
| `/okx/api/v5/...` | 代理 OKX REST |
| `/ext/fng` `/ext/cg` `/ext/cmc` | 指数代理 |

环境变量（可选）：

```bash
BOARD_USER=13517601192
BOARD_PASS=你的初始密码
HOST=0.0.0.0
PORT=8080
```

未设置时仍使用代码里的种子管理员。种子管理员角色不会被改掉。

---

## 更新文件时注意

1. 只覆盖四个源文件，不要覆盖整个 `okx-board/data/`
2. 浏览器 SSH 上传常变成 `server_(10).py` 这种名字，必须 `cp` 成不带编号的文件名
3. 拷完核对体积，再重启 `server.py`
4. 浏览器使用强制刷新（Ctrl+F5）

---

## 不做的事

- 不代下单、不接交易 API
- Telegram Bot 尚未接入（可做提醒与查询，不建议用 Bot 下单）
