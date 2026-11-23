#!/usr/bin/env python3
# encoding=utf-8
"""Local-OCR and human-in-the-loop assistance for tixCraft image verification codes."""

from __future__ import annotations

import base64
from io import BytesIO
import logging
import os
import re
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
CAPTCHA_CODE_MIN_LENGTH = 4
CAPTCHA_CODE_MAX_LENGTH = 6
CAPTCHA_CODE_PATTERN = re.compile(r"^[A-Za-z0-9]+$")


def capture_captcha_image(driver) -> Optional[bytes]:
    """Capture the first usable CAPTCHA image element as PNG bytes."""
    for selector in CAPTCHA_IMAGE_SELECTORS:
        try:
            image_element = driver.find_element(By.CSS_SELECTOR, selector)
            # Scroll above bottom overlays and prefer direct canvas pixel readback
            # so floating banners (e.g. cookie notices) cannot obscure the image.
            data_url = driver.execute_script(
                'var img = arguments[0];'
                'img.scrollIntoView({block: "start", inline: "center"});'
                'try {'
                '  if (img.complete && img.naturalWidth > 0 && img.naturalHeight > 0) {'
                '    var c = document.createElement("canvas");'
                '    c.width = img.naturalWidth;'
                '    c.height = img.naturalHeight;'
                '    c.getContext("2d").drawImage(img, 0, 0);'
                '    return c.toDataURL("image/png");'
                '  }'
                '} catch (e) {}'
                'return null;',
                image_element,
            )
            if isinstance(data_url, str) and data_url.startswith("data:image/png;base64,"):
                image_bytes = base64.b64decode(data_url.split(",", 1)[1])
                if image_bytes:
                    return image_bytes
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


_ocr_engine = None
_ocr_engine_error = None


def _get_ocr_engine():
    """Return a lazily-created ddddocr engine together with any init error."""
    global _ocr_engine, _ocr_engine_error
    if _ocr_engine is None and _ocr_engine_error is None:
        try:
            import ddddocr
        except Exception as exc:
            _ocr_engine_error = exc
            logger.warning(
                "ddddocr is not installed; automatic CAPTCHA recognition is unavailable: %s",
                exc,
            )
            return _ocr_engine, _ocr_engine_error

        try:
            _ocr_engine = ddddocr.DdddOcr(show_ad=False)
        except TypeError:
            # Older ddddocr releases do not accept ``show_ad``.
            _ocr_engine = ddddocr.DdddOcr()
        except Exception as exc:
            _ocr_engine_error = exc
            logger.warning("Unable to initialize ddddocr: %s", exc)

    return _ocr_engine, _ocr_engine_error


def _preprocess_variants(image_bytes: bytes):
    """Yield candidate image byte strings, from the raw capture to enhanced."""
    yield image_bytes

    try:
        from PIL import Image, ImageOps

        source = Image.open(BytesIO(image_bytes)).convert("RGB")
    except Exception:
        return

    resampling = getattr(Image, "Resampling", Image)
    gray = ImageOps.autocontrast(source.convert("L"))
    buffer = BytesIO()
    gray.save(buffer, format="PNG")
    yield buffer.getvalue()

    upscaled = gray.resize((gray.width * 3, gray.height * 3), resampling.LANCZOS)
    buffer = BytesIO()
    upscaled.save(buffer, format="PNG")
    yield buffer.getvalue()


def _normalize_code(raw_text) -> Optional[str]:
    """Validate and normalize an OCR result into a tixCraft-style code.

    tixCraft verification codes are case-sensitive, so the recognized case is
    preserved exactly; only whitespace and non-alphanumeric noise are removed.
    """
    if not isinstance(raw_text, str):
        return None
    code = re.sub(r"[^A-Za-z0-9]", "", raw_text.strip())
    if not (CAPTCHA_CODE_MIN_LENGTH <= len(code) <= CAPTCHA_CODE_MAX_LENGTH):
        return None
    return code


def recognize_captcha(image_bytes: bytes, engine=None) -> Optional[str]:
    """Recognize a tixCraft CAPTCHA image using local ddddocr OCR.

    Returns a normalized code or None when no plausible code can be read.
    ``engine`` is injectable for tests; when omitted a process-wide ddddocr
    engine is created lazily on first use.
    """
    if not image_bytes:
        return None

    if engine is None:
        engine, error = _get_ocr_engine()
        if error is not None or engine is None:
            return None

    for variant in _preprocess_variants(image_bytes):
        try:
            raw_text = engine.classification(variant)
        except Exception as exc:
            logger.warning("CAPTCHA OCR classification failed: %s", exc)
            continue
        code = _normalize_code(raw_text)
        if code:
            return code

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
        try:
            verify_input.click()
            verify_input.clear()
            verify_input.send_keys(code)
        except WebDriverException:
            # Fall back to JS when overlays (e.g. cookie banners) intercept clicks.
            driver.execute_script(
                'var el = arguments[0], val = arguments[1];'
                'el.scrollIntoView({block: "center", inline: "center"});'
                'el.focus();'
                'el.value = val;'
                'el.dispatchEvent(new Event("input", {bubbles: true}));'
                'el.dispatchEvent(new Event("change", {bubbles: true}));',
                verify_input,
                code,
            )
        return verify_input.get_attribute("value") == code
    except (NoSuchElementException, StaleElementReferenceException, WebDriverException) as exc:
        logger.warning("Unable to fill CAPTCHA input: %s", exc)
        return False


class CaptchaAssist:
    """Coordinate CAPTCHA capture, OCR/human recognition, and input filling."""

    def __init__(self, timeout_s: int = 60, max_retries: int = 3,
                 auto_ocr: bool = False, prompt_enabled: bool = True):
        self.timeout_s = max(int(timeout_s), 1)
        self.max_retries = max(int(max_retries), 1)
        self.auto_ocr = bool(auto_ocr)
        self.prompt_enabled = bool(prompt_enabled)

    def run(self, driver) -> bool:
        """Chain capture, recognition and fill, retrying transient failures.

        Each attempt re-captures the image so a replaced DOM element is never
        reused. When ``auto_ocr`` is enabled, local OCR runs first and its code
        is filled automatically; when that fails and ``prompt_enabled`` is on,
        the image is shown to the user as a fallback.

        Returns True once the input holds a code; it does not validate the code
        with the site. Returns False if the user cancels or the prompt times
        out, or after the last capture/fill failure, so the caller can hand
        control back to the user. The order form is never submitted here.
        """
        for attempt in range(1, self.max_retries + 1):
            image_bytes = capture_captcha_image(driver)
            if image_bytes is None:
                logger.warning("CAPTCHA attempt %d/%d: no image captured", attempt, self.max_retries)
                if attempt < self.max_retries:
                    time.sleep(RETRY_DELAY_S)
                continue

            if self.auto_ocr:
                code = recognize_captcha(image_bytes)
                if code:
                    logger.info("CAPTCHA attempt %d/%d: OCR recognized '%s'", attempt, self.max_retries, code)
                    if fill_captcha(driver, code):
                        return True
                    logger.warning("CAPTCHA attempt %d/%d: OCR code '%s' did not fill", attempt, self.max_retries, code)
                else:
                    logger.info("CAPTCHA attempt %d/%d: OCR produced no valid code", attempt, self.max_retries)

            if self.prompt_enabled:
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
