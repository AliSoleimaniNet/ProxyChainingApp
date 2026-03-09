import flet as ft
import json
import requests
import re

def get_ip_info():
    try:
        response = requests.get("https://ipapi.co/json/", timeout=5)
        data = response.json()
        return f"IP: {data.get('ip')} | Location: {data.get('city')}, {data.get('country_name')}"
    except:
        return "Unable to fetch IP info. Check your connection."

def main(page: ft.Page):
    page.title = "Proxy Chainer (Socks -> VLESS)"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.scroll = "adaptive"

    # UI Elements
    socks_input = ft.TextField(label="1. Socks Config (Input)", multiline=True, min_lines=3, placeholder="socks://...")
    vless_input = ft.TextField(label="2. VLESS Config (Input)", multiline=True, min_lines=3, placeholder="vless://...")
    final_output = ft.TextField(label="3. Final JSON Config (Output)", multiline=True, min_lines=10, read_only=True)
    ip_text = ft.Text(value="IP Info: Click refresh to check", color=ft.colors.BLUE_200)

    def process_chain(e):
        try:
            v_url = vless_input.value.strip()
            s_url = socks_input.value.strip()
            
            # Parsing SOCKS (Simple Regex)
            s_addr = re.search(r"@(.*?):", s_url).group(1)
            s_port = int(re.search(r":(\d+)", s_url).group(1).split('#')[0])

            # Parsing VLESS (Extracting main parts)
            v_id = re.search(r"vless://(.*?)@", v_url).group(1)
            v_addr = re.search(r"@(.*?):", v_url).group(1)
            v_port = int(re.search(r":(\d+)\?", v_url).group(1))
            
            # Extracting query params safely
            query_str = v_url.split('?')[1].split('#')[0]
            params = dict(x.split('=') for x in query_str.split('&'))

            # Building the DialerProxy JSON
            config = {
                "outbounds": [
                    {
                        "tag": "proxy-france",
                        "protocol": "vless",
                        "settings": {
                            "vnext": [{"address": v_addr, "port": v_port, "users": [{"id": v_id, "encryption": "none", "flow": params.get("flow", "")}]}]
                        },
                        "streamSettings": {
                            "network": params.get("type", "tcp"),
                            "security": params.get("security", ""),
                            "realitySettings": {
                                "serverName": params.get("sni", ""),
                                "fingerprint": params.get("fp", "chrome"),
                                "publicKey": params.get("pbk", ""),
                                "shortId": params.get("sid", ""),
                                "spiderX": params.get("spx", "").replace("%2F", "/")
                            },
                            "sockopt": {"dialerProxy": "iran-socks"}
                        }
                    },
                    {
                        "tag": "iran-socks",
                        "protocol": "socks",
                        "settings": {"servers": [{"address": s_addr, "port": s_port}]}
                    },
                    {"tag": "direct", "protocol": "freedom"}
                ],
                "routing": {"rules": [{"type": "field", "outboundTag": "proxy-france", "network": "tcp,udp"}]}
            }
            
            final_output.value = json.dumps(config, indent=2)
            page.set_clipboard(final_output.value)
            page.show_snack_bar(ft.SnackBar(ft.Text("Chain Config Generated & Copied!")))
            page.update()
        except Exception as ex:
            page.show_snack_bar(ft.SnackBar(ft.Text(f"Error: {str(ex)}")))

    def refresh_ip(e):
        ip_text.value = "Checking..."
        page.update()
        ip_text.value = get_ip_info()
        page.update()

    # Layout
    page.add(
        ft.Column([
            ft.Text("Proxy Chainer", size=30, weight="bold"),
            ft.Divider(),
            
            # Socks Box
            ft.Row([
                socks_input,
                ft.IconButton(icon=ft.icons.PASTE, on_click=lambda _: setattr(socks_input, 'value', page.get_clipboard()) or page.update())
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

            # VLESS Box
            ft.Row([
                vless_input,
                ft.IconButton(icon=ft.icons.PASTE, on_click=lambda _: setattr(vless_input, 'value', page.get_clipboard()) or page.update())
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

            ft.ElevatedButton("Generate & Copy Chain Config", icon=ft.icons.LINK, on_click=process_chain, width=400),
            
            # Output Box
            ft.Stack([
                final_output,
                ft.IconButton(icon=ft.icons.COPY, right=10, top=10, on_click=lambda _: page.set_clipboard(final_output.value))
            ]),

            ft.Divider(),
            ft.Row([
                ip_text,
                ft.IconButton(icon=ft.icons.REFRESH, on_click=refresh_ip)
            ])
        ])
    )

ft.app(target=main)