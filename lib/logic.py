# Bu fayl "biznes-mantiq" deb ataladigan qismni saqlaydi:
# xabar ichidan 9 xonali raqamlarni topish (INN va telefon uchun)

import re  # matn ichidan raqamlarni qidirish uchun "regular expression" kutubxonasi

# "INN", "telefon" kabi so'zlar — bular ko'pincha ikkita raqamning orasida kelib,
# "bu yerda yangi raqam boshlanadi" degan tabiiy belgi vazifasini bajaradi (vergul bo'lmasa ham)
_KALIT_SOZLAR = re.compile(r"(?i)\b(?:inn|stir|telefon|tel|raqami|raqam|nomeri|nomer|phone)\b")


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


def malumot_toliqmi(matn):
    # zayavka uchun kamida 2 ta har xil 9 xonali raqam (INN va telefon) topilgan-topilmaganini tekshiradi
    raqamlar = toqqiz_xonali_raqamlarni_top(matn)  # matn ichidan barcha 9 xonali raqamlarni topamiz
    return len(raqamlar) >= 2, raqamlar  # ikkitadan kam bo'lmasa "to'liq" deymiz, raqamlarni ham qaytaramiz


def shubhali_raqamlarni_top(matn):
    # "deyarli to'g'ri" (9 xonali BO'LISHI kerak edi, lekin bo'lmagan) raqamlarni topadi —
    # bu mijozga "aniq qaysi raqamda xato bor" deb ko'rsatish uchun ishlatiladi
    if not matn:
        return []

    natija = []  # topilgan shubhali (9 ham, 12 ham bo'lmagan) raqamlarni shu yerga yig'amiz
    # xuddi asosiy funksiyadagi kabi, avval vergul/nuqta-vergul (bo'shliqdan oldin)/yangi qator bo'yicha bo'lamiz
    asosiy_boklar = re.split(r"[,;]\s+|\n+", matn)

    for bolak in asosiy_boklar:
        faqat_raqam = re.sub(r"\D", "", bolak)  # bo'lakdan faqat raqamlarni qoldiramiz
        # 7-8 yoki 10-11 xonali raqamlar — "deyarli 9 xonali" deb hisoblanadi (typo bo'lishi mumkin)
        if len(faqat_raqam) in (7, 8, 10, 11):
            natija.append(faqat_raqam)

    return list(dict.fromkeys(natija))  # takrorlarni olib tashlab qaytaramiz
