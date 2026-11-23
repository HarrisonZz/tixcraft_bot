#!/usr/bin/env python3
# encoding=utf-8
"""Human-in-the-loop assistance for tixCraft image verification codes."""

from __future__ import annotations

from io import BytesIO
import logging
import os
import select
import sys
import tempfile
import time
from typing import Optional

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    WebDriverException,
)
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)

CAPTCHA_IMAGE_SELECTORS = (
    "#TicketForm_verifyCode-image",
    'img[id*="verifyCode"]',
    '#TicketForm img[src*="captcha"]',
    'img[src*="/captcha"]',
)
VERIFY_CODE_SELECTOR = "#TicketForm_verifyCode"
RETRY_DELAY_S = 0.25


def capture_captcha_image(driver) -> Optional[bytes]:
    """Capture the first usable CAPTCHA image element as PNG bytes."""
    for selector in CAPTCHA_IMAGE_SELECTORS:
        try:
            image_element = driver.find_element(By.CSS_SELECTOR, selector)
            driver.execute_script(
                'arguments[0].scrollIntoView({block: "center", inline: "center"});',
                image_element,
            )
            image_bytes = image_element.screenshot_as_png
            if image_bytes:
                return image_bytes
            logger.warning("CAPTCHA image matched %s but produced an empty screenshot", selector)
        except NoSuchElementException:
            continue
        except StaleElementReferenceException as exc:
            logger.warning("CAPTCHA image matched %s but became stale: %s", selector, exc)
        except WebDriverException as exc:
            logger.warning("Unable to capture CAPTCHA image matched by %s: %s", selector, exc)

    logger.warning("No usable CAPTCHA image element was found")
    return None


def _prompt_with_tk(image_bytes: bytes, timeout_s: int) -> Optional[str]:
    import tkinter as tk

    from PIL import Image, ImageTk

    root = tk.Tk()
    try:
        root.title("CAPTCHA assist")
        root.attributes("-topmost", True)
        root.resizable(False, False)

        source_image = Image.open(BytesIO(image_bytes))
        source_image.load()
        resampling = getattr(Image, "Resampling", Image)
        display_image = source_image.resize(
            (max(source_image.width * 2, 1), max(source_image.height * 2, 1)),
            resampling.LANCZOS,
        )
        photo = ImageTk.PhotoImage(display_image)

        tk.Label(root, image=photo).pack(padx=12, pady=(12, 6))
        entry_value = tk.StringVar()
        entry = tk.Entry(root, textvariable=entry_value, width=24, font=("TkDefaultFont", 16))
        entry.pack(padx=12, pady=6)
        countdown = tk.Label(root)
        countdown.pack(padx=12, pady=(0, 12))

        result = {"code": None}
        deadline_s = max(int(timeout_s), 1)

        def finish(code=None):
            result["code"] = code.strip() if isinstance(code, str) and code.strip() else None
            root.quit()

        def submit(_event=None):
            finish(entry_value.get())

        def tick(remaining):
            if remaining <= 0:
                finish()
                return
            countdown.configure(text="Time remaining: %d seconds" % remaining)
            root.after(1000, tick, remaining - 1)

        root.protocol("WM_DELETE_WINDOW", finish)
        entry.bind("<Return>", submit)
        root.after(0, entry.focus_force)
        tick(deadline_s)
        root.mainloop()
        return result["code"]
    finally:
        try:
            root.destroy()
        except tk.TclError:
            pass


