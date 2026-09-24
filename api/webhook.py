# Bu fayl Telegramdan keladigan HAR BIR yangilanishni (xabar, tugma bosish) qabul qiladigan asosiy fayl
# Telegram bu manzilga "webhook" sifatida ulanadi: https://sizning-domeningiz/api/webhook

from fastapi import FastAPI, Request  # veb-server yaratish uchun asosiy kutubxona
from lib import db  # ma'lumotlar bazasi funksiyalari
from lib import telegram as tg  # Telegramga xabar yuborish funksiyalari
from lib.logic import malumot_toliqmi  # INN/telefon tekshiruvchi funksiya
from lib.config import SUPPORT_GROUP_ID  # support guruh IDsi

app = FastAPI()  # FastAPI ilovasini yaratamiz, Vercel shu "app" obyektini avtomatik topadi


@app.post("/")
async def webhook(so_rov: Request):
    # Telegram har bir yangi voqeada shu funksiyaga POST so'rov yuboradi
    malumot = await so_rov.json()  # kelgan JSON ma'lumotni o'qiymiz

    if "message" in malumot:  # agar bu oddiy xabar bo'lsa (mijoz yoki xodim yozgan)
        await xabarni_qayta_ishla(malumot["message"])

    elif "callback_query" in malumot:  # agar bu tugma bosilishi bo'lsa (xodim tugma bosdi)
        await tugmani_qayta_ishla(malumot["callback_query"])

    return {"ok": True}  # Telegramga "hammasi joyida" deb javob qaytaramiz


async def xabarni_qayta_ishla(xabar):
    # faqat bizning support guruhimizdagi xabarlarni ko'rib chiqamiz
    chat_id = xabar.get("chat", {}).get("id")  # xabar yuborilgan chat IDsi
    if chat_id != SUPPORT_GROUP_ID:  # agar bu bizning guruhimiz bo'lmasa
        return  # e'tiborsiz qoldiramiz

    yuboruvchi = xabar.get("from", {})  # xabarni kim yuborgani haqida ma'lumot
    yuboruvchi_id = yuboruvchi.get("id")  # yuboruvchining Telegram IDsi
    matn = xabar.get("text", "")  # xabarning matni

    if not matn:  # agar xabarda matn bo'lmasa (masalan rasm yoki stiker bo'lsa)
        return  # hozircha bunday xabarlarni e'tiborsiz qoldiramiz

    # agar xabarni xodimlardan biri yozgan bo'lsa — bu mijoz murojaati emas, shuning uchun e'tiborsiz qoldiramiz
    if db.xodim_topilsin(yuboruvchi_id):
        return

    # mijozni bazadan topamiz yoki yangisini yaratamiz
    mijoz = db.mijoz_top_yoki_yarat(yuboruvchi_id, yuboruvchi.get("first_name", "Mijoz"))

    # shu mijozning hali tugallanmagan (malumot kutilayotgan) zayavkasi bor-yo'qligini tekshiramiz
    zayavka = db.ochiq_zayavka_top(mijoz["id"])

    if zayavka:  # agar ochiq zayavka mavjud bo'lsa — yangi xabarni eskisiga qo'shib qo'yamiz
        yangi_matn = (zayavka.get("matn") or "") + "\n" + matn
        db.zayavka_matnini_yangila(zayavka["id"], yangi_matn)
        zayavka["matn"] = yangi_matn  # keyingi tekshiruv uchun mahalliy nusxasini ham yangilaymiz
    else:  # aks holda yangi zayavka ochamiz
        zayavka = db.zayavka_yarat(mijoz["id"], chat_id, xabar.get("message_id"), matn)

    # endi INN va telefon (ikkalasi ham 9 xonali raqam) berilgan-berilmaganini tekshiramiz
    toliqmi, raqamlar = malumot_toliqmi(zayavka["matn"])

    if not toliqmi:  # agar hali ma'lumot yetarli bo'lmasa
        tg.xabar_yubor(
            chat_id,
            "Hurmatli mijoz! Murojaatingiz uchun rahmat.\n"
            "Sizga tezroq yordam berishimiz uchun iltimos <b>INN</b> va <b>telefon raqamingizni</b> yuboring.",
            reply_to=xabar.get("message_id")
        )
        return  # xodimlarni chaqirmasdan, mijozdan ma'lumot kutamiz

    # ma'lumot to'liq bo'lsa — mijozning INN/telefonini bazaga yozamiz (birinchi ikkita topilgan raqam sifatida)
    db.mijoz_malumotini_yangila(mijoz["id"], raqamlar[0], raqamlar[1])

    # shu mijoz uchun so'nggi 3 kun ichida ustuvor xodim bormi tekshiramiz
    ustuvor_xodim_id = db.ustuvor_xodimni_top(mijoz["id"])

    # zayavkani "navbatda" holatiga o'tkazamiz va taymerni shu daqiqadan boshlaymiz
    db.zayavkani_yangila(
        zayavka["id"],
        holat="navbatda",
        ustuvor_xodim_id=ustuvor_xodim_id,
        yaratilgan_vaqt=db.hozir().isoformat()
    )
    zayavka["ustuvor_xodim_id"] = ustuvor_xodim_id  # keyingi funksiyaga kerak bo'ladi

    xodimlarni_taklif_qil(zayavka)


