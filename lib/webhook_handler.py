# Bu fayl Telegramdan kelgan HAR BIR yangilanishni (xabar, tugma bosish) qayta ishlaydi
# Bu oddiy Python funksiyalari to'plami — FastAPI'ning o'zi bu yerda yo'q,
# uni faqat api/index.py chaqiradi (shu tarzda Vercel'ning yangi talabiga moslashadi)

import html  # kompaniya nomi kabi matnlarni Telegram HTML xabariga xavfsiz qo'yish uchun
from lib import db  # ma'lumotlar bazasi funksiyalari
from lib import telegram as tg  # Telegramga xabar yuborish funksiyalari
from lib import sheets  # Google Sheets'dagi mijozlar bazasini tekshirish funksiyasi
from lib.logic import malumot_toliqmi, shubhali_raqamlarni_top  # INN/telefon tekshiruvchi funksiyalar
from lib.config import (
    SUPPORT_GROUP_IDLAR, SHARTNOMA_XODIM_NICK, SHARTNOMA_XODIM_TEL, APP_URL,
    MUMKIN_YONALISHLAR, QONGIROQ_URINISH_MAKS, BOT_USERNAME
)


async def yangilanishni_qayta_ishla(malumot):
    # Telegramdan kelgan bitta "update" obyektini turiga qarab tegishli funksiyaga yo'naltiradi
    if "message" in malumot:  # agar bu oddiy xabar bo'lsa (mijoz yoki xodim yozgan)
        await xabarni_qayta_ishla(malumot["message"])
    elif "edited_message" in malumot:  # agar mijoz o'zining OLDINGI xabarini TAHRIRLAGAN bo'lsa
        await tahrirlangan_xabarni_qayta_ishla(malumot["edited_message"])
    elif "callback_query" in malumot:  # agar bu tugma bosilishi bo'lsa (xodim tugma bosdi)
        await tugmani_qayta_ishla(malumot["callback_query"])


