# Bu fayl Supabase (Postgres) ma'lumotlar bazasi bilan gaplashadigan barcha funksiyalarni saqlaydi
# Har bir funksiya bitta aniq vazifani bajaradi (mijoz topish, zayavka yaratish va h.k.)

from datetime import datetime, timezone, timedelta  # vaqt bilan ishlash uchun
from supabase import create_client  # Supabase mijoz (client) yaratish funksiyasi
from lib.config import SUPABASE_URL, SUPABASE_KEY, MUMKIN_YONALISHLAR  # sozlamalarni olib kelamiz

# Supabase bilan bog'lanish uchun bitta umumiy mijoz (client) obyekti yaratamiz
_client = create_client(SUPABASE_URL, SUPABASE_KEY)


def hozir():
    # hozirgi vaqtni UTC formatida qaytaradi (bazadagi vaqtlar bilan mos bo'lishi uchun)
    return datetime.now(timezone.utc)


# ---------------------- XODIMLAR BILAN ISHLASH ----------------------

def barcha_xodimlar():
    # bazadagi barcha xodimlar ro'yxatini qaytaradi
    natija = _client.table("xodimlar").select("*").execute()  # "xodimlar" jadvalidan hammasini olamiz
    return natija.data  # faqat ma'lumot qismini qaytaramiz


def xodim_topilsin(telegram_id):
    # berilgan Telegram ID bo'yicha xodimni qidiradi, topilmasa None qaytaradi
    natija = _client.table("xodimlar").select("*").eq("telegram_id", telegram_id).execute()
    if natija.data:  # agar ro'yxat bo'sh bo'lmasa
        return natija.data[0]  # birinchi (va yagona) topilgan xodimni qaytaramiz
    return None  # topilmasa None


def xodim_id_orqali(xodim_id):
    # xodimni ichki id raqami orqali topadi
    natija = _client.table("xodimlar").select("*").eq("id", xodim_id).execute()
    if natija.data:
        return natija.data[0]
    return None


def xodim_holatini_yangila(xodim_id, holat, joriy_zayavka_id=None):
    # xodimning holatini ('bosh' yoki 'band') va biriktirilgan zayavkasini yangilaydi
    _client.table("xodimlar").update({
        "holat": holat,
        "joriy_zayavka_id": joriy_zayavka_id
    }).eq("id", xodim_id).execute()


def bosh_xodimlar():
    # holati 'bosh' bo'lgan xodimlarni qaytaradi — FAQAT rol='xodim' bo'lganlar
    # ("owner" va "super_user" guruhda avtomatik tag qilinmaydi, lekin xohlasa Mini App orqali
    # baribir qabul qilaveradi — bu shunchaki guruhdagi bildirishnoma ro'yxatiga kirmaydi, xolos)
    natija = (_client.table("xodimlar").select("*")
              .eq("holat", "bosh")
              .eq("rol", "xodim")
              .execute())
    return natija.data


# ---------------------- MIJOZLAR BILAN ISHLASH ----------------------

def mijoz_top_yoki_yarat(telegram_id, ism):
    # avval mijoz mavjudmi tekshiradi, bo'lmasa yangisini yaratadi, ikkala holatda ham mijoz qaytadi
    natija = _client.table("mijozlar").select("*").eq("telegram_id", telegram_id).execute()
    if natija.data:  # agar mijoz allaqachon bazada bo'lsa
        return natija.data[0]  # mavjud mijozni qaytaramiz
    yangi = _client.table("mijozlar").insert({  # aks holda yangi mijoz yozuvi yaratamiz
        "telegram_id": telegram_id,
        "ism": ism
    }).execute()
    return yangi.data[0]  # yangi yaratilgan mijozni qaytaramiz


def mijoz_malumotini_yangila(mijoz_id, inn, telefon):
    # mijozning INN va telefon raqamini bazaga yozib qo'yadi
    _client.table("mijozlar").update({
        "inn": inn,
        "telefon": telefon
    }).eq("id", mijoz_id).execute()


def mijoz_kompaniyasini_yangila(mijoz_id, kompaniya_nomi):
    # Google Sheets'dan aniqlangan kompaniya nomini mijozga saqlaydi
    _client.table("mijozlar").update({"kompaniya_nomi": kompaniya_nomi}).eq("id", mijoz_id).execute()


def mijoz_kutayotgan_xabarini_saqla(mijoz_id, matn):
    # mijozga shaxsiy yuborib bo'lmagan (u botni hali "start" qilmagan) xabarni vaqtincha saqlab qo'yadi —
    # mijoz "start" bosgan zahoti shu matn avtomatik yuboriladi
    _client.table("mijozlar").update({"kutayotgan_xabar": matn}).eq("id", mijoz_id).execute()


def mijoz_kutayotgan_xabarini_tozala(mijoz_id):
    # kutayotgan xabar allaqachon yetkazilgach, uni bazadan tozalaydi (ikkinchi marta yubormaslik uchun)
    _client.table("mijozlar").update({"kutayotgan_xabar": None}).eq("id", mijoz_id).execute()


# ---------------------- ZAYAVKALAR BILAN ISHLASH ----------------------

def ochiq_zayavka_top(mijoz_id):
    # shu mijozning hali "malumot_kutilmoqda" holatidagi tugallanmagan zayavkasi bor-yo'qligini tekshiradi
    natija = (_client.table("zayavkalar").select("*")
              .eq("mijoz_id", mijoz_id)
              .eq("holat", "malumot_kutilmoqda")
              .order("id", desc=True).limit(1).execute())
    if natija.data:
        return natija.data[0]
    return None


