# Bu fayl Telegramdan kelgan HAR BIR yangilanishni (xabar, tugma bosish) qayta ishlaydi
# Bu oddiy Python funksiyalari to'plami — FastAPI'ning o'zi bu yerda yo'q,
# uni faqat api/index.py chaqiradi (shu tarzda Vercel'ning yangi talabiga moslashadi)

from lib import db  # ma'lumotlar bazasi funksiyalari
from lib import telegram as tg  # Telegramga xabar yuborish funksiyalari
from lib import sheets  # Google Sheets'dagi mijozlar bazasini tekshirish funksiyasi
from lib.logic import malumot_toliqmi, shubhali_raqamlarni_top  # INN/telefon tekshiruvchi funksiyalar
from lib.config import (
    SUPPORT_GROUP_ID, SHARTNOMA_XODIM_NICK, SHARTNOMA_XODIM_TEL, APP_URL,
    MUMKIN_YONALISHLAR, QONGIROQ_URINISH_MAKS, BOT_USERNAME
)


async def yangilanishni_qayta_ishla(malumot):
    # Telegramdan kelgan bitta "update" obyektini turiga qarab tegishli funksiyaga yo'naltiradi
    if "message" in malumot:  # agar bu oddiy xabar bo'lsa (mijoz yoki xodim yozgan)
        await xabarni_qayta_ishla(malumot["message"])
    elif "callback_query" in malumot:  # agar bu tugma bosilishi bo'lsa (xodim tugma bosdi)
        await tugmani_qayta_ishla(malumot["callback_query"])


async def xabarni_qayta_ishla(xabar):
    chat = xabar.get("chat", {})  # xabar yuborilgan chat haqida to'liq ma'lumot
    chat_id = chat.get("id")  # chat IDsi
    chat_turi = chat.get("type")  # "private" (shaxsiy) yoki "group"/"supergroup" (guruh)

    if chat_turi == "private":  # agar bu botning SHAXSIY chatida yozilgan bo'lsa (guruh emas)
        shaxsiy_chatni_boshqar(xabar)  # alohida funksiyaga uzatamiz (mijoz/xodimni farqlash uchun)
        return  # guruh mantig'iga o'tmaymiz

    # TASHXIS UCHUN: har bir (guruhdagi) xabarni albatta logga yozamiz — shunda "bu bizning
    # guruhimiz emas" deb sukut saqlab tashlab yuborilayotgan holatlar ham ko'rinadi
    print(f"Guruh xabari: chat_id={chat_id} (kutilgan SUPPORT_GROUP_ID={SUPPORT_GROUP_ID}), "
          f"matn={xabar.get('text', '')!r}")

    # faqat bizning support guruhimizdagi xabarlarni ko'rib chiqamiz
    if chat_id != SUPPORT_GROUP_ID:  # agar bu bizning guruhimiz bo'lmasa
        print(f"E'TIBORSIZ QOLDIRILDI: chat_id mos kelmadi ({chat_id} != {SUPPORT_GROUP_ID})")
        return  # e'tiborsiz qoldiramiz

    yuboruvchi = xabar.get("from", {})  # xabarni kim yuborgani haqida ma'lumot
    yuboruvchi_id = yuboruvchi.get("id")  # yuboruvchining Telegram IDsi
    matn = xabar.get("text", "")  # xabarning matni

    if not matn:  # agar xabarda matn bo'lmasa (masalan rasm yoki stiker bo'lsa)
        return  # hozircha bunday xabarlarni e'tiborsiz qoldiramiz

    # agar xabarni xodimlardan biri yozgan bo'lsa — bu mijoz murojaati emas, shuning uchun e'tiborsiz qoldiramiz
    aniqlangan_xodim = db.xodim_topilsin(yuboruvchi_id)
    if aniqlangan_xodim:
        print(f"E'TIBORSIZ QOLDIRILDI: yuboruvchi ({yuboruvchi_id}) xodim sifatida aniqlandi "
              f"({aniqlangan_xodim.get('ism_familiya')})")
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
        shubhali = shubhali_raqamlarni_top(zayavka["matn"])  # "deyarli to'g'ri" raqamlar bormi tekshiramiz

        if shubhali:  # agar mijoz yozgan raqamlardan biri 9 xonaga yaqin, lekin noto'g'ri bo'lsa
            # bu holatda aniq QAYSI raqamda xato borligini ko'rsatib, umumiy xabarni takrorlamaymiz
            royxat = ", ".join(f"«{r}» ({len(r)} xonali)" for r in shubhali)  # masalan: «87687876» (8 xonali)
            tg.xabar_yubor(
                chat_id,
                f"🇺🇿 Diqqat: {royxat} raqamingizda xatolik bo'lishi mumkin — "
                f"INN va telefon raqami <b>aynan 9 xonali</b> bo'lishi kerak.\n"
                f"Iltimos tekshirib, qaytadan to'liq yuboring.\n\n"
                f"🇷🇺 Внимание: возможно, в номере {royxat} есть ошибка — "
                f"ИНН и номер телефона должны состоять <b>ровно из 9 цифр</b>.\n"
                f"Пожалуйста, проверьте и отправьте заново.",
                reply_to=xabar.get("message_id")
            )
        else:  # hech qanday shubhali raqam yo'q — demak mijoz hali umuman ma'lumot bermagan, namuna ko'rsatamiz
            tg.xabar_yubor(
                chat_id,
                "🇺🇿 Hurmatli mijoz! Murojaatingiz uchun rahmat.\n"
                "Sizga tezroq yordam berishimiz uchun iltimos <b>INN</b> va <b>telefon raqamingizni</b> yuboring.\n"
                "Masalan: <code>INN: 123456789, tel: 901234567</code>\n\n"
                "🇷🇺 Уважаемый клиент! Спасибо за обращение.\n"
                "Чтобы мы могли быстрее вам помочь, пожалуйста, отправьте ваш <b>ИНН</b> и <b>номер телефона</b>.\n"
                "Например: <code>ИНН: 123456789, тел: 901234567</code>",
                reply_to=xabar.get("message_id")
            )
        return  # xodimlarni chaqirmasdan, mijozdan ma'lumot kutamiz

    # ma'lumot to'liq bo'lsa — mijozning INN/telefonini bazaga yozamiz (birinchi ikkita topilgan raqam sifatida)
    db.mijoz_malumotini_yangila(mijoz["id"], raqamlar[0], raqamlar[1])

    # ENDI eng muhim tekshiruv: shu INN bo'yicha amaldagi support shartnomasi bormi?
    # (Google Sheets'dagi "Ligotniy" va "Platniy" jadvallaridan tekshiramiz)
    shartnoma = sheets.mijoz_holati(raqamlar[0])  # raqamlar[0] — INN sifatida qabul qilingan raqam

    # MUHIM: INN va kompaniya nomini ENDI ZAYAVKANING O'ZIGA yozamiz (mijozning umumiy
    # yozuviga emas) — shunda agar shu odam keyinroq BOSHQA INN bilan murojaat qilsa,
    # bu eski zayavka o'zining haqiqiy (o'sha paytdagi) kompaniyasini saqlab qoladi,
    # keyingi murojaatlar buni "qayta yozib" o'zgartirmaydi
    db.zayavkani_yangila(zayavka["id"], inn=raqamlar[0], kompaniya_nomi=shartnoma.get("kompaniya_nomi"))

    if shartnoma.get("kompaniya_nomi"):  # agar Google Sheets'da kompaniya nomi topilgan bo'lsa
        # mijoz yozuviga ham "oxirgi ma'lum kompaniya" sifatida saqlab qo'yamiz (ixtiyoriy, qulaylik uchun)
        db.mijoz_kompaniyasini_yangila(mijoz["id"], shartnoma["kompaniya_nomi"])

    if shartnoma["holat"] != "faol":  # agar shartnoma umuman topilmasa yoki muddati o'tgan bo'lsa
        shartnoma_yoq_xabar_yubor(mijoz, xabar, chat_id, shartnoma["holat"])
        db.zayavkani_yangila(zayavka["id"], holat="shartnoma_yoq")  # bu zayavka navbatga qo'yilmaydi
        return  # xodimlarni chaqirmasdan, jarayonni shu yerda to'xtatamiz

    # zayavkani "navbatda" holatiga o'tkazamiz va taymerni shu daqiqadan boshlaymiz
    db.zayavkani_yangila(
        zayavka["id"],
        holat="navbatda",
        yaratilgan_vaqt=db.hozir().isoformat()
    )

    xodimlarni_taklif_qil(zayavka)


