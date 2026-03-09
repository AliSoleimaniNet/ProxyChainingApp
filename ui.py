"""
ui.py
Flet UI — layout, widgets, event handlers.
Imports business logic from network.py and parser.py.
"""

import flet as ft
import json
import threading
from urllib.parse import urlparse

from network import get_ip_info
from parser  import parse_proxy_url, build_outbound


# ── Theme / color tokens ──────────────────────────────────────────────────────

BG       = "#0A0C10"
SURFACE  = "#111318"
CARD     = "#161A22"
BORDER   = "#1E2330"
ACCENT   = "#00FFA3"
ACCENT2  = "#00FFFF"
MUTED    = "#4A5368"
TEXT     = "#E2E8F0"
TEXT_DIM = "#7A8499"
DANGER   = "#FF4757"


# ── Helpers ───────────────────────────────────────────────────────────────────

def ping_color(ms: float | None) -> str:
    if ms is None:  return "#888888"
    if ms < 300:    return ACCENT
    if ms < 1000:   return "#FFD700"
    if ms < 5000:   return "#FF8C00"
    if ms < 10000:  return DANGER
    return "#888888"


def all_border(color: str = BORDER) -> ft.Border:
    s = ft.BorderSide(1, color)
    return ft.Border(s, s, s, s)


# ── Widget factories ──────────────────────────────────────────────────────────

def make_mono(text: str, size: int = 13, color: str = TEXT,
              weight=ft.FontWeight.NORMAL) -> ft.Text:
    return ft.Text(text, font_family="JetBrains", size=size,
                   color=color, weight=weight)


def make_label(text: str) -> ft.Row:
    return ft.Row([
        ft.Container(width=3, height=14, bgcolor=ACCENT, border_radius=2),
        ft.Text(text, font_family="Syne-Bold", size=11, color=ACCENT,
                weight=ft.FontWeight.W_600,
                style=ft.TextStyle(letter_spacing=2)),
    ], spacing=8)


def make_glowing_divider() -> ft.Container:
    return ft.Container(
        height=1,
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, 0),
            end=ft.Alignment(1, 0),
            colors=["#00000000", ACCENT + "55", ACCENT2 + "33", "#00000000"],
        ),
        margin=ft.Margin(0, 4, 0, 4),
    )


def make_icon_btn(icon_name: str, tooltip: str, handler,
                  color: str = MUTED) -> ft.IconButton:
    return ft.IconButton(
        icon=icon_name, icon_color=color, icon_size=16,
        tooltip=tooltip, on_click=handler,
        style=ft.ButtonStyle(
            overlay_color={
                ft.ControlState.DEFAULT: "#00000000",
                ft.ControlState.HOVERED: ACCENT + "18",
            },
            shape=ft.RoundedRectangleBorder(radius=6),
            padding=ft.Padding(6, 6, 6, 6),
        ),
    )


def make_text_field(**kwargs) -> ft.TextField:
    """Base text field with shared styling."""
    defaults = dict(
        text_style=ft.TextStyle(font_family="JetBrains", size=12, color=TEXT),
        multiline=True, min_lines=3, max_lines=5, expand=True,
        bgcolor=BG, border_color=BORDER,
        focused_border_color=ACCENT, cursor_color=ACCENT,
        label_style=ft.TextStyle(color=MUTED, font_family="JetBrains", size=11),
        hint_style=ft.TextStyle(color=MUTED, font_family="JetBrains", size=12),
        content_padding=ft.Padding(14, 14, 14, 14),
        border_radius=8,
    )
    defaults.update(kwargs)
    return ft.TextField(**defaults)