async def xabarni_qayta_ishla(xabar):
    chat = xabar.get("chat", {})  # xabar yuborilgan chat haqida to'liq ma'lumot
    chat_id = chat.get("id")  # chat IDsi
    chat_turi = chat.get("type")  # "private" (shaxsiy) yoki "group"/"supergroup" (guruh)

    if chat_turi == "private":  # agar bu botning SHAXSIY chatida yozilgan bo'lsa (guruh emas)
        shaxsiy_chatni_boshqar(xabar)  # alohida funksiyaga uzatamiz (mijoz/xodimni farqlash uchun)
        return  # guruh mantig'iga o'tmaymiz

    # TASHXIS UCHUN: har bir (guruhdagi) xabarni albatta logga yozamiz — shunda "bizning
    # guruhlarimiz emas" deb sukut saqlab tashlab yuborilayotgan holatlar ham ko'rinadi
    print(f"Guruh xabari: chat_id={chat_id} (kutilgan SUPPORT_GROUP_IDLAR={SUPPORT_GROUP_IDLAR}), "
          f"matn={xabar.get('text', '')!r}")

    # faqat bizning support guruh(lar)imizdagi xabarlarni ko'rib chiqamiz (bir nechta guruh bo'lishi mumkin)
    if chat_id not in SUPPORT_GROUP_IDLAR:  # agar bu bizning guruhlarimizdan biri bo'lmasa
        print(f"E'TIBORSIZ QOLDIRILDI: chat_id mos kelmadi ({chat_id} ro'yxatda yo'q: {SUPPORT_GROUP_IDLAR})")
        return  # e'tiborsiz qoldiramiz

    yuboruvchi = xabar.get("from", {})  # xabarni kim yuborgani haqida ma'lumot
    yuboruvchi_id = yuboruvchi.get("id")  # yuboruvchining Telegram IDsi
    matn = xabar.get("text", "")  # xabarning matni

    if not matn:  # agar xabarda matn bo'lmasa (masalan rasm yoki stiker bo'lsa)
        return  # hozircha bunday xabarlarni e'tiborsiz qoldiramiz

    # MUHIM: agar mijoz shunchaki biror ODAMGA (masalan xodimga, skrinshot yoki tushunarsiz joyni
    # so'rab) TO'G'RIDAN-TO'G'RI javob (reply) yozayotgan bo'lsa — bu YANGI support so'rovi emas,
    # oddiy suhbat. Botni bunga aralashtirmaymiz. FARQ: agar bu BOTNING O'ZINING xabariga
    # (masalan "INN va telefon raqamingizni yuboring" degan so'rovimizga) javob bo'lsa — bu odatiy,
    # kutilgan holat, shuning uchun bunday holatda jarayonni davom ettiramiz
    javob_berilgan_xabar = xabar.get("reply_to_message")
    if javob_berilgan_xabar and not javob_berilgan_xabar.get("from", {}).get("is_bot"):
        print("E'TIBORSIZ QOLDIRILDI: xabar odamning o'ziga (botga emas) reply qilingan")
        return

    # xuddi shunday: agar xabarda kimnidir @ bilan belgilab chaqirish (mention) bo'lsa — bu ham
    # to'g'ridan-to'g'ri kimgadir qaratilgan xabar, umumiy support so'rovi emas
    mentionlar_bormi = any(e.get("type") in ("mention", "text_mention") for e in xabar.get("entities", []))
    if mentionlar_bormi:
        print("E'TIBORSIZ QOLDIRILDI: xabarda @belgilash (mention) bor")
        return

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
        xabarlar = zayavkaning_xabarlari(zayavka)  # shu zayavkadagi barcha xabarlar (ID va matn bilan)
        xabarlar.append({"id": xabar.get("message_id"), "t": matn})
        yangi_matn = "\n".join(x["t"] for x in xabarlar)
        db.zayavka_matnini_yangila(zayavka["id"], yangi_matn, xabarlar)
        zayavka["matn"] = yangi_matn  # keyingi tekshiruv uchun mahalliy nusxasini ham yangilaymiz
        zayavka["xabarlar"] = xabarlar
    else:  # aks holda yangi zayavka ochamiz
        zayavka = db.zayavka_yarat(mijoz["id"], chat_id, xabar.get("message_id"), matn)

    # endi INN/telefonni va shartnomani tekshirib, zayavkani kerakli holatga o'tkazamiz
    zayavkani_tekshir(zayavka, mijoz, xabar, chat_id)


def zayavkaning_xabarlari(zayavka):
    # zayavkadagi xabarlar ro'yxatini [{"id": xabar_id, "t": matn}, ...] ko'rinishida qaytaradi.
    # Eski zayavkalarda (ro'yxat saqlanmagan bo'lsa) butun matnni bitta xabar deb olamiz
    xabarlar = [dict(x) for x in (zayavka.get("xabarlar") or [])]
    if not xabarlar and zayavka.get("matn"):
        xabarlar = [{"id": zayavka.get("mijoz_xabar_id"), "t": zayavka["matn"]}]
    return xabarlar


# mijoz zayavkasi to'liq (INN + telefon) va shartnomasi faol bo'lganda guruhda shu xabar yuboriladi
RASMIY_QABUL_XABARI = (
    "🇺🇿 Assalomu alaykum, hurmatli mijoz! Murojaatingiz qabul qilindi.\n"
    "Yaqin 15-20 daqiqa ichida xodimlarimiz siz bilan bog'lanadi.\n\n"
    "🇷🇺 Здравствуйте, уважаемый клиент! Ваше обращение принято.\n"
    "В течение 15–20 минут наши сотрудники свяжутся с вами."
)


