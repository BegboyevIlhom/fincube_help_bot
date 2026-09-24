# Bu fayl "taymer tekshiruvchi" — tashqi bepul xizmat (masalan cron-job.org)
# tomonidan HAR 1 DAQIQADA chaqiriladi va barcha kutayotgan mijozlarning
# vaqtini tekshirib, kerak bo'lsa ogohlantirish yuboradi yoki mijozga uzr aytadi

from fastapi import FastAPI, Request  # veb-server va so'rovni o'qish uchun
from lib import db  # ma'lumotlar bazasi funksiyalari
from lib import telegram as tg  # Telegramga xabar yuborish funksiyalari
from lib.config import (
    CRON_SECRET, TAYMER_JAMI_DAQIQA, TAYMER_SARIQ_DAQIQA
)  # sozlamalarni olib kelamiz

app = FastAPI()  # FastAPI ilovasini yaratamiz


@app.post("/")
@app.get("/")  # ba'zi bepul cron xizmatlari GET so'rov yuboradi, shuning uchun ikkalasini ham qo'llaymiz
async def tekshir(so_rov: Request):
    # xavfsizlik: faqat to'g'ri maxfiy parol bilan kelgan so'rovlarga xizmat ko'rsatamiz
    kelgan_parol = so_rov.headers.get("x-cron-secret", "")
    if CRON_SECRET and kelgan_parol != CRON_SECRET:  # agar parol noto'g'ri bo'lsa
        return {"ok": False, "xato": "Ruxsat yo'q"}  # rad etamiz

    zayavkalar = db.navbatdagi_zayavkalar()  # hali xodim tayinlanmagan barcha "navbatda" zayavkalarni olamiz
    natijalar = []  # har bir zayavka bo'yicha nima qilinganini shu yerga yozib boramiz

    for zayavka in zayavkalar:  # har bir kutayotgan zayavkani birma-bir tekshiramiz
        natijalar.append(bitta_zayavkani_tekshir(zayavka))

    return {"ok": True, "tekshirilgan_soni": len(zayavkalar), "natijalar": natijalar}


def bitta_zayavkani_tekshir(zayavka):
    # zayavka to'liq bo'lgandan (yaratilgan_vaqt) beri necha daqiqa o'tganini hisoblaymiz
    yaratilgan = db_vaqtdan_datetime(zayavka["yaratilgan_vaqt"])
    otgan_daqiqa = (db.hozir() - yaratilgan).total_seconds() / 60

    if otgan_daqiqa >= TAYMER_JAMI_DAQIQA:  # 20 daqiqa to'liq o'tib ketgan bo'lsa
        return muddat_tugadi(zayavka)

    if otgan_daqiqa >= (TAYMER_JAMI_DAQIQA - 5) and not zayavka.get("besh_daqiqa_signal_yuborildimi"):
        # 15 daqiqa o'tgan, ya'ni oxirgi 5 daqiqa qolgan va hali majburiy signal yuborilmagan bo'lsa
        return majburiy_signal_yubor(zayavka)

    if otgan_daqiqa >= TAYMER_SARIQ_DAQIQA and zayavka.get("rang") == "yashil":
        # 10 daqiqa o'tgan va hali "sariq"ga o'tkazilmagan bo'lsa
        db.zayavkani_yangila(zayavka["id"], rang="sariq")
        return {"zayavka_id": zayavka["id"], "harakat": "sariqqa_otkazildi"}

    return {"zayavka_id": zayavka["id"], "harakat": "hozircha_kutilmoqda"}


def majburiy_signal_yubor(zayavka):
    # oxirgi 5 daqiqa qolganda — BAND bo'lgan xodimlar ham jumladan, BARCHA 4 xodimga majburiy signal yuboriladi
    barcha = db.barcha_xodimlar()  # bazadagi barcha xodimlarni olamiz (holatidan qat'iy nazar)
    for xodim in barcha:
        tg.xabar_yubor(
            zayavka["guruh_chat_id"],
            f"🔴 <b>DIQQAT!</b> Mijoz uchun atigi 5 daqiqa qoldi!\n"
            f"{xodim['ism_familiya']}, iltimos, imkoniyat bo'lsa qabul qiling 👇",
            reply_to=zayavka.get("mijoz_xabar_id"),
            tugmalar=tg.qabul_tugmasi(zayavka["id"])
        )
    # bu zayavka uchun majburiy signal allaqachon yuborilganini belgilab qo'yamiz (qayta-qayta yubormaslik uchun)
    db.zayavkani_yangila(zayavka["id"], rang="qizil", besh_daqiqa_signal_yuborildimi=True)
    return {"zayavka_id": zayavka["id"], "harakat": "majburiy_signal_yuborildi"}


def muddat_tugadi(zayavka):
    # 20 daqiqa to'liq o'tib, hech kim qabul qilmagan bo'lsa — mijozga uzr aytamiz
    tg.xabar_yubor(
        zayavka["guruh_chat_id"],
        "Hurmatli mijoz, uzr so'raymiz — hozirda barcha mutaxassislarimiz band. "
        "Tez orada siz bilan albatta bog'lanamiz. Kutganingiz uchun rahmat!",
        reply_to=zayavka.get("mijoz_xabar_id")
    )
    # zayavkani "muddati_otdi" holatiga o'tkazamiz, shunda u endi navbatda hisoblanmaydi
    db.zayavkani_yangila(zayavka["id"], holat="muddati_otdi")
    return {"zayavka_id": zayavka["id"], "harakat": "uzr_yuborildi"}


def db_vaqtdan_datetime(qiymat):
    # Supabase'dan matn ko'rinishida kelgan vaqtni Python'ning datetime obyektiga aylantiradi
    from datetime import datetime  # funksiya ichida import qilamiz (faqat shu yerda kerak)
    return datetime.fromisoformat(qiymat.replace("Z", "+00:00"))  # "Z" belgisini to'g'ri formatga o'girib beradi