def shaxsiy_chatni_boshqar(xabar):
    # botning shaxsiy (lichka) chatida yozilgan xabarni boshqaradi — xodim va mijozni farqlab,
    # faqat XODIMLARGA "Ish paneli" (Mini App) tugmasini ko'rsatadi
    yuboruvchi = xabar.get("from", {})  # xabar yuboruvchi haqida ma'lumot
    yuboruvchi_id = yuboruvchi.get("id")  # yuboruvchining Telegram IDsi
    chat_id = xabar.get("chat", {}).get("id")  # bu — shaxsiy chatning o'zi (odatda yuboruvchi_id bilan bir xil)
    matn = xabar.get("text", "")  # xabarning matni

    xodim = db.xodim_topilsin(yuboruvchi_id)  # yozgan odam xodimlar ro'yxatida bormi tekshiramiz

    if xodim:  # agar bu XODIM bo'lsa
        if APP_URL:  # agar bot manzili sozlangan bo'lsa
            tg.chat_menu_ornat(chat_id, f"{APP_URL}/app")  # unga "Ish paneli" tugmasini ko'rsatamiz
        tg.xabar_yubor(
            chat_id,
            f"Assalomu alaykum, <b>{xodim['ism_familiya']}</b>!\n"
            f"Pastdagi «Ish paneli» tugmasi orqali navbatdagi mijozlarni ko'rishingiz mumkin."
        )
        return

    # bu yerdan pastda — yozgan odam MIJOZ (yoki umuman xodim bo'lmagan boshqa odam)
    try:  # bu — faqat kosmetik amal (menyu tugmasi), muvaffaqiyatsiz bo'lsa ham davom etaveramiz
        tg.chat_menu_ornat(chat_id, None)  # hech qanday maxsus tugma ko'rsatmaymiz (ichki panel yashirin qoladi)
    except Exception:
        pass  # bu xatolik ASOSIY (pastdagi) mantiqni to'xtatib qo'ymasligi kerak

    mijoz = db.mijoz_top_yoki_yarat(yuboruvchi_id, yuboruvchi.get("first_name", "Mijoz"))

    # ENG MUHIM TEKSHIRUV: agar mijozga avval GURUHDA yuborib bo'lmagan (\"kutayotgan\") xabar
    # saqlangan bo'lsa (masalan \"shartnomangiz yo'q\" yoki \"telefonni ko'tarmadingiz\" eslatmasi) —
    # endi mijoz botga yozgani uchun uni LICHKASIGA avtomatik yetkazamiz va tozalaymiz.
    # Bu — aynan "🔔 Sizga botimizdan shaxsiy xabar bor, Start bosing" degan taklif ishlagan payt.
    kutayotgan_xabar = mijoz.get("kutayotgan_xabar")
    if kutayotgan_xabar:
        tg.xabar_yubor(chat_id, kutayotgan_xabar)  # avval kutib turgan xabarni yetkazamiz
        db.mijoz_kutayotgan_xabarini_tozala(mijoz["id"])  # qayta yubormaslik uchun tozalaymiz
        return  # bu safar shu bitta xabar yetarli, pastdagi umumiy javoblarni qo'shimcha yubormaymiz

    # YANA BIR TEKSHIRUV: mijozga avval BAHOLASH so'rovi (yulduzcha tugmalari bilan) yuborilmoqchi
    # bo'lgan-u, lekin u hali "start" qilmagani uchun yetkazib bo'lmagan bo'lsa — endi shu so'rovni
    # TO'LIQ (tugmalari bilan) yuboramiz (oddiy "kutayotgan_xabar" bunga yaramaydi, chunki tugma kerak)
    yuborilmagan_baholash = db.mijozning_yuborilmagan_baholashi(mijoz["id"])
    if yuborilmagan_baholash:
        matn = (
            "🇺🇿 Hurmatli mijoz! Consultatsiya yakunlandi.\n"
            "Iltimos, xizmatimizni baholang (1 dan 5 yulduzgacha):\n\n"
            "🇷🇺 Уважаемый клиент! Консультация завершена.\n"
            "Пожалуйста, оцените наш сервис (от 1 до 5 звёзд):"
        )
        natija = tg.xabar_yubor(chat_id, matn, tugmalar=tg.baholash_klaviaturasi(yuborilmagan_baholash["id"]))
        if natija.get("ok"):  # muvaffaqiyatli yuborilsa, chat_id/xabar_id'ni saqlab qo'yamiz
            db.baholashni_yangila(
                yuborilmagan_baholash["id"],
                chat_id=chat_id,
                xabar_id=natija["result"]["message_id"]
            )
        return  # bu safar shu bitta xabar yetarli

    # avval — balki bu mijoz yaqinda baholash bergan-u, ENDI IZOH yozayotgandir? Shuni tekshiramiz
    kutilayotgan_baholash = db.mijozning_izoh_kutayotgan_baholashi(mijoz["id"])

    if kutilayotgan_baholash and matn and matn != "/start":  # agar izoh kutilayotgan bo'lsa va bu buyruq bo'lmasa
        db.baholashni_yangila(kutilayotgan_baholash["id"], izoh=matn)  # yozgan matnini izoh sifatida saqlaymiz
        tg.xabar_yubor(
            chat_id,
            "🇺🇿 Rahmat! Izohingiz qabul qilindi. ✅\n\n"
            "🇷🇺 Спасибо! Ваш комментарий принят. ✅"
        )
        return

    # oddiy holat — mijoz botga birinchi marta yozgan yoki umuman aloqasi yo'q xabar yuborgan
    tg.xabar_yubor(
        chat_id,
        "🇺🇿 Salom! Savolingiz yoki murojaatingiz bo'lsa, iltimos FINCUBE support guruhiga yozing:\n"
        "https://t.me/+W2fmayb2qeMxZjJi\n\n"
        "🇷🇺 Здравствуйте! Если у вас есть вопрос, пожалуйста, напишите в группу поддержки FINCUBE:\n"
        "https://t.me/+W2fmayb2qeMxZjJi"
    )