# GURUH SIYOSATI: mijoz guruhida status xabari FAQAT BITTA va u faqat IKKI holatdan o'tadi:
#   1) "Assalomu alaykum... xodimlarimiz siz bilan bog'lanadi"   (zayavka to'liq kelganda)
#   2) "☑️ <xodim> consultatsiya berdi"                          (xodim yakunlaganda — xabar tahrirlanadi)
# Boshqa har qanday holat (kim qabul qilgani, kutish rejimi, band/bo'sh, qayta aloqa, javob bermadi...) guruhda
# ko'rinmaydi — ularni faqat owner/super_user Mini App'da ko'radi. Mijozga kerak xabarlar (masalan 20 daqiqadan
# keyingi uzr, shartnoma yo'qligi) esa uning SHAXSIY chatiga (botga) yuboriladi
def guruh_statusini_yangila(zayavka, status_matni):
    # guruhdagi rasmiy xabarni (mijozga yuborilgan) yangi status bilan TAHRIRLAYDI — yangi xabar yozmaydi.
    # Xabar topilmasa yoki Telegram tahrirga ruxsat bermasa, asosiy jarayon (qabul/yakunlash) to'xtamaydi
    xabar_id = zayavka.get("oxirgi_tag_xabar_id")
    if not xabar_id:  # eski zayavka — rasmiy xabar ID'si saqlanmagan
        return
    try:
        natija = tg.xabar_tahrirla(zayavka["guruh_chat_id"], xabar_id, status_matni)
        if not natija.get("ok"):
            print(f"Guruh statusini yangilab bo'lmadi: {natija.get('description')}")
    except Exception as xato:
        print(f"Guruh statusini yangilashda xatolik: {xato}")


def yakun_status_matni(xodim_ismi):
    ism = html.escape(xodim_ismi)
    return (
        f"☑️ <b>{ism}</b> consultatsiya berdi. Rahmat!\n\n"
        f"☑️ <b>{ism}</b> провёл(а) консультацию. Спасибо!"
    )


def malumot_yetarli_emas_xabari(matn, chat_id, javob_xabar_id):
    # INN/telefon to'liq bo'lmaganda mijozga nima qilish kerakligini aniq yozib yuboradi
    shubhali = shubhali_raqamlarni_top(matn)  # "deyarli to'g'ri" raqamlar bormi tekshiramiz

    if shubhali:  # agar mijoz yozgan raqamlardan biri 9 xonaga yaqin, lekin noto'g'ri bo'lsa
        # bu holatda aniq QAYSI raqamda xato borligini ko'rsatib, umumiy xabarni takrorlamaymiz
        royxat = ", ".join(f"«{r}» ({len(r)} xonali)" for r in shubhali)  # masalan: «87687876» (8 xonali)
        tg.xabar_yubor(
            chat_id,
            f"🇺🇿 Diqqat: {royxat} raqamingizda xatolik bo'lishi mumkin — "
            f"INN va telefon raqami <b>aynan 9 xonali</b> bo'lishi kerak.\n"
            f"Iltimos, tekshirib, xabaringizni <b>tahrirlang</b> yoki <b>yangi xabar</b> yozing.\n\n"
            f"🇷🇺 Внимание: возможно, в номере {royxat} есть ошибка — "
            f"ИНН и номер телефона должны состоять <b>ровно из 9 цифр</b>.\n"
            f"Пожалуйста, проверьте и <b>отредактируйте</b> сообщение или отправьте <b>новое</b>.",
            reply_to=javob_xabar_id
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
            reply_to=javob_xabar_id
        )