def zayavka_yarat(mijoz_id, guruh_chat_id, mijoz_xabar_id, matn):
    # yangi zayavka yozuvini "malumot_kutilmoqda" holatida yaratadi
    yangi = _client.table("zayavkalar").insert({
        "mijoz_id": mijoz_id,
        "guruh_chat_id": guruh_chat_id,
        "mijoz_xabar_id": mijoz_xabar_id,
        "matn": matn,
        "holat": "malumot_kutilmoqda"
    }).execute()
    return yangi.data[0]


def zayavka_matnini_yangila(zayavka_id, yangi_matn):
    # mijozdan kelgan qo'shimcha xabarni zayavka matniga qo'shib yangilaydi
    _client.table("zayavkalar").update({"matn": yangi_matn}).eq("id", zayavka_id).execute()


def zayavka_id_orqali(zayavka_id):
    # zayavkani uning ID raqami orqali topib qaytaradi
    natija = _client.table("zayavkalar").select("*").eq("id", zayavka_id).execute()
    if natija.data:
        return natija.data[0]
    return None


def zayavkani_yangila(zayavka_id, **maydonlar):
    # zayavkaning istalgan maydonlarini (holat, rang va h.k.) yangilash uchun umumiy funksiya
    _client.table("zayavkalar").update(maydonlar).eq("id", zayavka_id).execute()


def navbatdagi_zayavkalar():
    # holati "navbatda" bo'lgan, hali xodim tayinlanmagan barcha zayavkalarni qaytaradi (eng eskisi birinchi)
    natija = (_client.table("zayavkalar").select("*")
              .eq("holat", "navbatda")
              .order("yaratilgan_vaqt").execute())
    return natija.data


def keyingi_navbatdagi_zayavka():
    # navbatdagi eng eski (birinchi kelgan) zayavkani qaytaradi — oddiy FIFO (birinchi kelgan, birinchi xizmat) qoidasi
    natija = (_client.table("zayavkalar").select("*")
              .eq("holat", "navbatda")
              .order("yaratilgan_vaqt").limit(1).execute())
    if natija.data:
        return natija.data[0]
    return None


# ---------------------- TAKRORLANISHNING OLDINI OLISH ----------------------

def update_yangimi(update_id):
    # Telegramdan kelgan "update_id" bazada hali mavjud emasligini tekshiradi va yozib qo'yadi
    # Agar bu update_id allaqachon bazada bo'lsa — demak bu takroriy yuborilgan xabar, False qaytaradi
    # Agar yangi bo'lsa — bazaga yozib, True qaytaradi (endi qayta ishlash mumkin)
    try:
        _client.table("qayta_ishlangan_updatelar").insert({"update_id": update_id}).execute()
        return True  # muvaffaqiyatli yozildi — demak bu birinchi marta kelgan update
    except Exception as xato:
        matn = str(xato).lower()  # xatolik matnini kichik harflarga o'giramiz, solishtirish oson bo'lsin
        if "duplicate" in matn or "already exists" in matn or "23505" in matn:
            # bu ANIQ "allaqachon mavjud" xatoligi — demak chindan ham takroriy update
            return False
        # boshqa turdagi kutilmagan xatolik bo'lsa (masalan jadval hali yaratilmagan bo'lsa) —
        # botni butunlay to'xtatib qo'ymaslik uchun, xavfsiz tomonga o'tib, davom ettiramiz
        return True


# ---------------------- RAHBARLAR UCHUN STATISTIKA (dashboard) ----------------------

def kunlik_boshlanish_vaqti():
    # "bugun" tushunchasini Toshkent vaqti bo'yicha hisoblaymiz (Toshkent = UTC+5, yil bo'yi o'zgarmaydi)
    toshkent_hozir = hozir() + timedelta(hours=5)  # UTC vaqtini Toshkent vaqtiga o'tkazamiz
    toshkent_kun_boshi = toshkent_hozir.replace(hour=0, minute=0, second=0, microsecond=0)  # bugungi 00:00
    utc_kun_boshi = toshkent_kun_boshi - timedelta(hours=5)  # qaytadan UTC'ga o'tkazamiz (bazada shu formatda saqlanadi)
    return utc_kun_boshi.isoformat()


def sonini_ol(holat, faqat_bugun=False):
    # berilgan holatdagi zayavkalar sonini qaytaradi (agar faqat_bugun=True bo'lsa, faqat bugungilarni hisoblaydi)
    so_rov = _client.table("zayavkalar").select("id", count="exact").eq("holat", holat)  # holat bo'yicha filtr
    if faqat_bugun:  # agar faqat bugungi kun kerak bo'lsa
        so_rov = so_rov.gte("yaratilgan_vaqt", kunlik_boshlanish_vaqti())  # bugungi 00:00'dan keyingilarni olamiz
    natija = so_rov.execute()  # so'rovni bajaramiz
    return natija.count or 0  # sonini qaytaramiz (agar hech narsa topilmasa 0)


def bugungi_holat_sonlari():
    # TEZLIK UCHUN: oldin "bugun jami murojaat" sonini hisoblash uchun 6 ta ALOHIDA so'rov
    # (har bir holat uchun bittadan) yuborilar edi — bu Mini App panelini sekinlashtirar edi.
    # Endi BITTA so'rov bilan bugungi barcha zayavkalarning "holat" ustunini olib, sanashni
    # o'zimiz (Python'da) amalga oshiramiz — natija bir xil, lekin ancha tezroq
    natija = (_client.table("zayavkalar").select("holat")
              .gte("yaratilgan_vaqt", kunlik_boshlanish_vaqti())
              .execute())
    sonlar = {}  # holat nomi -> necha marta uchragani
    for qator in natija.data:
        holat = qator["holat"]
        sonlar[holat] = sonlar.get(holat, 0) + 1
    return sonlar