def shaxsiy_yoki_ogohlantirish_yubor(mijoz, guruh_chat_id, mijoz_xabar_id, matn):
    # AVVAL mijozning shaxsiy (lichka) chatiga to'liq xabarni yuborishga urinadi.
    # Agar bo'lmasa (mijoz botni hali "start" qilmagan bo'lsa), GURUHGA to'liq matnni YUBORMAYDI —
    # chunki bu yerda MAXFIY/shaxsiy mazmun bo'lishi mumkin (shartnoma holati, baholash so'rovi va h.k.)
    # va guruhdagi BOSHQA mijozlar buni ko'rmasligi kerak. Shuning uchun guruhga faqat hech narsani
    # oshkor qilmaydigan QISQA eslatma yuboriladi — pastida botning shaxsiy chatiga to'g'ridan-to'g'ri
    # o'tkazadigan tugma bilan (deep link). Mijoz shu tugmani bosib, "Start"ni bossa — YUQORIDAGI
    # matn AVTOMATIK ravishda uning shaxsiy chatiga yetkaziladi (pastdagi shaxsiy_chatni_boshqar'ga qarang).
    natija = tg.xabar_yubor(mijoz["telegram_id"], matn)

    if not natija.get("ok"):  # agar lichkaga yuborib bo'lmasa
        db.mijoz_kutayotgan_xabarini_saqla(mijoz["id"], matn)  # "start" bosilganda avtomatik yuborish uchun
        tg.xabar_yubor(
            guruh_chat_id,
            "🔔 Sizga botimizdan shaxsiy (lichka) xabar bor — pastdagi tugmani bosib, "
            "botning shaxsiy chatini oching, so'ng ochilgan oynada Telegram ko'rsatadigan "
            "<b>START</b> tugmasini bosing — xabar avtomatik yetkaziladi.",
            reply_to=mijoz_xabar_id,
            tugmalar=[[{"text": "💬 Botni ochish", "url": f"https://t.me/{BOT_USERNAME}?start=1"}]]
        )
    return natija.get("ok", False)


