#!/usr/bin/env python3
"""
Kimchi.dev API Key Auto Generator - Linux Headless Version
Generates Kimchi.dev API keys via automated signup + captcha solving.

Usage:
    YESCAPTCHA_KEY="your_key" INSTANCES=3 LOOPS=5 python3 kimchi_generator.py

Output: ~/kimchi_keys.txt (format: email|password|apikey)
"""
import asyncio
import urllib.request
import json
import time
import random
import string
import os
import base64
from playwright.async_api import async_playwright

# Config from env
YESCAPTCHA_API_KEY = os.environ.get("YESCAPTCHA_KEY", "")
OUTPUT_FILE = os.path.expanduser("~/kimchi_keys.txt")
NUM_INSTANCES = int(os.environ.get("INSTANCES", "3"))
NUM_LOOPS = int(os.environ.get("LOOPS", "0"))  # 0 = infinite
HEADLESS = True

def solve_captcha(worker_id, base64_img):
    client_key = YESCAPTCHA_API_KEY
    def wprint(msg):
        print(f"[Instance {worker_id}] {msg}")
    try:
        if "base64," in base64_img:
            base64_img = base64_img.split("base64,")[-1]
        data = json.dumps({
            "clientKey": client_key,
            "task": {"type": "ImageToTextTask", "body": base64_img}
        }).encode('utf-8')
        req = urllib.request.Request("https://api.yescaptcha.com/createTask", data=data, headers={'Content-Type': 'application/json'})
        res = urllib.request.urlopen(req)
        response_body = json.loads(res.read())
        if response_body.get("errorId") != 0:
            wprint(f"YesCaptcha error: {response_body.get('errorDescription')}")
            return None
        task_id = response_body.get("taskId")
        if response_body.get("status") == "ready" and response_body.get("solution"):
            return response_body["solution"].get("text")
        data_get = json.dumps({"clientKey": client_key, "taskId": task_id}).encode('utf-8')
        req_get = urllib.request.Request("https://api.yescaptcha.com/getTaskResult", data=data_get, headers={'Content-Type': 'application/json'})
        for _ in range(15):
            time.sleep(2)
            res_get = urllib.request.urlopen(req_get)
            body_get = json.loads(res_get.read())
            if body_get.get("status") == "ready":
                return body_get.get("solution", {}).get("text")
        return None
    except Exception as e:
        wprint(f"Captcha exception: {e}")
        return None

