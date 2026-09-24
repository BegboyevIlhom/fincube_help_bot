# Bu fayl "taymer tekshiruvchi" mantig'ini saqlaydi (FastAPI'siz, sof funksiyalar)
# Uni tashqaridan api/index.py chaqiradi, u esa tashqi cron xizmati tomonidan
# har 1 daqiqada chaqiriladi

from datetime import timedelta  # kunlarni hisoblash uchun (baholash muddatini tekshirish uchun kerak)
from lib import db  # ma'lumotlar bazasi funksiyalari
from lib import telegram as tg  # Telegramga xabar yuborish funksiyalari
from lib.config import TAYMER_JAMI_DAQIQA, TAYMER_SARIQ_DAQIQA, BAHOLASH_MUDDAT_KUN  # sozlamalar


def barcha_navbatni_tekshir():
    # navbatda turgan barcha zayavkalarni tekshirib chiqadi, har biri uchun natijani qaytaradi
    zayavkalar = db.navbatdagi_zayavkalar()  # hali xodim tayinlanmagan barcha "navbatda" zayavkalarni olamiz
    natijalar = []  # har bir zayavka bo'yicha nima qilinganini shu yerga yozib boramiz
    for zayavka in zayavkalar:  # har bir kutayotgan zayavkani birma-bir tekshiramiz
        natijalar.append(bitta_zayavkani_tekshir(zayavka))

    baholash_natija = eskirgan_baholashlarni_tekshir()  # muddati o'tgan baholashlarni ham tekshiramiz

    return {"tekshirilgan_soni": len(zayavkalar), "natijalar": natijalar, "baholash": baholash_natija}


def eskirgan_baholashlarni_tekshir():
    # BAHOLASH_MUDDAT_KUN (3 kun) ichida javob berilmagan baholash so'rovlarini "muddati_otdi" deb belgilaydi
    chegara = (db.hozir() - timedelta(days=BAHOLASH_MUDDAT_KUN)).isoformat()
    eskirganlar = db.eskirgan_baholashlar(chegara)
    for baholash in eskirganlar:
        db.baholashni_yangila(baholash["id"], holat="muddati_otdi")
    return {"eskirgan_soni": len(eskirganlar)}


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
    # oxirgi 5 daqiqa qolganda — BAND bo'lganlar ham jumladan, FAQAT rol='xodim' bo'lganlarga
    # BITTA majburiy xabar yuboriladi (owner va super_user bu yerga kirmaydi)
    barcha = [x for x in db.barcha_xodimlar() if x.get("rol") != "owner"]  # "owner"dan boshqa hamma (ishlaydiganlar)
    belgilar = tg.xodimlarni_belgila(barcha)  # hammasini bitta qatorda belgilaymiz
    tg.xabar_yubor(
        zayavka["guruh_chat_id"],
        f"🔴 <b>DIQQAT!</b> Mijoz uchun atigi 5 daqiqa qoldi!\n"
        f"{belgilar} — iltimos, imkoniyat bo'lsa Mini App orqali qabul qiling 👇",
        reply_to=zayavka.get("mijoz_xabar_id")
    )
    # bu zayavka uchun majburiy signal allaqachon yuborilganini belgilab qo'yamiz (qayta-qayta yubormaslik uchun)
    db.zayavkani_yangila(zayavka["id"], rang="qizil", besh_daqiqa_signal_yuborildimi=True)
    return {"zayavka_id": zayavka["id"], "harakat": "majburiy_signal_yuborildi"}


def muddat_tugadi(zayavka):
    # 20 daqiqa to'liq o'tib, hech kim qabul qilmagan bo'lsa — mijozga uzr aytamiz (ikki tilda)
    tg.xabar_yubor(
        zayavka["guruh_chat_id"],
        "🇺🇿 Hurmatli mijoz, uzr so'raymiz — hozirda barcha mutaxassislarimiz band. "
        "Tez orada siz bilan albatta bog'lanamiz. Kutganingiz uchun rahmat!\n\n"
        "🇷🇺 Уважаемый клиент, приносим извинения — в данный момент все наши специалисты заняты. "
        "Мы обязательно свяжемся с вами в ближайшее время. Спасибо за ожидание!",
        reply_to=zayavka.get("mijoz_xabar_id")
    )
    # zayavkani "muddati_otdi" holatiga o'tkazamiz, shunda u endi navbatda hisoblanmaydi
    db.zayavkani_yangila(zayavka["id"], holat="muddati_otdi")
    return {"zayavka_id": zayavka["id"], "harakat": "uzr_yuborildi"}


def db_vaqtdan_datetime(qiymat):
    # Supabase'dan matn ko'rinishida kelgan vaqtni Python'ning datetime obyektiga aylantiradi
    from datetime import datetime  # funksiya ichida import qilamiz (faqat shu yerda kerak)
    return datetime.fromisoformat(qiymat.replace("Z", "+00:00"))  # "Z" belgisini to'g'ri formatga o'girib beradi