def shartnoma_yoq_xabar_yubor(mijoz, xabar, guruh_chat_id, holat):
    # mijozga "sizda amaldagi support shartnomasi yo'q/tugagan" xabarini yuboradi,
    # shartnoma masalasi bilan shug'ullanadigan xodimning kontakti bilan birga (ikki tilda)
    sabab_uz = "sizda amaldagi support shartnomasi mavjud emas" if holat == "topilmadi" else \
        "sizning support shartnomangiz muddati tugagan"
    sabab_ru = "у вас нет действующего договора поддержки" if holat == "topilmadi" else \
        "срок действия вашего договора поддержки истёк"

    matn = (
        f"🇺🇿 Hurmatli mijoz, kechirasiz — {sabab_uz}.\n"
        f"Yangi shartnoma tuzish uchun quyidagi xodimimizga murojaat qiling:\n"
        f"👤 {SHARTNOMA_XODIM_NICK}\n📞 {SHARTNOMA_XODIM_TEL}\n\n"
        f"🇷🇺 Уважаемый клиент, извините — {sabab_ru}.\n"
        f"Для заключения нового договора обратитесь к нашему сотруднику:\n"
        f"👤 {SHARTNOMA_XODIM_NICK}\n📞 {SHARTNOMA_XODIM_TEL}"
    )
    shaxsiy_yoki_ogohlantirish_yubor(mijoz, guruh_chat_id, xabar.get("message_id"), matn)


def xodimlarni_taklif_qil(zayavka):
    # navbatdagi zayavka uchun bo'sh turgan barcha xodimlarni tag qilib, "Qabul qildim" tugmasi bilan taklif yuboradi
    bosh_turganlar = db.bosh_xodimlar()  # bo'sh turgan barcha xodimlarni topamiz

    if not bosh_turganlar:  # agar hozircha hech kim bo'sh bo'lmasa
        # xodimlar bilmasdan qolib ketmasligi uchun, "navbatda kutyapti" degan ko'rinadigan xabar yuboramiz
        tg.xabar_yubor(
            zayavka["guruh_chat_id"],
            "🕐 Yangi mijoz navbatga qo'shildi (hozircha barcha xodimlar band).\n"
            "Kimdir bo'shashi bilan avtomatik taklif yuboriladi.",
            reply_to=zayavka.get("mijoz_xabar_id")
        )
        return  # taklif tugmasi yubormaymiz, taymer tekshiruvchi (check_timers) va bo'shagan xodim o'zi kuzatadi

    # BARCHA bo'sh xodimlarga BITTA umumiy xabarda tag qilamiz (alohida-alohida emas, chalkashtirmasin)
    # DIQQAT: bu yerda tugma YO'Q — xodim endi FAQAT Mini App ("Ish paneli") orqali qabul qiladi
    belgilar = tg.xodimlarni_belgila(bosh_turganlar)  # masalan: "Aziz Aliyev, Sardor Karimov"
    natija = tg.xabar_yubor(
        zayavka["guruh_chat_id"],
        f"🆕 Yangi mijoz murojaati! Qabul qilish uchun Ish panelini oching.\n{belgilar}",
        reply_to=zayavka.get("mijoz_xabar_id")
    )
    if natija.get("ok"):  # agar xabar muvaffaqiyatli yuborilgan bo'lsa
        db.zayavkani_yangila(zayavka["id"], oxirgi_tag_xabar_id=natija["result"]["message_id"])


async def tugmani_qayta_ishla(callback):
    # DIQQAT: endi guruhda xodimlar uchun HECH QANDAY tugma yuborilmaydi — barcha amallar
    # (Qabul qildim, Consultatsiya berdim, Telefonni ko'tarmadi, Qayta qabul) FAQAT Mini App
    # ("Ish paneli") orqali bajariladi. Bu funksiya endi FAQAT mijozning baholash yulduzchasini
    # (lichkada yuboriladi) qayta ishlaydi. Agar kimdir DEPLOYdan OLDINGI eski xabardagi
    # tugmani bossa, unga xushmuomala tarzda "Mini App'dan foydalaning" deb javob beramiz.
    callback_id = callback.get("id")  # javob berish uchun kerak bo'ladigan callback IDsi
    data = callback.get("data", "")  # tugma nomi, masalan "baho:12:5"
    qismlar = data.split(":")  # ":" bo'yicha bo'laklarga ajratamiz
    turi = qismlar[0]  # birinchi bo'lak — bu amalning turi

    if turi == "baho":  # MIJOZ tomonidan bosiladigan yulduzcha — hamon shu yerda ishlaydi
        baholash_javobini_qayta_ishla(callback, int(qismlar[1]), int(qismlar[2]))
        return

    # boshqa (eski, endi ishlatilmaydigan) tugma turlari — faqat xushmuomala eslatma beramiz
    tg.callback_javob(
        callback_id,
        "Bu tugma endi ishlamaydi — iltimos, Mini App (Ish paneli) orqali davom eting.",
        ogohlantirish=True
    )