def xodimlarni_taklif_qil(zayavka):
    # navbatdagi zayavka uchun mos xodim(lar)ni tag qilib, "Qabul qildim" tugmasi bilan taklif yuboradi
    ustuvor_id = zayavka.get("ustuvor_xodim_id")  # ushbu mijoz uchun ustuvor xodim (agar bor bo'lsa)

    if ustuvor_id:  # agar oldingi 3 kun ichida shu mijoz bilan gaplashgan xodim bo'lsa
        ustuvor_xodim = db.xodim_id_orqali(ustuvor_id)
        if ustuvor_xodim and ustuvor_xodim["holat"] == "bosh":  # va u hozir bo'sh bo'lsa
            # faqat shu xodimga alohida, ustuvor tarzda taklif yuboramiz
            natija = tg.xabar_yubor(
                zayavka["guruh_chat_id"],
                f"🔁 <b>Qaytar mijoz!</b> Bu mijoz bilan oxirgi 3 kun ichida siz gaplashgan edingiz.\n"
                f"Iltimos, siz qabul qiling 👇",
                reply_to=zayavka.get("mijoz_xabar_id"),
                tugmalar=tg.qabul_tugmasi(zayavka["id"])
            )
            if natija.get("ok"):  # agar xabar muvaffaqiyatli yuborilgan bo'lsa
                db.zayavkani_yangila(zayavka["id"], oxirgi_tag_xabar_id=natija["result"]["message_id"])
            return  # boshqa xodimlarga hozircha tag qilmaymiz, ustuvor xodim javob kutiladi
        # agar ustuvor xodim band bo'lsa — pastga o'tib, baribir bo'sh xodimlarni ham taklif qilamiz
        # (talabga ko'ra: "boshqa xodim ham qabul qilishni istasa farqi yo'q")

    # bo'sh turgan barcha xodimlarni topamiz
    bosh_turganlar = db.bosh_xodimlar()

    if not bosh_turganlar:  # agar hozircha hech kim bo'sh bo'lmasa
        return  # hech narsa qilmaymiz, taymer tekshiruvchi (check_timers) keyin o'zi kuzatadi

    # bo'sh turgan har bir xodimga alohida taklif xabari yuboramiz
    for xodim in bosh_turganlar:
        tg.xabar_yubor(
            zayavka["guruh_chat_id"],
            "🆕 Yangi mijoz murojaati! Qabul qilasizmi?",
            reply_to=zayavka.get("mijoz_xabar_id"),
            tugmalar=tg.qabul_tugmasi(zayavka["id"])
        )