def make_input_card(title: str, step: str, field: ft.TextField,
                    paste_fn, accent: str = ACCENT,
                    muted: str = MUTED) -> ft.Container:
    return ft.Container(
        content=ft.Column([
            ft.Row([
                make_label(f"STEP {step}  //  {title}"),
                make_icon_btn(ft.Icons.CONTENT_PASTE, "Paste", paste_fn, muted),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=8),
            ft.Row([field], expand=True),
        ], spacing=0, expand=True),
        padding=ft.Padding(16, 16, 16, 16),
        expand=True, bgcolor=CARD, border_radius=10,
        border=all_border(),
    )


# ── Main page ─────────────────────────────────────────────────────────────────

def build_page(page: ft.Page) -> None:
    """Entry point called by ft.run — builds the entire UI."""

    page.title       = "ProxyChainer — SOCKS → Any"
    page.theme_mode  = ft.ThemeMode.DARK
    page.padding     = 0
    page.scroll      = ft.ScrollMode.AUTO
    page.bgcolor     = BG

    page.fonts = {
        "JetBrains":          "fonts/JetBrainsMono-Regular.ttf",
        "JetBrains-SemiBold": "fonts/JetBrainsMono-SemiBold.ttf",
        "JetBrains-Bold":     "fonts/JetBrainsMono-Bold.ttf",
        "Syne":               "fonts/Syne-Regular.ttf",
        "Syne-SemiBold":      "fonts/Syne-SemiBold.ttf",
        "Syne-Bold":          "fonts/Syne-Bold.ttf",
        "Syne-ExtraBold":     "fonts/Syne-ExtraBold.ttf",
    }

    # ── Fields ────────────────────────────────────────────────────
    socks_input = make_text_field(
        label="SOCKS PROXY  //  socks://user:pass@host:port",
        hint_text="socks://...",
    )
    proxy_input = make_text_field(
        label="CONFIG  //  vless / vmess / trojan / ss",
        hint_text="vless:// or vmess:// or trojan:// or ss://...",
    )
    mobile_mode_switch = ft.Switch(
        active_color=ACCENT2,
        value=False,
    )
    mobile_options_row = ft.Row(
        [
            ft.Icon(ft.Icons.PHONE_ANDROID, size=16, color=TEXT_DIM),
            ft.Text("OPTIMIZE FOR MOBILE", font_family="JetBrains", size=11, color=TEXT_DIM),
            mobile_mode_switch,
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=10
    )
    output_field = ft.TextField(
        label="GENERATED CONFIG  //  JSON OUTPUT",
        multiline=True, min_lines=12, expand=True, read_only=True,
        text_style=ft.TextStyle(font_family="JetBrains", size=11, color=ACCENT2),
        bgcolor=BG, border_color=BORDER,
        focused_border_color=ACCENT2, cursor_color=ACCENT2,
        label_style=ft.TextStyle(color=MUTED, font_family="JetBrains", size=11),
        content_padding=ft.Padding(14, 14, 14, 14), border_radius=8,
    )

    # ── Status widgets ────────────────────────────────────────────
    status_text = ft.Text("READY", font_family="JetBrains", size=11,
                          color=ACCENT, weight=ft.FontWeight.W_600)
    status_dot  = ft.Container(
        width=7, height=7, bgcolor=ACCENT, border_radius=50,
        animate=ft.Animation(800, ft.AnimationCurve.EASE_IN_OUT),
    )

    # ── IP footer row ─────────────────────────────────────────────
    ip_row = ft.Row([
        make_mono("IP ──", 11, TEXT_DIM),    make_mono("—", 11, MUTED),
        ft.Container(width=8),
        make_mono("CITY ──", 11, TEXT_DIM),  make_mono("—", 11, MUTED),
        ft.Container(width=8),
        make_mono("ORG ──", 11, TEXT_DIM),   make_mono("—", 11, MUTED),
    ], spacing=4, wrap=True)

    # ── Status helper ─────────────────────────────────────────────
    def set_status(msg: str, color: str = ACCENT, dot: str = ACCENT) -> None:
        status_text.value  = msg
        status_text.color  = color
        status_dot.bgcolor = dot
        page.update()

    # ── IP / ping refresh ─────────────────────────────────────────
    def refresh_ip(e) -> None:
        set_status("FETCHING IP + PING...", ACCENT2, ACCENT2)

        def _fetch():
            info = get_ip_info()
            if info:
                pc = ping_color(info["ping"])
                ip_row.controls = [
                    make_mono("IP ──",    11, TEXT_DIM),
                    make_mono(info["ip"], 11, ACCENT),
                    ft.Container(width=12),
                    make_mono("CITY ──",  11, TEXT_DIM),
                    make_mono(f"{info['city']}, {info['country']}", 11, TEXT),
                    ft.Container(width=12),
                    make_mono("ORG ──",   11, TEXT_DIM),
                    make_mono(info["org"], 11, TEXT_DIM),
                    ft.Container(width=12),
                    make_mono("PING ──",  11, TEXT_DIM),
                    make_mono(
                        f"{info['ping']} ms" if info["ping"] is not None else "N/A",
                        11, pc, ft.FontWeight.W_600,
                    ),
                    ft.Container(width=7, height=7, bgcolor=pc,
                                 border_radius=50, margin=ft.Margin(2, 0, 0, 0)),
                ]
                set_status("IP INFO LOADED", ACCENT, ACCENT)
            else:
                ip_row.controls = [
                    make_mono("UNABLE TO FETCH IP — CHECK CONNECTION", 11, DANGER)
                ]
                set_status("CONNECTION ERROR", DANGER, DANGER)
            page.update()

        threading.Thread(target=_fetch, daemon=True).start()

    # ── Generate ──────────────────────────────────────────────────
    async def process_chain(e) -> None:
        set_status("PROCESSING...", ACCENT2, ACCENT2)
        try:
            v_url = proxy_input.value.strip()
            s_url = socks_input.value.strip()
            is_mobile = mobile_mode_switch.value  # چک کردن وضعیت سوئیچ

            if not v_url or not s_url:
                raise ValueError("Both SOCKS and proxy config are required")

            s_parsed = urlparse(s_url)
            s_addr   = s_parsed.hostname
            s_port   = s_parsed.port
            if not s_addr or not s_port:
                raise ValueError(f"Invalid SOCKS URL: {s_url}")

            info     = parse_proxy_url(v_url)
            outbound = build_outbound(info, "iran-socks")

            config = {
                "log": {"loglevel": "warning"},
                "outbounds": [
                    outbound,
                    {
                        "tag": "iran-socks",
                        "protocol": "socks",
                        "settings": {"servers": [{"address": s_addr, "port": s_port}]},
                    },
                    {"tag": "direct", "protocol": "freedom", "settings": {"domainStrategy": "UseIP"}},
                    {"tag": "block", "protocol": "blackhole"},
                ]
            }

            if is_mobile:
                config["dns"] = {
                    "servers": ["1.1.1.1", "8.8.8.8", "https://dns.google/dns-query"]
                }
                config["routing"] = {
                    "domainStrategy": "IPIfNonMatch",
                    "rules": [
                        {"type": "field", "outboundTag": "direct", "domain": ["geosite:ir", "domain:.ir"]},
                        {"type": "field", "outboundTag": "direct", "ip": ["geoip:ir", "geoip:private"]},
                        {"type": "field", "outboundTag": "proxy-chain", "port": "0-65535"},
                    ]
                }
            else:
                config["inbounds"] = [
                    {
                        "tag": "socks-in", "port": 10808, "listen": "127.0.0.1", "protocol": "socks",
                        "settings": {"auth": "noauth", "udp": True},
                        "sniffing": {"enabled": True, "destOverride": ["http", "tls"]},
                    },
                    {
                        "tag": "http-in", "port": 10809, "listen": "127.0.0.1", "protocol": "http",
                        "settings": {},
                        "sniffing": {"enabled": True, "destOverride": ["http", "tls"]},
                    }
                ]
                config["routing"] = {
                    "domainStrategy": "IPIfNonMatch",
                    "rules": [
                        {"type": "field", "outboundTag": "proxy-chain", "port": "0-65535"},
                    ]
                }

            output_field.value = json.dumps(config, indent=2)
            await ft.Clipboard().set(output_field.value)
            
            mode_label = "MOBILE" if is_mobile else "DESKTOP"
            set_status(f"✓ {mode_label} CONFIG GENERATED & COPIED", ACCENT, ACCENT)
            page.update()

        except Exception as ex:
            set_status(f"ERROR: {ex}", DANGER, DANGER)
            page.update()
    
    # ── Clipboard helpers ─────────────────────────────────────────
    async def copy_output(e) -> None:
        if output_field.value:
            await ft.Clipboard().set(output_field.value)
            set_status("COPIED TO CLIPBOARD  ✓", ACCENT, ACCENT)

    async def paste_socks(e) -> None:
        socks_input.value = await ft.Clipboard().get() or ""
        page.update()

    async def paste_proxy(e) -> None:
        proxy_input.value = await ft.Clipboard().get() or ""
        page.update()

    def clear_all(e) -> None:
        socks_input.value  = ""
        proxy_input.value  = ""
        output_field.value = ""
        set_status("CLEARED", MUTED, MUTED)
        page.update()

    # ── Header ────────────────────────────────────────────────────
    header = ft.Container(
        content=ft.Row([
            ft.Row([
                ft.Container(width=4, height=28, bgcolor=ACCENT, border_radius=2),
                ft.Column([
                    ft.Text("PROXY CHAINER", font_family="Syne-ExtraBold",
                            size=20, color=TEXT, weight=ft.FontWeight.W_800,
                            style=ft.TextStyle(letter_spacing=3)),
                    ft.Text("SOCKS  →  VLESS / VMess / Trojan / SS",
                            font_family="JetBrains", size=10, color=TEXT_DIM,
                            style=ft.TextStyle(letter_spacing=1)),
                ], spacing=1, tight=True),
            ], spacing=12),
            ft.Container(
                content=ft.Row([status_dot, status_text], spacing=8),
                padding=ft.Padding(14, 8, 14, 8), bgcolor=SURFACE,
                border_radius=6, border=all_border(),
            ),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.Padding(20, 16, 20, 16), bgcolor=SURFACE,
        border=ft.Border(bottom=ft.BorderSide(1, BORDER)),
    )

    # ── Input cards ───────────────────────────────────────────────
    socks_card = make_input_card("SOCKS PROXY",  "01", socks_input, paste_socks)
    proxy_card = make_input_card("PROXY CONFIG", "02", proxy_input, paste_proxy)

    # ── Generate button ───────────────────────────────────────────
    generate_btn = ft.Container(
        content=ft.Button(
            content=ft.Row([
                ft.Icon(ft.Icons.BOLT, color=BG, size=18),
                ft.Text("GENERATE CHAIN CONFIG", font_family="Syne-Bold",
                        size=13, color=BG, weight=ft.FontWeight.W_700,
                        style=ft.TextStyle(letter_spacing=1.5)),
            ], spacing=10, tight=True),
            on_click=process_chain,
            style=ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: ACCENT,
                         ft.ControlState.HOVERED: "#00FFBF"},
                overlay_color="#00000000",
                elevation={ft.ControlState.DEFAULT: 0, ft.ControlState.HOVERED: 8},
                shadow_color=ACCENT + "55",
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding(32, 16, 32, 16),
                animation_duration=200,
            ),
        ),
        alignment=ft.Alignment(0, 0),
    )

    # ── Output card ───────────────────────────────────────────────
    output_card = ft.Container(
        content=ft.Column([
            ft.Row([
                make_label("STEP 03  //  JSON OUTPUT"),
                ft.Row([
                    make_icon_btn(ft.Icons.COPY_ALL,       "Copy",      copy_output, ACCENT2),
                    make_icon_btn(ft.Icons.DELETE_OUTLINE, "Clear All", clear_all,   MUTED),
                ], spacing=0),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=8),
            ft.Row([output_field], expand=True),
        ], spacing=0, expand=True),
        padding=ft.Padding(16, 16, 16, 16), expand=True,
        bgcolor=CARD, border_radius=10, border=all_border(),
    )

    # ── IP footer ─────────────────────────────────────────────────
    ip_footer = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.LANGUAGE, color=MUTED, size=14),
            ip_row,
            ft.Container(expand=True),
            make_icon_btn(ft.Icons.REFRESH, "Refresh IP", refresh_ip, ACCENT),
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding(20, 12, 20, 12), bgcolor=SURFACE,
        border=ft.Border(top=ft.BorderSide(1, BORDER)),
    )

    # ── Responsive input layout ───────────────────────────────────
    inputs_container = ft.Container()

    def build_inputs() -> ft.Control:
        if (page.width or 800) < 600:
            return ft.Column([socks_card, proxy_card], spacing=12)
        return ft.Row([
            ft.Column([socks_card], expand=1),
            ft.Column([proxy_card], expand=1),
        ], spacing=16)

    def on_resize(e) -> None:
        inputs_container.content = build_inputs()
        page.update()

    page.on_resized          = on_resize
    inputs_container.content = build_inputs()

    # ── Body ──────────────────────────────────────────────────────
    body = ft.Container(
        content=ft.Column([
            inputs_container,
            # استفاده از ردیف اصلاح شده
            ft.Container(content=mobile_options_row, margin=ft.margin.only(top=10)), 
            make_glowing_divider(),
            generate_btn,
            make_glowing_divider(),
            output_card,
        ], spacing=16),
        padding=ft.Padding(20, 20, 20, 20),
    )

    # ── Assemble ──────────────────────────────────────────────────
    page.add(
        ft.Column(
            controls=[
                header,
                ft.ListView(controls=[body], expand=True, padding=0),
                ip_footer,
            ],
            spacing=0, expand=True,
        )
    )

    # Auto-fetch IP + ping on startup
    threading.Thread(target=lambda: refresh_ip(None), daemon=True).start()