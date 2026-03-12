"""
core/network.py
Ping measurement and IP info fetching with multiple provider fallbacks.

Desktop / Android : uses requests → httpx (standard HTTP)
Web (Pyodide)     : uses the browser's native fetch() via the `js` module
                    to avoid CORS blocks that kill requests/httpx in workers.
"""

import sys
import time

# ── Detect environment ────────────────────────────────────────────────────────

_IS_PYODIDE = "pyodide" in sys.modules or "js" in sys.modules


def _ensure_pyodide() -> bool:
    """Return True if we're running inside Pyodide (Flet web)."""
    try:
        import js # type: ignore  # noqa: F401  (available only in Pyodide)
        return True
    except ImportError:
        return False


# ── Native HTTP (desktop / Android) ──────────────────────────────────────────

try:
    import requests as _req

    def _get_native(url: str, timeout: int = 8):
        r = _req.get(url, timeout=timeout)
        return r.status_code, r.json()

    def _get_raw_native(url: str, timeout: int = 8) -> int:
        return _req.get(url, timeout=timeout).status_code

    HAS_NATIVE = True
except ImportError:
    try:
        import httpx as _httpx

        def _get_native(url: str, timeout: int = 8):
            r = _httpx.get(url, timeout=timeout, follow_redirects=True)
            return r.status_code, r.json()

        def _get_raw_native(url: str, timeout: int = 8) -> int:
            return _httpx.get(url, timeout=timeout, follow_redirects=True).status_code

        HAS_NATIVE = True
    except ImportError:
        HAS_NATIVE = False


# ── Pyodide fetch (web) ───────────────────────────────────────────────────────

def _get_pyodide(url: str) -> dict | None:
    """
    Synchronous-style fetch via Pyodide's `js` bridge.
    Uses XMLHttpRequest (synchronous) which works from Pyodide workers.
    Falls back to pyodide.http if available.
    """
    # Try pyodide.http.open_url first (simplest, returns StringIO)
    try:
        from pyodide.http import open_url  # type: ignore
        import json
        text = open_url(url).read()
        return json.loads(text)
    except Exception:
        pass

    # Try synchronous XMLHttpRequest via js bridge
    try:
        import js  # type: ignore
        import json
        xhr = js.XMLHttpRequest.new()
        xhr.open("GET", url, False)   # False = synchronous
        xhr.send(None)
        if xhr.status == 200:
            return json.loads(xhr.responseText)
    except Exception:
        pass

    return None


# ── Unified get ───────────────────────────────────────────────────────────────

def _get(url: str, timeout: int = 8):
    """Returns (status_code, json_dict). Raises on failure."""
    if _ensure_pyodide():
        data = _get_pyodide(url)
        if data is None:
            raise ConnectionError(f"Pyodide fetch failed: {url}")
        return 200, data
    if HAS_NATIVE:
        return _get_native(url, timeout)
    raise RuntimeError("No HTTP library available")


def _get_raw(url: str, timeout: int = 8) -> int:
    if _ensure_pyodide():
        try:
            import js  # type: ignore
            xhr = js.XMLHttpRequest.new()
            xhr.open("GET", url, False)
            xhr.send(None)
            return xhr.status
        except Exception:
            return 0
    if HAS_NATIVE:
        return _get_raw_native(url, timeout)
    return 0


# ── Ping ──────────────────────────────────────────────────────────────────────

def measure_ping(count: int = 3) -> float | None:
    """HTTP ping via Google generate_204. Returns average ms or None on failure."""
    url   = "https://www.google.com/generate_204"
    times = []

    for _ in range(count):
        try:
            start   = time.perf_counter()
            status  = _get_raw(url, timeout=5)
            elapsed = (time.perf_counter() - start) * 1000
            if status in (200, 204):
                times.append(elapsed)
        except Exception:
            pass

    return round(sum(times) / len(times), 1) if times else None


# ── IP info ───────────────────────────────────────────────────────────────────

def get_ip_info() -> dict | None:
    """
    Try each provider in order. Returns dict:
        ip, city, country, org, ping
    Returns None if all providers fail.
    """
    for provider in [_from_ipinfo_io, _from_ipapi_co, _from_freeipapi, _from_ip_api_com]:
        try:
            info = provider()
            if info:
                info["ping"] = measure_ping()
                return info
        except Exception:
            continue

    return None


def _from_ipinfo_io() -> dict | None:
    # HTTPS — works in both desktop and Pyodide
    _, d = _get("https://ipinfo.io/json")
    if "ip" not in d:
        return None
    return {
        "ip":      d.get("ip",      "N/A"),
        "city":    d.get("city",    "N/A"),
        "country": d.get("country", "N/A"),
        "org":     d.get("org",     "N/A"),
    }


def _from_ipapi_co() -> dict | None:
    _, d = _get("https://ipapi.co/json/")
    if d.get("error"):
        return None
    return {
        "ip":      d.get("ip",           "N/A"),
        "city":    d.get("city",         "N/A"),
        "country": d.get("country_name", "N/A"),
        "org":     d.get("org",          "N/A"),
    }


def _from_freeipapi() -> dict | None:
    _, d = _get("https://freeipapi.com/api/json")
    if "ipAddress" not in d:
        return None
    return {
        "ip":      d.get("ipAddress",   "N/A"),
        "city":    d.get("cityName",    "N/A"),
        "country": d.get("countryName", "N/A"),
        "org":     "N/A",
    }


def _from_ip_api_com() -> dict | None:
    # HTTP only — blocked by mixed-content policy in browsers, last resort for desktop
    _, d = _get("http://ip-api.com/json/?fields=status,country,city,org,query")
    if d.get("status") != "success":
        return None
    return {
        "ip":      d.get("query",   "N/A"),
        "city":    d.get("city",    "N/A"),
        "country": d.get("country", "N/A"),
        "org":     d.get("org",     "N/A"),
    }