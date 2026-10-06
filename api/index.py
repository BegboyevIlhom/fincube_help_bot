# Bu — Vercel uchun YAGONA kirish nuqtasi (entrypoint).
# Vercel'ning yangi Python runtime'i endi bitta FastAPI ilovasini talab qiladi
# (ko'p fayl emas), shuning uchun ikkala vazifa (webhook va taymer tekshiruvchi)
# ham shu bitta faylda, lekin ikki xil manzil (yo'l) orqali ishlaydi.

from fastapi import FastAPI, Request  # veb-server yaratish uchun asosiy kutubxona
from fastapi.responses import HTMLResponse  # HTML sahifa qaytarish uchun kerak (dashboard/mini app uchun)
import traceback  # xatolik yuz berganda to'liq tafsilotni (qaysi qatorda, nima sababdan) ko'rish uchun
from lib import db  # ma'lumotlar bazasi funksiyalari
from lib import telegram_auth  # Mini App'dan kelgan so'rovni tasdiqlash funksiyasi
from lib.webhook_handler import (
    yangilanishni_qayta_ishla,  # Telegram xabarlarini qayta ishlovchi funksiya
    zayavkani_qabul_qil,  # "qabul qildim" umumiy funksiyasi (Mini App ham shuni ishlatadi)
    zayavkani_tugat,  # "consultatsiya berdim" umumiy funksiyasi (Mini App ham shuni ishlatadi)
    yonalish_royxatini_ornat,  # Mini App'da yo'nalish(lar)ni saqlash funksiyasi
    zayavkani_javob_bermadi_deb_belgila,  # "Telefonni ko'tarmadi" umumiy funksiyasi
    zayavkani_qayta_qabul_qil,  # "qayta aloqaga chiqish"dan "qabul qilish" umumiy funksiyasi
    zayavkani_kutishga_qoy,  # "Kutish rejimi"ni yoqish (muammo hali hal bo'lmaganda)
    zayavkani_kutishdan_davom_ettir,  # kutish rejimidagi mijozni "Davom ettirish"
)
from lib.timer_handler import barcha_navbatni_tekshir  # taymerlarni tekshiruvchi funksiya
from lib.dashboard_html import DASHBOARD_HTML  # rahbarlar paneli uchun tayyor HTML sahifa
from lib.mini_app_html import MINI_APP_HTML  # xodimlar uchun Mini App HTML sahifasi
from lib.config import CRON_SECRET  # taymer manzili uchun maxfiy parol

app = FastAPI()  # bitta umumiy FastAPI ilovasi — Vercel aynan shuni "app" deb topadi


@app.post("/api/webhook")
async def webhook(so_rov: Request):
    # Telegram har bir yangi voqeada (xabar, tugma bosish) shu manzilga so'rov yuboradi
    malumot = await so_rov.json()  # kelgan JSON ma'lumotni o'qiymiz

    # TASHXIS UCHUN: Telegram'dan kelgan HAR BIR yangilanishning TO'LIQ (xom) matnini logga yozamiz —
    # hech narsani filtrlamasdan. Shunda muammoni qidirishda hech narsa yashirin qolmaydi
    print(f"XOM YANGILANISH KELDI: {malumot}")

    update_id = malumot.get("update_id")  # Telegramning har bir yangilanishiga beradigan noyob raqami
    if update_id is not None and not db.update_yangimi(update_id):
        # agar bu update_id avval qayta ishlangan bo'lsa (Telegram uni ikki marta yuborgan bo'lsa)
        return {"ok": True}  # qayta ishlamasdan, shunchaki "joyida" deb javob qaytaramiz

    # MUHIM: xatolikni ushlab qolamiz va Vercel Logs'ga TO'LIQ matn bilan (qaysi qator, qaysi sabab)
    # chiqarib beramiz — aks holda xatolik "yashirin" qolib, sababini topib bo'lmay qoladi.
    # Shu bilan birga, Telegram'ga har doim 200 qaytaramiz — aks holda Telegram xatolikni
    # "webhook ishlamayapti" deb hisoblab, keyingi xabarlarni ham yuborishni to'xtatib qo'yishi mumkin.
    try:
        await yangilanishni_qayta_ishla(malumot)  # asosiy mantiqqa uzatamiz
    except Exception:
        print("XATOLIK /api/webhook ichida:")
        print(traceback.format_exc())  # to'liq xatolik matni — Vercel Logs'da ko'rinadi

    return {"ok": True}  # Telegramga har doim "hammasi joyida" deb javob qaytaramiz


