"""Capture the screenshots used in docs/index.md from a running Plone site.

Usage, with Plone running (``make start``) on a fresh site
(``DELETE_EXISTING=1 make create-site``)::

    playwright-python scripts/screenshots.py

The script drives a headless Chromium through the content rules UI: it creates
a rule, adds the "Call webhook" action, and assigns the rule to the site,
with one screenshot for each step.
Run it on a fresh site, because it creates the rule every time.

Environment variables:

PLONE_URL
    Site URL. Defaults to ``http://localhost:8080/Plone``.
    Do not use ``127.0.0.1``, because Plone disables the theme for that host.
PLONE_USER, PLONE_PASSWORD
    Manager credentials. Default to ``admin`` and ``admin``.
"""

from pathlib import Path
from playwright.sync_api import sync_playwright

import os


BASE = os.environ.get("PLONE_URL", "http://localhost:8080/Plone")
USER = os.environ.get("PLONE_USER", "admin")
PASSWORD = os.environ.get("PLONE_PASSWORD", "admin")
OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "_static"

RULE_TITLE = "Call webhook on change"
RULE_EVENT = "Object modified"
WEBHOOK_URL = "https://example.com/hooks/build"
WEBHOOK_PAYLOAD = '{"title": "${title}", "url": "${url}"}'


def document_box(locator):
    """Return the bounding box of ``locator`` in page (not viewport) coordinates."""
    return locator.evaluate(
        """el => {
            const r = el.getBoundingClientRect();
            return {
                x: r.left + window.scrollX,
                y: r.top + window.scrollY,
                width: r.width,
                height: r.height,
            };
        }"""
    )


def shoot(page, name, until=None):
    """Save the main content area as ``name``.

    When ``until`` is a locator, the image ends at the bottom of that element.
    """
    box = document_box(page.locator("#content"))
    height = box["height"]
    if until is not None:
        end = document_box(until)
        height = end["y"] + end["height"] - box["y"] + 16
    page.screenshot(
        path=str(OUTPUT / name),
        full_page=True,
        clip={**box, "height": height},
    )
    print(f"saved {name}")


def wait(page):
    page.wait_for_load_state("networkidle")


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        page = browser.new_page(viewport={"width": 1180, "height": 800})
        page.on("pageerror", lambda exc: print(f"pageerror: {exc}"))

        page.goto(f"{BASE}/login")
        page.fill("#__ac_name", USER)
        page.fill("#__ac_password", PASSWORD)
        page.get_by_role("button", name="Log in").click()
        wait(page)

        page.goto(f"{BASE}/@@rules-controlpanel", wait_until="networkidle")
        shoot(page, "content-rules.png")

        page.get_by_role("link", name="Add content rule").click()
        wait(page)
        page.get_by_label("Title").fill(RULE_TITLE)
        page.get_by_label("Triggering event").select_option(label=RULE_EVENT)
        shoot(page, "add-rule.png", until=page.get_by_role("button", name="Save"))
        page.get_by_role("button", name="Save").click()
        wait(page)

        page.get_by_label("Add action").select_option(label="Call webhook")
        shoot(page, "add-action.png")
        actions = page.get_by_role("group", name="Perform the following actions:")
        actions.get_by_role("button", name="Add").click()
        wait(page)

        page.get_by_label("Webhook URL").fill(WEBHOOK_URL)
        page.get_by_label("Call method").select_option(label="POST")
        page.get_by_label("JSON payload").fill(WEBHOOK_PAYLOAD)
        shoot(
            page,
            "webhook-action.png",
            until=page.get_by_role("button", name="Cancel"),
        )
        page.get_by_role("button", name="Save").click()
        wait(page)

        apply_button = page.get_by_role("button", name="Apply rule on the whole site")
        shoot(page, "apply-rule.png")
        apply_button.click()
        wait(page)
        assert "This rule is not assigned" not in page.locator("#content").inner_text()

        browser.close()


if __name__ == "__main__":
    main()