def statistika():
    # rahbarlar paneli uchun barcha kerakli raqamlarni bitta joyga yig'ib qaytaradi
    return {
        # "super_user" roli bu ro'yxatda ko'rsatilmaydi — u kuzatuvchi/admin, oddiy xodim emas
        "xodimlar": [x for x in barcha_xodimlar() if x.get("rol") != "super_user"],
        "hozir_consultatsiyada": sonini_ol("jarayonda"),  # ayni damda gaplashilayotgan mijozlar soni
        "navbatda_kutmoqda": sonini_ol("navbatda"),  # hali xodim tayinlanmagan, kutayotgan mijozlar soni
        "bugun_jami_murojaat": (
            sonini_ol("navbatda", faqat_bugun=True)
            + sonini_ol("jarayonda", faqat_bugun=True)
            + sonini_ol("qayta_aloqa", faqat_bugun=True)  # javob bermay, qayta urinish kutayotganlar ham hisoblanadi
            + sonini_ol("tugallandi", faqat_bugun=True)
            + sonini_ol("javob_bermadi", faqat_bugun=True)  # butunlay javob bermay yopilganlar ham hisoblanadi
            + sonini_ol("muddati_otdi", faqat_bugun=True)
        ),  # bugun to'liq ma'lumot bilan kelgan barcha murojaatlar (INN/tel berilganlar)
        "bugun_consultatsiya_berildi": sonini_ol("tugallandi", faqat_bugun=True),  # bugun muvaffaqiyatli tugagan
        "bugun_qolib_ketdi": sonini_ol("muddati_otdi", faqat_bugun=True),  # bugun 20 daqiqada ulgurilmagan
    }


def xodimning_joriy_zayavkasi(xodim_id):
    # xodim hozir band bo'lgan (joriy_zayavka_id'da saqlangan) zayavkani to'liq holda qaytaradi
    xodim = xodim_id_orqali(xodim_id)  # avval xodimning o'zini olamiz
    if not xodim or not xodim.get("joriy_zayavka_id"):  # agar xodim yo'q yoki hozir band emas bo'lsa
        return None
    return zayavka_id_orqali(xodim["joriy_zayavka_id"])  # band bo'lgan zayavkani to'liq qaytaramiz


# ---------------------- MINI APP UCHUN KENGAYTIRILGAN PANEL MA'LUMOTI ----------------------

def jarayondagi_zayavkalar():
    # hozir gaplashilayotgan (holat='jarayonda') BARCHA zayavkalarni qaytaradi (kim bo'lishidan qat'iy nazar)
    natija = (_client.table("zayavkalar").select("*")
              .eq("holat", "jarayonda")
              .order("jarayon_boshlangan_vaqt").execute())
    return natija.data


def qayta_aloqadagi_zayavkalar():
    # "Telefonni ko'tarmadi" bosilgan, lekin hali yopilmagan (3 martaga yetmagan) zayavkalarni qaytaradi —
    # bular biriktirilgan xodim "Qabul qilish"ni yana bosishini kutmoqda
    natija = (_client.table("zayavkalar").select("*")
              .eq("holat", "qayta_aloqa")
              .order("yaratilgan_vaqt").execute())
    return natija.data


def bugungi_muddati_otganlar():
    # bugun 20 daqiqada ulgurilmay "qolib ketgan" mijozlar ro'yxatini qaytaradi (eng yangisi birinchi)
    natija = (_client.table("zayavkalar").select("*")
              .eq("holat", "muddati_otdi")
              .gte("yaratilgan_vaqt", kunlik_boshlanish_vaqti())
              .order("yaratilgan_vaqt", desc=True).execute())
    return natija.data


def bugungi_tugallangan_yozuvlar():
    # bugun yakunlangan consultatsiyalarning xom ma'lumotini qaytaradi (analitika hisoblash uchun kerak)
    natija = (_client.table("zayavkalar").select("id, biriktirilgan_xodim_id, jarayon_boshlangan_vaqt, tugallangan_vaqt")
              .eq("holat", "tugallandi")
              .gte("yaratilgan_vaqt", kunlik_boshlanish_vaqti())
              .not_.is_("jarayon_boshlangan_vaqt", "null")  # boshlanish vaqti bo'lishi shart
              .not_.is_("tugallangan_vaqt", "null")  # tugash vaqti ham bo'lishi shart
              .execute())
    return natija.data


def vaqt_farqi_daqiqada(boshlanish_matni, tugash_matni):
    # ikkita vaqt matnini (Supabase'dan kelgan ISO format) solishtirib, orasidagi farqni daqiqada qaytaradi
    from datetime import datetime as _dt  # funksiya ichida import qilamiz
    boshlanish = _dt.fromisoformat(boshlanish_matni.replace("Z", "+00:00"))
    tugash = _dt.fromisoformat(tugash_matni.replace("Z", "+00:00"))
    return round((tugash - boshlanish).total_seconds() / 60, 1)  # daqiqaga o'tkazib, 1 xona aniqlikda qaytaramiz


