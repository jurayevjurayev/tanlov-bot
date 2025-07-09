# 📁 Fayl: test_handler.py

import json
import asyncio
from aiogram import Bot, Dispatcher, types
from datetime import datetime, timedelta

USERS_FILE = 'users.json'
TESTS_FILE = 'tests.json'

# Bu fayl main.py dan import qilinadi:
# bot, dp, ADMIN_ID, ACTIVE_TANLOV_ID, MAX_TEST_VAQTI, users, tests

# ✅ Har bir foydalanuvchining test natijasi vaqtinchalik saqlanadi:
test_sessions = {}

# 🔄 Savollarni yuborish
def get_question(tanlov_id, index):
    try:
        savol = tests[tanlov_id][index]
        variantlar = savol['variantlar']
        text = f"{index+1}. {savol['savol']}\n"
        for i, v in enumerate(variantlar):
            text += f"{chr(65+i)}. {v}\n"
        return text, variantlar
    except:
        return None, None

@dp.message_handler(commands=['start_test'])
async def start_test(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return
    for uid, data in users.items():
        if data.get('payments', {}).get(ACTIVE_TANLOV_ID, {}).get('step') == 'waiting_approval':
            data['payments'][ACTIVE_TANLOV_ID]['step'] = 'test_started'
            data['payments'][ACTIVE_TANLOV_ID]['start_time'] = datetime.now().isoformat()
            data['payments'][ACTIVE_TANLOV_ID]['answers'] = []
            await bot.send_message(uid, "🧪 Test boshlandi! Har bir savolga 20 soniyada javob bering.")
            await send_question(uid, 0)
    save_users(users)

@dp.message_handler(commands=['stop_test'])
async def stop_test(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return
    for uid, data in users.items():
        if ACTIVE_TANLOV_ID in data.get('payments', {}):
            data['payments'][ACTIVE_TANLOV_ID]['step'] = 'test_closed'
    save_users(users)
    await msg.answer("⛔ Test yopildi. Endi hech kim testga kira olmaydi.")

async def send_question(uid, index):
    user = users[uid]
    payment = user['payments'][ACTIVE_TANLOV_ID]

    if index >= len(tests[ACTIVE_TANLOV_ID]):
        await finish_test(uid)
        return

    question_text, variantlar = get_question(ACTIVE_TANLOV_ID, index)
    if not question_text:
        await bot.send_message(uid, "❗ Savollar yuklanishda xatolik.")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for v in variantlar:
        markup.add(v)
    payment['current_index'] = index
    save_users(users)

    await bot.send_message(uid, question_text, reply_markup=markup)

    # Taymer 20 soniya
    await asyncio.sleep(20)
    if len(payment['answers']) <= index:
        payment['answers'].append('-')
        await send_question(uid, index+1)

@dp.message_handler()
async def test_answer(msg: types.Message):
    uid = str(msg.from_user.id)
    user = users.get(uid)
    if not user:
        return

    payment = user.get('payments', {}).get(ACTIVE_TANLOV_ID)
    if not payment or payment.get('step') != 'test_started':
        return

    start_time = datetime.fromisoformat(payment['start_time'])
    if datetime.now() > start_time + timedelta(seconds=MAX_TEST_VAQTI):
        await bot.send_message(uid, "⏰ Test vaqtingiz tugadi.")
        payment['step'] = 'done'
        save_users(users)
        return

    index = payment.get('current_index', 0)
    javob = msg.text.strip()
    if len(payment['answers']) <= index:
        payment['answers'].append(javob)
    await send_question(uid, index+1)

async def finish_test(uid):
    user = users[uid]
    payment = user['payments'][ACTIVE_TANLOV_ID]
    payment['step'] = 'done'
    togrilar = 0

    for i, savol in enumerate(tests[ACTIVE_TANLOV_ID]):
        javob = payment['answers'][i] if i < len(payment['answers']) else '-'
        if javob == savol['javob']:
            togrilar += 1

    natija = f"{user['name']} — {togrilar}/{len(tests[ACTIVE_TANLOV_ID])}"
    await bot.send_message(uid, "✅ Test tugadi. 📊 Mandat natijalari tez orada e’lon qilinadi.")
    await bot.send_message(ADMIN_ID, natija)
    save_users(users)

# ✅ Yuklab olish va saqlash funksiyasi

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

with open(USERS_FILE, 'r', encoding='utf-8') as f:
    users = json.load(f)

with open(TESTS_FILE, 'r', encoding='utf-8') as f:
    tests = json.load(f)
