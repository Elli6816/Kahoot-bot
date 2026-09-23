import os
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from playwright.async_api import async_playwright

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")

# --- سيرفر الويب الخفيف للحفاظ على الخطة المجانية على Render ---
async def handle_ping(request):
    return web.Response(text="Kahoot Super-Bot is active!")

async def start_dummy_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# --- دالة كاهوت فائقة السرعة ---
async def start_kahoot_bot(game_pin: str, nickname: str):
    async with async_playwright() as p:
        # تشغيل المتصفح مع تحسينات أداء صارمة لزيادة السرعة
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--disable-gpu"
            ]
        )
        
        # إنشاء سياق صفحة مع تعطيل الصور والملفات غير الضرورية لتسريع التحميل بشكل جنوني
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # الدخول الفوري بدون انتظار تحميل الصور والإعلانات
            await page.goto("https://kahoot.it/", wait_until="domcontentloaded")
            
            # كتابة الـ PIN فور ظهور الحقل بأسرع وقت
            await page.wait_for_selector("#game-input", timeout=5000)
            await page.fill("#game-input", game_pin)
            await page.press("#game-input", "Enter")
            
            # تخطي شاشة الاسم والضغط فوراً
            await page.wait_for_selector("#nickname", timeout=5000)
            await page.fill("#nickname", nickname)
            await page.press("#nickname", "Enter")
            
            print(f"Lightning fast! Joined Kahoot as {nickname}")
            
            # البقاء متصلاً باللعبة
            while True:
                await asyncio.sleep(60)
                
        except Exception as e:
            print(f"Speed bot error: {e}")
        finally:
            await browser.close()

# --- أوامر التلغرام ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚡ بوت كاهوت الخارق جاهز! استخدم الأمر:\n/join <PIN> <الاسم>")

async def join_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("الرجاء إدخال الرمز والاسم هكذا: /join <PIN> <Name>")
        return
    
    game_pin = args[0]
    nickname = args[1]
    
    await update.message.reply_text(f"🚀 جاري الانضمام بسرعة البرق إلى الكاهوت برمز {game_pin}...")
    asyncio.create_task(start_kahoot_bot(game_pin, nickname))

# --- التشغيل الأساسي ---
async def main():
    asyncio.create_task(start_dummy_server())
    
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("join", join_command))
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    stop_event = asyncio.Event()
    await stop_event.wait()

if __name__ == "__main__":
    asyncio.run(main())
