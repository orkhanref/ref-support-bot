import asyncio, sqlite3, datetime, os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# Render ucun env, lokal ucun asagiya yaz
TOKEN = os.getenv("BOT_TOKEN") or "BURAYA TOKENINI YAZ"
ADMIN_ID = int(os.getenv("ADMIN_ID") or 0)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class UserStates(StatesGroup):
    waiting_suggest = State()
    waiting_question = State()

FAQ = {
    "cat_nazn": {"title": "📋 Təyinatlar", "answer": "Təyinatlar hər həftə Çərşənbə 18:00-dək rəsmi qrupda dərc olunur. 2 tur ardıcıl təyinat almamısansa, kuratora yaz."},
    "cat_cat": {"title": "⭐ Kateqoriya", "answer": "Kateqoriya artımı: qiymətlər, normativ, IFAB testi. Seminarlar ildə 2 dəfə olur."},
    "cat_train": {"title": "🏋️ Məşqlər və normativlər", "answer": "Normativ: Yo-Yo test minimum 16.5, sprint 6x40m 6.2 san. Həftədə minimum 3 məşq."},
    "cat_rules": {"title": "📖 IFAB Qaydaları 24/25", "answer": "Son dəyişikliklər: əllə oyun, ofsajd, əlavə dəqiqələr. Epizodu yaz."},
    "cat_pay": {"title": "💰 Ödənişlər", "answer": "Ödənişlər növbəti ayın 10-na qədər köçürülür."},
    "cat_problem": {"title": "⚠️ Problem / Konflikt", "answer": "Hadisə olubsa 24 saatda hesabat doldur və burada qısa təsvir et."},
    "cat_form": {"title": "👕 Forma", "answer": "Forma mövsüm əvvəlində verilir. Ölçü dəyişməli və ya cırılıbsa yaz."}
}

def init_db():
    conn = sqlite3.connect("referee_bot.db")
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY, user_id INTEGER, username TEXT, category TEXT, text TEXT, date TEXT)")
    conn.commit()
    conn.close()

def save_question(uid, uname, cat, txt):
    conn = sqlite3.connect("referee_bot.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO questions (user_id, username, category, text, date) VALUES (?, ?, ?, ?, ?)", (uid, uname, cat, txt, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✍️ Təklif bildir", callback_data="suggest")],[InlineKeyboardButton(text="❓ Sual ver", callback_data="ask")],[InlineKeyboardButton(text="📞 Əlaqə və kömək", callback_data="contacts")]])

def ask_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📋 Təyinatlar", callback_data="cat_nazn")],[InlineKeyboardButton(text="⭐ Kateqoriya", callback_data="cat_cat")],[InlineKeyboardButton(text="🏋️ Məşqlər", callback_data="cat_train")],[InlineKeyboardButton(text="📖 Qaydalar", callback_data="cat_rules")],[InlineKeyboardButton(text="💰 Ödənişlər", callback_data="cat_pay")],[InlineKeyboardButton(text="⚠️ Problem", callback_data="cat_problem")],[InlineKeyboardButton(text="👕 Forma", callback_data="cat_form")],[InlineKeyboardButton(text="⬅️ Geri", callback_data="back_main")]])

def faq_kb(k):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✉️ Kuratora yaz", callback_data=f"write_{k}")],[InlineKeyboardButton(text="⬅️ Kateqoriyalara", callback_data="ask")],[InlineKeyboardButton(text="🏠 Əsas menyu", callback_data="back_main")]])

@dp.message(Command("start"))
async def start_cmd(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Salam! Mən Ref Support — hakimlərə dəstək botuyam. 👋\n\nBurada təyinatlar, kateqoriya, IFAB qaydaları və problem barədə sual verə bilərsən. Şəxsi sualları yalnız baş kurator görür.", reply_markup=main_kb())

@dp.callback_query(F.data == "back_main")
async def back_main(c: CallbackQuery, state: FSMContext):
    await state.clear()
    await c.message.edit_text("Əsas menyu:", reply_markup=main_kb())

@dp.callback_query(F.data == "ask")
async def show_cats(c: CallbackQuery):
    await c.message.edit_text("Mövzunu seç:", reply_markup=ask_kb())

@dp.callback_query(F.data == "suggest")
async def suggest_start(c: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_suggest)
    await c.message.edit_text("Təklifini bir mesajla yaz.\nLəğv üçün /start")

@dp.callback_query(F.data.startswith("cat_"))
async def show_faq(c: CallbackQuery):
    d = FAQ.get(c.data)
    await c.message.edit_text(f"{d['title']}\n\n{d['answer']}", reply_markup=faq_kb(c.data))

@dp.callback_query(F.data.startswith("write_"))
async def write_q(c: CallbackQuery, state: FSMContext):
    cat = c.data.replace("write_","")
    await state.set_state(UserStates.waiting_question)
    await state.update_data(category=cat)
    title = FAQ.get(cat, {}).get("title", "Sual")
    await c.message.edit_text(f"Mövzu: {title}\n\nSualını bir mesajla yaz:")

@dp.message(StateFilter(UserStates.waiting_suggest))
async def get_suggest(m: Message, state: FSMContext):
    save_question(m.from_user.id, m.from_user.username, "Təklif", m.text)
    await state.clear()
    await m.answer("Təşəkkür! Mesajın kuratora göndərildi. ✅", reply_markup=main_kb())
    if ADMIN_ID != 0:
        try: await bot.send_message(ADMIN_ID, f"📩 YENİ TƏKLİF\n@{m.from_user.username} ({m.from_user.id})\n\n{m.text}")
        except: pass

@dp.message(StateFilter(UserStates.waiting_question))
async def get_q(m: Message, state: FSMContext):
    data = await state.get_data()
    cat = data.get("category","Sual")
    save_question(m.from_user.id, m.from_user.username, cat, m.text)
    await state.clear()
    await m.answer("Qəbul olundu! Sualın kuratora göndərildi. ✅", reply_markup=main_kb())
    if ADMIN_ID != 0:
        try: await bot.send_message(ADMIN_ID, f"❓ YENİ SUAL [{cat}]\n@{m.from_user.username} ({m.from_user.id})\n\n{m.text}")
        except: pass

@dp.callback_query(F.data == "contacts")
async def contacts(c: CallbackQuery):
    await c.message.edit_text("📞 Əlaqə: Kurator @sizin_nick\nTexniki: bu botda 'Təklif bildir' ilə yaz", reply_markup=main_kb())

async def main():
    init_db()
    print("Bot AZ 24/7 işə düşdü ✅")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