def zayavkani_tekshir(zayavka, mijoz, xabar, chat_id):
    # zayavka matni bo'yicha INN/telefonni, so'ng shartnomani tekshiradi va zayavkani kerakli holatga
    # o'tkazadi. Mijozning YANGI xabari ham, TAHRIRLANGAN xabari ham aynan shu yerdan o'tadi.
    # xabar — mijozning (yangi yoki tahrirlangan) xabari: bot javobini shu xabarga reply qilib yuboradi
    javob_xabar_id = xabar.get("message_id")

    # endi INN va telefon (ikkalasi ham 9 xonali raqam) berilgan-berilmaganini tekshiramiz
    toliqmi, raqamlar = malumot_toliqmi(zayavka["matn"])

    if not toliqmi:  # agar hali ma'lumot yetarli bo'lmasa
        malumot_yetarli_emas_xabari(zayavka["matn"], chat_id, javob_xabar_id)
        return  # mijozdan ma'lumot kutamiz

    # ma'lumot to'liq bo'lsa — mijozning INN/telefonini bazaga yozamiz (birinchi ikkita topilgan raqam sifatida)
    db.mijoz_malumotini_yangila(mijoz["id"], raqamlar[0], raqamlar[1])

    # ENDI eng muhim tekshiruv: shu INN bo'yicha amaldagi support shartnomasi bormi?
    # (Google Sheets'dagi "Ligotniy" va "Platniy" jadvallaridan tekshiramiz)
    shartnoma = sheets.mijoz_holati(raqamlar[0])  # raqamlar[0] — INN sifatida qabul qilingan raqam

    # MUHIM: INN va kompaniya nomini ZAYAVKANING O'ZIGA yozamiz (mijozning umumiy yozuviga emas) —
    # shunda agar shu odam keyinroq BOSHQA INN bilan murojaat qilsa, bu eski zayavka o'zining
    # haqiqiy (o'sha paytdagi) kompaniyasini saqlab qoladi
    kompaniya_nomi = shartnoma.get("kompaniya_nomi")
    db.zayavkani_yangila(zayavka["id"], inn=raqamlar[0], kompaniya_nomi=kompaniya_nomi)

    if kompaniya_nomi:  # agar Google Sheets'da kompaniya nomi topilgan bo'lsa
        # mijoz yozuviga ham "oxirgi ma'lum kompaniya" sifatida saqlab qo'yamiz (ixtiyoriy, qulaylik uchun)
        db.mijoz_kompaniyasini_yangila(mijoz["id"], kompaniya_nomi)

    if shartnoma["holat"] != "faol":  # agar shartnoma umuman topilmasa yoki muddati o'tgan bo'lsa
        # zayavka FAQAT hali xodim qo'liga o'tmagan bo'lsa "shartnoma_yoq" bo'ladi (poyga holatidan himoya)
        db.zayavkani_shartli_yangila(
            zayavka["id"], ["malumot_kutilmoqda", "navbatda", "shartnoma_yoq"], holat="shartnoma_yoq"
        )
        shartnoma_yoq_xabar_yubor(mijoz, xabar, chat_id, shartnoma["holat"])
        return  # xodimlarni chaqirmasdan, jarayonni shu yerda to'xtatamiz

    zayavkani_navbatga_qoy(zayavka, kompaniya_nomi, chat_id, javob_xabar_id)


def zayavkani_navbatga_qoy(zayavka, kompaniya_nomi, chat_id, javob_xabar_id):
    # zayavkani navbatga qo'yadi, mijozga rasmiy xabar yuboradi va bo'sh xodimlarga SHAXSIY bildirishnoma beradi.
    # Guruhda xodimlar tag QILINMAYDI — ular zayavkani Mini App'da ko'radi
    if not db.zayavkani_atomik_navbatga_qoy(zayavka["id"]):
        return False  # zayavka allaqachon navbatda (yoki xodim qo'lida) — qayta xabar yubormaymiz

    # 1) mijozga guruhda rasmiy xabar (uning xabariga reply qilib). Xabar ID'sini saqlab qo'yamiz —
    # xodim qabul qilganda/yakunlaganda shu xabarning O'ZI tahrirlanib, status yangilanadi (yangi xabar yozilmaydi)
    natija = tg.xabar_yubor(chat_id, RASMIY_QABUL_XABARI, reply_to=javob_xabar_id)
    if natija.get("ok"):
        db.zayavkani_yangila(zayavka["id"], oxirgi_tag_xabar_id=natija["result"]["message_id"])

    # 2) hozir bo'sh turgan xodimlarga shaxsiy bildirishnoma (band xodimlar o'z ishi tugagach xabar oladi)
    matn = "🆕 <b>Yangi mijoz murojaati!</b>\n"
    if kompaniya_nomi:
        matn += f"🏢 {html.escape(kompaniya_nomi)}\n"
    matn += "Qabul qilish uchun Ish panelini oching 👇"
    tg.xodimlarga_shaxsiy_xabar(db.bosh_xodimlar(), matn)
    return True


