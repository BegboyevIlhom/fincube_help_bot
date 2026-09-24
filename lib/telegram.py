# Bu fayl Telegram Bot API bilan gaplashish uchun barcha funksiyalarni saqlaydi
# (xabar yuborish, xabarni tahrirlash, tugma bosilganiga javob berish)

import requests  # HTTP so'rov yuborish uchun kutubxona
from lib.config import TELEGRAM_API  # tayyorlab qo'yilgan Telegram API manzili


def xabar_yubor(chat_id, matn, reply_to=None, tugmalar=None):
    # chat_id — kimga yuborilishi (guruh yoki shaxsiy chat)
    # matn — yuboriladigan xabar matni
    # reply_to — agar biror xabarga javob tariqasida yuborilsa, o'sha xabar IDsi
    # tugmalar — inline tugmalar ro'yxati (masalan [[{"text":"Qabul qildim","callback_data":"qabul:5"}]])
    url = f"{TELEGRAM_API}/sendMessage"  # Telegramning xabar yuborish manzili
    data = {"chat_id": chat_id, "text": matn, "parse_mode": "HTML"}  # asosiy parametrlar
    if reply_to:  # agar reply_to berilgan bo'lsa
        data["reply_to_message_id"] = reply_to  # javob berilayotgan xabarni belgilaymiz
    if tugmalar:  # agar tugmalar berilgan bo'lsa
        data["reply_markup"] = {"inline_keyboard": tugmalar}  # tugmalarni xabarga biriktiramiz
    javob = requests.post(url, json=data, timeout=10)  # Telegramga so'rov yuboramiz
    return javob.json()  # Telegramdan kelgan javobni qaytaramiz (message_id shu yerda bo'ladi)


def xabar_tahrirla(chat_id, message_id, matn, tugmalar=None):
    # allaqachon yuborilgan xabarning matnini/tugmalarini o'zgartirish uchun
    url = f"{TELEGRAM_API}/editMessageText"  # Telegramning xabar tahrirlash manzili
    data = {"chat_id": chat_id, "message_id": message_id, "text": matn, "parse_mode": "HTML"}
    if tugmalar is not None:  # agar yangi tugmalar berilgan bo'lsa
        data["reply_markup"] = {"inline_keyboard": tugmalar}  # yangi tugmalarni qo'yamiz
    javob = requests.post(url, json=data, timeout=10)  # so'rovni yuboramiz
    return javob.json()  # natijani qaytaramiz


def callback_javob(callback_query_id, matn="", ogohlantirish=False):
    # xodim tugmani bosganda Telegram "yuklanmoqda" belgisini olib tashlash uchun shu chaqiriladi
    url = f"{TELEGRAM_API}/answerCallbackQuery"  # Telegramning callback javob manzili
    data = {"callback_query_id": callback_query_id, "text": matn, "show_alert": ogohlantirish}
    javob = requests.post(url, json=data, timeout=10)  # so'rovni yuboramiz
    return javob.json()  # natijani qaytaramiz


def baholash_klaviaturasi(baholash_id):
    # mijoz uchun 1 dan 5 gacha yulduzcha tugmalari (har biri alohida qatorda, tushunarli bo'lishi uchun)
    tugmalar = []
    for son in range(1, 6):  # 1, 2, 3, 4, 5
        tugmalar.append([{"text": "⭐" * son, "callback_data": f"baho:{baholash_id}:{son}"}])
    return tugmalar


def chat_menu_ornat(chat_id, mini_app_url=None):
    # bitta shaxsiy chat uchun pastdagi "Menu Button"ni sozlaydi
    # mini_app_url berilsa — o'sha manzilga ochiladigan "Ish paneli" tugmasi ko'rinadi (xodimlar uchun)
    # mini_app_url berilmasa (None) — oddiy "buyruqlar" (commands) tugmasi ko'rsatiladi (mijozlar uchun)
    #
    # DIQQAT: "default" turi ISHLATILMAYDI — chunki u botning GLOBAL sozlamasiga (agar sozlangan bo'lsa)
    # qaytib ketadi, ya'ni mijozga ham eski "Ish paneli" tugmasi ko'rinib qolishi mumkin.
    # "commands" turi esa har doim aniq va ishonchli — hech qachon web-app tugmasiga aylanib qolmaydi
    url = f"{TELEGRAM_API}/setChatMenuButton"
    if mini_app_url:
        menu = {"type": "web_app", "text": "Ish paneli", "web_app": {"url": mini_app_url}}
    else:
        menu = {"type": "commands"}  # oddiy "/" buyruqlar tugmasi — web-app EMAS
    javob = requests.post(url, json={"chat_id": chat_id, "menu_button": menu}, timeout=10)
    return javob.json()


def xodim_belgisi(xodim):
    # xodimning ismini bosilganda uning Telegram profiliga o'tadigan "belgi" (mention) shaklida qaytaradi
    # bu usul @username talab qilmaydi — faqat telegram_id yetarli
    return f'<a href="tg://user?id={xodim["telegram_id"]}">{xodim["ism_familiya"]}</a>'


def xodimlarni_belgila(xodimlar):
    # bir nechta xodimni vergul bilan ajratib, bitta qatorda belgilab beradi
    return ", ".join(xodim_belgisi(x) for x in xodimlar)
