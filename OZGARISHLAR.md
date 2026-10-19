# Bu ZIP'da nima o'zgardi

## 1. Bitrix24 CRM integratsiyasi (YANGI)
- **`lib/bitrix.py`** — yangi fayl. Har bir mijoz uchun Bitrix'da bitta Deal ochadi/yangilaydi.
  Bitrix ishlamay qolsa ham (xato, sinov muddati tugashi va h.k.) bot hech qachon to'xtamaydi.
- **`lib/config.py`** — oxiriga Bitrix sozlamalari qo'shildi (`BITRIX_WEBHOOK_URL`,
  `BITRIX_CATEGORY_ID`, `BITRIX_FIELD_INN`, `BITRIX_BOSQICHLAR`).
- **`lib/db.py`** — oxiriga `mijoz_bitrix_malumotini_yangila()` funksiyasi qo'shildi.
- **`lib/webhook_handler.py`** — 8 joyga Bitrix sinxronlash chaqiruvi qo'shildi: navbatda,
  shartnoma yo'q, qabul qilindi, yakunlandi, qayta aloqa, javob bermadi, qayta qabul qilindi,
  kutishdan davom ettirildi.
- **`lib/timer_handler.py`** — 20 daqiqada muddati o'tgan zayavka uchun ham Bitrix yangilanadi.
- **`schema.sql`** — oxiriga yangi ustunlar qo'shildi (quyida, Supabase'da ishga tushirish kerak).

**Diqqat:** "Kutish rejimi" (`holat = "kutish"`) uchun Bitrix bosqichi hali yaratilmagan
(Bitrix'da shunday bosqich yo'q edi), shuning uchun bu holatda Bitrix sinxronlanmaydi —
xato bermaydi, shunchaki hech narsa qilmaydi. Kerak bo'lsa, keyin alohida bosqich qo'shib,
`BITRIX_STAGE_KUTISH` kabi yangi o'zgaruvchi qo'shish mumkin.

## 2. "1С" xatosi tuzatildi
- **`lib/logic.py`** — to'liq qayta yozildi. Oldin "тел 993808010 1С" kabi xabarda "1"
  raqami telefon raqamiga yopishib, uni 10 xonali (xato) qilib ko'rsatar edi. Endi harf
  aralashgan so'z ("1С" kabi) hech qanday raqamga ulanmaydi.

## Supabase'da ishga tushirish kerak bo'lgan SQL
```sql
alter table mijozlar add column if not exists bitrix_contact_id bigint;
alter table mijozlar add column if not exists bitrix_deal_id bigint;
alter table xodimlar add column if not exists bitrix_user_id bigint;  -- (allaqachon qo'shgan bo'lishingiz mumkin)

NOTIFY pgrst, 'reload schema';
```

## Vercel'ga qo'shiladigan Environment Variable'lar
`BITRIX_WEBHOOK_URL` allaqachon saqlangan bo'lsa, faqat quyidagilarni qo'shing:

| Nomi | Qiymati |
|---|---|
| `BITRIX_CATEGORY_ID` | `4` |
| `BITRIX_FIELD_INN` | `UF_CRM_INN` |
| `BITRIX_STAGE_NAVBATDA` | `C4:NEW` |
| `BITRIX_STAGE_JARAYONDA` | `C4:PREPARATION` |
| `BITRIX_STAGE_QAYTA_ALOQA` | `C4:PREPAYMENT_INVOICE` |
| `BITRIX_STAGE_SHARTNOMA_YOQ` | `C4:EXECUTING` |
| `BITRIX_STAGE_TUGALLANDI` | `C4:WON` |
| `BITRIX_STAGE_JAVOB_BERMADI` | `C4:LOSE` |
| `BITRIX_STAGE_MUDDATI_OTDI` | `C4:APOLOGY` |

## Qilish tartibi
1. Supabase'da yuqoridagi SQL'ni ishga tushiring.
2. Vercel'da yangi Environment Variable'larni qo'shing.
3. Shu ZIP ichidagi `fincube_help_bot-main` papkasini (yoki undagi o'zgargan fayllarni:
   `lib/bitrix.py`, `lib/config.py`, `lib/db.py`, `lib/logic.py`, `lib/webhook_handler.py`,
   `lib/timer_handler.py`, `schema.sql`) GitHub repo'ga qo'ying/almashtiring, commit va push qiling.
4. Vercel avtomatik qayta deploy qiladi (yoki qo'lda "Redeploy" bosing).
5. Guruhga INN+telefon bilan sinov xabari yuboring — Bitrix'dagi **Support** varonkasida
   yangi Deal paydo bo'lishini tekshiring.
6. "1С" so'zi bilan sinov xabari yuboring (masalan: "ИНН 304462751 тел 901234567 1С да muammo
   bor") — endi to'g'ri qabul qilinishi kerak.

## Tegilmagan fayllar
`lib/mini_app_html.py`, `lib/dashboard_html.py`, `lib/telegram.py`, `lib/telegram_auth.py`,
`lib/sheets.py`, `api/index.py`, `pyproject.toml`, `vercel.json`, `README.md` — o'zgarishsiz.