def navbat_haqida_xodimga_bildir(xodim):
    # xodim bo'shagach (yakunladi yoki "javob bermadi" bosdi), navbatda mijoz kutayotgan bo'lsa —
    # shu xodimga shaxsiy eslatma yuboradi (guruhga hech narsa yozilmaydi)
    tg.xodimlarga_shaxsiy_xabar(
        [xodim],
        "🕐 <b>Navbatda mijoz kutyapti.</b>\nQabul qilish uchun Ish panelini oching 👇"
    )


async def tahrirlangan_xabarni_qayta_ishla(xabar):
    # mijoz guruhdagi o'zining OLDINGI xabarini tahrirlaganda shu yerga tushadi (masalan INN yoki
    # telefon raqamidagi xatoni to'g'irlagan bo'lsa). Yangi xabar yozmasdan tuzatganini ham qabul qilamiz
    chat = xabar.get("chat", {})
    chat_id = chat.get("id")
    if chat.get("type") == "private" or chat_id not in SUPPORT_GROUP_IDLAR:
        return  # faqat bizning support guruh(lar)imizdagi tahrirlar ahamiyatli

    yangi_matn_xabari = xabar.get("text", "")
    if not yangi_matn_xabari:  # matnsiz (masalan rasm izohi) tahrirlarni e'tiborsiz qoldiramiz
        return

    xabar_id = xabar.get("message_id")
    mijoz = db.mijoz_topilsin(xabar.get("from", {}).get("id"))  # faqat qidiramiz, yangi mijoz yaratmaymiz
    if not mijoz:
        return  # bu odam bizda mijoz sifatida yo'q (masalan xodim yoki begona) — e'tiborsiz

    # tahrirlangan xabar mijozning qaysi zayavkasiga tegishli ekanini topamiz
    zayavka = None
    for z in db.mijozning_oxirgi_zayavkalari(mijoz["id"], 5):
        if z.get("guruh_chat_id") != chat_id:
            continue
        if z.get("mijoz_xabar_id") == xabar_id or any(x.get("id") == xabar_id for x in (z.get("xabarlar") or [])):
            zayavka = z
            break
    if not zayavka:
        print(f"Tahrirlangan xabar ({xabar_id}) hech bir zayavkaga tegishli emas — e'tiborsiz qoldirildi")
        return

    holat = zayavka.get("holat")
    if holat not in ("malumot_kutilmoqda", "shartnoma_yoq", "navbatda", "muddati_otdi", "jarayonda", "qayta_aloqa"):
        return  # tugallangan/yopilgan zayavkaning tarixini o'zgartirmaymiz

    # zayavkadagi shu xabarning matnini yangisiga ALMASHTIRAMIZ (eskisiga qo'shmaymiz)
    xabarlar = zayavkaning_xabarlari(zayavka)
    if any(x.get("id") == xabar_id for x in xabarlar):
        for x in xabarlar:
            if x.get("id") == xabar_id:
                x["t"] = yangi_matn_xabari
    else:  # eski zayavka (xabarlar ro'yxati saqlanmagan) — tahrirlangan xabarni yagona xabar deb olamiz
        xabarlar = [{"id": xabar_id, "t": yangi_matn_xabari}]
    yangi_matn = "\n".join(x["t"] for x in xabarlar)
    if yangi_matn == (zayavka.get("matn") or ""):
        return  # matn aslida o'zgarmagan (masalan faqat formatlash o'zgargan)

    toliqmi, raqamlar = malumot_toliqmi(yangi_matn)

    if holat == "malumot_kutilmoqda":  # hali ma'lumot yig'ilyapti — yangi xabardagidek to'liq tekshiramiz
        db.zayavka_matnini_yangila(zayavka["id"], yangi_matn, xabarlar)
        zayavka["matn"], zayavka["xabarlar"] = yangi_matn, xabarlar
        zayavkani_tekshir(zayavka, mijoz, xabar, chat_id)
        return

    # qolgan holatlarda tahrir zayavkani buzmasligi kerak: tahrirdan keyin ma'lumot to'liq bo'lmasa — e'tiborsiz
    if not toliqmi:
        return
    db.zayavka_matnini_yangila(zayavka["id"], yangi_matn, xabarlar)  # xodim kartasida yangi matn ko'rinsin
    zayavka["matn"], zayavka["xabarlar"] = yangi_matn, xabarlar

    # INN o'zgargan bo'lsa (shartnoma yo'q deb to'xtagan yoki navbatdagi zayavkada) — shartnomani qayta tekshiramiz
    if holat in ("shartnoma_yoq", "navbatda") and raqamlar[0] != (zayavka.get("inn") or ""):
        zayavkani_tekshir(zayavka, mijoz, xabar, chat_id)


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

    # DIQQAT: guruhga hech narsa yozilmaydi va statusda kim qabul qilgani ko'rsatilmaydi — bu faqat Mini App'da ko'rinadi

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

    # guruhdagi rasmiy xabar statusini yangilaymiz: "Consultatsiya yakunlandi"
    guruh_statusini_yangila(zayavka, yakun_status_matni(xodim["ism_familiya"]))

    # endi xodim bo'shadi — navbatda kutayotgan mijoz bormi tekshiramiz
    if db.keyingi_navbatdagi_zayavka():  # agar navbatda kimdir bo'lsa
        navbat_haqida_xodimga_bildir(xodim)  # faqat shu bo'shagan xodimga shaxsiy eslatma yuboramiz

    return {"ok": True, "xabar": "Yakunlandi."}


