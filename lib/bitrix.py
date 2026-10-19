# Bu fayl Bitrix24 CRM bilan gaplashish uchun barcha funksiyalarni saqlaydi.
#
# MUHIM QOIDA: bu yerdagi HAR BIR chaqiruv "xavfsiz" — agar Bitrix sekinlashsa, vaqtincha
# ishlamay qolsa (masalan sinov muddati tugasa) yoki tarmoq xatosi bersa, xatolik FAQAT shu
# yerda ushlanadi va faqat logga yoziladi. Bot va Telegram/Supabase mantig'i hech qachon
# Bitrix sababli to'xtab qolmaydi.
#
# Dizayn: har bir MIJOZ uchun Bitrix'da BITTA Deal (murojaat) ishlatiladi — mijoz birinchi
# marta to'liq ma'lumot (INN+telefon) bilan murojaat qilganda yangi Deal yaratiladi, keyingi
# barcha murojaatlari (va holat o'zgarishlari) O'SHA Deal'ning bosqichi va tarixiga (timeline)
# yoziladi, har safar yangi Deal yaratilmaydi.

import requests  # Bitrix REST API'ga HTTP so'rov yuborish uchun
from lib import db  # mijozga Bitrix ID'larini saqlash uchun
from lib.config import BITRIX_WEBHOOK_URL, BITRIX_CATEGORY_ID, BITRIX_FIELD_INN, BITRIX_BOSQICHLAR

_TIMEOUT = 6  # soniya — Bitrix sekinlashib ketsa ham, bot uzoq kutib qolmasligi uchun chegara


def _sorov(metod, parametrlar=None):
    # Bitrix REST API metodini chaqiradi. MUVAFFAQIYATSIZ bo'lsa (tarmoq xatosi, Bitrix xatosi,
    # yoki hali sozlanmagan bo'lsa) — None qaytaradi, HECH QACHON xatolik tashlamaydi
    if not BITRIX_WEBHOOK_URL:  # Bitrix hali ulanmagan/sozlanmagan bo'lsa, jim o'tkazib yuboramiz
        return None
    try:
        javob = requests.post(
            f"{BITRIX_WEBHOOK_URL}/{metod}.json",
            json=parametrlar or {},
            timeout=_TIMEOUT
        )
        natija = javob.json()
        if "error" in natija:  # Bitrix o'zi xatolik qaytarsa (masalan huquq yetmasa)
            print(f"BITRIX XATOSI ({metod}): {natija.get('error')} — {natija.get('error_description')}")
            return None
        return natija.get("result")
    except Exception as xato:  # tarmoq uzilishi, vaqt tugashi va h.k.
        print(f"BITRIX SO'ROV XATOSI ({metod}): {xato}")
        return None


def _kontakt_top_yoki_yarat(ism, telefon):
    # telefon raqami bo'yicha mavjud Kontaktni qidiradi, topilmasa yangisini yaratadi.
    # Muvaffaqiyatsiz bo'lsa None qaytaradi (Deal baribir Kontaktsiz ham yaratilaveradi)
    if not telefon:
        return None
    topilganlar = _sorov("crm.contact.list", {
        "filter": {"PHONE": telefon},
        "select": ["ID"]
    })
    if topilganlar:  # agar shu telefon bilan kontakt allaqachon bo'lsa
        return topilganlar[0]["ID"]
    return _sorov("crm.contact.add", {
        "fields": {
            "NAME": ism or "Mijoz",
            "PHONE": [{"VALUE": telefon, "VALUE_TYPE": "WORK"}]
        }
    })


