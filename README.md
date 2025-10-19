# Market sniping helper

This repository ships a single script, `auto_purchase.py`, which automates the
two-click checkout flow for time-limited items in a marketplace.  Configure it
with the CSS selectors for the countdown timer, the initial **Buy** button and
the confirmation button inside the popup.  The script monitors the countdown
and performs both clicks as soon as the timer reaches zero.

⚠️  Automation may violate the game’s terms of service.  Use the script at your
    own risk – your account could be suspended.

## Usage

1. Install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install selenium
   ```

2. Download a matching WebDriver binary (ChromeDriver, GeckoDriver …) and make
   sure it is available on your `PATH`.

3. Collect the relevant selectors on the marketplace page.  For example:

   ```text
   Countdown timer:  div.countdown span
   Buy button:       button.buy-btn
   Confirm button:   div.modal button.confirm
   ```

4. Run the script:

   ```bash
   python auto_purchase.py \
     --url "https://example.com/market/item/123" \
     --countdown-selector "div.countdown span" \
     --purchase-selector "button.buy-btn" \
     --confirm-selector "div.modal button.confirm" \
     --profile "$HOME/.config/google-chrome/Default" \
     --poll-interval 0.05
   ```

5. Keep the browser window in the foreground until the purchase is executed.

If the marketplace shows the countdown in a different format (for example
`29分30秒`), adjust the `parse_timespan` function in `auto_purchase.py` to match
your locale.