YANGI_USTUN_XABARI = ("Bazaga yangi ustunlar qo'shilmagan. Iltimos, MIGRATSIYA_kutish.sql faylini "
                      "Supabase SQL Editor'da bajaring.")


def zayavkani_kutishga_qoy(xodim, zayavka_id):
    # xodim mijoz bilan gaplashdi, lekin muammo hali hal bo'lmadi (masalan biror narsani tekshirish yoki
    # mijozdan hujjat kutish kerak) — "Kutish rejimi"ni yoqadi. Shu paytdan boshlab gaplashish vaqti
    # HISOBLANMAYDI, xodim esa bo'shaydi va boshqa mijozni qabul qila oladi
    if xodim.get("rol") == "owner":  # "owner" hech narsani o'zgartira olmaydi
        return {"ok": False, "xabar": "Sizda bu amalni bajarish huquqi yo'q (faqat kuzatish)."}

    zayavka = db.zayavka_id_orqali(zayavka_id)
    if not zayavka:
        return {"ok": False, "xabar": "Bu zayavka topilmadi."}
    if zayavka.get("holat") != "jarayonda":  # faqat hozir gaplashilayotgan zayavka uchun
        return {"ok": False, "xabar": "Bu mijoz hozir jarayonda emas."}
    if zayavka.get("biriktirilgan_xodim_id") != xodim["id"]:  # faqat o'zining mijozi uchun
        return {"ok": False, "xabar": "Bu sizning mijozingiz emas."}

    try:
        muvaffaqiyatli = db.zayavkani_atomik_kutishga_qoy(zayavka_id, xodim["id"])
    except Exception as xato:
        if "kutish_" in str(xato):  # migratsiya SQL'i hali bajarilmagan
            print("OGOHLANTIRISH: zayavkalar.kutish_* ustunlari topilmadi, MIGRATSIYA_kutish.sql'ni bajaring")
            return {"ok": False, "xabar": YANGI_USTUN_XABARI}
        raise
    if not muvaffaqiyatli:  # tugma qayta bosilgan yoki zayavka allaqachon boshqa holatga o'tgan
        return {"ok": False, "xabar": "Bu mijoz allaqachon kutish rejimida yoki yakunlangan."}

    # xodim BO'SHAYDI — boshqa mijozni qabul qila oladi
    db.xodim_holatini_yangila(xodim["id"], "bosh", None)

    # DIQQAT: guruhdagi status O'ZGARMAYDI ("... qabul qildi" bo'lib turaveradi) — kutish rejimi faqat Mini App'da ko'rinadi

    # xodim bo'shagani uchun, navbatda mijoz kutayotgan bo'lsa — shu xodimga eslatma yuboramiz
    if db.keyingi_navbatdagi_zayavka():
        navbat_haqida_xodimga_bildir(xodim)

    return {"ok": True, "xabar": "Kutish rejimi yoqildi. Vaqt hisoblanmaydi, siz bo'shadingiz."}


