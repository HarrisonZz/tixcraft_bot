# tixcraft_bot
maxbot(Max的搶票機器人) help you quickly buy your tickets

# binary download
https://github.com/max32002/tixcraft_bot/releases

# how to use
https://max-everyday.com/2018/03/tixcraft-bot/

# demo
https://youtu.be/U6xGBofx-O8

# how to execute source code (Python 3.12 + Selenium 4, managed with uv)

> **One-click shortcut**: You can run `.\setup.ps1` (or double-click `setup.bat`) on Windows, or `chmod +x setup.sh && ./setup.sh` on macOS / Linux to automatically perform Steps 1 and 2 below.

1. **Install `uv`** (skip if already installed):
   - **Windows (PowerShell)**:
     ```powershell
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```
     *(Restart your terminal after installation, or run `$env:Path = "$HOME\.local\bin;$env:Path"` in the current session.)*
   - **macOS / Linux**:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   Verify installation:
   ```bash
   uv --version
   ```

2. **Sync Python 3.12 & locked dependencies** (creates `.venv` from `pyproject.toml` and `uv.lock`; automatically downloads Python 3.12 if missing):
   ```bash
   uv sync --locked
   ```

3. **WebDriver setup**:
   - Selenium 4's built-in **Selenium Manager** automatically downloads and manages `chromedriver` / `geckodriver` when no local binary is present.
   - Optional: if you prefer a local driver binary, place `chromedriver` / `chromedriver.exe` (or `geckodriver` / `geckodriver.exe`) inside the `webdriver/` folder.

4. **Launch settings GUI or run directly**:
   ```bash
   uv run settings.py
   # or run directly using settings.json:
   uv run chrome_tixcraft.py
   ```
   *(Legacy fallback without `uv`: `pip install -r requirements.txt` and `python3 settings.py` / `python3 chrome_tixcraft.py`.)*

# attach to an already-open Chrome (skip the Cloudflare loop)
If the Chrome that the bot launches keeps getting stuck on the Cloudflare challenge, you can open Chrome yourself, log in / pass Cloudflare manually, and then let the bot take over that same window:

> **GUI shortcut (`settings.py`)**: Select `https://kktix.com` or `https://tixcraft.com` and click **`Open Browser`** — it automatically pauses the bot, fills `127.0.0.1:9222`, and launches Chrome with a dedicated profile. Once you finish logging in, click **`Run`** (or **`Resume`** if the bot is already running) to hand control back to the bot. Or skip `Open Browser` and click **`Run`** directly to launch a fresh browser.

1. Quit the bot (and any Chrome it launched).
2. Start Chrome from a terminal with remote debugging enabled. **You must pass a dedicated `--user-data-dir`** (modern Chrome refuses to open port `9222` on the default user profile or merges into an existing normal Chrome window):
   - **Windows (PowerShell, recommended — runs in background)**:
     ```powershell
     Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList @(
       "--remote-debugging-port=9222",
       "--user-data-dir=$HOME\tixcraft-chrome-profile"
     )
     ```
   - **Windows (CMD)**:
     ```cmd
     start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\tixcraft-chrome-profile"
     ```
   - **macOS**:
     ```bash
     "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
       --remote-debugging-port=9222 \
       --user-data-dir="$HOME/tixcraft-chrome-profile"
     ```
   - **Linux**:
     ```bash
     google-chrome \
       --remote-debugging-port=9222 \
       --user-data-dir="$HOME/tixcraft-chrome-profile"
     ```
   - **Verify port `9222` is listening** (should return JSON containing `Browser` and `webSocketDebuggerUrl`):
     ```powershell
     # Windows (PowerShell)
     Invoke-RestMethod http://127.0.0.1:9222/json/version
     ```
     ```bash
     # macOS / Linux
     curl -s http://127.0.0.1:9222/json/version
     ```
3. In that Chrome window, open your target site (e.g. `https://tixcraft.com` or `https://kktix.com`), log in if needed and solve any Cloudflare challenge manually. *(Your login session and cookies are preserved in `tixcraft-chrome-profile` for future runs.)*
4. Set `browser_debug_address` in `settings.json` to `127.0.0.1:9222` (or fill in the "Attach Chrome (debug addr)" field in `settings.py`), then run:
   ```bash
   uv run chrome_tixcraft.py
   ```
   The bot attaches to the Chrome window you already opened and keeps the page you are on (it only navigates to `homepage` if the tab is blank), so your Cloudflare cookie / login session is preserved.

Leave `browser_debug_address` empty (`""`) to go back to the default behaviour of launching a fresh Chrome.

# verification / tests
```bash
uv run python -m unittest discover -s tests -v
```

# build standalone app (PyInstaller `--onedir`)
To package the GUI (`settings`) and bot (`chrome_tixcraft`) into a self-contained `dist/tixcraft_bot/` folder that runs on machines without Python or `uv` installed (only Google Chrome is required):
```powershell
# Windows (PowerShell)
.\build.ps1
```
```bash
# macOS / Linux
chmod +x build.sh && ./build.sh
```
Zip and share the generated `dist/tixcraft_bot/` directory; users can launch `settings.exe` (`./settings` on macOS/Linux) directly.

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
