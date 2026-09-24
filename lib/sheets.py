# Bu fayl Google Sheets'dagi mijozlar bazasi (Ligotniy va Platniy shartnomalar) bilan gaplashadi
# Google'ning og'ir kutubxonasini (google-api-python-client) o'rnatmasdan, faqat yengil
# "google-auth" bilan token olib, oddiy HTTP so'rov (requests) orqali ma'lumot o'qiymiz

import json  # xizmat hisobi kalitini (JSON) o'qish uchun
from datetime import datetime, date  # sana bilan solishtirish uchun
import requests  # Google API'ga HTTP so'rov yuborish uchun
from google.oauth2 import service_account  # xizmat hisobi (Service Account) orqali kirish uchun
from google.auth.transport.requests import Request as GoogleRequest  # tokenni yangilash uchun kerak
from lib.config import GOOGLE_SERVICE_ACCOUNT_JSON, MIJOZLAR_SHEET_ID, LIGOTNIY_VARAQ, PLATNIY_VARAQ

# Google Sheets'ni FAQAT o'qish uchun ruxsat (yozish huquqi berilmaydi — xavfsizlik uchun)
_RUXSAT_QAMROVI = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def _token_ol():
    # xizmat hisobi kalitidan foydalanib, Google'dan vaqtinchalik kirish tokenini olamiz
    malumot = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)  # JSON matnini Python lug'atiga aylantiramiz
    kredensial = service_account.Credentials.from_service_account_info(malumot, scopes=_RUXSAT_QAMROVI)
    kredensial.refresh(GoogleRequest())  # Google'ga so'rov yuborib, haqiqiy tokenni olamiz
    return kredensial.token


def _varaqni_oqi(varaq_nomi):
    # bitta varaqning (masalan "Ligotniy") barcha ma'lumotini qator-qator qilib qaytaradi
    token = _token_ol()
    manzil = f"https://sheets.googleapis.com/v4/spreadsheets/{MIJOZLAR_SHEET_ID}/values/{varaq_nomi}"
    javob = requests.get(manzil, headers={"Authorization": f"Bearer {token}"}, timeout=15)
    javob.raise_for_status()  # agar xatolik bo'lsa (masalan ruxsat yo'q), shu yerda to'xtaydi
    return javob.json().get("values", [])  # qatorlar ro'yxati (har biri — ustunlar ro'yxati)


def _sanani_ayir(matn):
    # jadvaldan kelgan "20.12.2026" ko'rinishidagi sanani Python sana obyektiga aylantiradi
    if not matn:
        return None
    try:
        return datetime.strptime(matn.strip(), "%d.%m.%Y").date()
    except ValueError:
        return None  # kutilmagan formatda bo'lsa, sanasiz deb hisoblaymiz


def _sarlavha_qatorini_top(qatorlar):
    # ba'zi jadvallarda birinchi qatorda "Таблица1" kabi filter/jadval nomi bo'lishi mumkin,
    # haqiqiy ustun nomlari esa 2-qatorda turishi mumkin. Shuning uchun sarlavhani "qidirib" topamiz —
    # ichida "ИНН" so'zi bo'lgan BIRINCHI qatorni haqiqiy sarlavha deb hisoblaymiz
    for indeks, qator in enumerate(qatorlar[:5]):  # faqat birinchi 5 qatorni tekshirish yetarli
        if "ИНН" in qator:
            return indeks, qator
    return None, None  # 5 qator ichida "ИНН" topilmasa, bu varaqni o'qib bo'lmaydi


def _varaqdan_qidir(varaq_nomi, inn):
    # bitta varaq ichidan berilgan INN'ga mos qatorni qidiradi
    # topsa {"sana": ..., "kompaniya": ...} qaytaradi, topmasa None
    qatorlar = _varaqni_oqi(varaq_nomi)
    if not qatorlar:  # agar varaq bo'sh bo'lsa
        return None

    sarlavha_indeksi, sarlavha = _sarlavha_qatorini_top(qatorlar)  # sarlavha qaysi qatorda ekanini topamiz
    if sarlavha is None:  # agar "ИНН" so'zi umuman topilmasa
        return None  # bu varaqni o'qib bo'lmaydi

    try:
        inn_ustun = sarlavha.index("ИНН")  # "ИНН" ustuni qaysi tartib raqamida ekanini topamiz
        sana_ustun = sarlavha.index("Дата окончания")  # "tugash sanasi" ustuni ham shunday
    except ValueError:
        return None  # kerakli ustunlar topilmasa, hech narsa qila olmaymiz

    # "kompaniya nomi" ustuni ixtiyoriy — bo'lmasa ham xato bermaymiz, shunchaki nomsiz qoldiramiz
    try:
        kompaniya_ustun = sarlavha.index("Наименование организации")
    except ValueError:
        kompaniya_ustun = None

    # ma'lumotlar sarlavha qatoridan KEYINGI qatorlardan boshlanadi (1-qator emas, sarlavha qayerda bo'lsa o'shandan keyin)
    for qator in qatorlar[sarlavha_indeksi + 1:]:
        if len(qator) <= max(inn_ustun, sana_ustun):  # agar qator yetarlicha uzun bo'lmasa
            continue  # o'tkazib yuboramiz
        if qator[inn_ustun].strip() == inn:  # agar INN mos kelsa
            kompaniya = None
            if kompaniya_ustun is not None and len(qator) > kompaniya_ustun:
                kompaniya = qator[kompaniya_ustun].strip() or None
            return {"sana": _sanani_ayir(qator[sana_ustun]), "kompaniya": kompaniya}

    return None  # bu varaqda topilmadi


def mijoz_holati(inn):
    # asosiy funksiya: berilgan INN ikkala varaqda (Ligotniy va Platniy) qidiriladi
    # natija: {"holat": "faol"/"muddati_otgan"/"topilmadi", "kompaniya_nomi": "..." yoki None}
    if not GOOGLE_SERVICE_ACCOUNT_JSON or not MIJOZLAR_SHEET_ID:
        # agar hali Google Sheets ulanmagan bo'lsa (sozlamalar bo'sh bo'lsa),
        # xavfsiz tomonga o'tib, tekshiruvni o'tkazib yuboramiz (hammani "faol" deb hisoblaymiz)
        return {"holat": "faol", "kompaniya_nomi": None}

    topilganlar = []  # ikkala varaqda topilgan barcha yozuvlarni ({"sana","kompaniya"}) shu yerga yig'amiz
    for varaq in (LIGOTNIY_VARAQ, PLATNIY_VARAQ):
        natija = _varaqdan_qidir(varaq, inn)
        if natija:  # agar shu varaqda topilgan bo'lsa
            topilganlar.append(natija)

    if not topilganlar:  # ikkala varaqda ham umuman topilmadi
        return {"holat": "topilmadi", "kompaniya_nomi": None}

    # agar bir nechta yozuv topilsa (masalan avval ligotniy, keyin platniyga o'tgan bo'lsa),
    # ENG UZOQ (eng foydali) sanaga tegishli yozuvni tanlaymiz
    eng_yaxshisi = max(topilganlar, key=lambda x: x["sana"] or date.min)
    kompaniya_nomi = eng_yaxshisi["kompaniya"]

    if eng_yaxshisi["sana"] and eng_yaxshisi["sana"] >= date.today():  # tugash sanasi hali kelmagan bo'lsa
        return {"holat": "faol", "kompaniya_nomi": kompaniya_nomi}
    return {"holat": "muddati_otgan", "kompaniya_nomi": kompaniya_nomi}  # aks holda — muddati o'tgan
