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

# verification / tests
```bash
python3 -m unittest discover -s tests -v
```

# scope & notes
- This tool automates page navigation, date/area selection, ticket quantity selection, and agreement checkboxes based on `settings.json`.
- Account login, order confirmation, and payment remain manual in the browser window.
- When `tixcraft.captcha_assist` is enabled, the app enlarges and shows the CAPTCHA image in a small Tk window. The user still reads and types the code, and the app only copies that code into `#TicketForm_verifyCode`; it never submits the order form.
- CAPTCHA assist settings:
  - `captcha_assist`: opt in to the prompt (default: `false`).
  - `captcha_prompt_timeout_s`: seconds before each prompt closes (default: `60`).
  - `captcha_max_retries`: maximum capture/prompt/fill attempts (default: `3`).
- The graphical prompt requires Tkinter and Pillow. If Tk is unavailable, the app temporarily saves the image and prompts in the terminal with the same timeout.

# implement introduce
https://stackoverflow.max-everyday.com/2018/03/selenium-chrome-webdriver/

# suggestion 
please run this source code with high performance hardware computer and high speed + stable network.

門票的「限量」是很殘酷的，建議不要用破舊的電腦或連線不穩的手機網路來搶票，因為只要比別人慢個 0.1 秒，票可能就沒了。為了要搶到限量的票真心建議去一下網咖或找一個網路連線穩定且快的地方並使用硬體不差的電腦來搶票。