def xodimlar_analitikasi():
    # har bir xodim uchun: bugun nechta consultatsiya bergani va har biriga o'rtacha necha daqiqa
    # ("qabul qildim" bosilgandan "consultatsiya berdim" bosilgungacha) ketganini hisoblaydi
    # DIQQAT: "super_user" roli bu ro'yxatda ko'rsatilmaydi (u oddiy xodim emas, kuzatuvchi/admin)
    barcha = [x for x in barcha_xodimlar() if x.get("rol") != "super_user"]
    yozuvlar = bugungi_tugallangan_yozuvlar()  # bugun yakunlangan barcha consultatsiyalar

    guruhlangan = {}  # xodim_id -> [daqiqalar ro'yxati]
    for yozuv in yozuvlar:
        xodim_id = yozuv["biriktirilgan_xodim_id"]
        daqiqa = vaqt_farqi_daqiqada(yozuv["jarayon_boshlangan_vaqt"], yozuv["tugallangan_vaqt"])
        guruhlangan.setdefault(xodim_id, []).append(daqiqa)  # shu xodimning ro'yxatiga qo'shamiz

    natija = []
    for xodim in barcha:  # har bir xodim uchun yakuniy statistikani hisoblaymiz
        daqiqalar = guruhlangan.get(xodim["id"], [])  # shu xodimning bugungi barcha daqiqalari
        soni = len(daqiqalar)
        ortacha = round(sum(daqiqalar) / soni, 1) if soni > 0 else 0  # 0 ga bo'linishdan saqlanamiz
        natija.append({
            "xodim_id": xodim["id"],  # frontend'da "shu xodimga bos" tafsilotini ochish uchun kerak
            "ism_familiya": xodim["ism_familiya"],
            "consultatsiya_soni": soni,
            "ortacha_daqiqa": ortacha,
        })
    return natija


def xodimning_mijozlari(xodim_id, boshlanish_vaqti, holat="tugallandi"):
    # bitta xodim BERILGAN VAQTDAN buyon, BERILGAN HOLATDAGI mijozlarining to'liq ma'lumotini qaytaradi
    # (ism, telefon, INN, yozgan xabari/sababi, BAHOSI va IZOHI) — analitikada/oylik hisobotda
    # "xodim ustiga bosilganda" ko'rsatish uchun.
    # holat: "tugallandi" (consultatsiya berilgan) yoki "javob_bermadi" (mijoz javob bermagan)
    zayavkalar = (_client.table("zayavkalar").select(
        "id, mijoz_id, matn, jarayon_boshlangan_vaqt, tugallangan_vaqt, kompaniya_nomi, inn, qongiroq_soni")
                  .eq("biriktirilgan_xodim_id", xodim_id)
                  .eq("holat", holat)
                  .gte("yaratilgan_vaqt", boshlanish_vaqti)
                  .order("tugallangan_vaqt", desc=True).execute()).data

    return _mijoz_royxatini_toldir(zayavkalar)


def xodimning_qayta_aloqa_mijozlari(xodim_id, boshlanish_vaqti):
    # "qayta_aloqa" holatidagi mijozlar — telefon ko'tarilmagan, xodim "Qabul qilish"ni
    # yana bosishini kutmoqda (hali 3-martaga yetib, yopilmagan)
    zayavkalar = (_client.table("zayavkalar").select(
        "id, mijoz_id, matn, jarayon_boshlangan_vaqt, tugallangan_vaqt, kompaniya_nomi, inn, qongiroq_soni")
                  .eq("biriktirilgan_xodim_id", xodim_id)
                  .eq("holat", "qayta_aloqa")
                  .gte("yaratilgan_vaqt", boshlanish_vaqti)
                  .order("yaratilgan_vaqt", desc=True).execute()).data

    return _mijoz_royxatini_toldir(zayavkalar)


def _mijoz_royxatini_toldir(zayavkalar):
    # umumiy yordamchi: zayavkalar ro'yxatiga mijoz ma'lumoti, baho/izoh va gaplashish davomiyligini biriktiradi
    mijoz_idlar = list({z["mijoz_id"] for z in zayavkalar})  # takrorlanmagan mijoz ID'lar ro'yxati
    mijoz_map = {}
    if mijoz_idlar:  # agar hech bo'lmasa bitta mijoz bo'lsa
        mijozlar = _client.table("mijozlar").select("*").in_("id", mijoz_idlar).execute().data
        mijoz_map = {m["id"]: m for m in mijozlar}  # tezkor qidiruv uchun mijoz_id -> mijoz ma'lumoti

    # shu zayavkalarga tegishli baholashlarni (agar bor bo'lsa) bittalab so'ramaslik uchun,
    # hammasini bitta so'rov bilan olamiz
    zayavka_idlar = [z["id"] for z in zayavkalar]
    baholash_map = {}  # zayavka_id -> baholash yozuvi
    if zayavka_idlar:
        baholashlar = _client.table("baholashlar").select("*").in_("zayavka_id", zayavka_idlar).execute().data
        baholash_map = {b["zayavka_id"]: b for b in baholashlar}

    natija = []
    for z in zayavkalar:
        mijoz = mijoz_map.get(z["mijoz_id"], {})  # shu zayavkaga tegishli mijoz ma'lumoti
        baholash = baholash_map.get(z["id"])  # shu zayavkaga tegishli baholash (bo'lmasligi ham mumkin)
        daqiqa = None
        if z.get("jarayon_boshlangan_vaqt") and z.get("tugallangan_vaqt"):  # ikkalasi ham bo'lsa hisoblaymiz
            daqiqa = vaqt_farqi_daqiqada(z["jarayon_boshlangan_vaqt"], z["tugallangan_vaqt"])
        natija.append({
            "mijoz_ismi": mijoz.get("ism") or "Noma'lum",
            "mijoz_telefon": mijoz.get("telefon"),
            # DIQQAT: avval ZAYAVKAning o'z INN/kompaniyasini olamiz (o'sha paytdagi haqiqiy ma'lumot);
            # agar u bo'lmasa (eski, migratsiyadan oldingi yozuv), mijozning umumiy ma'lumotiga qaytamiz
            "mijoz_inn": z.get("inn") or mijoz.get("inn"),
            "kompaniya_nomi": z.get("kompaniya_nomi") or mijoz.get("kompaniya_nomi"),
            "matn": z.get("matn"),  # mijozning yozgan xabari (sababi shu ichida bo'lishi mumkin)
            "daqiqa": daqiqa,
            "qongiroq_soni": z.get("qongiroq_soni") or 0,  # necha marta "ko'tarmadi" bosilgani
            "yulduz": baholash["yulduz"] if baholash else None,  # 1-5 (hali baholamagan bo'lsa — None)
            "izoh": baholash["izoh"] if baholash else None,  # mijoz yozgan izoh (bo'lmasa — None)
            "baho_holati": baholash["holat"] if baholash else None,  # kutilmoqda | baholandi | muddati_otdi
        })
    return natija


