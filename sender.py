import os
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from playwright.async_api import async_playwright

# التوكن الخاص ببوت التلغرام
TELEGRAM_TOKEN = "8787978619:AAG0KWUdrU5PXgfcKGoD1lZD1Vi6Ltq709E"

# --- سيرفر الويب للحفاظ على الخطة المجانية على Render ---
async def handle_ping(request):
    return web.Response(text="Kahoot Blast-Bot is active!")

async def start_dummy_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# --- دالة دخول بوت واحد بسرعة البرق ---
async def launch_single_bot(game_pin: str, nickname: str):
    async with async_playwright() as p:
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
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # الدخول الفوري بدون انتظار الصور
            await page.goto("https://kahoot.it/", wait_until="domcontentloaded")
            
            # كتابة الـ PIN والضغط Enter
            await page.wait_for_selector("#game-input", timeout=5000)
            await page.fill("#game-input", game_pin)
            await page.press("#game-input", "Enter")
            
            # كتابة الاسم والضغط Enter
            await page.wait_for_selector("#nickname", timeout=5000)
            await page.fill("#nickname", nickname)
            await page.press("#nickname", "Enter")
            
            print(f"Blasted into Kahoot as: {nickname}")
            
            # البقاء داخل اللعبة
            while True:
                await asyncio.sleep(60)
                
        except Exception as e:
            print(f"Error for {nickname}: {e}")
        finally:
            await browser.close()

# --- أوامر التلغرام ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 بوت تفجير الكاهوت جاهز وبأقصى سرعة!\n"
        "استخدم الأمر برسالة واحدة هكذا:\n"
        "/blast <PIN> <العدد> <الأسماء>\n"
        "مثال:\n"
        "/blast 123456 15 أحمد توفيق"
    )

async def blast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    parts = text.split(" ")
    
    if len(parts) < 4:
        await update.message.reply_text("❌ الصيغة غلط! اكتب بالشكل التالي:\n/blast <PIN> <العدد> <الأسماء>\nمثال: /blast 123456 10 أحمد توفيق")
        return
    
    game_pin = parts[1]
    try:
        count = int(parts[2])
    except ValueError:
        await update.message.reply_text("❌ العدد لازم يكون رقم صحيح (مثلاً 10 أو 30).")
        return
        
    base_name = " ".join(parts[3:])
    
    await update.message.reply_text(f"🚀 جاري تفجير الكاهوت برمز {game_pin} وإطلاق {count} بوتات بسرعة فائقة جداً للوصول للبونوس!")

    # إطلاق البوتات بفارق زمني بسيط جداً (0.5 ثانية) لتدخل وراء بعضها كالصاروخ
    for i in range(1, count + 1):
        nickname = f"{base_name} {i}"
        asyncio.create_task(launch_single_bot(game_pin, nickname))
        await asyncio.sleep(0.5)

# --- التشغيل الأساسي ---
async def main():
    asyncio.create_task(start_dummy_server())
    
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("blast", blast_command))
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    stop_event = asyncio.Event()
    await stop_event.wait()

if __name__ == "__main__":
    asyncio.run(main())
