import asyncio
import sqlite3
import datetime
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# ========= AYARLAR - BURANI DOLDUR =========
# Lokal ucun buraya token yaz, hosting ucun Render-de Environment deyiseni kimi elave edeceksen
TOKEN = 8690723080:AAHM_ZzOmDdjoqROGDFqRzw3r5GsPnDqrhM
ADMIN_ID = 1301206951

# ===========================================

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class UserStates(StatesGroup):
    waiting_suggest = State()
    waiting_question = State()

# FAQ AZERBAYCANCA
FAQ = {
    "cat_nazn": {
        "title": "📋 Təyinatlar",
        "answer": "Təyinatlar hər həftə Çərşənbə günü saat 18:00-dək rəsmi qrupda dərc olunur.\n\n2 tur ardıcıl təyinat almamısansa, aşağıdakı düymə ilə kuratora yaz, kateqoriyanı və şəhərini qeyd et."
    },
    "cat_cat": {
        "title": "⭐ Kateqoriya və artım",
        "answer": "Kateqoriya artımı bunlardan asılıdır:\n1) Inspektor qiymətləri\n2) Normativ nəticələri\n3) IFAB qaydaları üzrə test.\n\nArtım seminarları ildə 2 dəfə olur. Anonsları izlə."
    },
    "cat_train": {
        "title": "🏋️ Məşqlər və normativlər",
        "answer": "Hakim normativi: Yo-Yo test minimum 16.5 səviyyə, 6x40m sprint 6.2 saniyədən az.\n\nHəftədə minimum 3 məşq. Testi buraxmısansa, kuratora yaz."
    },
    "cat_rules": {
        "title": "📖 IFAB Qaydaları 24/25",
        "answer": "Son dəyişikliklər: əllə oyun, ofsajd, əlavə olunmuş dəqiqələr.\n\nKonkret epizodu yaz (məs: 'cərimə meydançasında əllə oyun') — qayda üzrə eksperta göndərəcəm."
    },
    "cat_pay": {
        "title": "💰 Ödənişlər",
        "answer": "Ödənişlər növbəti ayın 10-na qədər köçürülür. Əgər gəlməyibsə, sistemdə hesabatı təhvil verdiyini yoxla. Hər şey qaydasındadırsa, 'Kuratora yaz' düyməsinə bas."
    },
    "cat_problem": {
        "title": "⚠️ Oyun zamanı problem",
        "answer": "Hadisə olubsa:\n1) 24 saat ərzində hesabatı doldur\n2) Burada qısa təsvir et\n3) Təhlükəsizlik təhlükəsi varsa, birbaşa kuratora zəng et.\n\nBot mesajını anonim şəkildə göndərəcək."
    },
    "cat_form": {
        "title": "👕 Forma və ləvazimat",
        "answer": "Forma dəsti mövsüm əvvəlində verilir. Ölçü dəyişməli və ya cırılıbsa, foto və ölçü ilə kuratora yaz."
    }
}

