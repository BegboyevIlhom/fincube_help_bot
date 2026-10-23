# Bu ZIP'da nima o'zgardi (2-versiya)

## 1. Bitrix'da bitta mijoz uchun bir nechta Deal yaratilib ketishi — TUZATILDI
**Sabab:** `mijozlar` jadvalida `bitrix_contact_id`/`bitrix_deal_id` ustunlari yo'q edi
(yoki baza yozuvi boshqa sababdan muvaffaqiyatsiz bo'lgan), shuning uchun bot har safar
"bu mijozning Deal'i hali yo'q" deb o'ylab, yangisini yarataverardi.

**Tuzatish — ikki qatlamli himoya (`lib/bitrix.py`):**
1. Avvalgidek, bazada saqlangan `bitrix_deal_id` bo'lsa, o'shani ishlatadi.
2. **YANGI:** agar bazada yo'q bo'lsa, yangi Deal yaratishdan OLDIN, Bitrix'ning
   o'zidan shu mijozning (Kontaktning) ESKI Deal'i bormi qidiradi. Topilsa, o'shani
   ishlatadi — hatto baza yozuvi ishlamagan bo'lsa ham, endi takroriy Deal yaratilmaydi.
3. Baza yozuvi muvaffaqiyatsiz bo'lsa, endi aniq ogohlantirish logga yoziladi:
   `"OGOHLANTIRISH: Bitrix ID'lari bazaga yozilmadi ..."`

**SHART:** quyidagi SQL Supabase'da ishga tushirilishi KERAK (agar hali qilinmagan bo'lsa):
```sql
alter table mijozlar add column if not exists bitrix_contact_id bigint;
alter table mijozlar add column if not exists bitrix_deal_id bigint;

NOTIFY pgrst, 'reload schema';
```
Buni ishga tushirmasangiz ham bot endi takroriy Deal yaratmaydi (yangi himoya tufayli),
lekin har safar Bitrix'ga qo'shimcha so'rov yuborishga majbur bo'ladi (sal sekinroq) va
mas'ul xodim/bosqich tarixi kamroq ishonchli bo'ladi. **SQL'ni ishga tushirish tavsiya qilinadi.**

## 2. Guruh havolasi — TUZATILDI
`lib/webhook_handler.py` da eski (`https://t.me/+W2fmayb2qeMxZjJi`) havola bot mijozga
botning shaxsiy chatida "support guruhiga yozing" deganda ishlatilar edi. Endi
`https://t.me/fincube_its` ga almashtirildi.

## 3. "edited_message" (tahrirlangan xabar) — KOD TOMONDAN TAYYOR, lekin Telegram
sozlamasini QO'LDA tekshirish kerak
Ilgari bu muammo bir marta tuzatilgan edi, lekin Bitrix Contact Center bilan sarguzashtlar
paytida webhook qayta o'rnatilganda bu sozlama qayta eskiga qaytib ketgan bo'lishi mumkin.
Quyidagini brauzerda oching (TOKEN — `fincube_help_bot` tokeni):
```
https://api.telegram.org/botTOKEN/setWebhook?url=https://fincube-help-bot.vercel.app/api/webhook&allowed_updates=["message","edited_message","callback_query"]
```
So'ng tekshiring:
```
https://api.telegram.org/botTOKEN/getWebhookInfo
```
`allowed_updates` ichida `edited_message` ham ko'rinishi SHART. Bu bo'lmasa, mijoz avvalgi
xabarini tahrirlab INN/telefon qo'shsa, bot buni ko'rmay qoladi.