def zayavkani_kutishdan_davom_ettir(xodim, zayavka_id):
    # "Kutish rejimida" turgan mijozni xodim "Davom ettirish" bilan qaytaradi: zayavka yana "jarayonda"
    # bo'ladi, gaplashish vaqti qolgan joyidan davom etadi (kutishda o'tgan vaqt qo'shilmaydi)
    if xodim.get("rol") == "owner":
        return {"ok": False, "xabar": "Sizda bu amalni bajarish huquqi yo'q (faqat kuzatish)."}
    if xodim.get("holat") == "band":  # hozir boshqa mijoz bilan band bo'lsa, ikkalasini bir vaqtda ololmaydi
        return {"ok": False, "xabar": "Siz hozir boshqa mijoz bilan bandsiz. Avval uni yakunlang yoki kutishga qo'ying."}

    zayavka = db.zayavka_id_orqali(zayavka_id)
    if not zayavka:
        return {"ok": False, "xabar": "Bu zayavka topilmadi."}
    if zayavka.get("holat") != "kutish":
        return {"ok": False, "xabar": "Bu mijoz endi kutish rejimida emas."}
    if zayavka.get("biriktirilgan_xodim_id") != xodim["id"]:  # faqat avval mas'ul bo'lgan xodim davom ettiradi
        return {"ok": False, "xabar": "Bu sizning mijozingiz emas."}

    if not db.zayavkani_atomik_kutishdan_qaytar(zayavka, xodim["id"]):
        return {"ok": False, "xabar": "Bu mijoz endi kutish rejimida emas."}

    db.xodim_holatini_yangila(xodim["id"], "band", zayavka_id)

    # DIQQAT: guruhga hech narsa yozilmaydi — status allaqachon "... qabul qildi" turibdi

    return {"ok": True, "xabar": "Davom ettirildi. Vaqt qolgan joyidan hisoblanadi."}


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

        # DIQQAT: guruhga endi hech qanday qo'shimcha xabar yubormaymiz — bu holat allaqachon
        # Mini App'dagi "Qayta aloqaga chiqish" bo'limida to'liq ko'rinib turibdi

        if db.keyingi_navbatdagi_zayavka():  # xodim bo'shagani uchun navbatdagi mijozga o'tishi mumkin
            navbat_haqida_xodimga_bildir(xodim)

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

    # DIQQAT: guruhga endi hech qanday qo'shimcha xabar yubormaymiz — bu holat Mini App'dagi
    # "Javob bermadi" bo'limida to'liq ko'rinib turibdi

    # navbatda kutayotgan boshqa mijoz bormi tekshiramiz (xuddi oddiy yakunlashdagidek)
    if db.keyingi_navbatdagi_zayavka():
        navbat_haqida_xodimga_bildir(xodim)

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

    yangilanish = {"holat": "jarayonda", "jarayon_boshlangan_vaqt": db.hozir().isoformat()}
    if zayavka.get("kutish_jami_soniya"):  # vaqt hisobi qayta noldan boshlanadi — eski kutilgan soniyalar aralashmasin
        yangilanish["kutish_jami_soniya"] = 0
    db.zayavkani_yangila(zayavka_id, **yangilanish)
    db.xodim_holatini_yangila(xodim["id"], "band", zayavka_id)

    # DIQQAT: guruhga endi hech qanday qo'shimcha xabar yubormaymiz

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
