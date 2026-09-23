import os
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from playwright.async_api import async_playwright

# احصل على التوكن من متغيرات البيئة أو ضعه هنا مباشرة
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")

# --- 1. سيرفر الويب الخفيف لإرضاء منصة Render ومنح الخطة المجانية ---
async def handle_ping(request):
    return web.Response(text="Kahoot Bot is active and running!")

async def start_dummy_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Dummy web server running on port {port}")

# --- 2. وظائف بوت كاهوت و Playwright ---
async def start_kahoot_bot(game_pin: str, nickname: str):
    """دالة لتشغيل متصفح خفي والدخول إلى لعبة كاهوت تلقائياً"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        page = await browser.new_page()
        
        try:
            print(f"Navigating to Kahoot with PIN: {game_pin}")
            await page.goto("https://kahoot.it/")
            
            # كتابة رقم الـ PIN
            await page.fill("#game-input", game_pin)
            await page.click("button[type='submit']")
            
            # انتظار واختيار اسم المستخدم (Nickname)
            await page.wait_for_selector("#nickname", timeout=10000)
            await page.fill("#nickname", nickname)
            await page.click("button[type='submit']")
            
            print(f"Successfully joined Kahoot as {nickname}!")
            
            # البقاء داخل اللعبة
            while True:
                await asyncio.sleep(60)
                
        except Exception as e:
            print(f"Error in Kahoot automation: {e}")
        finally:
            await browser.close()

# --- 3. أوامر التلغرام ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! بوت كاهوت جاهز. استخدم الأمر /join PIN NICKNAME للدخول.")

async def join_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("الرجاء إدخال الرمز والاسم هكذا: /join <PIN> <Name>")
        return
    
    game_pin = args[0]
    nickname = args[1]
    
    await update.message.reply_text(f"جاري الانضمام إلى لعبة كاهوت برمز {game_pin} باسم {nickname}...")
    asyncio.create_task(start_kahoot_bot(game_pin, nickname))

# --- 4. الدالة الرئيسية لتشغيل السيرفر والبوت معاً ---
async def main():
    # تشغيل سيرفر الويب في الخلفية من أجل Render
    asyncio.create_task(start_dummy_server())
    
    # إعداد بوت التلغرام
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("join", join_command))
    
    print("Telegram bot is starting...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    stop_event = asyncio.Event()
    await stop_event.wait()

if __name__ == "__main__":
    asyncio.run(main())
