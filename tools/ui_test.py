"""End-to-end UI test of the judge's path. Works against local or live URL.

  python tools/ui_test.py --url http://localhost:8765 --shots out_dir [--live]

--live additionally asserts real AWS behaviour (Bedrock engine, Polly audio, Translate).
Requires: pip install playwright  (uses the installed Microsoft Edge, no download).
"""
import argparse
import os
import sys
import time

from playwright.sync_api import expect, sync_playwright

p = argparse.ArgumentParser()
p.add_argument("--url", default="http://localhost:8765")
p.add_argument("--shots", default="ui_shots")
p.add_argument("--live", action="store_true")
p.add_argument("--headed", action="store_true")
args = p.parse_args()
os.makedirs(args.shots, exist_ok=True)

failures = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        failures.append(msg)


with sync_playwright() as pw:
    browser = pw.chromium.launch(channel="msedge", headless=not args.headed)
    for label, vp in (("desktop", {"width": 1280, "height": 900}), ("mobile", {"width": 390, "height": 844})):
        ctx = browser.new_context(viewport=vp, locale="en-IN", device_scale_factor=1 if label == "desktop" else 2)
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

        t0 = time.time()
        page.goto(args.url, wait_until="networkidle")
        check(time.time() - t0 < 8, f"[{label}] home loads in {time.time() - t0:.1f}s")
        page.screenshot(path=f"{args.shots}/{label}-1-home.png", full_page=True)
        no_hscroll = page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
        check(no_hscroll, f"[{label}] no horizontal scroll on home")

        # Sample flow
        t0 = time.time()
        page.click("#btn-sample")
        expect(page.locator("#screen-docs")).to_be_visible()
        page.wait_for_function("document.querySelectorAll('.doc .status.ok').length === 5", timeout=90_000)
        read_s = time.time() - t0
        check(True, f"[{label}] all 5 sample docs read in {read_s:.1f}s")
        page.screenshot(path=f"{args.shots}/{label}-2-docs.png", full_page=True)

        page.click("#btn-docs-next")
        expect(page.locator("#screen-review")).to_be_visible()
        holder = page.input_value("#f-bank-holder_name")
        check("PRIANKA" in holder.upper(), f"[{label}] bank holder name extracted as misspelt: {holder!r}")
        check(page.input_value("#f-income-issue_date") == "12/03/2025", f"[{label}] income issue date read: {page.input_value('#f-income-issue_date')!r}")
        last4 = page.input_value("#f-aadhaar-aadhaar_last4")
        check(last4 == "4821", f"[{label}] Aadhaar masked to last 4: {last4!r}")
        if args.live:
            engines = page.locator(".review-doc .engine").all_inner_texts()
            check(all("Bedrock" in e for e in engines), f"[{label}] all docs read by Bedrock: {engines}")
            for f, want in (("#f-aadhaar-name", "PRIYANKA KUMARI"), ("#f-aadhaar-dob", "14/08/2005"),
                            ("#f-bank-ifsc", "DEMO0004587"), ("#f-marksheet-father_name", "RAMESH PRASAD"),
                            ("#f-marksheet-dob", "14/08/2005"), ("#f-income-annual_income", "180000"),
                            ("#f-caste-category", "SC")):
                got = page.input_value(f).strip().upper()
                check(got == want, f"[{label}] {f} == {want!r} (got {got!r})")
        page.screenshot(path=f"{args.shots}/{label}-3-review.png", full_page=True)

        page.click("#btn-check")
        expect(page.locator("#screen-report")).to_be_visible(timeout=20_000)
        titles = page.locator(".issue h3").all_inner_texts()
        print("   issues:", titles)
        check(any("spelled differently on the bank passbook" in x for x in titles), f"[{label}] bank spelling issue shown")
        check(any("income certificate is too old" in x.lower() for x in titles), f"[{label}] old income certificate shown")
        check(any("DBT" in x for x in titles), f"[{label}] DBT seeding reminder shown")
        check(page.locator(".diff del").count() >= 1, f"[{label}] name diff highlighted")
        check(page.locator(".good li").count() >= 3, f"[{label}] passed checks listed")
        page.screenshot(path=f"{args.shots}/{label}-4-report.png", full_page=True)

        # Hindi
        page.click(".lang-toggle button[data-lang=hi]")
        hi_titles = page.locator(".issue h3").all_inner_texts()
        check(any("बैंक पासबुक" in x for x in hi_titles), f"[{label}] report switches to Hindi")
        page.screenshot(path=f"{args.shots}/{label}-5-report-hi.png", full_page=True)

        # Marathi via Translate
        page.select_option("#report-lang", "mr")
        page.wait_for_timeout(500)
        page.wait_for_function("!document.querySelector('.issue h3').textContent.includes('बँक') || true")
        mr = page.locator(".issue h3").first.inner_text()
        if args.live:
            page.wait_for_function("document.querySelector('#report-lang').value === 'mr'", timeout=20_000)
            page.wait_for_timeout(4000)
            mr = page.locator(".issue h3").first.inner_text()
            check(not mr.startswith("[mr]") and mr != hi_titles[0], f"[{label}] Marathi translation: {mr!r}")
        else:
            check(mr.startswith("[mr]"), f"[{label}] translate wired (mock): {mr!r}")
        page.screenshot(path=f"{args.shots}/{label}-6-report-mr.png", full_page=True)

        if args.live and label == "desktop":
            page.select_option("#report-lang", "hi")
            page.click("#btn-listen")
            page.wait_for_timeout(9000)
            playing = page.evaluate("document.querySelector('#btn-listen').textContent.includes('■')")
            check(playing, "[desktop] Polly Hindi audio plays")
            page.click("#btn-listen")

        # Insights
        page.click(".lang-toggle button[data-lang=en]")
        page.click("a[data-go=insights]")
        page.wait_for_timeout(1500)
        page.screenshot(path=f"{args.shots}/{label}-7-insights.png", full_page=True)
        if args.live:
            check(page.locator(".kpi").count() == 3, f"[{label}] insights KPIs rendered")

        # Validation: wrong file type
        page.goto("about:blank")
        page.goto(args.url + "#scheme", wait_until="networkidle")
        page.click("label.choice >> nth=0")
        page.click("#btn-scheme-next")
        page.click("#btn-docs-next")
        check(page.locator("#toast.show").count() == 1, f"[{label}] empty-docs validation toast")

        real_errors = [e for e in errors if "favicon" not in e]
        check(not real_errors, f"[{label}] no console errors {real_errors[:3]}")
        ctx.close()
    browser.close()

print("\nRESULT:", "ALL PASSED" if not failures else f"{len(failures)} FAILED")
sys.exit(1 if failures else 0)
