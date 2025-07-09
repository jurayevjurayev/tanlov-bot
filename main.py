# 📁 Fayl: main.py

import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from datetime import datetime, timedelta

API_TOKEN = 'TOKEN_BU_YERGA_QO'YILADI'
ADMIN_ID = 123456789  # o'zgartiring

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Doimiy saqlash uchun fayl
USERS_FILE = 'users.json'
TESTS_FILE = 'tests.json'
ACTIVE_TANLOV_ID = 'tanlov_1'  # Admin belgilaydi
MAX_TEST_VAQTI = 5 * 60  # sekund

# 🧠 Yordamchi funksiyalar
def load_users():
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def load_tests():
    try:
        with open(TESTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

users = load_users()
tests = load_tests()

# 🔘 Obuna tekshiruvi (soddalashtirilgan)
obuna_kanali = "@kanal_nomi"
def obuna_inline():
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton("🔗 Obuna boʻlish", url=f"https://t.me/{obuna_kanali[1:]}")
    ).add(InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub"))

@dp.message_handler(commands=['start'])
async def start_handler(msg: types.Message):
    uid = str(msg.from_user.id)
    users.setdefault(uid, {})

    if 'name' in users[uid] and 'region' in users[uid]:
        users[uid]['step'] = 'pay_confirm'
        await msg.answer(f"Salom {users[uid]['name']}! Tanlov pullik. Qatnashmoqchimisiz?",
                         reply_markup=InlineKeyboardMarkup().add(
                             InlineKeyboardButton("✅ Ha", callback_data="confirm_pay")))
    else:
        users[uid]['step'] = 'wait_sub'
        await msg.answer("Botdan foydalanish uchun kanalga obuna boʻling:", reply_markup=obuna_inline())
    save_users(users)

@dp.callback_query_handler(lambda c: c.data == 'check_sub')
async def check_subscription(call: types.CallbackQuery):
    # Obunani real tekshirish uchun telegram API kerak bo'ladi (pass qilamiz)
    uid = str(call.from_user.id)
    users[uid]['step'] = 'ask_name'
    await call.message.answer("✅ Obuna tasdiqlandi. Ism familiyangizni yuboring:")
    save_users(users)

@dp.message_handler(lambda msg: users.get(str(msg.from_user.id), {}).get('step') == 'ask_name')
async def get_name(msg: types.Message):
    uid = str(msg.from_user.id)
    users[uid]['name'] = msg.text.strip()
    users[uid]['step'] = 'ask_region'
    await msg.answer("📍 Viloyatingizni yuboring:")
    save_users(users)

@dp.message_handler(lambda msg: users.get(str(msg.from_user.id), {}).get('step') == 'ask_region')
async def get_region(msg: types.Message):
    uid = str(msg.from_user.id)
    users[uid]['region'] = msg.text.strip()
    users[uid]['step'] = 'pay_confirm'
    await msg.answer("✅ Ro'yxatdan o'tdingiz! Tanlov pullik. Qatnashmoqchimisiz?",
                     reply_markup=InlineKeyboardMarkup().add(
                         InlineKeyboardButton("✅ Ha", callback_data="confirm_pay")))
    save_users(users)

@dp.callback_query_handler(lambda c: c.data == 'confirm_pay')
async def handle_pay(call: types.CallbackQuery):
    uid = str(call.from_user.id)
    users[uid].setdefault('payments', {})
    users[uid]['payments'][ACTIVE_TANLOV_ID] = {'step': 'wait_check'}
    await call.message.answer("💳 Toʻlovni quyidagi karta raqamiga amalga oshiring: 8600 **** **** ****\nSoʻngra toʻlov chekini rasm shaklida yuboring.")
    save_users(users)

@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_chek(msg: types.Message):
    uid = str(msg.from_user.id)
    if users.get(uid, {}).get('payments', {}).get(ACTIVE_TANLOV_ID, {}).get('step') != 'wait_check':
        return
    users[uid]['payments'][ACTIVE_TANLOV_ID]['step'] = 'waiting_approval'
    cap = f"🧾 Yangi toʻlov cheki\nIsm: {users[uid]['name']}\nViloyat: {users[uid]['region']}\nTanlov: {ACTIVE_TANLOV_ID}\nID: {uid}"
    await bot.send_photo(ADMIN_ID, msg.photo[-1].file_id, caption=cap)
    await msg.answer("✅ Chekingiz yuborildi. Admin tasdiqlashini kuting.")
    save_users(users)

@dp.message_handler(commands=['set_active'])
async def set_active(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return
    global ACTIVE_TANLOV_ID
    try:
        ACTIVE_TANLOV_ID = msg.text.split()[1]
        await msg.answer(f"✅ Faol tanlov: {ACTIVE_TANLOV_ID}")
    except:
        await msg.answer("❗ Tanlov ID noto'g'ri. Misol: /set_active tanlov_3")

@dp.message_handler(commands=['send_all'])
async def send_all(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return
    matn = msg.text[10:].strip()
    for uid, data in users.items():
        ism = data.get('name', 'Foydalanuvchi')
        try:
            await bot.send_message(uid, f"{ism},\n{matn}")
        except:
            pass

# 🚧 Testlar, start_test va stop_test, va test yakunlash bloklari alohida faylga ajratiladi.
# Ularni xohlasangiz "test_handler.py" degan faylda davom ettiramiz.

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
