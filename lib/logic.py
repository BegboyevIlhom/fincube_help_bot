# Bu fayl "biznes-mantiq" deb ataladigan qismni saqlaydi:
# xabar ichidan 9 xonali raqamlarni topish (INN va telefon uchun)

import re  # matn ichidan raqamlarni qidirish uchun "regular expression" kutubxonasi

_KALIT_SOZLAR = re.compile(
    r"(?i)\b(?:inn|stir|telefon|tel|raqami|raqam|nomeri|nomer|phone|"
    r"инн|стир|телефон|тел|рақами|рақам|номери|номер)\b"
)

_INN_YORLIQ_SOZI = re.compile(r"(?i)\b(?:inn|stir|tin|инн|стир)\b")

# Bitta "so'z" (bo'shliqlar bilan ajratilgan) FAQAT raqam/+/-/() belgilaridan iborat bo'lsa,
# u "raqam qismi" hisoblanadi. Agar so'zda bitta ham harf bo'lsa (masalan "1С", "2GIS"),
# bu so'z "raqam emas" deb hisoblanadi va qo'shni raqamlarga ASLO ulanib ketmaydi —
# shunday qilib "993808010 1С" deganda "1С" telefon raqamiga ulanib qolmaydi
# (1С — "1C" dasturi, FINCUBE mijozlari buni tez-tez eslatadi, shuning uchun bu muhim)
_RAQAM_SOZI = re.compile(r"^[+\d\-()]+$")


def _raqam_guruhlarini_top(matn):
    # matnni bo'shliq bo'yicha so'zlarga bo'lib, KETMA-KET kelgan "faqat raqam" so'zlarni
    # bitta guruh qilib birlashtiradi (masalan "90 123 45 67" -> bitta guruh).
    # Harf aralashgan so'z guruhni albatta to'xtatadi va o'zi hech qanday guruhga QO'SHILMAYDI
    if not matn:
        return []
    guruhlar = []
    joriy = []
    for soz in matn.split():
        if _RAQAM_SOZI.match(soz):
            joriy.append(soz)
        else:
            if joriy:
                guruhlar.append("".join(joriy))
                joriy = []
    if joriy:
        guruhlar.append("".join(joriy))
    return guruhlar


def _qismdan_raqamlarni_ajrat(qism):
    # bitta matn qismi (bolak yoki kichik_qism) ichidagi barcha 9/12(+998) xonali raqamlarni qaytaradi
    natija = []
    for guruh in _raqam_guruhlarini_top(qism):
        faqat_raqam = re.sub(r"\D", "", guruh)
        if len(faqat_raqam) == 9:
            natija.append(faqat_raqam)
        elif len(faqat_raqam) == 12 and faqat_raqam.startswith("998"):
            natija.append(faqat_raqam[3:])
    return natija


def toqqiz_xonali_raqamlarni_top(matn):
    # matn — mijozdan kelgan xabar (yoki bir nechta xabarlarning yig'indisi)
    # natija — matn ichidan topilgan barcha 9 xonali raqamlar ro'yxati (masalan INN va telefon)
    if not matn:
        return []

    natija = []
    # matnni vergul/nuqta-vergul (BO'SHLIQDAN OLDIN kelsa) yoki yangi qator bo'yicha bo'lamiz
    asosiy_boklar = re.split(r"[,;]\s+|\n+", matn)

    for bolak in asosiy_boklar:
        # "INN", "telefon" kabi so'zlar ko'rinishidagi yorliqlar atrofida ham to'g'ri ajratish uchun,
        # bolakni shu kalit so'zlar bo'yicha kichikroq qismlarga bo'lamiz (label bo'lmasa, bolakning o'zi qoladi)
        kichik_qismlar = _KALIT_SOZLAR.split(bolak)
        manba = kichik_qismlar if len(kichik_qismlar) > 1 else [bolak]
        for qism in manba:
            natija.extend(_qismdan_raqamlarni_ajrat(qism))

    # takrorlanmagan (bir xil bo'lmagan) raqamlarni qaytaramiz
    return list(dict.fromkeys(natija))  # dict.fromkeys tartibni saqlab, takrorlarni olib tashlaydi


def yorliqlangan_inn_ni_top(matn):
    # matn ichida "INN"/"ИНН"/"STIR" kabi so'zdan DARHOL keyin keladigan 9 xonali raqamni qidiradi.
    if not matn:
        return None
    moslik = _INN_YORLIQ_SOZI.search(matn)
    if not moslik:
        return None
    keyingi_qism = matn[moslik.end():moslik.end() + 30]
    topilganlar = _qismdan_raqamlarni_ajrat(keyingi_qism)
    return topilganlar[0] if topilganlar else None


def malumot_toliqmi(matn):
    # zayavka uchun kamida 2 ta har xil 9 xonali raqam (INN va telefon) topilgan-topilmaganini tekshiradi
    raqamlar = toqqiz_xonali_raqamlarni_top(matn)

    yorliqli_inn = yorliqlangan_inn_ni_top(matn)
    if yorliqli_inn and yorliqli_inn in raqamlar and raqamlar[0] != yorliqli_inn:
        raqamlar = [yorliqli_inn] + [r for r in raqamlar if r != yorliqli_inn]

    return len(raqamlar) >= 2, raqamlar


def shubhali_raqamlarni_top(matn):
    # "deyarli to'g'ri" (9 xonali BO'LISHI kerak edi, lekin bo'lmagan) raqamlarni topadi
    if not matn:
        return []

    natija = []
    asosiy_boklar = re.split(r"[,;]\s+|\n+", matn)

    for bolak in asosiy_boklar:
        kichik_qismlar = _KALIT_SOZLAR.split(bolak)
        manba = kichik_qismlar if len(kichik_qismlar) > 1 else [bolak]
        for qism in manba:
            for guruh in _raqam_guruhlarini_top(qism):
                faqat_raqam = re.sub(r"\D", "", guruh)
                if len(faqat_raqam) in (7, 8, 10, 11):
                    natija.append(faqat_raqam)

    return list(dict.fromkeys(natija))
