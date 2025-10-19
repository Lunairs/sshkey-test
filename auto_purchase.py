"""Automate the purchase of time-limited items in a marketplace.

This script is intentionally written in a configuration-heavy way so that you
can plug it into the actual marketplace UI you are targeting.  Update the
CSS/XPath selectors and URLs below before using it.

⚠️  The game’s terms of service may forbid automation.  Use it at your own
    risk – running the script could get the account suspended or banned.

Prerequisites
-------------
- Python 3.9+
- Selenium WebDriver (`pip install selenium`)
- A webdriver binary (ChromeDriver / GeckoDriver, etc.) that matches your
  browser version and is available on your PATH.

The script assumes that the target page already has the user logged in.  If
the marketplace requires authentication, open the browser manually once,
log in, and save the profile.  Then configure Selenium to reuse the profile
folder.
"""

from __future__ import annotations

import argparse
import dataclasses
import logging
import sys
import time
from typing import Optional

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


@dataclasses.dataclass
class ScriptConfig:
    """Configuration knobs for the automation logic."""

    market_url: str
    countdown_selector: str
    purchase_button_selector: str
    confirm_button_selector: str
    profile_path: Optional[str] = None
    poll_interval: float = 0.05
    prewarm_margin: float = 2.0
    post_click_wait: float = 10.0


def parse_timespan(text: str) -> float:
    """Convert a countdown string (``HH:MM:SS`` or ``MM:SS``) into seconds.

    The marketplace usually shows a format like ``00:05:12``.  If the actual
    UI differs, adjust this parser accordingly.
    """

    pieces = [p.strip() for p in text.split(":") if p.strip()]
    if not pieces or any(not piece.isdigit() for piece in pieces):
        raise ValueError(f"Unsupported countdown text: {text!r}")

    seconds = 0
    for piece in pieces:
        seconds = seconds * 60 + int(piece)
    return float(seconds)


def wait_for_countdown(driver, selector: str, *, poll_interval: float, margin: float) -> None:
    """Block until the countdown reaches zero (or slightly below).

    ``margin`` is subtracted from the remaining time so that the script queues
    the click a tiny bit before the timer reaches 0.
    """

    logging.info("Waiting for countdown to hit zero...")
    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))

    while True:
        element = driver.find_element(By.CSS_SELECTOR, selector)
        remaining_text = element.text.strip()

        try:
            remaining = parse_timespan(remaining_text)
        except ValueError:
            logging.warning("Ignoring non-numeric countdown text: %s", remaining_text)
            time.sleep(poll_interval)
            continue

        logging.debug("Countdown = %.3fs", remaining)

        if remaining <= margin:
            logging.info("Countdown threshold reached: %.3fs", remaining)
            return

        sleep_for = min(poll_interval, max(remaining - margin, poll_interval))
        time.sleep(sleep_for)


def click_when_clickable(driver, selector: str, *, timeout: float) -> None:
    logging.info("Clicking %s", selector)
    wait = WebDriverWait(driver, timeout)
    element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
    element.click()


def run(config: ScriptConfig) -> None:
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--start-maximized")
    if config.profile_path:
        chrome_options.add_argument(f"--user-data-dir={config.profile_path}")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        logging.info("Opening %s", config.market_url)
        driver.get(config.market_url)

        wait_for_countdown(
            driver,
            config.countdown_selector,
            poll_interval=config.poll_interval,
            margin=config.poll_interval,
        )

        click_when_clickable(driver, config.purchase_button_selector, timeout=10)
        click_when_clickable(driver, config.confirm_button_selector, timeout=5)

        logging.info("Purchase flow completed; waiting for confirmation dialog to close.")
        time.sleep(config.post_click_wait)
    finally:
        logging.info("Closing browser.")
        driver.quit()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Marketplace purchase automator")
    parser.add_argument("--url", dest="market_url", required=True, help="URL of the item page")
    parser.add_argument(
        "--countdown-selector",
        required=True,
        help="CSS selector pointing to the countdown timer element",
    )
    parser.add_argument(
        "--purchase-selector",
        required=True,
        help="CSS selector of the main 'Buy' button",
    )
    parser.add_argument(
        "--confirm-selector",
        required=True,
        help="CSS selector of the confirmation button inside the modal",
    )
    parser.add_argument("--profile", dest="profile_path", help="Path to Chrome user-data directory")
    parser.add_argument(
        "--poll-interval",
        dest="poll_interval",
        type=float,
        default=0.05,
        help="Time (seconds) between countdown checks",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging for debugging"
    )

    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s",
    )

    config = ScriptConfig(
        market_url=args.market_url,
        countdown_selector=args.countdown_selector,
        purchase_button_selector=args.purchase_selector,
        confirm_button_selector=args.confirm_selector,
        profile_path=args.profile_path,
        poll_interval=args.poll_interval,
    )

    try:
        run(config)
    except NoSuchElementException as exc:
        logging.error("Failed to locate an element – double-check the selectors: %s", exc)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
