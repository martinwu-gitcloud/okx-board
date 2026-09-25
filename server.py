#!/usr/bin/env python3
"""Login gate: multi-user, per-user watchlists, roles and expiry."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
import urllib.error
import urllib.request
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
USERS_FILE = DATA / "users.json"
WATCH_DIR = DATA / "watchlists"
BOARD = ROOT / "okx-swap-board.html"
LOGIN = ROOT / "login.html"
ADMIN_PAGE = ROOT / "admin.html"
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8080"))

SEED_ADMIN = os.environ.get("BOARD_USER", "13517601192")
SEED_PASS_SHA = hashlib.sha256(os.environ.get("BOARD_PASS", "wyx654777").encode("utf-8")).hexdigest()

OKX_PREFIX = "https://www.okx.com"
EXT = {
    "/ext/fng": "https://api.alternative.me/fng/?limit=1",
    "/ext/cg": "https://api.coingecko.com/api/v3/global",
    "/ext/cmc": "https://pro-api.coinmarketcap.com/public-api/v1/altcoin-season-index/latest",
}

ROLES = ("admin", "svip", "vip")
ROLE_LABEL = {"admin": "管理员", "svip": "SVIP", "vip": "VIP"}
ADD_DAYS = (1, 15, 30)
FAIL_WINDOW = 600
FAIL_MAX = 5
LOCK_SECS = 900
GUARD_FILE = DATA / "login_guard.json"
_GUARD_LOCK = threading.Lock()

DATA.mkdir(exist_ok=True)
WATCH_DIR.mkdir(exist_ok=True)
SECRET_FILE = DATA / "secret.txt"
if SECRET_FILE.exists():
    SECRET = SECRET_FILE.read_text().strip().encode()
else:
    SECRET = secrets.token_hex(32).encode()
    SECRET_FILE.write_text(SECRET.decode())


def sha_pass(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


def norm_role(role: str | None) -> str:
    if role == "user":
        return "vip"
    if role in ROLES:
        return role
    return "vip"


def ensure_fields(name: str, rec: dict | None) -> dict:
    rec = dict(rec or {})
    rec["role"] = norm_role(rec.get("role"))
    now = int(time.time())
    if not rec.get("created_at"):
        rec["created_at"] = now
    if rec["role"] == "admin":
        rec["expires_at"] = 0
    elif "expires_at" not in rec:
        rec["expires_at"] = 0
    rec.setdefault("last_login", 0)
    rec.setdefault("last_ip", "")
    return rec


def load_users() -> dict:
    raw = {}
    if USERS_FILE.exists():
        try:
            raw = json.loads(USERS_FILE.read_text(encoding="utf-8"))
        except Exception:
            raw = {}
    if not raw:
        raw = {SEED_ADMIN: {"pass": SEED_PASS_SHA, "role": "admin"}}
    changed = False
    users = {}
    for name, rec in raw.items():
        fixed = ensure_fields(name, rec)
        if fixed != rec:
            changed = True
        users[name] = fixed
    if SEED_ADMIN not in users:
        users[SEED_ADMIN] = ensure_fields(SEED_ADMIN, {"pass": SEED_PASS_SHA, "role": "admin"})
        changed = True
    if changed or not USERS_FILE.exists():
        save_users(users)
    return users


def save_users(users: dict) -> None:
    USERS_FILE.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")


def role_of(user: str) -> str:
    return ensure_fields(user, load_users().get(user)).get("role") or "vip"


def is_expired(rec: dict | None) -> bool:
    rec = rec or {}
    if norm_role(rec.get("role")) == "admin":
        return False
    exp = int(rec.get("expires_at") or 0)
    if exp == 0:
        return False
    return exp < time.time()


def is_permanent(rec: dict | None) -> bool:
    rec = rec or {}
    if norm_role(rec.get("role")) == "admin":
        return True
    return int(rec.get("expires_at") or 0) == 0


def public_row(name: str, rec: dict, self_name: str | None = None) -> dict:
    rec = ensure_fields(name, rec)
    expired = is_expired(rec)
    return {
        "user": name,
        "role": rec["role"],
        "role_label": ROLE_LABEL.get(rec["role"], rec["role"]),
        "self": name == self_name,
        "created_at": int(rec.get("created_at") or 0),
        "expires_at": 0 if rec["role"] == "admin" else int(rec.get("expires_at") or 0),
        "permanent": is_permanent(rec),
        "expired": expired,
        "status": "已到期" if expired else "正常",
        "last_login": int(rec.get("last_login") or 0),
        "last_ip": rec.get("last_ip") or "",
        "last_geo": rec.get("last_geo") or "",
        "locked": name == SEED_ADMIN,
    }


def client_ip(handler) -> str:
    fwd = (handler.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
    if fwd:
        return fwd[:64]
    real = (handler.headers.get("X-Real-IP") or "").strip()
    if real:
        return real[:64]
    try:
        return str(handler.client_address[0])
    except Exception:
        return ""


def _load_guard() -> dict:
    if GUARD_FILE.exists():
        try:
            return json.loads(GUARD_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {"ip": {}, "user": {}}
    return {"ip": {}, "user": {}}


def _save_guard(g: dict) -> None:
    GUARD_FILE.write_text(json.dumps(g), encoding="utf-8")


def _bucket_locked(bucket: dict, key: str, now: float) -> int:
    rec = bucket.get(key) or {}
    until = float(rec.get("until") or 0)
    if until > now:
        return int(until - now)
    hits = [t for t in (rec.get("hits") or []) if now - t <= FAIL_WINDOW]
    rec["hits"] = hits
    bucket[key] = rec
    return 0


def login_blocked(ip: str, name: str) -> int:
    now = time.time()
    with _GUARD_LOCK:
        g = _load_guard()
        g.setdefault("ip", {})
        g.setdefault("user", {})
        left = max(_bucket_locked(g["ip"], ip or "-", now), _bucket_locked(g["user"], (name or "-").lower(), now))
        _save_guard(g)
        return left


def login_fail(ip: str, name: str) -> int:
    now = time.time()
    with _GUARD_LOCK:
        g = _load_guard()
        g.setdefault("ip", {})
        g.setdefault("user", {})
        locked = 0
        for bucket, key in ((g["ip"], ip or "-"), (g["user"], (name or "-").lower())):
            rec = bucket.get(key) or {"hits": [], "until": 0}
            hits = [t for t in rec.get("hits") or [] if now - t <= FAIL_WINDOW]
            hits.append(now)
            rec["hits"] = hits
            if len(hits) >= FAIL_MAX:
                rec["until"] = now + LOCK_SECS
                rec["hits"] = []
            locked = max(locked, int(max(0, rec.get("until") or 0) - now))
            bucket[key] = rec
        _save_guard(g)
        return locked


def login_ok(ip: str, name: str) -> None:
    with _GUARD_LOCK:
        g = _load_guard()
        g.setdefault("ip", {})
        g.setdefault("user", {})
        g["ip"].pop(ip or "-", None)
        g["user"].pop((name or "-").lower(), None)
        _save_guard(g)


def lookup_geo(ip: str) -> str:
    ip = (ip or "").strip()
    if not ip or ip in ("127.0.0.1", "::1") or ip.startswith("10.") or ip.startswith("192.168.") or ip.startswith("172."):
        return "内网"
    cache_path = DATA / "ip_geo.json"
    cache = {}
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            cache = {}
    if ip in cache and cache[ip]:
        return str(cache[ip])
    url = "http://ip-api.com/json/%s?fields=status,country,regionName,city,isp&lang=zh-CN" % ip
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "okx-board-gate/3"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            obj = json.loads(resp.read().decode("utf-8") or "{}")
        if obj.get("status") == "success":
            parts = [obj.get("country") or "", obj.get("regionName") or "", obj.get("city") or ""]
            text = " ".join(p for p in parts if p).strip() or "未知"
            isp = obj.get("isp") or ""
            if isp:
                text = text + " · " + isp
        else:
            text = "未知"
    except Exception:
        text = "查询失败"
    cache[ip] = text
    try:
        cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
    return text


def admin_count(users: dict) -> int:
    return sum(1 for rec in users.values() if norm_role((rec or {}).get("role")) == "admin")


def watch_path(user: str) -> Path:
    safe = re.sub(r"[^0-9A-Za-z_.-]+", "_", user) or "user"
    return WATCH_DIR / (safe + ".json")


def migrate_old_watch() -> None:
    old = DATA / "watchlist.json"
    dest = watch_path(SEED_ADMIN)
    if old.exists() and not dest.exists():
        dest.write_bytes(old.read_bytes())


migrate_old_watch()
SITE_BORN_FILE = DATA / "site_born.txt"


def site_born() -> int:
    if SITE_BORN_FILE.exists():
        try:
            return int(SITE_BORN_FILE.read_text().strip() or "0")
        except Exception:
            pass
    ts = int(time.time())
    SITE_BORN_FILE.write_text(str(ts), encoding="utf-8")
    return ts


site_born()


def sign(user: str, exp: int) -> str:
    return hmac.new(SECRET, f"{user}|{exp}".encode(), hashlib.sha256).hexdigest()


def make_token(user: str, days: int) -> str:
    exp = int(time.time()) + days * 86400
    return f"{user}|{exp}|{sign(user, exp)}"


def parse_token(raw: str | None):
    if not raw:
        return None
    parts = raw.split("|")
    if len(parts) != 3:
        return None
    user, exp_s, sig = parts
    try:
        exp = int(exp_s)
    except ValueError:
        return None
    if exp < time.time():
        return None
    if not hmac.compare_digest(sig, sign(user, exp)):
        return None
    if user not in load_users():
        return None
    return user


def read_body(handler) -> bytes:
    n = int(handler.headers.get("Content-Length") or 0)
    return handler.rfile.read(n) if n else b""


def cookie_user(handler):
    jar = SimpleCookie()
    if handler.headers.get("Cookie"):
        jar.load(handler.headers.get("Cookie"))
    if "board_sess" in jar:
        return parse_token(jar["board_sess"].value)
    return None


class Handler(BaseHTTPRequestHandler):
    server_version = "okx-board-gate/3"

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))

    def _send(self, code, body, ctype="text/html; charset=utf-8", extra=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if extra:
            for k, v in extra:
                self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, code, obj, extra=None):
        self._send(code, json.dumps(obj, ensure_ascii=False), "application/json; charset=utf-8", extra)

    def _need_login(self, reason=""):
        loc = "/login?reason=expired" if reason == "expired" else "/login"
        extra = [("Location", loc)]
        if reason == "expired":
            extra.append(("Set-Cookie", "board_sess=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"))
        self._send(302, b"", extra=extra)

    def _active(self, user, api=False):
        if not user:
            if api:
                self._json(401, {"error": "login required"})
            else:
                self._need_login()
            return False
        rec = load_users().get(user)
        if is_expired(rec):
            if api:
                self._json(403, {"error": "账户已到期", "expired": True})
            else:
                self._need_login("expired")
            return False
        return True

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        user = cookie_user(self)
        if path in ("/", "/index.html"):
            if user and not is_expired(load_users().get(user)):
                return self._send(302, b"", extra=[("Location", "/board")])
            return self._send(302, b"", extra=[("Location", "/login")])
        if path == "/api/uptime":
            born = site_born()
            now = int(time.time())
            files = [BOARD, LOGIN, ADMIN_PAGE, Path(__file__)]
            updated = 0
            for f in files:
                try:
                    if f.exists():
                        updated = max(updated, int(f.stat().st_mtime))
                except Exception:
                    pass
            return self._json(200, {"born": born, "now": now, "seconds": max(0, now - born), "updated": updated})
        if path == "/login":
            return self._send(200, LOGIN.read_text(encoding="utf-8") if LOGIN.exists() else "missing login.html")
        if path == "/logout":
            extra = [("Set-Cookie", "board_sess=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"), ("Location", "/login")]
            return self._send(302, b"", extra=extra)
        if path == "/board":
            if not self._active(user):
                return
            return self._send(200, BOARD.read_text(encoding="utf-8") if BOARD.exists() else "missing board")
        if path == "/admin":
            if not self._active(user):
                return
            if role_of(user) not in ("admin", "svip"):
                return self._send(403, "没有账号管理权限")
            return self._send(200, ADMIN_PAGE.read_text(encoding="utf-8") if ADMIN_PAGE.exists() else "missing admin.html")
        if path == "/api/me":
            if not user:
                return self._json(401, {"error": "login required"})
            rec = load_users().get(user) or {}
            row = public_row(user, rec, user)
            row["can_admin"] = row["role"] in ("admin", "svip") and not row["expired"]
            return self._json(200, row)
        if path == "/api/users":
            if not self._active(user, api=True):
                return
            if role_of(user) not in ("admin", "svip"):
                return self._json(403, {"error": "无权查看账号"})
            admin = role_of(user) == "admin"
            rows = []
            for u, rec in load_users().items():
                row = public_row(u, rec, user)
                if admin:
                    plain = (rec or {}).get("pass_plain") or ""
                    row["password"] = plain
                    row["password_hidden"] = not bool(plain)
                rows.append(row)
            order = {"admin": 0, "svip": 1, "vip": 2}
            rows.sort(key=lambda r: (order.get(r["role"], 9), r["user"]))
            return self._json(200, {"users": rows, "me": public_row(user, load_users().get(user) or {}, user)})
        if path == "/api/watchlist":
            if not self._active(user, api=True):
                return
            p = watch_path(user)
            if p.exists():
                return self._send(200, p.read_bytes(), "application/json; charset=utf-8")
            return self._json(200, {"list": []})
        if path.startswith("/okx/"):
            if not self._active(user, api=True):
                return
            return self._proxy(OKX_PREFIX + path[len("/okx"):])
        if path in EXT:
            if not self._active(user, api=True):
                return
            return self._proxy(EXT[path])
        return self._send(404, "not found")

    def do_PUT(self):
        path = urlparse(self.path).path
        user = cookie_user(self)
        if path != "/api/watchlist":
            return self._send(404, "not found")
        if not self._active(user, api=True):
            return
        try:
            data = json.loads(read_body(self).decode("utf-8") or "{}")
            lst = data.get("list") if isinstance(data, dict) else None
            if not isinstance(lst, list):
                return self._json(400, {"error": "list required"})
            clean = []
            for x in lst:
                s = str(x).strip().upper()
                if s:
                    clean.append(s)
            watch_path(user).write_text(
                json.dumps({"list": clean, "user": user, "ts": int(time.time())}, ensure_ascii=False),
                encoding="utf-8",
            )
            return self._json(200, {"ok": True, "n": len(clean)})
        except Exception as e:
            return self._json(400, {"error": str(e)})

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/login":
            return self._login()
        if path == "/api/users":
            return self._add_user()
        if path == "/api/users/batch-delete":
            return self._batch_delete()
        if path == "/api/me/password":
            return self._change_own_pass()
        return self._send(404, "not found")

    def do_PATCH(self):
        path = urlparse(self.path).path
        if path == "/api/users":
            return self._patch_user()
        return self._send(404, "not found")

    def do_DELETE(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/users":
            return self._send(404, "not found")
        user = cookie_user(self)
        if not self._active(user, api=True):
            return
        if role_of(user) != "admin":
            return self._json(403, {"error": "只有管理员能删除账号"})
        target = (parse_qs(parsed.query).get("user") or [""])[0].strip()
        users = load_users()
        if not target or target not in users:
            return self._json(404, {"error": "用户不存在"})
        if target == user:
            return self._json(400, {"error": "不能删除当前账号"})
        if target == SEED_ADMIN:
            return self._json(400, {"error": "主管理员账号已锁死，不能删除"})
        users.pop(target, None)
        save_users(users)
        wp = watch_path(target)
        if wp.exists():
            wp.unlink()
        return self._json(200, {"ok": True})

    def _batch_delete(self):
        user = cookie_user(self)
        if not self._active(user, api=True):
            return
        if role_of(user) != "admin":
            return self._json(403, {"error": "只有管理员能删除账号"})
        try:
            data = json.loads(read_body(self).decode("utf-8") or "{}")
        except Exception:
            return self._json(400, {"error": "bad json"})
        names = data.get("users") if isinstance(data, dict) else None
        if not isinstance(names, list) or not names:
            return self._json(400, {"error": "请选择要删除的账号"})
        users = load_users()
        deleted, skipped = [], []
        for raw in names:
            target = str(raw or "").strip()
            if not target or target not in users:
                skipped.append(target or "?")
                continue
            if target == user or target == SEED_ADMIN:
                skipped.append(target)
                continue
            if norm_role((users.get(target) or {}).get("role")) == "admin" and admin_count(users) <= 1:
                skipped.append(target)
                continue
            users.pop(target, None)
            wp = watch_path(target)
            if wp.exists():
                wp.unlink()
            deleted.append(target)
        save_users(users)
        return self._json(200, {"ok": True, "deleted": deleted, "skipped": skipped})

    def _login(self):
        try:
            data = json.loads(read_body(self).decode("utf-8") or "{}")
        except Exception:
            return self._json(400, {"error": "bad json"})
        name = str(data.get("user") or "").strip()
        pw = str(data.get("pass") or "")
        remember = bool(data.get("remember"))
        ip = client_ip(self)
        wait = login_blocked(ip, name)
        if wait > 0:
            mins = max(1, (wait + 59) // 60)
            return self._json(429, {"error": "尝试过多，请 %s 分钟后再试" % mins, "retry_after": wait})
        users = load_users()
        rec = users.get(name)
        hashed = sha_pass(pw)
        if not rec or not hmac.compare_digest(hashed, rec.get("pass") or ""):
            extra = login_fail(ip, name)
            print("[%s] LOGIN_FAIL ip=%s user=%s" % (time.strftime("%d/%b/%Y %H:%M:%S"), ip, name or "-"))
            time.sleep(0.4)
            if extra > 0:
                mins = max(1, (extra + 59) // 60)
                return self._json(429, {"error": "尝试过多，请 %s 分钟后再试" % mins, "retry_after": extra})
            return self._json(401, {"error": "账号或密码错误"})
        rec = ensure_fields(name, rec)
        if is_expired(rec):
            return self._json(403, {"error": "账户已到期，请联系管理员续期", "expired": True})
        login_ok(ip, name)
        rec["last_login"] = int(time.time())
        rec["last_ip"] = ip
        rec["last_geo"] = lookup_geo(ip)
        users[name] = rec
        save_users(users)
        days = 30 if remember else 1
        token = make_token(name, days)
        cookie = f"board_sess={token}; Path=/; Max-Age={days * 86400}; HttpOnly; SameSite=Lax"
        return self._json(200, {"ok": True, **public_row(name, rec, name)}, extra=[("Set-Cookie", cookie)])

    def _add_user(self):
        user = cookie_user(self)
        if not self._active(user, api=True):
            return
        my_role = role_of(user)
        if my_role not in ("admin", "svip"):
            return self._json(403, {"error": "没有添加账号权限"})
        try:
            data = json.loads(read_body(self).decode("utf-8") or "{}")
        except Exception:
            return self._json(400, {"error": "bad json"})
        name = str(data.get("user") or "").strip()
        pw = str(data.get("pass") or "")
        role = norm_role(data.get("role") or "vip")
        if my_role != "admin":
            role = "vip"
        if role not in ROLES:
            role = "vip"
        if not re.fullmatch(r"[0-9A-Za-z_.-]{3,32}", name):
            return self._json(400, {"error": "账号限 3-32 位字母数字"})
        if len(pw) < 6:
            return self._json(400, {"error": "密码至少 6 位"})
        users = load_users()
        if name in users:
            return self._json(400, {"error": "账号已存在"})
        now = int(time.time())
        rec = ensure_fields(name, {
            "pass": sha_pass(pw),
            "pass_plain": pw,
            "role": role,
            "created_at": now,
            "expires_at": 0 if role == "admin" else now + 86400,
            "last_login": 0,
            "last_ip": "",
            "last_geo": "",
        })
        users[name] = rec
        save_users(users)
        return self._json(200, {"ok": True, "user": public_row(name, rec)})

    def _patch_user(self):
        user = cookie_user(self)
        if not self._active(user, api=True):
            return
        if role_of(user) != "admin":
            return self._json(403, {"error": "只有管理员能改角色或续期"})
        try:
            data = json.loads(read_body(self).decode("utf-8") or "{}")
        except Exception:
            return self._json(400, {"error": "bad json"})
        name = str(data.get("user") or "").strip()
        users = load_users()
        if not name or name not in users:
            return self._json(404, {"error": "用户不存在"})
        rec = ensure_fields(name, users[name])
        if name == SEED_ADMIN and "role" in data and norm_role(data.get("role")) != "admin":
            return self._json(400, {"error": "主管理员角色已锁死，不能修改"})
        if "role" in data:
            role = norm_role(data.get("role"))
            if role not in ROLES:
                return self._json(400, {"error": "角色只能是管理员 / SVIP / VIP"})
            if rec.get("role") == "admin" and role != "admin" and admin_count(users) <= 1:
                return self._json(400, {"error": "不能取消唯一管理员"})
            rec["role"] = role
            if role == "admin":
                rec["expires_at"] = 0
        if data.get("pass"):
            pw = str(data.get("pass") or "")
            if len(pw) < 6:
                return self._json(400, {"error": "密码至少 6 位"})
            rec["pass"] = sha_pass(pw)
            rec["pass_plain"] = pw
        if data.get("clear_expiry"):
            if rec["role"] == "admin":
                return self._json(400, {"error": "不能清空管理员有效期"})
            rec["expires_at"] = int(time.time()) - 1
        elif data.get("permanent"):
            rec["expires_at"] = 0
        elif data.get("add_days") is not None:
            try:
                days = int(data.get("add_days"))
            except (TypeError, ValueError):
                return self._json(400, {"error": "续期天数无效"})
            if days not in ADD_DAYS:
                return self._json(400, {"error": "只能续期 1 / 15 / 30 天"})
            if rec["role"] == "admin":
                rec["expires_at"] = 0
            else:
                now = int(time.time())
                base = int(rec.get("expires_at") or 0)
                if base < now:
                    base = now
                rec["expires_at"] = base + days * 86400
        rec = ensure_fields(name, rec)
        users[name] = rec
        save_users(users)
        return self._json(200, {"ok": True, "user": public_row(name, rec, user)})

    def _change_own_pass(self):
        user = cookie_user(self)
        if not self._active(user, api=True):
            return
        try:
            data = json.loads(read_body(self).decode("utf-8") or "{}")
        except Exception:
            return self._json(400, {"error": "bad json"})
        old = str(data.get("old") or "")
        new = str(data.get("new") or "")
        if len(new) < 6:
            return self._json(400, {"error": "新密码至少 6 位"})
        users = load_users()
        rec = users.get(user)
        if not rec:
            return self._json(404, {"error": "用户不存在"})
        if not hmac.compare_digest(sha_pass(old), rec.get("pass") or ""):
            time.sleep(0.3)
            return self._json(400, {"error": "当前密码不正确"})
        rec["pass"] = sha_pass(new)
        rec["pass_plain"] = new
        users[user] = rec
        save_users(users)
        return self._json(200, {"ok": True})

    def _proxy(self, url: str):
        q = urlparse(self.path).query
        if q and "?" not in url:
            url = url + "?" + q
        req = urllib.request.Request(url, headers={"User-Agent": "okx-board-gate/3", "Accept": "application/json"}, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                return self._send(200, resp.read(), resp.headers.get("Content-Type", "application/json"))
        except urllib.error.HTTPError as e:
            return self._send(e.code, e.read() or b"", e.headers.get("Content-Type", "text/plain"))
        except Exception as e:
            return self._json(502, {"error": str(e), "url": url.split("?")[0]})


def main():
    load_users()
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"OKX board gate http://{HOST}:{PORT}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
