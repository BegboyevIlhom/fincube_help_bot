# Bu fayl "biznes-mantiq" deb ataladigan qismni saqlaydi:
# xabar ichidan 9 xonali raqamlarni topish (INN va telefon uchun)

import re  # matn ichidan raqamlarni qidirish uchun "regular expression" kutubxonasi

_INN_YORLIQ_SOZI = re.compile(r"(?i)\b(?:inn|stir|tin|инн|стир)\b")

# Raqamlar orasida "bog'lovchi" (ajratuvchi, lekin raqamni UZMAYDIGAN) hisoblanadigan
# belgilar: bo'shliq, +, -, (, ), nuqta, qiyshiq chiziq, vergul. Shu belgilar orqali
# yozilgan raqamlar ("90 123 45 67", "304.462.751", "304/462/751", "+998-90-123-45-67")
# BITTA raqam deb hisoblanadi
_BOGLOVCHI_BELGI = re.compile(r"[\s+\-().,/]")

# Sana shaklidagi ketma-ketlikni ("20.12.2026", "20/12/2026") RAQAM deb QABUL QILMASLIK
# uchun — aks holda xabar ichida tasodifan aytilgan sana (masalan "shartnoma 20.12.2026
# gacha") INN/telefon qidiruvini chalg'itib, noto'g'ri ogohlantirishga olib kelishi mumkin
_SANA_SHAKLI = re.compile(r"^\d{1,2}[./]\d{1,2}[./]\d{2,4}$")


def _guruh_yaroqlimi(xom_guruh):
    # bo'sh yoki faqat bog'lovchi belgilardan iborat (hech qanday raqamsiz) guruhlarni,
    # shuningdek sana ko'rinishidagi guruhlarni RAQAM EMAS deb hisoblaymiz
    if not xom_guruh:
        return False
    tozalangan = xom_guruh.strip(" +-().,/")
    if not tozalangan or not any(belgi.isdigit() for belgi in tozalangan):
        return False
    if _SANA_SHAKLI.match(tozalangan):
        return False
    return True


def _raqam_guruhlarini_top(matn):
    # Matnni BELGI-BA-BELGI aylanib chiqadi (so'zlarga bo'lmasdan — shunday qilib
    # bo'shliqsiz yopishgan ikkita raqamni ham, masalan "304462751/901234567" yoki
    # "304462751,901234567", to'g'ri ajrata oladi).
    #
    # Qoida:
    #   - RAQAM uchrasa — joriy guruhga qo'shiladi; LEKIN agar joriy guruh ALLAQACHON
    #     aynan 9 ta raqamga yetgan bo'lsa, bu YANGI raqam boshlanayotganini bildiradi —
    #     eski guruh yakunlanadi va yangisi shu raqamdan boshlanadi. Shunday qilib
    #     "90 123 45 67" (hali 9 taga yetmagan) yoki "+998 90 123 45 67" (9 dan 12 gacha
    #     o'sadigan) kabi ATAYLAB guruhlangan YAGONA raqamlar buzilmaydi, lekin ikkita
    #     TO'LIQ, ortiqcha yopishgan raqam ("306724336977929193" yoki ".../...") to'g'ri
    #     ikkiga bo'linadi.
    #   - BOG'LOVCHI belgi (bo'shliq, +, -, ., /, (, ), vergul) uchrasa — joriy guruh
    #     davom etadi (raqam sonini oshirmaydi, faqat matnni saqlaydi).
    #   - Boshqa HAR QANDAY belgi (harf, ":", ";" va h.k.) uchrasa — bu "chegara":
    #     joriy guruh (agar yaroqli bo'lsa) yakunlanadi va hech qanday raqamga
    #     ULANMAYDI. Shu sabab "993808010 1С" deganda "1С" raqamga yopishib qolmaydi
    #     (1С — "1C" dasturi, FINCUBE mijozlari buni tez-tez eslatadi), xuddi shunday
    #     "tel;938535257" dagi "tel" so'zi ham raqamga ulanib ketmaydi
    if not matn:
        return []

    guruhlar = []
    joriy = ""  # xom matn (bog'lovchilar bilan birga)
    joriy_raqamlar = ""  # joriy guruhdagi FAQAT raqamlar (tezkor tekshirish uchun)

    for belgi in matn:
        if belgi.isdigit():
            # TO'XTATISH QOIDASI: agar joriy guruh aynan 9 ta raqamga yetgan bo'lsa VA bu
            # "998" bilan BOSHLANMAGAN bo'lsa — demak bu TO'LIQ, alohida 9 xonali raqam,
            # yangisi boshlanmoqda. Lekin "998" bilan boshlangan bo'lsa — hali 12 xonali
            # (+998) raqam bo'lish extimoli bor, shuning uchun 12 taga yetguncha davom
            # ettiramiz. 12 taga yetganda esa — har doim to'xtatamiz (bundan uzun bo'lishi
            # mumkin emas)
            toxtatish_kerak = (
                (len(joriy_raqamlar) == 9 and not joriy_raqamlar.startswith("998"))
                or len(joriy_raqamlar) == 12
            )
            if toxtatish_kerak:
                if _guruh_yaroqlimi(joriy):
                    guruhlar.append(joriy)
                joriy = ""
                joriy_raqamlar = ""
            joriy += belgi
            joriy_raqamlar += belgi
        elif _BOGLOVCHI_BELGI.match(belgi):
            if joriy:  # guruh hali boshlanmagan bo'lsa, bekorchi bog'lovchini saqlamaymiz
                joriy += belgi
        else:  # harf yoki boshqa chegara belgisi
            if _guruh_yaroqlimi(joriy):
                guruhlar.append(joriy)
            joriy = ""
            joriy_raqamlar = ""

    if _guruh_yaroqlimi(joriy):
        guruhlar.append(joriy)

    return guruhlar


def _qismdan_raqamlarni_ajrat(qism):
    # bitta matn qismi ichidagi barcha 9/12(+998) xonali raqamlarni qaytaradi
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
    natija = _qismdan_raqamlarni_ajrat(matn)
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
    for guruh in _raqam_guruhlarini_top(matn):
        faqat_raqam = re.sub(r"\D", "", guruh)
        if len(faqat_raqam) in (7, 8, 10, 11):
            natija.append(faqat_raqam)
    return list(dict.fromkeys(natija))
