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
#
# IKKI QATLAMLI HIMOYA takroriy Deal yaratilib ketmasligi uchun:
#   1) mijoz['bitrix_deal_id'] — bazada saqlangan, eng tezkor yo'l
#   2) agar (1) bazaga biror sabab bilan yozilmagan bo'lsa (masalan ustun hali qo'shilmagan,
#      yoki vaqtinchalik xatolik bo'lgan), Bitrix'ning O'ZIDAN shu Kontaktga tegishli
#      eski Deal bormi qidiriladi — shu orqali baza "unutib qo'ysa" ham, Bitrix'da
#      bitta mijoz uchun bir nechta Deal ko'payib ketmaydi

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


def _deal_top(contact_id):
    # XAVFSIZLIK TO'RI: bazada bitrix_deal_id saqlanmagan/yo'qolgan bo'lsa ham, shu Kontaktga
    # tegishli ESKI Deal Bitrix'ning o'zida bormi tekshiradi — shunday qilib, baza yozuvi
    # muvaffaqiyatsiz bo'lsa ham, bitta mijoz uchun bir nechta Deal yaratilib ketmaydi
    if not contact_id:
        return None
    topilganlar = _sorov("crm.deal.list", {
        "filter": {"CONTACT_ID": contact_id, "CATEGORY_ID": BITRIX_CATEGORY_ID},
        "select": ["ID"],
        "order": {"ID": "DESC"}
    })
    return topilganlar[0]["ID"] if topilganlar else None


def _deal_yarat(contact_id, ism, telefon, inn, bosqich_kodi, izoh):
    # Yangi Deal (murojaat) yaratadi. Muvaffaqiyatli bo'lsa deal_id qaytaradi, aks holda None
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

    return _sorov("crm.deal.add", {"fields": maydonlar})


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


def _mijozga_saqla(mijoz, contact_id, deal_id):
    # bitrix ID'larini bazaga yozadi. Bu yozuv MUVAFFAQIYATSIZ bo'lsa ham (masalan ustun hali
    # qo'shilmagan bo'lsa), Deal o'zi allaqachon yaratilgan/yangilangan bo'ladi — shuning uchun
    # bu yerdagi xatolik alohida ushlanadi va faqat ogohlantirish sifatida logga yoziladi
    try:
        db.mijoz_bitrix_malumotini_yangila(mijoz["id"], bitrix_contact_id=contact_id, bitrix_deal_id=deal_id)
        mijoz["bitrix_deal_id"] = deal_id
        mijoz["bitrix_contact_id"] = contact_id
    except Exception as xato:
        print(
            f"OGOHLANTIRISH: Bitrix ID'lari bazaga yozilmadi (mijoz_id={mijoz.get('id')}): {xato}. "
            f"Supabase'da 'mijozlar' jadvalida 'bitrix_contact_id' va 'bitrix_deal_id' "
            f"ustunlari borligini tekshiring."
        )


def zayavkani_sinxronla(mijoz, zayavka, holat_nomi, mas_ul_bitrix_user_id=None, izoh=None):
    # ASOSIY funksiya — webhook_handler.py va timer_handler.py shu yerdan foydalanadi.
    # mijoz uchun Bitrix Deal'ni yaratadi (agar hali yo'q bo'lsa) yoki mavjudini
    # yangilaydi (bosqich + ixtiyoriy izoh). HAR DOIM xavfsiz ishlaydi.
    bosqich_kodi = BITRIX_BOSQICHLAR.get(holat_nomi)
    if not bosqich_kodi:  # Bitrix hali sozlanmagan yoki bu holat uchun bosqich belgilanmagan
        return

    try:
        deal_id = mijoz.get("bitrix_deal_id")
        contact_id = mijoz.get("bitrix_contact_id")

        if not deal_id:
            # bazada saqlangan Deal yo'q — avval Kontaktni topamiz/yaratamiz
            if not contact_id:
                contact_id = _kontakt_top_yoki_yarat(mijoz.get("ism"), mijoz.get("telefon"))
            # SO'NG, yangi Deal yaratishdan OLDIN, shu Kontaktga tegishli ESKI Deal
            # Bitrix'ning o'zida bormi tekshiramiz (baza "unutgan" bo'lsa ham himoya)
            deal_id = _deal_top(contact_id)

        if deal_id:  # mavjud Deal topildi (bazadan yoki Bitrix'dan) — shuni yangilaymiz
            _deal_bosqichini_yangila(deal_id, bosqich_kodi, mas_ul_bitrix_user_id)
            if izoh:
                _deal_ga_izoh_qosh(deal_id, izoh)
        else:  # chindan ham birinchi marta — yangi Deal yaratamiz
            inn = zayavka.get("inn") or mijoz.get("inn")
            telefon = mijoz.get("telefon")
            ism = mijoz.get("ism")
            deal_id = _deal_yarat(contact_id, ism, telefon, inn, bosqich_kodi, izoh or zayavka.get("matn") or "")
            if deal_id and mas_ul_bitrix_user_id:  # kamdan-kam holat (yaratish paytidayoq mas'ul ma'lum bo'lsa)
                _deal_bosqichini_yangila(deal_id, bosqich_kodi, mas_ul_bitrix_user_id)

        if deal_id:  # topilgan/yaratilgan deal_id'ni har doim bazaga qayta saqlashga urinamiz
            _mijozga_saqla(mijoz, contact_id, deal_id)
    except Exception as xato:
        # BITRIX BILAN BOG'LIQ HECH QANDAY XATOLIK BOTNI TO'XTATMASLIGI SHART
        print(f"BITRIX SINXRONLASH XATOSI (mijoz_id={mijoz.get('id')}, holat={holat_nomi}): {xato}")