def _deal_yarat(ism, telefon, inn, bosqich_kodi, izoh):
    # Yangi Deal (murojaat) yaratadi. Muvaffaqiyatli bo'lsa (deal_id, contact_id) qaytaradi,
    # muvaffaqiyatsiz bo'lsa (None, None)
    contact_id = _kontakt_top_yoki_yarat(ism, telefon)

    maydonlar = {
        "TITLE": f"Support: {ism or 'Mijoz'} ({telefon or '—'})",
        "CATEGORY_ID": BITRIX_CATEGORY_ID,
        "STAGE_ID": bosqich_kodi,
        "COMMENTS": izoh or "",
    }
    if contact_id:
        maydonlar["CONTACT_ID"] = contact_id
    if inn and BITRIX_FIELD_INN:
        maydonlar[BITRIX_FIELD_INN] = inn

    deal_id = _sorov("crm.deal.add", {"fields": maydonlar})
    return deal_id, contact_id


def _deal_bosqichini_yangila(deal_id, bosqich_kodi, mas_ul_bitrix_user_id=None):
    # mavjud Deal'ning bosqichini (va ixtiyoriy ravishda mas'ul xodimni) yangilaydi
    maydonlar = {"STAGE_ID": bosqich_kodi}
    if mas_ul_bitrix_user_id:
        maydonlar["ASSIGNED_BY_ID"] = mas_ul_bitrix_user_id
    _sorov("crm.deal.update", {"id": deal_id, "fields": maydonlar})


def _deal_ga_izoh_qosh(deal_id, matn):
    # Deal tarixiga (timeline) yangi izoh (comment) qo'shadi
    if not matn:
        return
    _sorov("crm.timeline.comment.add", {
        "fields": {
            "ENTITY_ID": deal_id,
            "ENTITY_TYPE": "deal",
            "COMMENT": matn
        }
    })


def zayavkani_sinxronla(mijoz, zayavka, holat_nomi, mas_ul_bitrix_user_id=None, izoh=None):
    # ASOSIY funksiya — webhook_handler.py va timer_handler.py shu yerdan foydalanadi.
    # mijoz uchun Bitrix Deal'ni yaratadi (agar hali yo'q bo'lsa) yoki mavjudini
    # yangilaydi (bosqich + ixtiyoriy izoh). HAR DOIM xavfsiz ishlaydi.
    bosqich_kodi = BITRIX_BOSQICHLAR.get(holat_nomi)
    if not bosqich_kodi:  # Bitrix hali sozlanmagan yoki bu holat uchun bosqich belgilanmagan
        return

    try:
        mavjud_deal_id = mijoz.get("bitrix_deal_id")

        if mavjud_deal_id:  # mijozning Bitrix'da allaqachon Deal'i bor — o'shani yangilaymiz
            _deal_bosqichini_yangila(mavjud_deal_id, bosqich_kodi, mas_ul_bitrix_user_id)
            if izoh:
                _deal_ga_izoh_qosh(mavjud_deal_id, izoh)
            return

        # mijozning hali Deal'i yo'q — yangisini yaratamiz
        inn = zayavka.get("inn") or mijoz.get("inn")
        telefon = mijoz.get("telefon")
        ism = mijoz.get("ism")
        deal_id, contact_id = _deal_yarat(ism, telefon, inn, bosqich_kodi, izoh or zayavka.get("matn") or "")

        if deal_id:  # muvaffaqiyatli yaratilsa, mijozga saqlab qo'yamiz (keyingi safar shuni ishlatish uchun)
            db.mijoz_bitrix_malumotini_yangila(mijoz["id"], bitrix_contact_id=contact_id, bitrix_deal_id=deal_id)
            mijoz["bitrix_deal_id"] = deal_id  # mahalliy nusxani ham yangilaymiz
            if mas_ul_bitrix_user_id:  # agar yaratish paytidayoq mas'ul xodim ma'lum bo'lsa (kamdan-kam holat)
                _deal_bosqichini_yangila(deal_id, bosqich_kodi, mas_ul_bitrix_user_id)
    except Exception as xato:
        # BITRIX BILAN BOG'LIQ HECH QANDAY XATOLIK BOTNI TO'XTATMASLIGI SHART
        print(f"BITRIX SINXRONLASH XATOSI (mijoz_id={mijoz.get('id')}, holat={holat_nomi}): {xato}")
