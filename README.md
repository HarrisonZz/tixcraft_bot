# tixcraft_bot
maxbot(Max的搶票機器人) help you quickly buy your tickets

# binary download
https://github.com/max32002/tixcraft_bot/releases

# how to use
https://max-everyday.com/2018/03/tixcraft-bot/

# demo
https://youtu.be/U6xGBofx-O8

# how to execute source code (Python 3 + Selenium 4)
1. Install dependencies:
```bash
pip install -r requirements.txt
```
2. WebDriver setup:
- Selenium 4's built-in **Selenium Manager** automatically downloads and manages `chromedriver` / `geckodriver` when no local binary is present.
- Optional: if you prefer a local driver binary, place `chromedriver` / `chromedriver.exe` (or `geckodriver` / `geckodriver.exe`) inside the `webdriver/` folder.
3. Launch settings GUI or run directly:
```bash
python3 settings.py
# or run directly using settings.json:
python3 chrome_tixcraft.py
```

# attach to an already-open Chrome (skip the Cloudflare loop)
If the Chrome that the bot launches keeps getting stuck on the Cloudflare challenge, you can open Chrome yourself, log in / pass Cloudflare manually, and then let the bot take over that same window:

1. Quit the bot (and any Chrome it launched).
2. Start Chrome from a terminal with remote debugging enabled (use a dedicated profile so it does not clash with your normal Chrome):
   ```bash
   # macOS
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
     --remote-debugging-port=9222 \
     --user-data-dir="$HOME/tixcraft-chrome-profile"
   ```
   Windows / Linux: launch `chrome.exe` / `google-chrome` with the same
   `--remote-debugging-port=9222 --user-data-dir=...` flags.
3. In that Chrome window, open KKTIX (`https://kktix.com`), log in if needed and solve the Cloudflare challenge manually.
4. Set `browser_debug_address` in `settings.json` to `127.0.0.1:9222` (or fill in the "Attach Chrome (debug addr)" field in `settings.py`), then run:
   ```bash
   python3 chrome_tixcraft.py
   ```
   The bot attaches to the Chrome window you already opened and keeps the page you are on (it only navigates to `homepage` if the tab is blank), so your Cloudflare cookie / login session is preserved.

Leave `browser_debug_address` empty (`""`) to go back to the default behaviour of launching a fresh Chrome.

# verification / tests
```bash
python3 -m unittest discover -s tests -v
```

# scope & notes
- This tool automates page navigation, date/area selection, ticket quantity selection, and agreement controls based on `settings.json`.
- **KKTIX**: supports automatic navigation from event pages (`/events/...`) to `/registrations/new` using a blocking `driver.get` (so the asynchronously-rendered ticket list is detected reliably), comma-separated priority keywords in `kktix.area_keyword` (case-insensitive and thousands-comma insensitive, e.g. `VIP, $3,800, $2800`), exclude keywords in `kktix.area_exclude_keyword` (e.g. `身障, 輪椅`), hidden-row/hidden-button filtering, `+` button fallback, automatic refresh when tickets are not yet available or filtered out, pausing auto-refresh when `/registrations/new` prompts for login, Next Step duplicate-click cooldown, and auto-pressing **"電腦配位"** (computer seat assignment) over **"自行選位"** (manual seat map) for seated events.
- **KKTIX step 2 (fill registration info, `/registrations/<order_id>`)**: the bot auto-checks the agreement controls — the "我同意KKTIX系統所分配之門票，購買後將不能更改或退款" radio and the "我已經閱讀並同意 服務條款 與 隱私權政策" checkbox (`person_agree_terms`, matched by label text) — and, when `kktix.auto_press_next_step_button` is enabled, auto-presses the **"確認表單資料"** (confirm form data) button after any CAPTCHA has been filled. It pauses with one-time input focus while a human verification / CAPTCHA is still empty.
- **Pause / Resume**: click the **Pause / Resume** button in `settings.py` at any time to temporarily pause all automated clicks/refreshes for manual browser control; the bot also automatically pauses when a Cloudflare verification page is detected.
- Account login and payment remain manual in the browser window; the final payment is never submitted by the bot.
- When `tixcraft.captcha_assist` is enabled, the app enlarges and shows the CAPTCHA image in a small Tk window. The user still reads and types the code, and the app only copies that code into `#TicketForm_verifyCode`; it never submits the order form.
- When `tixcraft.captcha_auto_ocr` is enabled, the app first tries to recognize the code locally with `ddddocr` (offline, no API key) and fills it automatically; if recognition fails it falls back to the manual prompt when `captcha_assist` is also enabled.
- When `tixcraft.auto_press_confirm_button` is enabled, the app clicks the "確認張數" (confirm quantity) button once the quantity, agreement checkbox, and verification code have been filled.
- CAPTCHA assist settings:
  - `captcha_assist`: opt in to the manual prompt (default: `false`).
  - `captcha_auto_ocr`: opt in to local OCR recognition (default: `false`).
  - `auto_press_confirm_button`: opt in to auto-clicking the confirm quantity button (default: `false`).
  - `captcha_prompt_timeout_s`: seconds before each prompt closes (default: `60`).
  - `captcha_max_retries`: maximum capture/recognize/fill attempts (default: `3`).
- The graphical prompt requires Tkinter and Pillow. If Tk is unavailable, the app temporarily saves the image and prompts in the terminal with the same timeout.
- Local OCR requires the `ddddocr` package (install with `pip install ddddocr`).

# implement introduce
https://stackoverflow.max-everyday.com/2018/03/selenium-chrome-webdriver/

# suggestion 
please run this source code with high performance hardware computer and high speed + stable network.

門票的「限量」是很殘酷的，建議不要用破舊的電腦或連線不穩的手機網路來搶票，因為只要比別人慢個 0.1 秒，票可能就沒了。為了要搶到限量的票真心建議去一下網咖或找一個網路連線穩定且快的地方並使用硬體不差的電腦來搶票。
