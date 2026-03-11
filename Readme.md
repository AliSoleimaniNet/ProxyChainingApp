# ⚡ ProxyChainer

**Chain two proxies into a single Xray-core / V2Ray config — any protocol to any protocol.**

```
Your Device  →  Hop 1  →  Hop 2  →  Internet
              VLESS/VMess/Trojan/SS/SOCKS
```

Available as a **Windows app**, **Android APK**, and **Web app**.

<img width="1632" height="1020" alt="Single Tab" src="https://github.com/user-attachments/assets/848ee3e2-7048-4cfc-8b3c-528d5ba25fa7" />

<img width="1632" height="1020" alt="Group Tab" src="https://github.com/user-attachments/assets/a1a3ee34-bbe9-47c9-887c-ef9f51780840" />

<img width="1632" height="1020" alt="Log Tab" src="https://github.com/user-attachments/assets/16cf989a-471c-47ff-b38d-4f6e6a7e9115" />

---

## 🌐 Try it now

**[→ Open Web App](https://AliSoleimaniNet.github.io/ProxyChainer/)**

---

## 📥 Download

Go to the [**Releases**](https://github.com/AliSoleimaniNet/ProxyChainer/releases) page and download:

| Platform | File |
|----------|------|
| Windows | `ProxyChainer-Windows.zip` |
| Android | `ProxyChainer-Android.apk` |

---

## What it does

Paste two proxy URLs — ProxyChainer generates a ready-to-use JSON config that chains them together using Xray's `dialerProxy`. Supports **VLESS**, **VMess**, **Trojan**, **Shadowsocks**, and **SOCKS**.

- **Single mode** — one hop1 + one hop2 → one config, auto-copied to clipboard
- **Group mode** — lists of hop1 + hop2 URLs → generate all combinations and save as a batch
- **PC / Mobile toggle** — desktop config uses SOCKS5 `10808` + HTTP `10809` inbounds; mobile config bypasses Iran geosite/geoip
- **IP & ping info** — shows your current exit IP, city, and latency

---

## Built with

[Flet](https://flet.dev) · [Xray-core](https://github.com/XTLS/Xray-core) · Python 3.11+
