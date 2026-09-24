# FINCUBE Support Bot — o'rnatish yo'riqnomasi

Bu bot FINCUBE support guruhiga tushgan mijoz murojaatlarini avtomatik boshqaradi:
INN/telefon tekshiradi, 4 nafar xodim orasida navbat bilan taqsimlaydi va 20 daqiqalik
taymerni kuzatadi.

## 1-qadam: Telegram bot yaratish

1. Telegram'da **@BotFather**ga yozing, `/newbot` buyrug'ini bering, botga nom bering.
2. BotFather sizga **token** beradi (masalan `123456:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`) — buni saqlab qo'ying.
3. Botni FINCUBE support guruhingizga **admin** qilib qo'shing (xabarlarni o'qishi va yozishi uchun).
4. Guruhning **chat ID**sini bilish uchun botga guruhda biror xabar yozdiring, so'ng brauzerda quyidagi manzilni oching (TOKEN o'rniga o'z tokeningizni qo'ying):
   `https://api.telegram.org/botTOKEN/getUpdates`
   Javobda `"chat":{"id": -100xxxxxxxxxx, ...}` qatorini topasiz — shu raqam sizning `SUPPORT_GROUP_ID`ingiz.

## 2-qadam: Supabase (bepul baza) ochish

1. https://supabase.com saytida ro'yxatdan o'ting, yangi loyiha (**New Project**) yarating.
2. Chap menyudan **SQL Editor**ni oching, ushbu papkadagi `schema.sql` faylining ichidagi
   barcha matnni nusxalab joylashtiring va **Run** tugmasini bosing — bu 3 ta jadvalni yaratadi.
3. Chap menyudan **Table Editor -> xodimlar** bo'limiga o'ting va 4 nafar xodimingizni
   qo'lda kiriting: har biri uchun `telegram_id` (xodimning shaxsiy Telegram ID raqami —
   buni bilish uchun xodim @userinfobot'ga yozishi kifoya) va `ism_familiya`ni yozing.
4. **Settings -> API** bo'limidan `Project URL` (bu `SUPABASE_URL`) va
   `service_role` kaliti (bu `SUPABASE_KEY`, MAXFIY — hech kimga bermang) ni oling.

## 3-qadam: Vercel'ga joylashtirish

1. Bu papkani GitHub'ga yuklang (yangi repository yarating, shu fayllarni push qiling).
2. https://vercel.com saytida **Add New -> Project** tugmasi orqali o'sha repositoryni tanlang.
3. **Environment Variables** bo'limiga quyidagilarni kiriting:
   - `TELEGRAM_BOT_TOKEN` — 1-qadamda olingan token
   - `SUPPORT_GROUP_ID` — 1-qadamda topilgan guruh IDsi (manfiy son, masalan `-1001234567890`)
   - `SUPABASE_URL` — 2-qadamdagi Project URL
   - `SUPABASE_KEY` — 2-qadamdagi service_role kaliti
   - `CRON_SECRET` — o'zingiz o'ylab topgan istalgan maxfiy so'z (masalan `fincube_maxfiy_2025`)
4. **Deploy** tugmasini bosing. Bir necha daqiqadan so'ng sizga
   `https://loyihangiz-nomi.vercel.app` ko'rinishidagi manzil beriladi.

## 4-qadam: Telegram webhook'ni ulash

Brauzerda (yoki terminalda) quyidagi manzilni oching — TOKEN va DOMENINGIZNI almashtiring:

```
https://api.telegram.org/botTOKEN/setWebhook?url=https://loyihangiz-nomi.vercel.app/api/webhook
```

Javobda `"ok":true` chiqsa — muvaffaqiyatli ulandi.

## 5-qadam: Har 1 daqiqada taymerni tekshiruvchi cron sozlash

Vercel'ning bepul tarifida o'zining cron funksiyasi kuniga faqat 1 marta ishlaydi,
bizga esa har daqiqada tekshirish kerak. Shuning uchun **bepul tashqi xizmat** ishlatamiz:

1. https://cron-job.org saytida bepul ro'yxatdan o'ting.
2. Yangi "cronjob" yarating:
   - **URL:** `https://loyihangiz-nomi.vercel.app/api/check_timers`
   - **Schedule:** har 1 daqiqada (`* * * * *`)
   - **Request method:** GET
   - **Custom header** qo'shing: `x-cron-secret` = 3-qadamda o'zingiz o'ylab topgan `CRON_SECRET` qiymati
3. Saqlang — endi bot har daqiqada barcha kutayotgan mijozlarni avtomatik tekshiradi.

## Botning ishlash mantig'i (qisqacha)

