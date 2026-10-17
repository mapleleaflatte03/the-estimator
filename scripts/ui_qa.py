"""Screenshot every screen at several widths and report horizontal overflow (QA, needs `pip install playwright`).

Usage: python scripts/ui_qa.py --url http://127.0.0.1:8000 --out <dir> [--widths 375 1280] [--dark]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

OVERFLOW_JS = """
() => {
  const vw = document.documentElement.clientWidth;
  const out = [];
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (!r.width || getComputedStyle(el).position === 'fixed') continue;
    const clipped = el.scrollWidth > el.clientWidth + 1 && ['visible', ''].includes(getComputedStyle(el).overflowX) === false ? false
                  : el.scrollWidth > el.clientWidth + 1 && getComputedStyle(el).overflowX === 'visible';
    if (r.right > vw + 1 || clipped) {
      out.push({tag: el.tagName, cls: (el.className && el.className.baseVal === undefined ? el.className : '').slice(0, 60),
                text: (el.innerText || '').slice(0, 50), right: Math.round(r.right), vw});
    }
  }
  return out.slice(0, 15);
}
"""


def shoot(page, out: Path, name: str, report: dict) -> None:
    page.wait_for_timeout(400)
    page.screenshot(path=str(out / f"{name}.png"), full_page=True)
    report[name] = page.evaluate(OVERFLOW_JS)


def run(url: str, out: Path, width: int, dark: bool) -> dict:
    report: dict = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900}, color_scheme="dark" if dark else "light")
        tag = f"{width}{'-dark' if dark else ''}"
        page.goto(url)
        page.wait_for_load_state("networkidle")
        page.get_by_role("button", name="New project").first.click()
        page.get_by_role("button", name="Investor onboarding portal for a private equity fund").click()
        page.locator("form").get_by_role("button", name="Estimate", exact=True).click()
        page.get_by_text("Estimated effort").wait_for(timeout=60000)
        shoot(page, out, f"{tag}-1-estimate", report)
        nav = page.get_by_role("navigation")
        nav.get_by_role("button", name="Work", exact=True).click()
        shoot(page, out, f"{tag}-2-scope", report)
        nav.get_by_role("button", name="Questions").click()
        shoot(page, out, f"{tag}-3-questions", report)
        nav.get_by_role("button", name="Actual hours", exact=True).click()
        page.get_by_text("Actual hours per requirement").click()
        shoot(page, out, f"{tag}-4-actuals", report)
        nav.get_by_role("button", name="Evidence", exact=True).click()
        page.get_by_text("Measured on real data").wait_for(timeout=30000)
        shoot(page, out, f"{tag}-5-evidence", report)
        page.get_by_role("button", name="Your Jev key").click()
        shoot(page, out, f"{tag}-6-key", report)
        browser.close()
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    ap.add_argument("--out", required=True)
    ap.add_argument("--widths", nargs="*", type=int, default=[375, 1280])
    ap.add_argument("--dark", action="store_true")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for w in args.widths:
        rep = run(args.url, out, w, args.dark)
        print(w, json.dumps({k: v for k, v in rep.items() if v}, ensure_ascii=False, indent=1) or "no overflow")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