async def tugmani_qayta_ishla(callback):
    # xodim "Qabul qildim" yoki "Consultatsiya berdim" tugmasini bosganda shu yerga tushadi
    xodim_telegram_id = callback.get("from", {}).get("id")  # tugmani bosgan odamning IDsi
    callback_id = callback.get("id")  # javob berish uchun kerak bo'ladigan callback IDsi
    data = callback.get("data", "")  # tugma qanday nom bilan yuborilgani (masalan "qabul:12")

    xodim = db.xodim_topilsin(xodim_telegram_id)  # bosgan odam haqiqatan xodim ekanini tekshiramiz
    if not xodim:  # agar u ro'yxatdagi xodim bo'lmasa
        tg.callback_javob(callback_id, "Siz xodimlar ro'yxatida emassiz.", ogohlantirish=True)
        return

    turi, _, zayavka_id_str = data.partition(":")  # "qabul:12" -> turi="qabul", zayavka_id_str="12"
    zayavka_id = int(zayavka_id_str)  # matn ko'rinishidagi ID raqamini songa aylantiramiz
    zayavka = db.zayavka_id_orqali(zayavka_id)  # tegishli zayavkani bazadan olamiz

    if not zayavka:  # agar zayavka topilmasa (o'chirilgan yoki xato bo'lsa)
        tg.callback_javob(callback_id, "Bu zayavka topilmadi.", ogohlantirish=True)
        return

    if turi == "qabul":  # agar "Qabul qildim" tugmasi bosilgan bo'lsa
        qabul_qilishni_boshqar(callback, xodim, zayavka)
    elif turi == "tugadi":  # agar "Consultatsiya berdim" tugmasi bosilgan bo'lsa
        tugatishni_boshqar(callback, xodim, zayavka)


def qabul_qilishni_boshqar(callback, xodim, zayavka):
    callback_id = callback.get("id")

    # agar boshqa xodim ulgurib allaqachon shu mijozni qabul qilib bo'lgan bo'lsa
    if zayavka["holat"] != "navbatda":
        tg.callback_javob(callback_id, "Kechirasiz, bu mijozni allaqachon boshqa xodim qabul qilgan.", ogohlantirish=True)
        return

    # zayavkani shu xodimga biriktiramiz va "jarayonda" holatiga o'tkazamiz
    db.zayavkani_yangila(
        zayavka["id"],
        holat="jarayonda",
        biriktirilgan_xodim_id=xodim["id"],
        jarayon_boshlangan_vaqt=db.hozir().isoformat()
    )
    # xodimni "band" holatiga o'tkazamiz
    db.xodim_holatini_yangila(xodim["id"], "band", zayavka["id"])

    # bosilgan xabarni tahrirlab, endi kim qabul qilganini ko'rsatamiz va tugmani almashtiramiz
    xabar = callback.get("message", {})
    tg.xabar_tahrirla(
        xabar.get("chat", {}).get("id"),
        xabar.get("message_id"),
        f"✅ Ushbu mijozni <b>{xodim['ism_familiya']}</b> qabul qildi.",
        tugmalar=tg.tugadi_tugmasi(zayavka["id"])
    )
    tg.callback_javob(callback_id, "Qabul qilindi, omad!")


def tugatishni_boshqar(callback, xodim, zayavka):
    callback_id = callback.get("id")

    # faqat shu mijozni qabul qilgan xodimning o'zi "tugatishi" mumkin
    if zayavka.get("biriktirilgan_xodim_id") != xodim["id"]:
        tg.callback_javob(callback_id, "Bu sizning mijozingiz emas.", ogohlantirish=True)
        return

    # zayavkani "tugallandi" holatiga o'tkazamiz
    db.zayavkani_yangila(zayavka["id"], holat="tugallandi", tugallangan_vaqt=db.hozir().isoformat())
    # xodimni yana "bosh" holatiga qaytaramiz
    db.xodim_holatini_yangila(xodim["id"], "bosh", None)

    xabar = callback.get("message", {})
    tg.xabar_tahrirla(
        xabar.get("chat", {}).get("id"),
        xabar.get("message_id"),
        f"☑️ Consultatsiya yakunlandi ({xodim['ism_familiya']})."
    )
    tg.callback_javob(callback_id, "Yakunlandi.")

    # endi xodim bo'shadi — navbatda uni kutayotgan (yoki unga ustuvor) mijoz bormi tekshiramiz
    keyingi = db.keyingi_zayavka_shu_xodim_uchun(xodim["id"])
    if keyingi:  # agar navbatda kimdir bo'lsa
        xodimlarni_taklif_qil(keyingi)  # o'sha mijoz uchun taklif jarayonini qayta ishga tushiramiz