def yonalish_royxatini_ornat(xodim, zayavka_id, yonalishlar):
    # Mini App'dan kelgan "shu ro'yxatni saqla" so'rovini qayta ishlaydi (guruhdagi bitta-bitta
    # yoqish/o'chirishdan farqli — bu yerda butun ro'yxat bir yo'la yuboriladi)
    zayavka = db.zayavka_id_orqali(zayavka_id)
    if not zayavka:
        return {"ok": False, "xabar": "Bu zayavka topilmadi."}
    if zayavka.get("biriktirilgan_xodim_id") != xodim["id"]:
        return {"ok": False, "xabar": "Bu sizning mijozingiz emas."}

    # faqat MUMKIN_YONALISHLAR ro'yxatidagi qiymatlarni, va ko'pi bilan 2 tasini qabul qilamiz
    toza_royxat = [y for y in yonalishlar if y in MUMKIN_YONALISHLAR][:2]
    if not toza_royxat:
        return {"ok": False, "xabar": "Kamida 1 ta yo'nalish (ZUB / Buxgalteriya / UNF) tanlang."}

    db.yonalishlarni_ornat(zayavka_id, toza_royxat)
    return {"ok": True, "tanlangan": toza_royxat}


def zayavkani_qabul_qil(xodim, zayavka_id):
    # bitta xodim bitta zayavkani "qabul qildim" deb belgilashi uchun ASOSIY (umumiy) funksiya
    # buni Mini App ishlatadi
    if xodim.get("rol") == "owner":  # "owner" roli faqat kuzatuvchi — hech narsani o'zgartira olmaydi
        return {"ok": False, "xabar": "Sizda bu amalni bajarish huquqi yo'q (faqat kuzatish)."}

    zayavka = db.zayavka_id_orqali(zayavka_id)  # tegishli zayavkani bazadan olamiz (guruh ma'lumoti uchun)

    if not zayavka:  # agar zayavka topilmasa (o'chirilgan yoki xato bo'lsa)
        return {"ok": False, "xabar": "Bu zayavka topilmadi."}

    # MUHIM: bu yerda oldin "o'qib-keyin-yozish" (read-then-write) usuli ishlatilgan edi — tugma
    # tez-tez (bir necha marta ketma-ket) bosilsa, bir nechta urinish bab-baravar muvaffaqiyatli
    # bo'lib ketishi (poyga holati) mumkin edi. Endi bitta ATOMIK bazaviy so'rov orqali —
    # FAQAT BIRINCHI urinish haqiqiy qabul hisoblanadi
    muvaffaqiyatli = db.zayavkani_atomik_qabul_qil(zayavka_id, xodim["id"])
    if not muvaffaqiyatli:
        return {"ok": False, "xabar": "Kechirasiz, bu mijozni allaqachon boshqa xodim qabul qilgan."}

    # xodimni "band" holatiga o'tkazamiz
    db.xodim_holatini_yangila(xodim["id"], "band", zayavka["id"])

    # guruhdagi taklif xabarini tahrirlab, endi kim qabul qilganini ko'rsatamiz — ENDI TUGMASIZ
    # (bu — Mini App orqali qabul qilingan bo'lsa ham, GURUHDA ko'rinishini ta'minlaydi)
    if zayavka.get("oxirgi_tag_xabar_id"):  # agar avval yuborilgan tag xabari saqlangan bo'lsa
        tg.xabar_tahrirla(
            zayavka["guruh_chat_id"],
            zayavka["oxirgi_tag_xabar_id"],
            f"✅ Ushbu mijozni <b>{xodim['ism_familiya']}</b> qabul qildi."
        )

    return {"ok": True, "xabar": "Qabul qilindi, omad!"}