def xodimning_bugungi_mijozlari(xodim_id):
    # xodim ustiga "Analitika" bo'limida bosilganda — bugungi 3 toifani (tugallandi/qayta
    # aloqa/javob bermadi) bitta lug'atda qaytaradi (Mini App'da tab'lar orqali ko'rsatiladi)
    boshlanish = kunlik_boshlanish_vaqti()
    return {
        "tugallandi": xodimning_mijozlari(xodim_id, boshlanish, holat="tugallandi"),
        "qayta_aloqa": xodimning_qayta_aloqa_mijozlari(xodim_id, boshlanish),
        "javob_bermadi": xodimning_mijozlari(xodim_id, boshlanish, holat="javob_bermadi"),
    }


def xodimning_oylik_mijozlari(xodim_id):
    # xodim ustiga "Oylik hisobot"da bosilganda — shu oy bo'yicha xuddi shu 3 toifani qaytaradi
    boshlanish = oy_boshlanish_vaqti()
    return {
        "tugallandi": xodimning_mijozlari(xodim_id, boshlanish, holat="tugallandi"),
        "qayta_aloqa": xodimning_qayta_aloqa_mijozlari(xodim_id, boshlanish),
        "javob_bermadi": xodimning_mijozlari(xodim_id, boshlanish, holat="javob_bermadi"),
    }


def app_panel_malumoti(rol):
    # Mini App uchun barcha kerakli ma'lumotni bitta joyga yig'ib qaytaradi
    # "rol" — so'rovni yuborayotgan odamning roli; owner/super_user uchun qo'shimcha ma'lumot ham qo'shiladi

    barcha = barcha_xodimlar()  # keyinroq xodim ismini biriktirish uchun kerak bo'ladi
    ism_map = {x["id"]: x["ism_familiya"] for x in barcha}  # xodim_id -> ism tezkor qidiruv jadvali

    jarayondagilar = jarayondagi_zayavkalar()
    for z in jarayondagilar:  # har biriga kim gaplashayotganini (ismini) biriktiramiz
        z["xodim_ismi"] = ism_map.get(z.get("biriktirilgan_xodim_id"), "?")

    qayta_aloqadagilar = qayta_aloqadagi_zayavkalar()  # "Telefonni ko'tarmadi" bosilib, qayta urinish kutayotganlar
    for z in qayta_aloqadagilar:  # har biriga kim mas'ul ekanini (ismini) biriktiramiz
        z["xodim_ismi"] = ism_map.get(z.get("biriktirilgan_xodim_id"), "?")

    # TEZLIK: bugungi barcha holatlar sonini BITTA so'rov bilan olamiz (oldin 6 ta alohida so'rov edi)
    bugun = bugungi_holat_sonlari()
    bugun_jami = sum(bugun.get(h, 0) for h in
                      ("navbatda", "jarayonda", "qayta_aloqa", "tugallandi", "javob_bermadi", "muddati_otdi"))

    natija = {
        # DIQQAT: "kompaniya_nomi" endi zayavkaning o'zida (select "*" orqali) tayyor keladi —
        # mijoz orqali alohida "join" qilishning hojati yo'q (avvalgi xato aynan shu joyda edi)
        "navbatdagilar": navbatdagi_zayavkalar(),  # 1) navbat kutayotganlar
        "jarayondagilar": jarayondagilar,  # 2) consultatsiya jarayonda
        "qayta_aloqadagilar": qayta_aloqadagilar,  # 2.5) mijoz javob bermay, qayta urinish kutilayotganlar
        "bugun_jami_murojaat": bugun_jami,  # 3) bugun jami murojaatlar
        "bugun_consultatsiya_berildi": bugun.get("tugallandi", 0),  # 4) bugun tugallanganlar
        "muddati_otganlar": bugungi_muddati_otganlar(),  # 5) o'tib ketganlar
    }

    if rol in ("owner", "super_user"):  # faqat owner va super_user uchun qo'shimcha bo'limlar
        # "super_user" roli bu yerda KO'RSATILMAYDI — u kuzatuvchi/admin, oddiy xodim sifatida sanalmaydi
        natija["xodimlar_holati"] = [x for x in barcha if x.get("rol") != "super_user"]
        natija["analitika"] = xodimlar_analitikasi()  # 7) har bir xodimning o'rtacha gaplashish vaqti
        natija["xodimlar_reytingi"] = xodimlar_reytingi()  # 8) mijozlar bergan yulduzcha reytingi
        natija["yonalishlar_statistikasi"] = yonalishlar_statistikasi()  # 9) eng ko'p so'ralgan yo'nalish
        natija["oylik_hisobot"] = oylik_hisobot()  # 10) shu oy bo'yicha umumiy hisobot
        natija["kompaniyalar_statistikasi"] = kompaniyalar_statistikasi()  # 11) qaysi kompaniya nima bilan ko'p murojaat qiladi

    return natija


# ---------------------- YO'NALISHLAR (ZUB / Buxgalteriya / UNF) ----------------------

def yonalishlarni_ornat(zayavka_id, yonalishlar_royxati):
    # zayavkaga tanlangan yo'nalishlar ro'yxatini (masalan ["ZUB", "UNF"]) vergul bilan ajratib saqlaydi
    matn = ",".join(yonalishlar_royxati)  # ["ZUB","UNF"] -> "ZUB,UNF"
    _client.table("zayavkalar").update({"yonalishlar": matn}).eq("id", zayavka_id).execute()


