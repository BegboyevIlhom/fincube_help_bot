# Bu fayl "biznes-mantiq" deb ataladigan qismni saqlaydi:
# xabar ichidan 9 xonali raqamlarni topish (INN va telefon uchun)

import re  # matn ichidan raqamlarni qidirish uchun "regular expression" kutubxonasi

# "INN", "telefon" kabi so'zlar — bular ko'pincha ikkita raqamning orasida kelib,
# "bu yerda yangi raqam boshlanadi" degan tabiiy belgi vazifasini bajaradi (vergul bo'lmasa ham).
# DIQQAT: kirill yozuvidagi so'zlar ("инн", "стир", "тел", "телефон", "рақами") ham qo'shilgan —
# chunki ba'zi mijozlar kirill alifbosida yozadi
_KALIT_SOZLAR = re.compile(
    r"(?i)\b(?:inn|stir|telefon|tel|raqami|raqam|nomeri|nomer|phone|"
    r"инн|стир|телефон|тел|рақами|рақам|номери|номер)\b"
)

# Faqat "bu — aniq INN" deb ANIQ belgilaydigan so'zlar (telefon so'zlari bu yerga kirmaydi) —
# lotin va kirill ikkalasida ham
_INN_YORLIQ_SOZI = re.compile(r"(?i)\b(?:inn|stir|tin|инн|стир)\b")


def toqqiz_xonali_raqamlarni_top(matn):
    # matn — mijozdan kelgan xabar (yoki bir nechta xabarlarning yig'indisi)
    # natija — matn ichidan topilgan barcha 9 xonali raqamlar ro'yxati (masalan INN va telefon)

    if not matn:  # agar matn bo'sh bo'lsa
        return []  # bo'sh ro'yxat qaytaramiz

    natija = []  # topilgan 9 xonali raqamlarni shu yerga yig'amiz

    def raqamni_tekshir(parcha):
        # bitta matn parchasidan faqat raqamlarni qoldirib, 9 (yoki +998 bilan 12) xonali bo'lsa qo'shadi
        faqat_raqam = re.sub(r"\D", "", parcha)  # harf, bo'shliq, tire, qavs va h.k.ni olib tashlaymiz
        if len(faqat_raqam) == 9:  # aynan 9 ta raqam qolsa — bitta to'liq raqam (INN yoki telefon)
            natija.append(faqat_raqam)
            return True
        if len(faqat_raqam) == 12 and faqat_raqam.startswith("998"):  # +998 bilan yozilgan telefon
            natija.append(faqat_raqam[3:])
            return True
        return False

    # 1-BOSQICH: matnni vergul/nuqta-vergul (BO'SHLIQDAN OLDIN kelsa) yoki yangi qator bo'yicha bo'lamiz
    # (agar vergul so'z ICHIDA, bo'shliqsiz kelsa — masalan "435,435,567" — buni bitta raqam deb qoldiramiz)
    asosiy_boklar = re.split(r"[,;]\s+|\n+", matn)

    for bolak in asosiy_boklar:  # har bir asosiy bo'lakni tekshiramiz
        if raqamni_tekshir(bolak):  # agar bo'lakning O'ZI to'g'ridan-to'g'ri 9/12 xonali raqam bo'lib chiqsa
            continue  # keyingi bo'lakka o'tamiz, bu yetarli

        # 2-BOSQICH: bo'lak to'g'ridan-to'g'ri mos kelmasa, uni "INN", "telefon", "nomer" kabi
        # so'zlar bo'yicha kichikroq qismlarga bo'lib, har birini alohida tekshiramiz — bu VERGULSIZ
        # yozilgan, lekin so'zlar bilan ajratilgan holatlarni ("INN 908 543 234 telefon nomer 99 776 54 32")
        # to'g'ri aniqlash uchun kerak
        kichik_qismlar = _KALIT_SOZLAR.split(bolak)
        topildimi = False
        for qism in kichik_qismlar:
            if raqamni_tekshir(qism):
                topildimi = True

        if topildimi:  # agar 2-bosqichda kamida bitta raqam topilgan bo'lsa
            continue

        # 3-BOSQICH: hali ham hech narsa topilmasa, so'zlarga (bo'shliq bo'yicha) bo'lib, har birini tekshiramiz
        # (masalan tasodifan yakka holda kelgan 9 xonali raqamlarni ushlab qolish uchun)
        for soz in bolak.split():
            raqamni_tekshir(soz)

    # takrorlanmagan (bir xil bo'lmagan) raqamlarni qaytaramiz
    return list(dict.fromkeys(natija))  # dict.fromkeys tartibni saqlab, takrorlarni olib tashlaydi