def zayavkani_tugat(xodim, zayavka_id):
    # bitta xodim bitta zayavkani "consultatsiya berdim" deb yakunlashi uchun ASOSIY (umumiy) funksiya
    # buni Telegram guruhidagi "Tasdiqlash" tugmasi ham, Mini App ham bab-baravar ishlatadi
    if xodim.get("rol") == "owner":  # "owner" roli faqat kuzatuvchi — hech narsani o'zgartira olmaydi
        return {"ok": False, "xabar": "Sizda bu amalni bajarish huquqi yo'q (faqat kuzatish)."}

    zayavka = db.zayavka_id_orqali(zayavka_id)  # tegishli zayavkani bazadan olamiz

    if not zayavka:  # agar zayavka topilmasa
        return {"ok": False, "xabar": "Bu zayavka topilmadi."}

    if zayavka.get("biriktirilgan_xodim_id") != xodim["id"]:  # faqat mijozni qabul qilgan xodimning o'zi tugata oladi
        return {"ok": False, "xabar": "Bu sizning mijozingiz emas."}

    # MAJBURIY tekshiruv: kamida 1 ta yo'nalish (ZUB/Buxgalteriya/UNF) tanlangan bo'lishi shart
    yonalishlar = db.zayavka_yonalishlari(zayavka)
    if not yonalishlar:
        return {"ok": False, "xabar": "Avval ZUB / Buxgalteriya / UNF dan kamida bittasini tanlang."}

    # MUHIM: bu yerda oldin "o'qib-keyin-yozish" usuli ishlatilgan edi — "Yakunlash" tugmasi
    # tez-tez (bir necha marta ketma-ket) bosilsa, mijozga bir necha marta baholash so'rovi
    # ketib qolishi (poyga holati) mumkin edi. Endi bitta ATOMIK bazaviy so'rov orqali —
    # FAQAT BIRINCHI urinish haqiqiy yakunlash hisoblanadi, qolganlari hech narsa qilmaydi
    muvaffaqiyatli = db.zayavkani_atomik_tugat(zayavka_id, xodim["id"])
    if not muvaffaqiyatli:
        return {"ok": False, "xabar": "Bu zayavka allaqachon yakunlangan yoki sizning mijozingiz emas."}

    # xodimni yana "bosh" holatiga qaytaramiz
    db.xodim_holatini_yangila(xodim["id"], "bosh", None)

    # endi mijozga baholash so'rovini yuboramiz (1-5 yulduzcha, majburiy)
    baholash_sorovini_yubor(zayavka, xodim)

    # guruhdagi eng oxirgi xabarni yangilaymiz — ENDI TUGMASIZ (xodim faqat Mini App orqali ishlaydi)
    if zayavka.get("oxirgi_tag_xabar_id"):
        tg.xabar_tahrirla(
            zayavka["guruh_chat_id"],
            zayavka["oxirgi_tag_xabar_id"],
            f"☑️ Consultatsiya yakunlandi ({xodim['ism_familiya']})."
        )

    # endi xodim bo'shadi — navbatda kutayotgan mijoz bormi tekshiramiz
    keyingi = db.keyingi_navbatdagi_zayavka()
    if keyingi:  # agar navbatda kimdir bo'lsa
        xodimlarni_taklif_qil(keyingi)  # o'sha mijoz uchun taklif jarayonini qayta ishga tushiramiz

    return {"ok": True, "xabar": "Yakunlandi."}