def init_db():
    conn = sqlite3.connect("referee_bot.db")
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        category TEXT,
        text TEXT,
        date TEXT
    )""")
    conn.commit()
    conn.close()

def save_question(user_id, username, category, text):
    conn = sqlite3.connect("referee_bot.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO questions (user_id, username, category, text, date) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, category, text, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Təklif bildir", callback_data="suggest")],
        [InlineKeyboardButton(text="❓ Sual ver", callback_data="ask")],
        [InlineKeyboardButton(text="📞 Əlaqə və kömək", callback_data="contacts")]
    ])

def ask_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Təyinatlar", callback_data="cat_nazn")],
        [InlineKeyboardButton(text="⭐ Kateqoriya", callback_data="cat_cat")],
        [InlineKeyboardButton(text="🏋️ Məşqlər", callback_data="cat_train")],
        [InlineKeyboardButton(text="📖 Qaydalar", callback_data="cat_rules")],
        [InlineKeyboardButton(text="💰 Ödənişlər", callback_data="cat_pay")],
        [InlineKeyboardButton(text="⚠️ Problem", callback_data="cat_problem")],
        [InlineKeyboardButton(text="👕 Forma", callback_data="cat_form")],
        [InlineKeyboardButton(text="⬅️ Geri", callback_data="back_main")]
    ])

def faq_kb(cat_key):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Kuratora öz sualımı yaz", callback_data=f"write_{cat_key}")],
        [InlineKeyboardButton(text="⬅️ Kateqoriyalara", callback_data="ask")],
        [InlineKeyboardButton(text="🏠 Əsas menyu", callback_data="back_main")]
    ])

@dp.message(Command("start"))
async def start_cmd(m: Message, state: FSMContext):
    await state.clear()
    await m.answer(
        "Salam! Mən Ref Support — hakimlərə dəstək botuyam. 👋\n\n"
        "Burada təyinatlar, kateqoriya, IFAB qaydaları, ödənişlər və forma ilə bağlı sual verə və ya problem barədə məlumat verə bilərsən.\n"
        "Şəxsi sualları yalnız baş kurator görür.",
        reply_markup=main_kb()
    )

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
    await c.message.edit_text(
        "Təklifini və ya məlumatını bir mesajla yaz.\n\nMəs: 'Video təhlillərin qrupa əlavə olunmasını təklif edirəm'\n\nLəğv üçün /start",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Ləğv et", callback_data="back_main")]])
    )

@dp.callback_query(F.data.startswith("cat_"))
async def show_faq(c: CallbackQuery):
    cat = c.data
    data = FAQ.get(cat)
    if not data:
        return
    text = f"{data['title']}\n\n{data['answer']}\n\nCavab kifayət etmədisə, aşağıdakı düyməni bas."
    await c.message.edit_text(text, reply_markup=faq_kb(cat))

@dp.callback_query(F.data.startswith("write_"))
async def write_question(c: CallbackQuery, state: FSMContext):
    cat = c.data.replace("write_", "")
    await state.set_state(UserStates.waiting_question)
    await state.update_data(category=cat)
    title = FAQ.get(cat, {}).get("title", "Sual")
    await c.message.edit_text(
        f"Mövzu: {title}\n\nSualını bir mesajla, qısa və konkret yaz.\nLəğv üçün /start"
    )

@dp.message(StateFilter(UserStates.waiting_suggest))
async def get_suggest(m: Message, state: FSMContext):
    save_question(m.from_user.id, m.from_user.username, "Təklif", m.text)
    await state.clear()
    await m.answer("Təşəkkür! Mesajın kuratora göndərildi. ✅", reply_markup=main_kb())
    if ADMIN_ID != 0:
        try:
            await bot.send_message(ADMIN_ID, f"📩 YENİ TƏKLİF\nKimdən: @{m.from_user.username} ({m.from_user.id})\n\n{m.text}\n\nCavab: /reply {m.from_user.id} MƏTN")
        except:
            pass

@dp.message(StateFilter(UserStates.waiting_question))
async def get_question(m: Message, state: FSMContext):
    data = await state.get_data()
    cat = data.get("category", "Sual")
    cat_title = FAQ.get(cat, {}).get("title", cat)
    save_question(m.from_user.id, m.from_user.username, cat_title, m.text)
    await state.clear()
    await m.answer("Qəbul olundu! Sualın kuratora göndərildi. Cavab bu botda gələcək. ✅", reply_markup=main_kb())
    if ADMIN_ID != 0:
        try:
            await bot.send_message(ADMIN_ID, f"❓ YENİ SUAL [{cat_title}]\nKimdən: @{m.from_user.username} ({m.from_user.id})\n\n{m.text}\n\nCavab: /reply {m.from_user.id} MƏTN")
        except:
            pass

@dp.callback_query(F.data == "contacts")
async def contacts(c: CallbackQuery):
    await c.message.edit_text(
        "📞 Hakimlərə dəstək — Əlaqə:\n\n"
        "Kurator: @sizin_nick\n"
        "Texniki dəstək: bu botda 'Təklif bildir' ilə yaz\n\n"
        "Oyun zamanı təcili hal — birbaşa kuratora zəng et.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Geri", callback_data="back_main")]])
    )

@dp.message(Command("reply"))
async def admin_reply(m: Message):
    if m.from_user.id != ADMIN_ID:
        return
    try:
        parts = m.text.split(maxsplit=2)
        user_id = int(parts[1])
        answer = parts[2]
        await bot.send_message(user_id, f"💬 Kuratordan cavab:\n\n{answer}")
        await m.answer("Göndərildi ✅")
    except Exception as e:
        await m.answer(f"Format: /reply USER_ID mətn\nNümunə: /reply 123456 Sualınız həll olundu\nXəta: {e}")

@dp.message(Command("stats"))
async def stats(m: Message):
    if m.from_user.id != ADMIN_ID:
        return
    conn = sqlite3.connect("referee_bot.db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM questions")
    total = cur.fetchone()[0]
    conn.close()
    await m.answer(f"Ümumi müraciətlər: {total}")

@dp.message()
async def fallback(m: Message):
    await m.answer("Menyudan istifadə et:", reply_markup=main_kb())

async def main():
    init_db()
    print("Bot işə düşdü... Telegram-da /start yaz ✅")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