def _read_cli_line(timeout_s: int) -> Optional[str]:
    """Read one terminal line within the configured timeout."""
    timeout_s = max(int(timeout_s), 1)
    prompt = "Enter CAPTCHA code (blank to cancel): "

    if os.name == "nt":
        import msvcrt

        characters = []
        deadline = time.monotonic() + timeout_s
        print(prompt, end="", flush=True)
        while time.monotonic() < deadline:
            if not msvcrt.kbhit():
                time.sleep(0.05)
                continue

            character = msvcrt.getwch()
            if character in ("\r", "\n"):
                print()
                return "".join(characters)
            if character == "\x03":
                raise KeyboardInterrupt
            if character == "\b":
                if characters:
                    characters.pop()
                    print("\b \b", end="", flush=True)
                continue
            if character in ("\x00", "\xe0"):
                # Discard the second byte of a Windows special key.
                if msvcrt.kbhit():
                    msvcrt.getwch()
                continue

            characters.append(character)
            print(character, end="", flush=True)

        print()
        return None

    print(prompt, end="", flush=True)
    try:
        ready, _, _ = select.select([sys.stdin], [], [], timeout_s)
    except (OSError, TypeError, ValueError) as exc:
        logger.warning("Timed terminal input is unavailable: %s", exc)
        print()
        return None

    if not ready:
        print()
        return None
    return sys.stdin.readline()


def _prompt_with_cli(image_bytes: bytes, timeout_s: int) -> Optional[str]:
    image_path = None
    try:
        with tempfile.NamedTemporaryFile(prefix="tixcraft-captcha-", suffix=".png", delete=False) as image_file:
            image_file.write(image_bytes)
            image_path = image_file.name
        print("CAPTCHA image saved to: %s" % image_path)
        code = _read_cli_line(timeout_s)
        return code.strip() if isinstance(code, str) and code.strip() else None
    except (EOFError, KeyboardInterrupt):
        return None
    finally:
        if image_path:
            try:
                os.unlink(image_path)
            except OSError:
                pass


def prompt_user_for_code(image_bytes: bytes, timeout_s: int) -> Optional[str]:
    """Show the CAPTCHA image and return the code typed by the user."""
    if not image_bytes:
        return None

    try:
        code = _prompt_with_tk(image_bytes, timeout_s)
    except Exception as exc:
        logger.warning("CAPTCHA window unavailable; using terminal prompt: %s", exc)
        code = _prompt_with_cli(image_bytes, timeout_s)

    return code.strip() if isinstance(code, str) and code.strip() else None


def fill_captcha(driver, code: str) -> bool:
    """Fill the verification input and confirm that its value matches the code."""
    if not code:
        return False

    try:
        verify_input = driver.find_element(By.CSS_SELECTOR, VERIFY_CODE_SELECTOR)
        verify_input.click()
        verify_input.clear()
        verify_input.send_keys(code)
        return verify_input.get_attribute("value") == code
    except (NoSuchElementException, StaleElementReferenceException, WebDriverException) as exc:
        logger.warning("Unable to fill CAPTCHA input: %s", exc)
        return False


class CaptchaAssist:
    """Coordinate CAPTCHA capture, human entry, and input filling."""

    def __init__(self, timeout_s: int = 60, max_retries: int = 3):
        self.timeout_s = max(int(timeout_s), 1)
        self.max_retries = max(int(max_retries), 1)

    def run(self, driver) -> bool:
        """Chain capture, prompt and fill, retrying transient failures.

        Each attempt re-captures the image so a replaced DOM element is never
        reused. Returns True once the input holds the code the user typed; it
        does not validate the code with the site. Returns False if the user
        cancels or the prompt times out, or after the last capture/fill failure,
        so the caller can hand control back to the user. The order form is
        never submitted here.
        """
        for attempt in range(1, self.max_retries + 1):
            image_bytes = capture_captcha_image(driver)
            if image_bytes is None:
                logger.warning("CAPTCHA attempt %d/%d: no image captured", attempt, self.max_retries)
                if attempt < self.max_retries:
                    time.sleep(RETRY_DELAY_S)
                continue

            code = prompt_user_for_code(image_bytes, self.timeout_s)
            if code is None:
                logger.info("CAPTCHA attempt %d/%d: no code entered; stopping", attempt, self.max_retries)
                return False

            if fill_captcha(driver, code):
                return True
            logger.warning("CAPTCHA attempt %d/%d: input value did not match", attempt, self.max_retries)
            if attempt < self.max_retries:
                time.sleep(RETRY_DELAY_S)

        logger.warning("CAPTCHA assist exhausted %d attempts; returning control to user", self.max_retries)
        return False