def zayavkani_javob_bermadi_deb_belgila(xodim, zayavka_id):
    # xodim "Telefonni ko'tarmadi" tugmasini bosganda shu yerga tushadi.
    # 1-2 marta bosilganda — mijozga eslatma boradi, zayavka "qayta_aloqa" holatiga o'tadi (xodim BO'SHAYDI,
    # boshqa mijozga o'tishi mumkin), va shu xodim keyinroq "Qabul qilish"ni yana bosishi kerak.
    # 3-marta (QONGIROQ_URINISH_MAKS'ga yetganda) — mijozga YAKUNIY xabar boradi, zayavka butunlay yopiladi.
    if xodim.get("rol") == "owner":  # "owner" hech narsani o'zgartira olmaydi
        return {"ok": False, "xabar": "Sizda bu amalni bajarish huquqi yo'q (faqat kuzatish)."}

    zayavka = db.zayavka_id_orqali(zayavka_id)
    if not zayavka:
        return {"ok": False, "xabar": "Bu zayavka topilmadi."}
    if zayavka.get("holat") != "jarayonda":  # faqat hozir gaplashilayotgan zayavka uchun ishlaydi
        return {"ok": False, "xabar": "Bu mijoz hozir jarayonda emas."}
    if zayavka.get("biriktirilgan_xodim_id") != xodim["id"]:  # faqat o'zining mijozi uchun
        return {"ok": False, "xabar": "Bu sizning mijozingiz emas."}

    mijoz = db.mijoz_id_orqali(zayavka["mijoz_id"])
    if not mijoz:
        return {"ok": False, "xabar": "Mijoz topilmadi."}

    yangi_son = (zayavka.get("qongiroq_soni") or 0) + 1  # bu safargi urinish tartib raqami
    db.zayavkani_yangila(zayavka_id, qongiroq_soni=yangi_son)

    if yangi_son < QONGIROQ_URINISH_MAKS:  # hali qayta urinish uchun imkoniyat bor
        matn = (
            "🇺🇿 Hurmatli mijoz, sizga qo'ng'iroq qildik, lekin javob bermadingiz.\n"
            "Iltimos, keyingi safar qo'ng'iroq qilganimizda ko'taring.\n\n"
            "🇷🇺 Уважаемый клиент, мы вам звонили, но вы не ответили.\n"
            "Пожалуйста, в следующий раз, когда мы позвоним, ответьте на звонок."
        )
        shaxsiy_yoki_ogohlantirish_yubor(mijoz, zayavka["guruh_chat_id"], zayavka.get("mijoz_xabar_id"), matn)

        # zayavkani "qayta aloqa" holatiga o'tkazamiz — xodim endi BO'SHAYDI (boshqa mijozga o'tishi mumkin),
        # lekin bu mijoz "Qayta aloqaga chiqish" bo'limida turaveradi, xodim tayyor bo'lganda yana qabul qiladi
        db.zayavkani_yangila(zayavka_id, holat="qayta_aloqa")
        db.xodim_holatini_yangila(xodim["id"], "bosh", None)

        # guruhdagi eng oxirgi xabarni yangilaymiz — ENDI TUGMASIZ (xodim Mini App'dagi
        # "Qayta aloqaga chiqish" bo'limidan qayta qabul qiladi)
        if zayavka.get("oxirgi_tag_xabar_id"):
            tg.xabar_tahrirla(
                zayavka["guruh_chat_id"],
                zayavka["oxirgi_tag_xabar_id"],
                f"📵 Mijoz javob bermadi ({yangi_son}/{QONGIROQ_URINISH_MAKS}). "
                f"<b>{xodim['ism_familiya']}</b> Mini App'dan qayta bog'lanishi mumkin."
            )

        keyingi = db.keyingi_navbatdagi_zayavka()  # xodim bo'shagani uchun navbatdagi mijozga o'tishi mumkin
        if keyingi:
            xodimlarni_taklif_qil(keyingi)

        return {
            "ok": True,
            "yopildimi": False,
            "urinish": yangi_son,
            "xabar": f"{yangi_son}/{QONGIROQ_URINISH_MAKS} — mijozga eslatma yuborildi. \"Qayta aloqaga chiqish\"ga o'tdi."
        }

    # QONGIROQ_URINISH_MAKSga yetdi (3-marta) — yakuniy xabar va zayavkani butunlay yopish
    matn = (
        "🇺🇿 Hurmatli mijoz, biz siz bilan bog'lanishga bir necha marta urindik, lekin javob bermadingiz.\n"
        "Xizmatimizdan foydalanish uchun, iltimos, qaytadan ma'lumotingizni qoldiring.\n\n"
        "🇷🇺 Уважаемый клиент, мы несколько раз пытались с вами связаться, но вы не ответили.\n"
        "Чтобы воспользоваться нашей услугой, пожалуйста, отправьте свои данные заново."
    )
    shaxsiy_yoki_ogohlantirish_yubor(mijoz, zayavka["guruh_chat_id"], zayavka.get("mijoz_xabar_id"), matn)

    # zayavkani yopamiz (alohida holat — "tugallandi" bilan aralashib ketmasin, statistikada alohida sanaladi)
    db.zayavkani_yangila(zayavka_id, holat="javob_bermadi", tugallangan_vaqt=db.hozir().isoformat())
    db.xodim_holatini_yangila(xodim["id"], "bosh", None)  # xodim endi bo'sh

    # guruhdagi eng oxirgi xabarni yangilaymiz
    if zayavka.get("oxirgi_tag_xabar_id"):
        tg.xabar_tahrirla(
            zayavka["guruh_chat_id"],
            zayavka["oxirgi_tag_xabar_id"],
            f"📵 Mijoz {QONGIROQ_URINISH_MAKS} marta javob bermadi — zayavka yopildi ({xodim['ism_familiya']})."
        )

    # navbatda kutayotgan boshqa mijoz bormi tekshiramiz (xuddi oddiy yakunlashdagidek)
    keyingi = db.keyingi_navbatdagi_zayavka()
    if keyingi:
        xodimlarni_taklif_qil(keyingi)

    return {"ok": True, "yopildimi": True, "xabar": "Mijoz bilan bog'lanib bo'lmadi, zayavka yopildi."}


def zayavkani_qayta_qabul_qil(xodim, zayavka_id):
    # "Qayta aloqaga chiqish" bo'limidagi mijozni xodim yana "Qabul qilish" bosganda shu yerga tushadi —
    # bu deyarli oddiy qabul qilish kabi, faqat zayavka "navbatda" emas, "qayta_aloqa" holatidan keladi
    if xodim.get("rol") == "owner":  # "owner" hech narsani o'zgartira olmaydi
        return {"ok": False, "xabar": "Sizda bu amalni bajarish huquqi yo'q (faqat kuzatish)."}
    if xodim.get("holat") == "band":  # hozir boshqa mijoz bilan band bo'lsa, ikkalasini bir vaqtda ololmaydi
        return {"ok": False, "xabar": "Siz hozir boshqa mijoz bilan bandsiz."}

    zayavka = db.zayavka_id_orqali(zayavka_id)
    if not zayavka:
        return {"ok": False, "xabar": "Bu zayavka topilmadi."}
    if zayavka.get("holat") != "qayta_aloqa":  # boshqa xodim ulgurib olgan yoki allaqachon yopilgan bo'lishi mumkin
        return {"ok": False, "xabar": "Bu mijoz endi bu bo'limda emas."}
    if zayavka.get("biriktirilgan_xodim_id") != xodim["id"]:  # faqat avval mas'ul bo'lgan xodim qayta qabul qiladi
        return {"ok": False, "xabar": "Bu sizning mijozingiz emas."}

    db.zayavkani_yangila(zayavka_id, holat="jarayonda", jarayon_boshlangan_vaqt=db.hozir().isoformat())
    db.xodim_holatini_yangila(xodim["id"], "band", zayavka_id)

    # guruhdagi eng oxirgi xabarni yangilaymiz — ENDI TUGMASIZ
    if zayavka.get("oxirgi_tag_xabar_id"):
        tg.xabar_tahrirla(
            zayavka["guruh_chat_id"],
            zayavka["oxirgi_tag_xabar_id"],
            f"✅ Ushbu mijozni <b>{xodim['ism_familiya']}</b> qayta qabul qildi."
        )

    return {"ok": True, "xabar": "Qabul qilindi, omad!"}


