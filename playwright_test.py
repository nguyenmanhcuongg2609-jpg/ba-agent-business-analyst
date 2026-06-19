"""
playwright_test.py
------------------
Auto-test giao diện Streamlit bằng Playwright.
Test song song nhiều kịch bản, chụp screenshot làm bằng chứng báo cáo.

Yêu cầu:
  pip install playwright
  playwright install chromium

Chạy app trước:  streamlit run app_agent.py
Sau đó chạy:     python playwright_test.py
"""

import asyncio
import os
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

APP_URL        = "http://localhost:8501"
SCREENSHOT_DIR = "screenshots"
TIMEOUT_MS     = 90_000   # 90s — Agent có thể suy nghĩ lâu

os.makedirs(SCREENSHOT_DIR, exist_ok=True)


# ==========================================
# HELPER
# ==========================================
def log(name: str, msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{name}] {msg}")


async def select_mode(page, mode: str):
    """
    Chọn mode BA hoặc QA trên sidebar st.radio.
    mode: "BA" | "QA"
    """
    label = "🧑💼 Business Analyst Mode" if mode == "BA" else "🕵️ Tester / QA Mode"
    try:
        radio = page.get_by_label(label)
        await radio.click()
        await page.wait_for_timeout(1000)
    except Exception:
        # Fallback: click vào text trực tiếp
        await page.get_by_text(label).first.click()
        await page.wait_for_timeout(1000)


async def send_query_and_wait(page, name: str, query: str):
    """Gõ câu hỏi vào chat input và đợi Agent trả lời xong."""
    log(name, f"Gửi câu hỏi: '{query[:60]}...'")

    textarea = page.locator("textarea").last
    await textarea.fill(query)
    await textarea.press("Enter")

    log(name, "Đang đợi Agent suy nghĩ...")

    # Đợi status box chuyển sang "complete" (text Hoàn tất)
    await page.wait_for_selector(
        'text="✅ Hoàn tất!"',
        state="visible",
        timeout=TIMEOUT_MS,
    )
    log(name, "Agent đã trả lời xong!")


async def take_screenshot(page, filename: str):
    path = os.path.join(SCREENSHOT_DIR, filename)
    await page.screenshot(path=path, full_page=True)
    log(filename, f"✅ Đã lưu screenshot: {path}")
    return path


# ==========================================
# CÁC KỊCH BẢN TEST
# ==========================================
async def scenario_ba_tool_calling(browser, delay=0):
    """BA Mode — Tool Calling: hỏi khái niệm Wikipedia."""
    name = "BA-01_ToolCalling"
    await asyncio.sleep(delay)
    context = await browser.new_context(viewport={"width": 1280, "height": 800})
    page = await context.new_page()
    try:
        log(name, "Mở trình duyệt...")
        await page.goto(APP_URL, wait_until="networkidle")
        await page.wait_for_selector("textarea", state="visible", timeout=15000)

        await select_mode(page, "BA")
        await send_query_and_wait(page, name, "Khái niệm OAuth 2.0 là gì?")
        await take_screenshot(page, f"{name}.png")

    except Exception as e:
        log(name, f"❌ LỖI: {e}")
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"{name}_ERROR.png"))
    finally:
        await context.close()


async def scenario_ba_clarification(browser, delay=0):
    """BA Mode — Clarification: yêu cầu mập mờ."""
    name = "BA-02_Clarification"
    await asyncio.sleep(delay)
    context = await browser.new_context(viewport={"width": 1280, "height": 800})
    page = await context.new_page()
    try:
        log(name, "Mở trình duyệt...")
        await page.goto(APP_URL, wait_until="networkidle")
        await page.wait_for_selector("textarea", state="visible", timeout=15000)

        await select_mode(page, "BA")
        await send_query_and_wait(
            page, name,
            "Tôi muốn xây dựng app quản lý khách sạn. Hãy viết User Story."
        )
        await take_screenshot(page, f"{name}.png")

    except Exception as e:
        log(name, f"❌ LỖI: {e}")
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"{name}_ERROR.png"))
    finally:
        await context.close()


async def scenario_qa_functional(browser, delay=0):
    """QA Mode — Functional Test Case generation."""
    name = "QA-01_FunctionalTest"
    await asyncio.sleep(delay)
    context = await browser.new_context(viewport={"width": 1280, "height": 800})
    page = await context.new_page()
    try:
        log(name, "Mở trình duyệt...")
        await page.goto(APP_URL, wait_until="networkidle")
        await page.wait_for_selector("textarea", state="visible", timeout=15000)

        await select_mode(page, "QA")
        await send_query_and_wait(
            page, name,
            "Viết Test Case cho chức năng Đăng nhập. "
            "Actor: Người dùng cuối. Loại test: Functional. "
            "Khoá tài khoản sau 5 lần sai. Cần happy path và negative case."
        )
        await take_screenshot(page, f"{name}.png")

    except Exception as e:
        log(name, f"❌ LỖI: {e}")
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"{name}_ERROR.png"))
    finally:
        await context.close()


async def scenario_qa_clarification(browser, delay=0):
    """QA Mode — Clarification: yêu cầu thiếu thông tin."""
    name = "QA-02_Clarification"
    await asyncio.sleep(delay)
    context = await browser.new_context(viewport={"width": 1280, "height": 800})
    page = await context.new_page()
    try:
        log(name, "Mở trình duyệt...")
        await page.goto(APP_URL, wait_until="networkidle")
        await page.wait_for_selector("textarea", state="visible", timeout=15000)

        await select_mode(page, "QA")
        await send_query_and_wait(
            page, name,
            "Viết Test Case cho hệ thống thanh toán."   # Cố tình mập mờ
        )
        await take_screenshot(page, f"{name}.png")

    except Exception as e:
        log(name, f"❌ LỖI: {e}")
        await page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"{name}_ERROR.png"))
    finally:
        await context.close()


# ==========================================
# MAIN
# ==========================================
async def main():
    print("=" * 60)
    print("🤖 PLAYWRIGHT AUTO-TEST — BA & QA AGENT (CHẠY TUẦN TỰ)")
    print(f"   App URL : {APP_URL}")
    print(f"   Screenshots → ./{SCREENSHOT_DIR}/")
    print("=" * 60 + "\n")

    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=300)

        # Chạy từng cái một, nghỉ 10 giây ở giữa để không bị đụng Rate Limit
        print("📌 Đang chạy: BA-01 Tool Calling")
        await scenario_ba_tool_calling(browser, delay=0)
        
        print("\n⏳ Nghỉ 10 giây để reset Quota API...\n")
        await asyncio.sleep(10)

        print("📌 Đang chạy: QA-02 Clarification")
        await scenario_qa_clarification(browser, delay=0)
        
        print("\n⏳ Nghỉ 10 giây để reset Quota API...\n")
        await asyncio.sleep(10)

        print("📌 Đang chạy: BA-02 Clarification")
        await scenario_ba_clarification(browser, delay=0)
        
        print("\n⏳ Nghỉ 10 giây để reset Quota API...\n")
        await asyncio.sleep(10)

        print("📌 Đang chạy: QA-01 Functional Test")
        await scenario_qa_functional(browser, delay=0)

        await browser.close()

    print("\n" + "=" * 60)
    print("✅ ĐÃ HOÀN TẤT PLAYWRIGHT AUTO-TEST!")
    print(f"📁 Tất cả screenshot đã lưu tại: ./{SCREENSHOT_DIR}/")
    screenshots = [f for f in os.listdir(SCREENSHOT_DIR) if f.endswith(".png")]
    for s in sorted(screenshots):
        print(f"   - {s}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
