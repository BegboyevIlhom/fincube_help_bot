# Bu fayl barcha maxfiy sozlamalarni (token, kalit va h.k.) bir joydan olib turadi
# Bu qiymatlarni Vercel panelida "Environment Variables" bo'limiga kiritasiz —
# kodning ichiga hech qachon to'g'ridan-to'g'ri yozmaslik kerak (xavfsizlik uchun)

import os  # operatsion tizim muhit o'zgaruvchilarini o'qish uchun kutubxona

# Telegram bot tokeni (BotFather'dan olinadi)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# Telegram Bot API manzili, tokenni ichiga qo'shib tayyorlab qo'yamiz
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# FINCUBE support guruh(lar)ining Telegram chat ID raqami (manfiy son bo'ladi, masalan -1001234567890).
# Bir nechta guruh bo'lsa, VERGUL bilan ajratib yozing, masalan: "-1001234567890,-1009876543210"
SUPPORT_GROUP_IDLAR = [
    int(x.strip()) for x in os.environ.get("SUPPORT_GROUP_ID", "0").split(",") if x.strip()
]

# Supabase loyihasining URL manzili (Supabase panel -> Settings -> API)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")

# Supabase'ning maxfiy (service_role) kaliti — yozish huquqi uchun kerak
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# Taymer tekshiruvchi manzilni tashqi shaxslar chaqirib yubormasligi uchun maxfiy parol
# cron-job.org sozlaganda shu parolni so'rov headeriga qo'shamiz
CRON_SECRET = os.environ.get("CRON_SECRET", "")

# Taymer sozlamalari (daqiqalarda) — talab shartlariga mos
TAYMER_JAMI_DAQIQA = 20      # mijoz 20 daqiqa ichida aloqaga chiqilishi kerak
TAYMER_SARIQ_DAQIQA = 10     # 10 daqiqadan keyin "sariq" bosqich boshlanadi
TAYMER_QIZIL_QOLGAN_DAQIQA = 5  # oxirgi 5 daqiqa qolganda majburiy barcha xodimlarni chaqirish

# Xodim mijozga qo'ng'iroq qilib, javob bermasa, shuncha marta urinishi mumkin
# (shu sondan o'tsa, mijozga yakuniy xabar boradi va zayavka yopiladi)
# Xodim "Consultatsiya berdim" bosishdan oldin shulardan kamida 1, ko'pi bilan 2 tasini tanlashi shart
MUMKIN_YONALISHLAR = ["ZUB", "Buxgalteriya", "UNF"]

# Xodim mijozga qo'ng'iroq qilib, javob bermasa, shuncha marta urinishi mumkin
# (shu sondan o'tsa, mijozga yakuniy xabar boradi va zayavka yopiladi)
QONGIROQ_URINISH_MAKS = 3

# Mijoz baholashni shuncha kun ichida bermasa, so'rov "muddati o'tgan" deb belgilanadi
BAHOLASH_MUDDAT_KUN = 3

# Botning umumiy joylashgan manzili (Mini App havolasini avtomatik yasash uchun kerak)
# masalan: https://fincubesupportbot.vercel.app
APP_URL = os.environ.get("APP_URL", "").rstrip("/")

# Botning foydalanuvchi nomi (@ belgisisiz) — mijozni to'g'ridan-to'g'ri botning shaxsiy chatiga
# ochib beradigan havola (deep link) yasash uchun kerak, masalan: https://t.me/<BOT_USERNAME>?start=...
BOT_USERNAME = os.environ.get("BOT_USERNAME", "fincube_support_bot")

# ---------------------- GOOGLE SHEETS (mijozlar bazasi) ----------------------

# Xizmat hisobining (Service Account) maxfiy kaliti — JSON faylining TO'LIQ matni
# ("{" dan "}" gacha), bitta qator sifatida Vercel Environment Variables'ga joylashtiriladi
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")

# Mijozlar bazasi joylashgan Google Sheets jadvalining ID raqami
# (jadval havolasidagi /d/ va /edit orasidagi uzun matn)
MIJOZLAR_SHEET_ID = os.environ.get("MIJOZLAR_SHEET_ID", "")

# Bepul (90 kunlik) va pullik obuna ma'lumotlari saqlangan varaq (tab) nomlari
LIGOTNIY_VARAQ = os.environ.get("LIGOTNIY_VARAQ", "Ligotniy")
PLATNIY_VARAQ = os.environ.get("PLATNIY_VARAQ", "Platniy")

# Shartnoma masalasi bilan shug'ullanadigan xodimning kontakti
# (mijozga "shartnomangiz yo'q/tugagan" xabarida shu kontakt ko'rsatiladi)
SHARTNOMA_XODIM_NICK = os.environ.get("SHARTNOMA_XODIM_NICK", "@sotuv_menejer")
SHARTNOMA_XODIM_TEL = os.environ.get("SHARTNOMA_XODIM_TEL", "+998 90 000 00 00")