def zayavka_yonalishlari(zayavka):
    # zayavkaning "yonalishlar" ustunidagi matnni ro'yxatga aylantirib qaytaradi (bo'sh bo'lsa — bo'sh ro'yxat)
    matn = zayavka.get("yonalishlar") or ""
    return [y for y in matn.split(",") if y]  # bo'sh qatorlarni chiqarib tashlaymiz


# ---------------------- MIJOZ (qo'shimcha qidiruv) ----------------------

def mijoz_id_orqali(mijoz_id):
    # mijozni uning ichki ID raqami orqali topib qaytaradi
    natija = _client.table("mijozlar").select("*").eq("id", mijoz_id).execute()
    if natija.data:
        return natija.data[0]
    return None


# ---------------------- BAHOLASH (reyting) ----------------------

def baholash_yarat(zayavka_id, mijoz_id, xodim_id):
    # yangi baholash so'rovi yozuvini "kutilmoqda" holatida yaratadi
    yangi = _client.table("baholashlar").insert({
        "zayavka_id": zayavka_id,
        "mijoz_id": mijoz_id,
        "xodim_id": xodim_id,
        "holat": "kutilmoqda"
    }).execute()
    return yangi.data[0]


def zayavkani_atomik_qabul_qil(zayavka_id, xodim_id):
    # MUHIM: bu — ATOMIK amal. Faqat hozir "navbatda" yoki "muddati_otdi" holatida bo'lgan
    # zayavkanigina yangilaydi (bazaning o'zida, bitta so'rovda tekshirib-yozadi). Shuning uchun
    # xodim tugmani necha marta (tez-tez, deyarli bir vaqtda) bossa ham — FAQAT BIRINCHI urinish
    # muvaffaqiyatli bo'ladi, qolganlari hech narsa o'zgartirmaydi (poyga holati bo'lmaydi)
    natija = (_client.table("zayavkalar")
              .update({
                  "holat": "jarayonda",
                  "biriktirilgan_xodim_id": xodim_id,
                  "jarayon_boshlangan_vaqt": hozir().isoformat()
              })
              .eq("id", zayavka_id)
              .in_("holat", ["navbatda", "muddati_otdi"])
              .execute())
    return len(natija.data) > 0  # True — bu chindan ham BIRINCHI marta qabul qilindi


def zayavkani_atomik_tugat(zayavka_id, xodim_id):
    # xuddi yuqoridagi kabi ATOMIK amal — faqat hozir shu xodimga biriktirilgan va "jarayonda"
    # holatidagi zayavkanigina "tugallandi" qiladi. "Yakunlash" necha marta bosilsa ham,
    # FAQAT BIRINCHI marta haqiqiy yakunlanadi (masalan bitta mijozga bir nechta baholash
    # so'rovi ketib qolishining oldini oladi)
    natija = (_client.table("zayavkalar")
              .update({"holat": "tugallandi", "tugallangan_vaqt": hozir().isoformat()})
              .eq("id", zayavka_id)
              .eq("biriktirilgan_xodim_id", xodim_id)
              .eq("holat", "jarayonda")
              .execute())
    return len(natija.data) > 0


def baholashni_birinchi_marta_belgila(baholash_id, yulduz):
    # MUHIM: bu funksiya ATOMIK ishlaydi — faqat hali "kutilmoqda" holatida bo'lgan yozuvnigina yangilaydi.
    # Agar mijoz bir necha marta ketma-ket (yoki deyarli bir vaqtda) bossa — FAQAT BIRINCHISI hisoblanadi,
    # chunki ".eq('holat','kutilmoqda')" sharti bazaning o'zida tekshiriladi (o'qib-keyin-yozish emas,
    # bitta so'rovda tekshirib-yozish), shuning uchun poyga holati (race condition) yuzaga kelmaydi
    natija = (_client.table("baholashlar")
              .update({"yulduz": yulduz, "holat": "baholandi", "javob_vaqt": hozir().isoformat()})
              .eq("id", baholash_id)
              .eq("holat", "kutilmoqda")  # faqat shu shart bajarilgan qatorgina yangilanadi
              .execute())
    return len(natija.data) > 0  # True — bu chindan ham BIRINCHI marta saqlandi; False — allaqachon baholangan edi


def baholash_id_orqali(baholash_id):
    # baholash yozuvini ID raqami orqali topadi
    natija = _client.table("baholashlar").select("*").eq("id", baholash_id).execute()
    if natija.data:
        return natija.data[0]
    return None


def baholashni_yangila(baholash_id, **maydonlar):
    # baholash yozuvining istalgan maydonlarini yangilash uchun umumiy funksiya
    _client.table("baholashlar").update(maydonlar).eq("id", baholash_id).execute()


def mijozning_izoh_kutayotgan_baholashi(mijoz_id):
    # shu mijozning yaqinda (yulduzcha bosilgan, lekin izoh hali yozilmagan) baholashini topadi —
    # keyingi shaxsiy xabarini "izoh" sifatida qabul qilish uchun kerak
    natija = (_client.table("baholashlar").select("*")
              .eq("mijoz_id", mijoz_id)
              .eq("holat", "baholandi")
              .is_("izoh", "null")  # hali izoh yozilmagan
              .order("javob_vaqt", desc=True).limit(1).execute())
    if natija.data:
        return natija.data[0]
    return None