@app.get("/api/check_timers")
@app.post("/api/check_timers")
async def check_timers(so_rov: Request):
    # tashqi cron xizmati (masalan cron-job.org) har 1 daqiqada shu manzilga so'rov yuboradi
    kelgan_parol = so_rov.headers.get("x-cron-secret", "")  # so'rov headeridagi maxfiy parolni o'qiymiz
    if CRON_SECRET and kelgan_parol != CRON_SECRET:  # agar parol noto'g'ri bo'lsa
        return {"ok": False, "xato": "Ruxsat yo'q"}  # rad etamiz
    natija = barcha_navbatni_tekshir()  # barcha navbatdagi zayavkalarni tekshiramiz
    return {"ok": True, **natija}  # natijani qaytaramiz


@app.get("/")
async def salomat():
    # bu oddiy "tekshiruv" manzili — brauzerda ochib, bot ishlab turganini bilish uchun
    return {"holat": "FINCUBE support bot ishlamoqda"}


@app.get("/dashboard")
async def dashboard_sahifasi():
    # rahbarlar uchun jonli statistika sahifasi — brauzerda ochib, istalgan payt kuzatib turish mumkin
    return HTMLResponse(content=DASHBOARD_HTML)


@app.get("/api/dashboard")
async def dashboard_malumoti():
    # dashboard sahifasi shu manzildan har 5 soniyada yangi ma'lumot so'rab turadi
    return db.statistika()


@app.get("/app")
async def mini_app_sahifasi():
    # xodimlar uchun Telegram Mini App sahifasi — bot menyusidan ochiladi
    return HTMLResponse(content=MINI_APP_HTML)


def _foydalanuvchini_tekshir(so_rov: Request):
    # Mini App'dan kelgan so'rov ichidagi "initData"ni tekshirib, tegishli xodimni topadi
    # agar tasdiqlanmasa yoki xodim topilmasa, None qaytaradi
    init_data = so_rov.headers.get("x-telegram-init-data", "")  # header'dan initData'ni olamiz
    foydalanuvchi = telegram_auth.tekshir_init_data(init_data)  # imzoni tekshiramiz
    if not foydalanuvchi:  # agar imzo noto'g'ri bo'lsa
        return None
    return db.xodim_topilsin(foydalanuvchi["id"])  # shu Telegram ID bo'yicha xodimni qidiramiz


@app.get("/api/app/royxat")
async def app_royxat(so_rov: Request):
    # Mini App ochilganda, xodimning holati va butun panel ma'lumotini qaytaradi
    xodim = _foydalanuvchini_tekshir(so_rov)
    if not xodim:  # agar tasdiqlanmasa yoki xodimlar ro'yxatida bo'lmasa
        return {"ok": False, "xato": "Siz xodimlar ro'yxatida emassiz yoki ilova tasdiqlanmadi."}

    joriy = db.xodimning_joriy_zayavkasi(xodim["id"]) if xodim["holat"] == "band" else None
    panel = db.app_panel_malumoti(xodim.get("rol", "xodim"))  # rolga qarab mos ma'lumotlarni olamiz

    return {
        "ok": True,
        "xodim": xodim,
        "mening_joriyim": joriy,
        **panel,  # navbatdagilar, jarayondagilar, bugungi statistika va (kerak bo'lsa) owner ma'lumotlari
    }


@app.post("/api/app/qabul")
async def app_qabul(so_rov: Request):
    # Mini App'da "Qabul qildim" tugmasi bosilganda shu manzilga so'rov keladi
    xodim = _foydalanuvchini_tekshir(so_rov)
    if not xodim:
        return {"ok": False, "xabar": "Siz xodimlar ro'yxatida emassiz."}
    gavda = await so_rov.json()  # so'rov ichidagi {"zayavka_id": ...} ni o'qiymiz
    return zayavkani_qabul_qil(xodim, gavda.get("zayavka_id"))


@app.post("/api/app/yonalish")
async def app_yonalish(so_rov: Request):
    # Mini App'da xodim ZUB/Buxgalteriya/UNF dan tanlab, saqlaganda shu manzilga so'rov keladi
    xodim = _foydalanuvchini_tekshir(so_rov)
    if not xodim:
        return {"ok": False, "xabar": "Siz xodimlar ro'yxatida emassiz."}
    gavda = await so_rov.json()  # {"zayavka_id": ..., "yonalishlar": ["ZUB", "UNF"]}
    return yonalish_royxatini_ornat(xodim, gavda.get("zayavka_id"), gavda.get("yonalishlar", []))


@app.post("/api/app/tugat")
async def app_tugat(so_rov: Request):
    # Mini App'da "Consultatsiya berdim" tugmasi bosilganda shu manzilga so'rov keladi
    xodim = _foydalanuvchini_tekshir(so_rov)
    if not xodim:
        return {"ok": False, "xabar": "Siz xodimlar ro'yxatida emassiz."}
    gavda = await so_rov.json()
    return zayavkani_tugat(xodim, gavda.get("zayavka_id"))