def yorliqlangan_inn_ni_top(matn):
    # matn ichida "INN"/"ИНН"/"STIR" kabi so'zdan DARHOL keyin keladigan 9 xonali raqamni qidiradi.
    # Agar topilsa — bu mijoz xabarida QAYSI TARTIBDA yozilishidan qat'iy nazar (masalan telefon
    # birinchi, INN ikkinchi kelsa ham), ANIQ INN ekanini bildiradi
    if not matn:
        return None
    moslik = _INN_YORLIQ_SOZI.search(matn)
    if not moslik:  # agar matnda "INN" so'zi umuman bo'lmasa
        return None
    # so'zdan keyingi qismni olib (30 ta belgigacha), undan birinchi 9(+) xonali raqam guruhini izlaymiz
    keyingi_qism = matn[moslik.end():moslik.end() + 30]
    raqam_moslik = re.search(r"\d[\d\s\-()]{6,}\d|\d{9,}", keyingi_qism)
    if not raqam_moslik:
        return None
    faqat_raqam = re.sub(r"\D", "", raqam_moslik.group())
    return faqat_raqam if len(faqat_raqam) == 9 else None


def malumot_toliqmi(matn):
    # zayavka uchun kamida 2 ta har xil 9 xonali raqam (INN va telefon) topilgan-topilmaganini tekshiradi
    raqamlar = toqqiz_xonali_raqamlarni_top(matn)  # matn ichidan barcha 9 xonali raqamlarni topamiz

    # agar matnda "INN" so'zi bilan ANIQ belgilangan raqam bo'lsa — uni ro'yxatning BOSHIGA o'tkazamiz
    # (chunki qolgan kod har doim raqamlar[0]ni INN deb qabul qiladi — tartib emas, yorliq hal qiladi)
    yorliqli_inn = yorliqlangan_inn_ni_top(matn)
    if yorliqli_inn and yorliqli_inn in raqamlar and raqamlar[0] != yorliqli_inn:
        raqamlar = [yorliqli_inn] + [r for r in raqamlar if r != yorliqli_inn]

    return len(raqamlar) >= 2, raqamlar  # ikkitadan kam bo'lmasa "to'liq" deymiz, raqamlarni ham qaytaramiz


def shubhali_raqamlarni_top(matn):
    # "deyarli to'g'ri" (9 xonali BO'LISHI kerak edi, lekin bo'lmagan) raqamlarni topadi —
    # bu mijozga "aniq qaysi raqamda xato bor" deb ko'rsatish uchun ishlatiladi
    if not matn:
        return []

    natija = []  # topilgan shubhali (9 ham, 12 ham bo'lmagan) raqamlarni shu yerga yig'amiz

    def tekshir(parcha):
        faqat_raqam = re.sub(r"\D", "", parcha)  # parchadan faqat raqamlarni qoldiramiz
        # 7-8 yoki 10-11 xonali raqamlar — "deyarli 9 xonali" deb hisoblanadi (typo bo'lishi mumkin)
        if len(faqat_raqam) in (7, 8, 10, 11):
            natija.append(faqat_raqam)
            return True
        return False

    # xuddi asosiy funksiyadagi kabi, avval vergul/nuqta-vergul (bo'shliqdan oldin)/yangi qator bo'yicha bo'lamiz
    asosiy_boklar = re.split(r"[,;]\s+|\n+", matn)

    for bolak in asosiy_boklar:
        if tekshir(bolak):  # bo'lakning o'zi to'g'ridan-to'g'ri shubhali raqam bo'lsa
            continue
        # VERGULSIZ yozilgan holat ("INN 310260424 tel 90956864"): "INN", "tel" kabi so'zlar bo'yicha
        # bo'lib, har bir qismni alohida tekshiramiz (aks holda ikkala raqam birlashib ketib, xato topilmaydi)
        for qism in _KALIT_SOZLAR.split(bolak):
            tekshir(qism)

    return list(dict.fromkeys(natija))  # takrorlarni olib tashlab qaytaramiz