async def run_bot(p, worker_id):
    def wprint(msg):
        print(f"[Instance {worker_id}] {msg}")
    browser = None
    try:
        wprint("Launching Chromium headless...")
        browser = await p.chromium.launch(headless=HEADLESS, args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'])
        context = await browser.new_context()
        page = await context.new_page()
        wprint("Opening Kimchi.dev signup...")
        await page.goto("https://t.co/F0sfVaI3YP", wait_until="load")
        start_btn = page.locator('a[data-cta="Start free"]')
        await start_btn.wait_for(state="visible")
        async with context.expect_page() as new_page_info:
            await start_btn.click()
        new_page = await new_page_info.value
        await new_page.wait_for_load_state("load")
        signup_email = new_page.locator('#signup-email')
        try:
            await signup_email.wait_for(state="visible", timeout=15000)
        except:
            signup_btn = new_page.locator('a.btn-goto-signup')
            if await signup_btn.is_visible():
                await signup_btn.click()
                await new_page.wait_for_timeout(2000)
            await signup_email.wait_for(state="visible")
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        email = f"{random_str}@spamok.com"
        password = "LoeSiapaAJG@"
        wprint(f"Signup: {email}")
        await new_page.fill('#signup-email', email)
        await new_page.fill('#signup-password', password)
        while True:
            img_locator = new_page.locator('#signup-captcha-container .captcha-challenge img')
            await img_locator.wait_for(state='visible')
            png_bytes = await img_locator.screenshot(type="png")
            base64_img = base64.b64encode(png_bytes).decode('utf-8')
            captcha_text = await asyncio.to_thread(solve_captcha, worker_id, base64_img)
            if captcha_text:
                wprint(f"Captcha: {captcha_text}")
                await new_page.fill('#signup-captcha-container input[name="captcha"]', captcha_text)
                await new_page.click('#btn-signup')
                await new_page.wait_for_timeout(4000)
                success = new_page.locator('h2[data-testid="error-title"]')
                if await success.is_visible() and "Confirm your email" in await success.inner_text():
                    break
                if await img_locator.is_visible():
                    reload_btn = new_page.locator('#signup-captcha-container .captcha-reload')
                    if await reload_btn.is_visible(): await reload_btn.click()
                    await new_page.wait_for_timeout(1000)
                    continue
                else:
                    break
            else:
                reload_btn = new_page.locator('#signup-captcha-container .captcha-reload')
                if await reload_btn.is_visible(): await reload_btn.click()
        spamok_url = f"https://spamok.com/{random_str}"
        await new_page.goto(spamok_url, wait_until="load")
        email_row = new_page.locator('tr', has_text="no-reply@cast.ai").first
        while True:
            try:
                await email_row.wait_for(state="visible", timeout=5000)
                break
            except:
                await new_page.reload(wait_until="load")
        await email_row.locator('strong').first.click(force=True)
        await new_page.wait_for_timeout(2000)
        verify_btn = new_page.locator('a#verify-button')
        try:
            await verify_btn.wait_for(state="visible", timeout=10000)
        except:
            verify_btn = new_page.frame_locator('iframe').locator('a#verify-button').first
            await verify_btn.wait_for(state="visible", timeout=10000)
        async with context.expect_page() as vp:
            await verify_btn.click(force=True)
        verify_page = await vp.value
        await verify_page.wait_for_load_state("load")
        try:
            login_email = verify_page.locator('#login-email')
            await login_email.wait_for(state="visible", timeout=10000)
            await verify_page.fill('#login-email', email)
            await verify_page.fill('#login-password', password)
            while True:
                img_login = verify_page.locator('#login-captcha-container .captcha-challenge img')
                await img_login.wait_for(state='visible')
                png = await img_login.screenshot(type="png")
                b64 = base64.b64encode(png).decode('utf-8')
                ct = await asyncio.to_thread(solve_captcha, worker_id, b64)
                if ct:
                    await verify_page.fill('#login-captcha-container input[name="captcha"]', ct)
                    await verify_page.click('#btn-login')
                    await verify_page.wait_for_timeout(4000)
                    if await img_login.is_visible():
                        rl = verify_page.locator('#login-captcha-container .captcha-reload')
                        if await rl.is_visible(): await rl.click()
                        continue
                    break
                else:
                    rl = verify_page.locator('#login-captcha-container .captcha-reload')
                    if await rl.is_visible(): await rl.click()
        except:
            pass
        await verify_page.wait_for_load_state("load")
        account_btn = verify_page.locator('button:has-text("Account")')
        await account_btn.wait_for(state="visible", timeout=15000)
        await account_btn.click()
        api_btn = verify_page.locator('a[role="menuitem"]:has-text("API Keys")')
        await api_btn.wait_for(state="visible", timeout=5000)
        await api_btn.click()
        await verify_page.wait_for_load_state("load")
        await verify_page.wait_for_timeout(5000)
        create_btn = verify_page.locator('button[data-variant="default"]:has-text("Create API Key")').first
        await create_btn.wait_for(state="visible", timeout=15000)
        await create_btn.click()
        key_input = verify_page.locator('#key-name')
        await key_input.wait_for(state="visible", timeout=10000)
        await key_input.fill('CloakBotKey')
        create = verify_page.locator('div[role="dialog"] button', has_text="Create").first
        await create.click()
        api_input = verify_page.locator('div[role="dialog"] input[readonly]').first
        await api_input.wait_for(state="visible", timeout=15000)
        api_key = await api_input.input_value()
        wprint(f"API Key: {api_key}")
        with open(OUTPUT_FILE, "a") as f:
            f.write(f"{email}|{password}|{api_key}\n")
        done = verify_page.locator('div[role="dialog"] button:has-text("Done")').first
        await done.click()
        await browser.close()
        return api_key
    except Exception as e:
        wprint(f"Error: {e}")
        return None
    finally:
        if browser:
            try: await browser.close()
            except: pass

async def run_batch(n):
    async with async_playwright() as p:
        tasks = [run_bot(p, i+1) for i in range(n)]
        for i in range(n):
            await asyncio.sleep(1)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, str) and r.startswith("castai")]

async def main():
    print(f"Kimchi Key Generator | Instances: {NUM_INSTANCES} | Loops: {'∞' if NUM_LOOPS==0 else NUM_LOOPS}")
    keys, loop = [], 0
    while True:
        loop += 1
        print(f"\n--- LOOP {loop} ---")
        new = await run_batch(NUM_INSTANCES)
        keys.extend(new)
        print(f"Got {len(new)} keys. Total: {len(keys)}")
        if NUM_LOOPS and loop >= NUM_LOOPS:
            break
        await asyncio.sleep(5)
    print(f"\n=== {len(keys)} KEYS ===")
    for k in keys: print(k)

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: print("\nStopped.")