@app.post("/api/app/javob-bermadi")
async def app_javob_bermadi(so_rov: Request):
    # Mini App'da "Telefonni ko'tarmadi" tugmasi bosilganda shu manzilga so'rov keladi
    xodim = _foydalanuvchini_tekshir(so_rov)
    if not xodim:
        return {"ok": False, "xabar": "Siz xodimlar ro'yxatida emassiz."}
    gavda = await so_rov.json()
    return zayavkani_javob_bermadi_deb_belgila(xodim, gavda.get("zayavka_id"))


@app.post("/api/app/qayta-qabul")
async def app_qayta_qabul(so_rov: Request):
    # Mini App'da "Qayta aloqaga chiqish" bo'limida "Qabul qilish" bosilganda shu manzilga so'rov keladi
    xodim = _foydalanuvchini_tekshir(so_rov)
    if not xodim:
        return {"ok": False, "xabar": "Siz xodimlar ro'yxatida emassiz."}
    gavda = await so_rov.json()
    return zayavkani_qayta_qabul_qil(xodim, gavda.get("zayavka_id"))


@app.post("/api/app/kutish")
async def app_kutish(so_rov: Request):
    # Mini App'da "Kutish rejimi" tugmasi bosilganda shu manzilga so'rov keladi
    xodim = _foydalanuvchini_tekshir(so_rov)
    if not xodim:
        return {"ok": False, "xabar": "Siz xodimlar ro'yxatida emassiz."}
    gavda = await so_rov.json()
    return zayavkani_kutishga_qoy(xodim, gavda.get("zayavka_id"))


@app.post("/api/app/kutishdan-davom")
async def app_kutishdan_davom(so_rov: Request):
    # Mini App'da kutish rejimidagi mijoz uchun "Davom ettirish" bosilganda shu manzilga so'rov keladi
    xodim = _foydalanuvchini_tekshir(so_rov)
    if not xodim:
        return {"ok": False, "xabar": "Siz xodimlar ro'yxatida emassiz."}
    gavda = await so_rov.json()
    return zayavkani_kutishdan_davom_ettir(xodim, gavda.get("zayavka_id"))


def _rolga_qarab_tozala(tekshiruvchi, malumot):
    # Mijozning bahosi va izohi FAQAT rahbarlarga (owner/super_user) yuboriladi. Oddiy xodim o'z
    # ko'rsatkichlarini ochganda bu maydonlar serverning o'zida olib tashlanadi — shunda ular
    # brauzerga umuman yetib bormaydi (faqat ekranda yashirish yetarli emas)
    if tekshiruvchi.get("rol") in ("owner", "super_user"):
        return malumot
    for kalit in ("tugallandi", "qayta_aloqa", "javob_bermadi"):
        for mijoz in malumot.get(kalit, []):
            mijoz["yulduz"] = None
            mijoz["izoh"] = None
            mijoz["baho_holati"] = None
    return malumot


@app.get("/api/app/xodim-mijozlari/{xodim_id}")
async def app_xodim_mijozlari(xodim_id: int, so_rov: Request):
    # Analitikada bitta xodim ustiga bosilganda, uning BUGUN gaplashgan mijozlari 3 toifada
    # (tugallandi / qayta_aloqa / javob_bermadi) qaytariladi — bu MAXFIY ma'lumot,
    # shuning uchun faqat owner/super_user YOKI shu xodimning O'ZI ko'rishi mumkin
    tekshiruvchi = _foydalanuvchini_tekshir(so_rov)
    ruxsat_bormi = tekshiruvchi and (
        tekshiruvchi.get("rol") in ("owner", "super_user") or tekshiruvchi.get("id") == xodim_id
    )
    if not ruxsat_bormi:
        return {"ok": False, "xato": "Sizda bu ma'lumotni ko'rish huquqi yo'q."}
    return {"ok": True, **_rolga_qarab_tozala(tekshiruvchi, db.xodimning_bugungi_mijozlari(xodim_id))}


@app.get("/api/app/xodim-oylik-mijozlari/{xodim_id}")
async def app_xodim_oylik_mijozlari(xodim_id: int, so_rov: Request):
    # Oylik hisobotda bitta xodim ustiga bosilganda, uning SHU OY gaplashgan mijozlari
    # xuddi shu 3 toifada qaytariladi — faqat owner/super_user YOKI shu xodimning O'ZI ko'rishi mumkin
    tekshiruvchi = _foydalanuvchini_tekshir(so_rov)
    ruxsat_bormi = tekshiruvchi and (
        tekshiruvchi.get("rol") in ("owner", "super_user") or tekshiruvchi.get("id") == xodim_id
    )
    if not ruxsat_bormi:
        return {"ok": False, "xato": "Sizda bu ma'lumotni ko'rish huquqi yo'q."}
    return {"ok": True, **_rolga_qarab_tozala(tekshiruvchi, db.xodimning_oylik_mijozlari(xodim_id))}