def mijozning_yuborilmagan_baholashi(mijoz_id):
    # shu mijozga baholash so'rovi YARATILGAN, lekin hali LICHKAGA yetkazilmagan (mijoz "start"
    # bosmagani uchun chat_id hali bo'sh) yozuvni topadi — "start" bosilganda uni to'liq
    # (yulduzcha tugmalari bilan) qayta yuborish uchun kerak
    natija = (_client.table("baholashlar").select("*")
              .eq("mijoz_id", mijoz_id)
              .eq("holat", "kutilmoqda")
              .is_("chat_id", "null")  # hali hech qachon yuborilmagan
              .order("id", desc=True).limit(1).execute())
    if natija.data:
        return natija.data[0]
    return None


def eskirgan_baholashlar(necha_kun_oldin_iso):
    # "kutilmoqda" holatida, berilgan sanadan OLDIN yaratilgan (demak muddati o'tgan) baholashlarni qaytaradi
    natija = (_client.table("baholashlar").select("*")
              .eq("holat", "kutilmoqda")
              .lt("yaratilgan_vaqt", necha_kun_oldin_iso).execute())
    return natija.data


# ---------------------- XODIMLAR REYTINGI VA YO'NALISHLAR STATISTIKASI ----------------------

def xodimlar_reytingi():
    # har bir xodimning mijozlar tomonidan berilgan BARCHA (butun davr bo'yicha) o'rtacha yulduzcha
    # bahosini va nechta baho olganini hisoblaydi — "super_user" bu ro'yxatda ko'rsatilmaydi
    barcha = [x for x in barcha_xodimlar() if x.get("rol") != "super_user"]

    baholashlar = (_client.table("baholashlar").select("xodim_id, yulduz")
                   .eq("holat", "baholandi").execute()).data  # faqat javob berilgan baholarni olamiz

    guruhlangan = {}  # xodim_id -> [yulduzlar ro'yxati]
    for baholash in baholashlar:
        xodim_id = baholash.get("xodim_id")
        if xodim_id is None:  # xodim biriktirilmagan (bo'lmasligi kerak, lekin xavfsizlik uchun)
            continue
        guruhlangan.setdefault(xodim_id, []).append(baholash["yulduz"])

    natija = []
    for xodim in barcha:
        yulduzlar = guruhlangan.get(xodim["id"], [])
        soni = len(yulduzlar)
        ortacha = round(sum(yulduzlar) / soni, 2) if soni > 0 else None  # baho bo'lmasa — None
        natija.append({
            "xodim_id": xodim["id"],
            "ism_familiya": xodim["ism_familiya"],
            "baho_soni": soni,
            "ortacha_baho": ortacha,
        })

    # eng yuqori reytingdan pastga qarab saralaymiz; hali umuman baholanmaganlar oxirida turadi
    natija.sort(key=lambda x: (x["ortacha_baho"] is None, -(x["ortacha_baho"] or 0)))
    return natija


def yonalishlar_statistikasi():
    # yakunlangan (tugallandi) barcha zayavkalar bo'yicha, har bir yo'nalish (ZUB/Buxgalteriya/UNF)
    # nechchi marta tanlanganini hisoblaydi — "eng ko'p so'raladigan yo'nalish"ni ko'rsatish uchun
    yozuvlar = (_client.table("zayavkalar").select("yonalishlar")
                .eq("holat", "tugallandi").execute()).data

    hisoblagich = {yonalish: 0 for yonalish in MUMKIN_YONALISHLAR}  # hammasi 0 dan boshlanadi
    for yozuv in yozuvlar:
        matn = yozuv.get("yonalishlar") or ""
        for yonalish in matn.split(","):  # bitta zayavkada 1-2 ta yo'nalish bo'lishi mumkin
            yonalish = yonalish.strip()
            if yonalish in hisoblagich:
                hisoblagich[yonalish] += 1

    natija = [{"yonalish": y, "soni": hisoblagich[y]} for y in MUMKIN_YONALISHLAR]
    natija.sort(key=lambda x: -x["soni"])  # eng ko'p so'ralgani birinchi bo'lib chiqadi
    return natija


# ---------------------- OYLIK HISOBOT ----------------------

def oy_boshlanish_vaqti():
    # "shu oy" tushunchasini Toshkent vaqti bo'yicha hisoblaymiz — oyning 1-kuni, soat 00:00
    toshkent_hozir = hozir() + timedelta(hours=5)
    oy_boshi_toshkent = toshkent_hozir.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    utc_oy_boshi = oy_boshi_toshkent - timedelta(hours=5)
    return utc_oy_boshi.isoformat()


