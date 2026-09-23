import asyncio
import random
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from playwright.async_api import async_playwright

TELEGRAM_TOKEN = "8787978619:AAG0KWUdrU5PXgfcKGoD1lZD1Vi6Ltq709E"

# حالات المحادثة بالترتيب
PIN_COUNT, NAMES = range(2)

def generate_name_variations(names_list, count):
    generated = []
    for i in range(count):
        shuffled = names_list.copy()
        random.shuffle(shuffled)
        base_name = " ".join(shuffled)
        final_name = f"{base_name} {i+1}"
        generated.append(final_name)
    return generated

async def launch_kahoot_bot(page, pin, name):
    try:
        await page.goto("https://kahoot.it/", wait_until="domcontentloaded")
        await page.fill('input[name="gameId"]', str(pin))
        await page.click('button[type="submit"]')
        
        await page.wait_for_selector('input[name="nickname"]', timeout=8000)
        await page.fill('input[name="nickname"]', name)
        await page.click('button[type="submit"]')
        print(f"[+] تم دخول البوت: {name}")
    except Exception as e:
        print(f"[!] خطأ مع {name}: {e}")

# البدء بأمر /k
async def start_kahoot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📌 أهلاً بك! أرسل لي الآن **رقم اللعبة (PIN)** و **عدد البوتات** مفصولين بمسافة (مثال: `822781 5`)", parse_mode="Markdown")
    return PIN_COUNT

# الخطوة الأولى: استقبال الـ PIN والعدد
async def receive_pin_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    parts = text.split()
    
    if len(parts) < 2:
        await update.message.reply_text("❌ خطأ! الرجاء إرسال الرقم والعدد هكذا: `822781 5`", parse_mode="Markdown")
        return PIN_COUNT

    pin = parts[0]
    try:
        bot_count = int(parts[1])
    except ValueError:
        await update.message.reply_text("❌ عدد البوتات يجب أن يكون رقماً صحيحاً. حاول مجدداً:")
        return PIN_COUNT

    # حفظهم مؤقتاً
    context.user_data['pin'] = pin
    context.user_data['bot_count'] = bot_count

    await update.message.reply_text("👤 ممتاز! الآن أرسل **3 أسماء** مفصولة بمسافات (مثال: `احمد توفيق عياش`)")
    return NAMES

# الخطوة الثانية: استقبال الأسماء وتشغيل البوتات
async def receive_names(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    names = text.split()

    if len(names) < 3:
        await update.message.reply_text("❌ الرجاء إرسال 3 أسماء على الأقل مفصولة بمسافات:")
        return NAMES

    pin = context.user_data.get('pin')
    bot_count = context.user_data.get('bot_count')
    input_names = names[:3]

    generated_names = generate_name_variations(input_names, bot_count)

    await update.message.reply_text(
        f"🚀 جاري تشغيل {bot_count} بوتات من السيرفر السحابي...\n"
        f"📌 اللعبة: {pin}\n"
        f"👤 الأسماء: {', '.join(generated_names[:3])}..."
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        tasks = []
        
        for name in generated_names:
            context_page = await browser.new_context()
            page = await context_page.new_page()
            task = asyncio.create_task(launch_kahoot_bot(page, pin, name))
            tasks.append(task)
            await asyncio.sleep(1.5)

        await asyncio.gather(*tasks)
        await update.message.reply_text("✅ تم إدخال جميع البوتات بنجاح!")
        await asyncio.sleep(900)
        await browser.close()

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ تم إلغاء العملية.")
    return ConversationHandler.END

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 البوت شغال بالسحاب ومستعد! أرسل الأمر `/k` للبدء.", parse_mode="Markdown")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # استخدام ConversationHandler عشان يسألك بالترتيب وبدون لخبطة
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("k", start_kahoot)],
        states={
            PIN_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_pin_count)],
            NAMES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_names)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(conv_handler)
    
    print("🤖 البوت شغال في السحاب...")
    app.run_polling()
