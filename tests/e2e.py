"""Run with the app on port 8000: python tests/e2e.py"""

from pathlib import Path
import shutil

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
ARTIFACTS.mkdir(exist_ok=True)
ANSWER = """During a FastAPI project, I was responsible for a slow API endpoint. First, I measured response latency and checked the database query logs to find where time was spent. I added an index for the repeated lookup and wrote unit and integration tests around the endpoint. Because some reads did not change often, I added a small cache and documented the invalidation trade-off. The result reduced response time by 42 percent. I communicated the change to my teammate, added a regression check, and learned to profile before optimizing."""

with sync_playwright() as playwright:
    system_chrome = shutil.which("google-chrome") or shutil.which("chromium")
    launch_options = {"executable_path": system_chrome} if system_chrome else {}
    browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"], **launch_options)
    page = browser.new_page(viewport={"width": 1440, "height": 1050})
    errors = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))

    page.goto("http://127.0.0.1:8000", wait_until="networkidle")
    page.get_by_role("heading", name="Practice with purpose.").wait_for()
    page.screenshot(path=str(ARTIFACTS / "01-overview.png"), full_page=True)

    page.get_by_role("button", name="New practice").first.click()
    page.get_by_label("Target role").fill("Backend Developer")
    page.get_by_label("Job description").fill("Python FastAPI SQL PostgreSQL Docker. Build reliable APIs and test production services.")
    page.get_by_role("button", name="Build my practice").click()
    page.get_by_role("heading", name="Your answer", exact=True).wait_for()
    page.locator("#answer-input").fill(ANSWER)
    page.screenshot(path=str(ARTIFACTS / "03-practice.png"), full_page=True)
    page.get_by_role("button", name="Review my answer").click()
    page.get_by_role("heading", name="What worked. What to sharpen.").wait_for()
    page.locator(".feedback-list li").first.wait_for()
    page.screenshot(path=str(ARTIFACTS / "04-feedback.png"), full_page=True)
    assert page.locator(".feedback-list li").count() >= 4
    assert "local rubric" in page.locator(".analysis-label").inner_text().lower()

    page.get_by_role("button", name="Next question").click()
    page.get_by_role("heading", name="Your answer", exact=True).wait_for()
    assert "QUESTION 2 OF 5" in page.locator(".practice-count").inner_text()

    mobile = browser.new_page(viewport={"width": 390, "height": 844})
    mobile.goto("http://127.0.0.1:8000", wait_until="networkidle")
    mobile.get_by_role("heading", name="Practice with purpose.").wait_for()
    mobile.screenshot(path=str(ARTIFACTS / "05-mobile-overview.png"), full_page=True)
    assert not errors, errors
    print("Browser smoke test passed. Screenshots saved to artifacts/.")
    browser.close()