def baholash_sorovini_yubor(zayavka, xodim):
    # consultatsiya tugagach, mijozga "xizmatimizni baholang" so'rovini yuboradi (1-5 yulduzcha, majburiy)
    mijoz = db.mijoz_id_orqali(zayavka["mijoz_id"])
    if not mijoz:  # bo'lishi shart emas, lekin xavfsizlik uchun tekshiramiz
        return

    baholash = db.baholash_yarat(zayavka["id"], mijoz["id"], xodim["id"])  # yangi "kutilmoqda" yozuv

    matn = (
        "🇺🇿 Hurmatli mijoz! Consultatsiya yakunlandi.\n"
        "Iltimos, xizmatimizni baholang (1 dan 5 yulduzgacha):\n\n"
        "🇷🇺 Уважаемый клиент! Консультация завершена.\n"
        "Пожалуйста, оцените наш сервис (от 1 до 5 звёзд):"
    )

    # AVVAL lichkaga urinamiz; bo'lmasa — guruhga faqat qisqa (mazmunsiz) eslatma ketadi
    natija = tg.xabar_yubor(mijoz["telegram_id"], matn, tugmalar=tg.baholash_klaviaturasi(baholash["id"]))

    if natija.get("ok"):  # agar lichkaga muvaffaqiyatli yuborilgan bo'lsa
        db.baholashni_yangila(
            baholash["id"],
            chat_id=mijoz["telegram_id"],
            xabar_id=natija["result"]["message_id"]
        )
    else:  # lichkaga yuborib bo'lmasa (mijoz hali botni "start" qilmagan)
        # DIQQAT: bu yerda matnni oddiy "kutayotgan_xabar" sifatida saqlamaymiz (chunki bu yerda
        # yulduzcha TUGMALARI ham kerak, oddiy matn yetarli emas). Buning o'rniga, mijoz keyinroq
        # "start" bosganda, shaxsiy_chatni_boshqar ichida ushbu "kutilmoqda va hali yuborilmagan"
        # (chat_id=None) baholashni o'zi avtomatik topib, to'liq (tugmalari bilan) qayta yuboradi.
        tg.xabar_yubor(
            zayavka["guruh_chat_id"],
            "🔔 Sizga botimizdan shaxsiy (lichka) xabar bor — pastdagi tugmani bosib, "
            "botning shaxsiy chatini oching, so'ng ochilgan oynada Telegram ko'rsatadigan "
            "<b>START</b> tugmasini bosing — xabar avtomatik yetkaziladi.",
            reply_to=zayavka.get("mijoz_xabar_id"),
            tugmalar=[[{"text": "💬 Botni ochish", "url": f"https://t.me/{BOT_USERNAME}?start=1"}]]
        )


def baholash_javobini_qayta_ishla(callback, baholash_id, yulduz):
    # mijoz yulduzcha (1-5) bosganda shu yerga tushadi
    callback_id = callback.get("id")
    baholash = db.baholash_id_orqali(baholash_id)

    if not baholash:  # baholash yozuvi topilmasa
        tg.callback_javob(callback_id, "Bu so'rov topilmadi.", ogohlantirish=True)
        return

    # MUHIM: bu yerda oldin "o'qib-keyin-yozish" (read-then-write) usuli ishlatilgan edi — bu esa
    # mijoz tez-tez (yoki tizim sekinlashib, bilmasdan) bir necha marta bossa, HAMMASI hisoblanib
    # ketishi mumkin bo'lgan "poyga holati" (race condition) xatosiga olib kelardi.
    # Endi bitta ATOMIK bazaviy so'rov orqali — faqat "kutilmoqda" holatidagi yozuvgina yangilanadi,
    # shuning uchun necha marta bosilishidan qat'iy nazar, FAQAT BIRINCHISI hisoblanadi
    birinchi_martami = db.baholashni_birinchi_marta_belgila(baholash_id, yulduz)

    if not birinchi_martami:  # agar bu birinchi marta bo'lmasa (allaqachon baholangan)
        tg.callback_javob(callback_id, "Siz allaqachon baholagansiz.", ogohlantirish=True)
        return

    # xabarni tahrirlab, rahmat va ixtiyoriy izoh so'raymiz
    xabar_obyekti = callback.get("message", {})
    tg.xabar_tahrirla(
        xabar_obyekti.get("chat", {}).get("id"),
        xabar_obyekti.get("message_id"),
        f"Bahoyingiz: {'⭐' * yulduz}\n\n"
        f"🇺🇿 Rahmat! Agar qo'shimcha izohingiz bo'lsa, shu yerga yozib qoldirishingiz mumkin (ixtiyoriy).\n\n"
        f"🇷🇺 Спасибо! Если у вас есть комментарий, вы можете написать его здесь (по желанию)."
    )
    tg.callback_javob(callback_id, "Rahmat!")