## Qilish tartibi
1. **Supabase**: yuqoridagi (1-bo'lim) SQL'ni ishga tushiring.
2. **Vercel**: shu ZIP'dagi `lib/bitrix.py` va `lib/webhook_handler.py` fayllarini
   GitHub repo'ga qo'yib, commit/push qiling (deploy avtomatik ishga tushadi).
3. **Telegram**: yuqoridagi (3-bo'lim) `setWebhook` havolasini oching.
4. **Sinov**: yangi (hali murojaat qilmagan) raqamdan guruhga INN+telefon bilan xabar
   yuboring, bot javob berganini va Bitrix'da BITTA Deal paydo bo'lganini tekshiring.
   Keyin SHU raqamdan yana bir marta murojaat yuboring — Bitrix'da YANGI Deal EMAS,
   ESKISIGA izoh qo'shilganini tekshiring.

## Tegilmagan fayllar
`lib/mini_app_html.py`, `lib/dashboard_html.py`, `lib/telegram.py`, `lib/telegram_auth.py`,
`lib/sheets.py`, `lib/logic.py`, `lib/config.py`, `lib/db.py`, `lib/timer_handler.py`,
`api/index.py`, `schema.sql`, `pyproject.toml`, `vercel.json`, `README.md` — bu safar
o'zgarishsiz (ular o'tgan safar allaqachon tuzatilgan edi).

## 4. (v3) Yakuniy tekshiruv — bitta qo'shimcha tuzatish
`lib/webhook_handler.py`ning `shartnoma_yoq` filialida Bitrix sinxronlash endi faqat
bazaviy (shartli/atomik) yozuv chindan muvaffaqiyatli bo'lgandagina chaqiriladi. Avval
bu tekshiruvsiz chaqirilar edi — kamdan-kam holatda (ikkita deyarli bir vaqtdagi
xabar/tahrir) Bitrix'dagi Deal'ni noto'g'ri "shartnoma yo'q"ga qaytarib yuborishi
mumkin edi. Boshqa hamma joy to'liq qayta tekshirildi — muammo topilmadi.

## 5. (v4) Yana bitta "1С-fix"dan kelib chiqqan nuqson tuzatildi
`lib/logic.py` — agar label (masalan "tel") raqamga **bo'shliqsiz, tinish belgisi bilan**
yopishgan bo'lsa (masalan "tel;938535257", bo'shliqsiz ";" bilan), oldingi tuzatishim
bu raqamni butunlay yo'qotib yuborar edi (chunki so'z ";" bilan boshlangani uchun
"sof raqam" deb hisoblanmas edi). Endi so'zning chetidagi tinish belgilari (:, ;, ,, .
va h.k.) avval olib tashlanadi, SHUNDAN KEYIN "sof raqammi" deb tekshiriladi — bu "1С"
tuzatishiga TEGMAYDI (harflar hamon to'g'ri rad etiladi), faqat tinish belgilarini
to'g'ri o'tkazib yuboradi. 10 xil holat bilan qayta sinovdan o'tkazildi, hammasi to'g'ri.

## 6. (v5) Google Sheets: shartnoma "topilmadi" degan noto'g'ri natija — TUZATILDI
`lib/sheets.py`da ikkita zaif nuqta topildi va tuzatildi:

1. **INN solishtirish juda qattiq edi.** Agar Sheets'da INN ustuni "raqam" turida
   saqlangan bo'lsa, Google uni ba'zan "313 003 874" yoki "313,003,874" ko'rinishida
   formatlab qaytarishi mumkin. Bizning tomondagi toza "313003874" bilan so'z-ba-so'z
   solishtirilgani uchun, mos kelmay, "topilmadi" deb chiqardi — garchi shartnoma
   chindan bor bo'lsa ham. Endi solishtirishdan oldin ikkala tomondagi raqamlardan
   FAQAT sonlarni olib solishtiramiz.
2. **Ustun sarlavhalari ("ИНН", "Дата окончания") aynan bir xil bo'lishi talab
   qilinardi.** Agar bitta jadvalda sarlavhada ortiqcha bo'shliq yoki boshqacha
   katta-kichik harf bo'lsa, O'SHA BUTUN JADVAL sukut saqlab o'tkazib yuborilardi
   (hech qanday xato chiqmasdan). Endi bo'shliq va katta-kichik harfga e'tibor
   berilmaydi.

Sintetik sinov (Platniy'da bo'shliqli INN + ertangi sana bilan FAOL shartnoma,
Ligotniy'da toza INN + kechagi sana bilan MUDDATI O'TGAN shartnoma) bilan tekshirildi
— natija to'g'ri "faol" chiqdi.

**Diqqat:** qidiruv TARTIBI (Platniy/Ligotniy ikkalasini ham to'liq tekshirib, eng
yaxshi/eng uzoq sanani tanlash) allaqachon to'g'ri ishlar edi — bu muammo emas edi.
Asosiy xato INN va sarlavha solishtirishning haddan tashqari qattiqligida edi.