def oylik_hisobot():
    # har bir xodim uchun SHU OY (1-kunidan hozirgacha) bo'yicha umumiy hisobotni tayyorlaydi:
    # nechta mijoz bilan gaplashgani, jami necha daqiqa/soat, nechta izoh, nechtasi ijobiy/salbiy,
    # va jami yig'gan yulduzchalari soni
    barcha = [x for x in barcha_xodimlar() if x.get("rol") != "super_user"]  # super_user kirmaydi
    boshlanish = oy_boshlanish_vaqti()

    # SHU OY ICHIDA TUGALLANGAN zayavkalar — gaplashish vaqtini va mijozlar sonini hisoblash uchun
    zayavkalar = (_client.table("zayavkalar").select("biriktirilgan_xodim_id, jarayon_boshlangan_vaqt, tugallangan_vaqt")
                  .eq("holat", "tugallandi")
                  .gte("tugallangan_vaqt", boshlanish)
                  .not_.is_("jarayon_boshlangan_vaqt", "null")
                  .not_.is_("tugallangan_vaqt", "null")
                  .execute()).data

    daqiqa_jami = {}  # xodim_id -> jami daqiqa
    mijoz_soni = {}  # xodim_id -> nechta mijoz
    for z in zayavkalar:
        xodim_id = z["biriktirilgan_xodim_id"]
        daqiqa = vaqt_farqi_daqiqada(z["jarayon_boshlangan_vaqt"], z["tugallangan_vaqt"])
        daqiqa_jami[xodim_id] = daqiqa_jami.get(xodim_id, 0) + daqiqa
        mijoz_soni[xodim_id] = mijoz_soni.get(xodim_id, 0) + 1

    # SHU OY ICHIDA JAVOB BERILGAN baholashlar — izoh/ijobiy/salbiy/yulduz hisoblari uchun
    baholashlar = (_client.table("baholashlar").select("xodim_id, yulduz, izoh")
                   .eq("holat", "baholandi")
                   .gte("javob_vaqt", boshlanish)
                   .execute()).data

    izoh_soni = {}
    ijobiy_soni = {}  # 4-5 yulduz — ijobiy fikr deb hisoblanadi
    salbiy_soni = {}  # 1-2 yulduz — salbiy fikr (muammo) deb hisoblanadi
    baho_soni = {}
    yulduz_yigindisi = {}
    for baholash in baholashlar:
        xodim_id = baholash.get("xodim_id")
        if xodim_id is None:
            continue
        yulduz = baholash.get("yulduz") or 0
        baho_soni[xodim_id] = baho_soni.get(xodim_id, 0) + 1
        yulduz_yigindisi[xodim_id] = yulduz_yigindisi.get(xodim_id, 0) + yulduz
        if baholash.get("izoh"):  # agar izoh yozilgan bo'lsa
            izoh_soni[xodim_id] = izoh_soni.get(xodim_id, 0) + 1
        if yulduz >= 4:  # 4 yoki 5 yulduz — ijobiy
            ijobiy_soni[xodim_id] = ijobiy_soni.get(xodim_id, 0) + 1
        elif 1 <= yulduz <= 2:  # 1 yoki 2 yulduz — salbiy
            salbiy_soni[xodim_id] = salbiy_soni.get(xodim_id, 0) + 1

    natija = []
    for xodim in barcha:
        xodim_id = xodim["id"]
        jami_daqiqa = round(daqiqa_jami.get(xodim_id, 0), 1)
        natija.append({
            "xodim_id": xodim_id,  # frontend'da "shu xodimga bos" tafsilotini ochish uchun kerak
            "ism_familiya": xodim["ism_familiya"],
            "mijozlar_soni": mijoz_soni.get(xodim_id, 0),
            "jami_daqiqa": jami_daqiqa,
            "jami_soat": round(jami_daqiqa / 60, 1),
            "izohlar_soni": izoh_soni.get(xodim_id, 0),
            "ijobiy_soni": ijobiy_soni.get(xodim_id, 0),
            "salbiy_soni": salbiy_soni.get(xodim_id, 0),
            "baho_soni": baho_soni.get(xodim_id, 0),
            "yulduzlar_yigindisi": yulduz_yigindisi.get(xodim_id, 0),
        })

    natija.sort(key=lambda x: -x["jami_daqiqa"])  # eng ko'p ishlagan xodim birinchi
    return natija


def kompaniyalar_statistikasi():
    # har bir kompaniya bo'yicha, yakunlangan zayavkalarda qaysi yo'nalish (ZUB/Buxgalteriya/UNF)
    # necha marta tanlanganini hisoblaydi — "qaysi kompaniya nima bilan ko'proq murojaat qilyapti"
    # degan savolga javob berish uchun. DIQQAT: kompaniya nomi endi ZAYAVKAning o'zidan olinadi
    # (mijoz orqali "join" qilinmaydi) — shunda har bir murojaat o'zining haqiqiy (o'sha paytdagi)
    # kompaniyasiga to'g'ri hisoblanadi
    zayavkalar = (_client.table("zayavkalar").select("yonalishlar, kompaniya_nomi")
                  .eq("holat", "tugallandi")
                  .neq("yonalishlar", "")  # yo'nalishi bo'sh bo'lmaganlarni olamiz
                  .execute()).data

    if not zayavkalar:  # hech narsa topilmasa, bo'sh ro'yxat qaytaramiz
        return []

    # kompaniya nomi -> {"jami": son, "ZUB": son, "Buxgalteriya": son, "UNF": son}
    hisoblagich = {}
    for zayavka in zayavkalar:
        kompaniya = zayavka.get("kompaniya_nomi")
        if not kompaniya:  # kompaniya nomi aniqlanmagan bo'lsa (masalan Google Sheets hali ulanmagan bo'lsa)
            continue
        if kompaniya not in hisoblagich:
            hisoblagich[kompaniya] = {"jami": 0, **{y: 0 for y in MUMKIN_YONALISHLAR}}
        for yonalish in (zayavka.get("yonalishlar") or "").split(","):
            yonalish = yonalish.strip()
            if yonalish in MUMKIN_YONALISHLAR:
                hisoblagich[kompaniya][yonalish] += 1
                hisoblagich[kompaniya]["jami"] += 1

    natija = []
    for kompaniya, sonlar in hisoblagich.items():
        # shu kompaniya uchun eng ko'p tanlangan yo'nalishni topamiz ("eng ko'p shu bilan murojaat qiladi")
        eng_kop = max(MUMKIN_YONALISHLAR, key=lambda y: sonlar[y])
        natija.append({
            "kompaniya": kompaniya,
            "jami": sonlar["jami"],
            "eng_kop_yonalish": eng_kop if sonlar[eng_kop] > 0 else "—",
            "taqsimot": {y: sonlar[y] for y in MUMKIN_YONALISHLAR},
        })

    natija.sort(key=lambda x: -x["jami"])  # eng ko'p murojaat qilgan kompaniya birinchi
    return natija[:15]  # ro'yxat cheksiz uzun bo'lib ketmasligi uchun eng faol 15 tasini qaytaramiz
