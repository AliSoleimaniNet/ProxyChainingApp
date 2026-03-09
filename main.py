"""
main.py
Entry point — just launches the Flet app.
"""

import flet as ft
from ui import build_page

ft.run(build_page, assets_dir="assets")