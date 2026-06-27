#!/usr/bin/env python3
"""Screenshot a standalone HTML design preview.

Use after building a single-file HTML mockup served via `python3 -m http.server`.
Loads the page, takes element-level screenshots of each component (hero, phone frames,
feature sections), saves as PNGs ready to send via Telegram with MEDIA: prefix.

CRITICAL pitfall: NEVER use waitUntil='networkidle' on pages with Google Fonts —
they never reach idle state, hangs 60s. Use 'domcontentloaded' + wait_for_timeout.

Usage:
    1. cd ~/<project>-design-preview && python3 -m http.server 8765 &
    2. PYTHON=/tmp/pw-venv/bin/python3  # or any venv with playwright installed
    3. $PYTHON this_script.py
    4. Send PNGs via send_message with MEDIA: prefix, one per message
"""
from playwright.sync_api import sync_playwright

# --- CONFIG (edit these) ---
CHROME = '/home/ubuntu/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome'
URL = 'http://localhost:8765/index.html'
OUT_DIR = '/home/ubuntu/<project>-design-preview'

# (output_name, css_selector, description) — list as many as you have
# For phone mockup grids: use .phone:nth-of-type(N) to grab each phone
SHOTS = [
    ('1-hero',     '.showcase-header',           'Hero / 3D logo area'),
    ('2-phone',    '.phone:nth-of-type(1)',      'Phone screen 1 (Home)'),
    ('3-phone',    '.phone:nth-of-type(2)',      'Phone screen 2 (Detail)'),
    ('4-phone',    '.phone:nth-of-type(3)',      'Phone screen 3 (Profile)'),
    ('5-phone',    '.phone:nth-of-type(4)',      'Phone screen 4 (Downloads)'),
    ('6-features', '.premium-section',           'Premium features section'),
]
# --- /CONFIG ---

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=CHROME,
            args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'],
        )
        ctx = browser.new_context(viewport={'width': 1600, 'height': 1000}, device_scale_factor=1)
        page = ctx.new_page()
        # CRITICAL: domcontentloaded, NOT networkidle (Google Fonts hang networkidle)
        page.goto(URL, wait_until='domcontentloaded', timeout=15000)
        page.wait_for_timeout(2500)  # let fonts settle

        for name, sel, desc in SHOTS:
            try:
                el = page.locator(sel).first
                el.scroll_into_view_if_needed()
                page.wait_for_timeout(300)
                out = f'{OUT_DIR}/shot-{name}.png'
                el.screenshot(path=out)
                print(f'OK {name} ({desc}) -> {out}')
            except Exception as e:
                print(f'FAIL {name} ({desc}): {e}')

        browser.close()
    print('DONE — verify each shot with vision_analyze before sending to user')

if __name__ == '__main__':
    main()
