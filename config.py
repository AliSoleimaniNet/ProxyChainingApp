"""
config.py — Xray/v2ray config builder logic.
All functions are pure (no UI / page state).
"""

import json
from urllib.parse import urlparse

from parser import parse_proxy_url, build_outbound


def build_config(socks_url: str, proxy_url: str, mobile: bool) -> dict:
    """
    Parse inputs and return a complete Xray JSON config dict.
    Raises ValueError with a human-readable message on bad input.
    """
    v_url = proxy_url.strip()
    s_url = socks_url.strip()

    if not v_url or not s_url:
        raise ValueError("Both SOCKS and proxy fields are required")

    s_parsed = urlparse(s_url)
    s_addr   = s_parsed.hostname
    s_port   = s_parsed.port
    if not s_addr or not s_port:
        raise ValueError(f"Invalid SOCKS URL: {s_url!r}")

    info     = parse_proxy_url(v_url)
    outbound = build_outbound(info, "iran-socks")

    config: dict = {
        "log": {"loglevel": "warning"},
        "outbounds": [
            outbound,
            {
                "tag": "iran-socks",
                "protocol": "socks",
                "settings": {
                    "servers": [{"address": s_addr, "port": s_port}]
                },
            },
            {
                "tag": "direct",
                "protocol": "freedom",
                "settings": {"domainStrategy": "UseIP"},
            },
            {"tag": "block", "protocol": "blackhole"},
        ],
    }

    if mobile:
        _apply_mobile_routing(config)
    else:
        _apply_desktop_routing(config)

    return config


def build_config_json(socks_url: str, proxy_url: str, mobile: bool) -> str:
    """Return the config as a pretty-printed JSON string."""
    return json.dumps(build_config(socks_url, proxy_url, mobile), indent=2)


def get_protocol(proxy_url: str) -> str:
    """Return the protocol name of the proxy URL (e.g. 'vless')."""
    info = parse_proxy_url(proxy_url.strip())
    return info["protocol"]


def get_filename(socks_url: str, proxy_url: str) -> str:
    """
    Build a filename from both inputs:
      <socks_host>-<proxy_remark_or_host>.json

    Examples:
      1.2.3.4-MyServer.json
      iran-proxy-🇩🇪Frankfurt.json
    """
    import re

    def _safe(name: str) -> str:
        """Keep letters, digits, dots, hyphens, underscores. Replace rest with _."""
        # Normalize unicode (e.g. emoji in remarks) — keep as-is, just strip path chars
        name = name.strip()
        name = re.sub(r'[\/:*?"<>|]', "_", name)   # strip filesystem-illegal chars
        return name[:48] or "unnamed"                 # max 48 chars per segment

    # SOCKS name → #remark if present, else hostname
    try:
        from urllib.parse import urlparse as _up
        s_raw = socks_url.strip()
        if "#" in s_raw:
            socks_host = s_raw[s_raw.index("#") + 1:]
        else:
            socks_host = _up(s_raw).hostname or s_raw
    except Exception:
        socks_host = socks_url.strip()

    # Proxy name → #remark if present, else hostname
    try:
        info = parse_proxy_url(proxy_url.strip())
        proxy_name = info.get("remark") or info.get("addr") or "proxy"
    except Exception:
        proxy_name = "proxy"

    return f"{_safe(socks_host)}-{_safe(proxy_name)}"


# ── Private helpers ────────────────────────────────────────────────────────────

def _apply_mobile_routing(config: dict) -> None:
    """Add mobile-style DNS + Iran-bypass routing rules."""
    config["dns"] = {"servers": ["1.1.1.1", "8.8.8.8"]}
    config["routing"] = {
        "domainStrategy": "IPIfNonMatch",
        "rules": [
            {
                "type": "field",
                "outboundTag": "direct",
                "domain": ["geosite:ir", "domain:.ir"],
            },
            {
                "type": "field",
                "outboundTag": "direct",
                "ip": ["geoip:ir", "geoip:private"],
            },
            {
                "type": "field",
                "outboundTag": "proxy-chain",
                "port": "0-65535",
            },
        ],
    }


def _apply_desktop_routing(config: dict) -> None:
    """Add desktop inbounds (SOCKS 10808 + HTTP 10809) and simple routing."""
    config["inbounds"] = [
        {
            "tag": "socks-in",
            "port": 10808,
            "listen": "127.0.0.1",
            "protocol": "socks",
            "settings": {"auth": "noauth", "udp": True},
            "sniffing": {"enabled": True, "destOverride": ["http", "tls"]},
        },
        {
            "tag": "http-in",
            "port": 10809,
            "listen": "127.0.0.1",
            "protocol": "http",
            "settings": {},
            "sniffing": {"enabled": True, "destOverride": ["http", "tls"]},
        },
    ]
    config["routing"] = {
        "domainStrategy": "IPIfNonMatch",
        "rules": [
            {
                "type": "field",
                "outboundTag": "proxy-chain",
                "port": "0-65535",
            }
        ],
    }