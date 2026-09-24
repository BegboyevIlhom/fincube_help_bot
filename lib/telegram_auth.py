# Bu fayl Telegram Mini App'dan (ilova ichidan) kelgan so'rovlarning "haqiqiy"ligini tekshiradi
# Telegram har bir Mini App foydalanuvchisiga "initData" degan imzolangan ma'lumot beradi —
# biz shu imzoni bot tokenimiz yordamida tekshirib, soxta so'rovlarni rad etamiz

import hashlib  # imzo hisoblash uchun kerak bo'ladigan kriptografik funksiyalar
import hmac  # xavfsiz imzo taqqoslash uchun kerak bo'ladigan funksiya
import json  # foydalanuvchi ma'lumotini o'qish uchun
import urllib.parse  # "initData" satrini bo'laklarga ajratish uchun
from lib.config import TELEGRAM_TOKEN  # imzoni tekshirish uchun bot tokeni kerak


def tekshir_init_data(init_data):
    # init_data — Mini App tomonidan yuborilgan, Telegram imzolagan matn
    # agar imzo to'g'ri bo'lsa — foydalanuvchi ma'lumotini (id, ism va h.k.) qaytaradi
    # agar imzo noto'g'ri yoki soxta bo'lsa — None qaytaradi (ishonch yo'q)

    if not init_data:  # agar umuman hech narsa yuborilmagan bo'lsa
        return None

    try:
        # initData'ni kalit=qiymat juftliklariga ajratamiz (masalan "user=...&auth_date=...&hash=...")
        juftliklar = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))

        kelgan_hash = juftliklar.pop("hash", None)  # Telegram yuborgan imzoni ajratib olamiz
        if not kelgan_hash:  # agar imzo umuman bo'lmasa
            return None

        # qolgan barcha juftliklarni alifbo tartibida qatorga yig'amiz (Telegram talabiga ko'ra)
        qatorlar = [f"{kalit}={qiymat}" for kalit, qiymat in sorted(juftliklar.items())]
        tekshiruv_matni = "\n".join(qatorlar)

        # Telegram'ning rasmiy formulasi bo'yicha maxfiy kalitni hisoblaymiz
        maxfiy_kalit = hmac.new(b"WebAppData", TELEGRAM_TOKEN.encode(), hashlib.sha256).digest()
        # shu maxfiy kalit bilan tekshiruv matnining imzosini hisoblaymiz
        hisoblangan_hash = hmac.new(maxfiy_kalit, tekshiruv_matni.encode(), hashlib.sha256).hexdigest()

        if hisoblangan_hash != kelgan_hash:  # agar bizning hisoblagan imzo Telegramnikiga mos kelmasa
            return None  # demak bu soxta yoki buzilgan so'rov — rad etamiz

        foydalanuvchi_matni = juftliklar.get("user")  # foydalanuvchi ma'lumoti shu yerda (JSON ko'rinishida)
        if not foydalanuvchi_matni:
            return None

        return json.loads(foydalanuvchi_matni)  # {"id": 123456, "first_name": "...", ...} qaytaramiz

    except Exception:
        # kutilmagan xatolik chiqsa (masalan noto'g'ri format), xavfsizlik uchun "ishonch yo'q" deb hisoblaymiz
        return None
