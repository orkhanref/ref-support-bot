import asyncio, sqlite3, datetime, os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = os.getenv("BOT_TOKEN") or "BURAYA TOKENINI YAZ"
ADMIN_ID = int(os.getenv("ADMIN_ID") or 0)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class UserStates(StatesGroup):
    waiting_suggest = State()
    waiting_question = State()

FAQ = {
    "cat_nazn": {"title": "📋 Təyinatlar", "answer": "Təyinatlar Çərşənbə 18:00-dək dərc olunur."},
    "cat_cat": {"title": "⭐ Kateqoriya", "answer": "Kateqoriya: qiymətlər, normativ, IFAB testi."},
    "cat_train": {"title": "🏋️ Məşqlər", "answer": "Yo-Yo 16.5+, 6x40m 6.2s."},
    "cat_rules": {"title": "📖 Qaydalar", "answer": "IFAB 24/25."},
    "cat_pay": {"title": "💰 Ödənişlər", "answer": "Ayın 10-na qədər."},
    "cat_problem": {"title": "⚠️ Problem", "answer": "24 saatda hesabat yaz."},
    "cat_form": {"title": "👕 Forma", "answer": "Mövsüm əvvəlində verilir."}
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
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✍️ Təklif bildir", callback_data="suggest")],[InlineKeyboardButton(text="❓ Sual ver", callback_data="ask")],[InlineKeyboardButton(text="📞 Əlaqə", callback_data="contacts")]])

def ask_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📋 Təyinatlar", callback_data="cat_nazn")],[InlineKeyboardButton(text="⭐ Kateqoriya", callback_data="cat_cat")],[InlineKeyboardButton(text="🏋️ Məşqlər", callback_data="cat_train")],[InlineKeyboardButton(text="📖 Qaydalar", callback_data="cat_rules")],[InlineKeyboardButton(text="💰 Ödənişlər", callback_data="cat_pay")],[InlineKeyboardButton(text="⚠️ Problem", callback_data="cat_problem")],[InlineKeyboardButton(text="👕 Forma", callback_data="cat_form")],[InlineKeyboardButton(text="⬅️ Geri", callback_data="back_main")]])

def faq_kb(k):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✉️ Kuratora yaz", callback_data=f"write_{k}")],[InlineKeyboardButton(text="⬅️ Geri", callback_data="ask")]])

@dp.message(Command("start"))
async def start_cmd(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Salam! Mən Ref Support — hakimlərə dəstək botuyam. Mövzu seç:", reply_markup=main_kb())

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
    await c.message.edit_text("Təklifini bir mesajla yaz:")

@dp.callback_query(F.data.startswith("cat_"))
async def show_faq(c: CallbackQuery):
    d = FAQ.get(c.data)
    await c.message.edit_text(f"{d['title']}\n\n{d['answer']}", reply_markup=faq_kb(c.data))

@dp.callback_query(F.data.startswith("write_"))
async def write_q(c: CallbackQuery, state: FSMContext):
    cat = c.data.replace("write_","")
    await state.set_state(UserStates.waiting_question)
    await state.update_data(category=cat)
    await c.message.edit_text("Sualını bir mesajla yaz:")

@dp.message(StateFilter(UserStates.waiting_suggest))
async def get_suggest(m: Message, state: FSMContext):
    save_question(m.from_user.id, m.from_user.username, "Təklif", m.text)
    await state.clear()
    await m.answer("Qəbul olundu! ✅", reply_markup=main_kb())

@dp.message(StateFilter(UserStates.waiting_question))
async def get_q(m: Message, state: FSMContext):
    d = await state.get_data()
    cat = d.get("category","Sual")
    save_question(m.from_user.id, m.from_user.username, cat, m.text)
    await state.clear()
    await m.answer("Göndərildi! ✅", reply_markup=main_kb())

@dp.callback_query(F.data == "contacts")
async def contacts(c: CallbackQuery):
    await c.message.edit_text("📞 Əlaqə: Kurator @sizin_nick", reply_markup=main_kb())

async def main():
    init_db()
    print("Bot AZ 24/7 ready ✅")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