- Mijoz guruhga yozadi → bot INN va telefonni (ikkalasi ham 9 xonali raqam, formatidan qat'i nazar) qidiradi.
- Topilmasa — mijozdan qayta so'raydi va xodimlarni chaqirmaydi.
- Topilsa — agar shu mijoz bilan so'nggi 3 kun ichida gaplashgan xodim bo'lsa, birinchi navbatda O'SHA xodimga taklif yuboriladi; aks holda barcha bo'sh xodimlarga.
- Xodim "✅ Qabul qildim" bossa — u band bo'ladi, boshqalarga endi bu mijoz ko'rinmaydi.
- Xodim "☑️ Consultatsiya berdim" bossa — u bo'shaydi va navbatdagi (yoki unga ustuvor) mijozga avtomatik taklif ketadi.
- 10 daqiqa o'tsa — holat "sariq"qa o'tadi (ichki belgi).
- 15 daqiqa o'tsa (5 daqiqa qolganda) — BARCHA 4 xodimga, band bo'lsa ham, majburiy signal boradi.
- 20 daqiqa to'lib, hech kim qabul qilmasa — mijozga avtomatik uzr xabari yuboriladi.

## Keyingi bosqich: FINCUBE / 1C bazasiga o'tish

Bot sinovdan muvaffaqiyatli o'tgach, faqat `lib/db.py` faylini FINCUBE/1C bazangizga
mos ravishda qayta yozish kifoya — qolgan barcha fayllar (webhook.py, check_timers.py)
o'zgarishsiz qoladi, chunki ular faqat `db.py`dagi funksiyalarni chaqiradi.

## 6-qadam: Mini App'ni bot menyusiga ulash (ixtiyoriy, lekin tavsiya etiladi)

Xodimlar botning ichida (Telegram guruhidan tashqarida ham) "Ish paneli"ni ochib,
mijozlarni qabul qilishi/yakunlashi uchun:

1. Telegram'da **@BotFather**ga yozing
2. `/mybots` buyrug'ini yuboring, botingizni tanlang
3. **"Bot Settings"** → **"Menu Button"** → **"Configure Menu Button"** ni tanlang
4. So'ralganda:
   - **Button text:** `Ish paneli` (yoki xohlagan nom)
   - **Web App URL:** `https://fincubesupportbot.vercel.app/app`

Shundan keyin har bir xodim botning yozish oynasi tagida (chap pastda, 📎 yonida)
"Ish paneli" tugmasini ko'radi — bosilsa, ilova ochiladi. Ilovadagi "Qabul qildim" /
"Consultatsiya berdim" tugmalari guruhdagi bilan bir xil ishlaydi va guruhdagi
xabarni ham yangilaydi.

## Rahbarlar paneli (statistika)

Istalgan brauzerda oching: `https://fincubesupportbot.vercel.app/dashboard`
Bu sahifa har 5 soniyada avtomatik yangilanadi, login talab qilmaydi — havolani
faqat ishonchli odamlarga bering (chunki hozircha ochiq, parolsiz).

## Xodimlarga rol belgilash

Har bir xodimga uchta roldan birini berish mumkin: `super_user`, `owner`, `xodim`.
Sozlanmagan xodimlar avtomatik `xodim` (oddiy support) hisoblanadi.

Supabase SQL Editor'da, xodimning telegram_id'sini bilgan holda:

```sql
-- Masalan, birovni "owner" (faqat ko'ruvchi, hech narsani o'zgartira olmaydigan) qilib belgilash:
update xodimlar set rol = 'owner' where telegram_id = 111111111;

-- Yoki "super_user" qilib belgilash (to'liq huquq):
update xodimlar set rol = 'super_user' where telegram_id = 111111111;
```

**Rollar:**
- `xodim` — mijoz qabul qiladi va consultatsiya yakunlaydi (support team / support person)
- `super_user` — xuddi xodim kabi to'liq huquqqa ega
- `owner` — Mini App'ni ochib ko'ra oladi (navbat, taymerlar, statistika), lekin
  "Qabul qildim" / "Consultatsiya berdim" tugmalari unga ko'rinmaydi va u bosishga
  urinsa ham, server rad etadi (xavfsizlik serverning o'zida tekshiriladi, faqat
  ekranda yashirilib qolmaydi)

## Google Sheets (mijozlar bazasi) ulash

Bot endi har bir mijozning INN'ini Google Sheets'dagi "Ligotniy" va "Platniy"
jadvallaridan avtomatik tekshiradi. Agar mijoz topilmasa yoki shartnoma muddati
o'tgan bo'lsa, unga (imkon bo'lsa shaxsiy chatiga, bo'lmasa guruhga) uzr xabari
va shartnoma bo'yicha mas'ul xodimning kontakti yuboriladi — navbatga qo'yilmaydi.

**Vercel Environment Variables'ga qo'shing:**

| Nomi | Qiymati |
|---|---|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Service Account'dan yuklab olgan `.json` faylining TO'LIQ matni (hammasi, `{` dan `}` gacha, bitta qatorga joylashtiring) |
| `MIJOZLAR_SHEET_ID` | Google Sheets havolasidagi ID (masalan `1TfKjT-VvXoL5yUwimQoNwsm7kzORvizGzddLFMjri44`) |
| `LIGOTNIY_VARAQ` | Bepul support varag'ining nomi (standart: `Ligotniy`) |
| `PLATNIY_VARAQ` | Pullik obuna varag'ining nomi (standart: `Platniy`) |
| `SHARTNOMA_XODIM_NICK` | Shartnoma bo'yicha mas'ul xodimning Telegram nomi (masalan `@aziz_sales`) |
| `SHARTNOMA_XODIM_TEL` | Shu xodimning telefon raqami |

**Muhim eslatma:** Telegram qoidasiga ko'ra, bot mijozga **shaxsiy (lichka)** xabar
yubora olishi uchun, mijoz avval botning shaxsiy chatini ochib, kamida bir marta
`/start` bosishi kerak. Agar mijoz buni qilmagan bo'lsa, bot lichkaga yoza olmaydi
va **avtomatik ravishda guruhga** (mijozning xabariga javob tariqasida) yozadi —
xabar baribir yetib boradi, faqat guruh ichida.

Jadval ustunlari **aynan** shu nomda bo'lishi shart: `ИНН` va `Дата окончания`
(sana `DD.MM.YYYY` formatida, masalan `20.12.2026`).

## Muhim: "Ish paneli" tugmasi endi faqat xodimlarga ko'rinadi

Avval BotFather orqali sozlangan Menu Button **BUTUN bot uchun global** edi — ya'ni
mijozlar ham botga yozganda shu tugmani ko'rar edi (garchi ichkariga kira olmasa ham).
Endi bu avtomatik boshqariladi: bot birinchi marta shaxsiy xabar kelganda (masalan
`/start`), yozgan odam xodimmi-yo'qmi tekshiradi va faqat xodimlarga alohida tugma
beradi.

**Shuning uchun BotFather'dagi global Menu Button sozlamasini olib tashlang:**
1. **@BotFather** → `/mybots` → botingiz → **Bot Settings** → **Menu Button**
2. **"Remove Menu Button"** (yoki shunga o'xshash, tugmani o'chirish/standartga qaytarish) variantini tanlang

Yangi Environment Variable qo'shing:

| Nomi | Qiymati |
|---|---|
| `APP_URL` | `https://fincubesupportbot.vercel.app` (oxirida `/` bo'lmasin) |

## Yo'nalish tanlovi va baholash tizimi

Endi xodim "Consultatsiya berdim" bosganda, DARHOL yakunlanmaydi — avval **ZUB /
Buxgalteriya / UNF** dan kamida 1, ko'pi bilan 2 tasini tanlashi (guruhda ham,
Mini App'da ham) shart. Shundan keyingina zayavka yakunlanadi.

Yakunlangach, mijozga (imkon bo'lsa lichkaga) **1-5 yulduzcha baholash so'rovi**
avtomatik yuboriladi, tagida ixtiyoriy izoh yozish imkoniyati bilan. Agar mijoz
**3 kun** ichida baholamasa, so'rov "muddati o'tgan" deb belgilanadi.

**Muhim (maxfiylik):** agar mijozga lichkaga yozib bo'lmasa (u botni hali "start"
qilmagan bo'lsa), bot HECH QACHON to'liq (maxfiy) matnni guruhga yubormaydi —
guruhda faqat "sizga shaxsiy xabarimiz bor, /start bosing" degan, hech narsani
oshkor qilmaydigan qisqa eslatma qoladi.

Bazaga yangi jadval/ustun qo'shildi — SQL Editor'da ishga tushiring:
```sql
alter table zayavkalar add column if not exists yonalishlar text not null default '';

create table if not exists baholashlar (
    id bigserial primary key,
    zayavka_id bigint not null references zayavkalar(id),
    mijoz_id bigint not null references mijozlar(id),
    xodim_id bigint references xodimlar(id),
    yulduz int,
    izoh text,
    holat text not null default 'kutilmoqda',
    chat_id bigint,
    xabar_id bigint,
    yaratilgan_vaqt timestamptz not null default now(),
    javob_vaqt timestamptz
);
create index if not exists idx_baholash_holat on baholashlar(holat);
create index if not exists idx_baholash_mijoz on baholashlar(mijoz_id);
```
