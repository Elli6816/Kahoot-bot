import asyncio
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from playwright.async_api import async_playwright

# ⚠️ استبدل النص التالي بالتوكن اللي نسخته من BotFather
TELEGRAM_TOKEN = "ضع_التوكن_هنا"

def generate_name_variations(names_list, count):
    """توليد أسماء مختلفة بناءً على الأسماء الثلاثة المدخلة"""
    generated = []
    for i in range(count):
        shuffled = names_list.copy()
        random.shuffle(shuffled)
        base_name = " ".join(shuffled)
        final_name = f"{base_name} {i+1}"
        generated.append(final_name)
    return generated

async def launch_kahoot_bot(page, pin, name):
    """تسجيل دخول البوت عبر Playwright بسرعة فائقة"""
    try:
        await page.goto("https://kahoot.it/", wait_until="domcontentloaded")
        
        # إدخال ה-PIN
        await page.fill('input[name="gameId"]', str(pin))
        await page.click('button[type="submit"]')
        
        # انتظار حقل الاسم والإدخال
        await page.wait_for_selector('input[name="nickname"]', timeout=8000)
        await page.fill('input[name="nickname"]', name)
        await page.click('button[type="submit"]')
        
        print(f"[+] تم دخول הבוט بنجاح: {name}")
    except Exception as e:
        print(f"[!] خطأ أثناء دخول הבוט {name}: {e}")

async def start_kahoot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    أمر التلغرام:
    /k [PIN] [العدد] [اسم1] [اسم2] [اسم3]
    مثال: /k 822781 5 احمد توفيق عياش
    """
    args = context.args
    if len(args) < 5:
        await update.message.reply_text(
            "❌ استخدام خاطئ للأمر!\n"
            "الصيغة الصحيحة:\n"
            "`/k [PIN] [العدد] [اسم1] [اسم2] [اسم3]`\n\n"
            "مثال:\n`/k 822781 5 احمد توفيق عياش`",
            parse_mode="Markdown"
        )
        return

    pin = args[0]
    try:
        bot_count = int(args[1])
    except ValueError:
        await update.message.reply_text("❌ عدد البوتات يجب أن يكون رقماً.")
        return

    input_names = args[2:5]
    generated_names = generate_name_variations(input_names, bot_count)

    await update.message.reply_text(
        f"🚀 جاري تشغيل {bot_count} بوتات بسرعة فائقة...\n"
        f"📌 اللعبة: {pin}\n"
        f"👤 الأسماء: {', '.join(generated_names[:3])}..."
    )

    async with async_playwright() as p:
        # تشغيل متصفح خفي (Headless)
        browser = await p.chromium.launch(headless=True)
        tasks = []
        
        for name in generated_names:
            context_page = await browser.new_context()
            page = await context_page.new_page()
            
            task = asyncio.create_task(launch_kahoot_bot(page, pin, name))
            tasks.append(task)
            
            # فاصل 1.5 ثانية لمنع الحظر
            await asyncio.sleep(1.5)

        await asyncio.gather(*tasks)
        await update.message.reply_text("✅ تم إدخال جميع البوتات بنجاح إلى اللعبة!")
        
        # إبقاء المتصفح شغالاً لمدة 15 دقيقة أثناء اللعبة
        await asyncio.sleep(900) 
        await browser.close()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 البوت شغال ومستعد! أرسل الأمر:\n`/k [PIN] [العدد] [اسم1] [اسم2] [اسم3]`")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("k", start_kahoot))
    
    print("🤖 بوت التلغرام شغال ومستعد لاستقبال الأوامر...")
    app.run_polling()
