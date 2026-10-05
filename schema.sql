-- ============================================================
-- FINCUBE SUPPORT BOT UCHUN SUPABASE (POSTGRES) JADVALLARI
-- Bu faylni Supabase paneli -> SQL Editor bo'limiga qo'yib,
-- "Run" tugmasini bossangiz, barcha jadvallar avtomatik yaraladi.
-- ============================================================

-- 1-JADVAL: XODIMLAR
-- Zayavka qabul qiluvchi 4 nafar xodim shu yerda ro'yxatda turadi
create table xodimlar (
    id bigserial primary key,                          -- xodimning ichki tartib raqami
    telegram_id bigint unique not null,                 -- xodimning shaxsiy Telegram ID raqami
    ism_familiya text not null,                         -- xabarlarda ko'rinadigan ismi
    holat text not null default 'bosh',                 -- 'bosh' (mijoz kutyapti) yoki 'band' (mijoz bilan gaplashyapti)
    joriy_zayavka_id bigint                              -- hozir band bo'lgan zayavka IDsi (bo'sh bo'lsa NULL)
);

-- 2-JADVAL: MIJOZLAR
-- Support guruhiga yozgan har bir mijoz shu yerda saqlanadi
create table mijozlar (
    id bigserial primary key,                            -- mijozning ichki tartib raqami
    telegram_id bigint unique not null,                  -- mijozning Telegram ID raqami
    ism text,                                             -- mijozning Telegramdagi ismi
    inn text,                                             -- mijoz INN raqami (topilgach yoziladi)
    telefon text                                          -- mijoz telefon raqami (topilgach yoziladi)
);

-- 3-JADVAL: ZAYAVKALAR
-- Mijozning har bir murojaati (so'rovi) shu yerda kuzatiladi
create table zayavkalar (
    id bigserial primary key,                                            -- zayavkaning ichki tartib raqami
    mijoz_id bigint not null references mijozlar(id),                    -- qaysi mijozga tegishli
    guruh_chat_id bigint not null,                                       -- qaysi guruhda yozilgan (javob yuborish uchun)
    mijoz_xabar_id bigint,                                               -- mijozning asl xabari (reply qilish uchun)
    holat text not null default 'malumot_kutilmoqda',                    -- malumot_kutilmoqda | navbatda | jarayonda | tugallandi | muddati_otdi
    biriktirilgan_xodim_id bigint references xodimlar(id),               -- kim qabul qildi
    ustuvor_xodim_id bigint references xodimlar(id),                     -- 3 kunlik qoidaga ko'ra ustuvor xodim
    matn text,                                                            -- mijozdan kelgan xabarlar matni (INN/tel qidirish uchun)
    yaratilgan_vaqt timestamptz not null default now(),                   -- zayavka TO'LIQ bo'lgan (taymer boshlangan) vaqt
    jarayon_boshlangan_vaqt timestamptz,                                  -- xodim "Qabul qildim" bosgan vaqt
    tugallangan_vaqt timestamptz,                                         -- xodim "Consultatsiya berdim" bosgan vaqt
    rang text not null default 'yashil',                                  -- yashil | sariq | qizil (taymer holati)
    besh_daqiqa_signal_yuborildimi boolean not null default false,        -- majburiy signal yuborilganmi
    oxirgi_tag_xabar_id bigint                                            -- guruhga yuborilgan oxirgi tag xabari IDsi (tahrirlash uchun)
);

-- Tezkor qidiruv uchun indekslar (ixtiyoriy, lekin foydali)
create index idx_zayavka_holat on zayavkalar(holat);
create index idx_zayavka_mijoz on zayavkalar(mijoz_id);
create index idx_zayavka_vaqt on zayavkalar(yaratilgan_vaqt);

-- Xodimlarni qo'lda qo'shish namunasi (o'z telegram_id va ismlaringizni yozing):
-- insert into xodimlar (telegram_id, ism_familiya) values
--   (111111111, 'Aziz Aliyev'),
--   (222222222, 'Sardor Karimov'),
--   (333333333, 'Dilnoza Yusupova'),
--   (444444444, 'Jasur Rahimov');

-- ============================================================
-- QO'SHIMCHA O'ZGARISH (agar jadval allaqachon yaratilgan bo'lsa, shu qatorni alohida ishga tushiring):
-- Ustuvor xodim 5 daqiqada javob bermasa, boshqalarga xabar borganini belgilash uchun
alter table zayavkalar add column if not exists ustuvor_kengaytirildi boolean not null default false;

-- ============================================================
-- QO'SHIMCHA JADVAL: Telegram'dan kelgan har bir yangilanishni faqat
-- BIR MARTA qayta ishlash uchun (Telegram ba'zan bitta voqeani ikki marta
-- yuborishi mumkin — sekin javob berilganda "qayta urinish" qiladi)
create table if not exists qayta_ishlangan_updatelar (
    update_id bigint primary key   -- Telegramning har bir yangilanishiga beradigan noyob raqami
);

-- ============================================================
-- QO'SHIMCHA: Mini App'da rollarni ajratish uchun (agar jadval allaqachon
-- yaratilgan bo'lsa, shu qatorni alohida ishga tushiring):
-- rol: 'super_user' | 'owner' | 'xodim'
--   super_user — hammasini ko'radi va o'zgartira oladi
--   owner      — faqat ko'radi, hech narsani o'zgartira olmaydi
--   xodim      — mijoz qabul qiladi/yakunlaydi (support team / support person)
alter table xodimlar add column if not exists rol text not null default 'xodim';

-- ============================================================
-- QO'SHIMCHA: Yo'nalish tanlovi (ZUB / Buxgalteriya / UNF) va baholash tizimi uchun
-- ============================================================

-- Har bir zayavkaga xodim tanlagan yo'nalish(lar) — vergul bilan ajratilgan matn (masalan "ZUB,UNF")
alter table zayavkalar add column if not exists yonalishlar text not null default '';

-- Mijozlarning baholashlari (consultatsiya tugagach yuboriladi)
create table if not exists baholashlar (
    id bigserial primary key,
    zayavka_id bigint not null references zayavkalar(id),      -- qaysi zayavka bo'yicha
    mijoz_id bigint not null references mijozlar(id),            -- qaysi mijoz
    xodim_id bigint references xodimlar(id),                     -- qaysi xodim xizmat ko'rsatgan
    yulduz int,                                                    -- 1 dan 5 gacha (javob berilmaguncha NULL)
    izoh text,                                                     -- ixtiyoriy izoh matni
    holat text not null default 'kutilmoqda',                     -- kutilmoqda | baholandi | muddati_otdi
    chat_id bigint,                                                -- so'rov yuborilgan chat (lichka yoki guruh)
    xabar_id bigint,                                               -- yuborilgan xabar IDsi (tahrirlash uchun)
    yaratilgan_vaqt timestamptz not null default now(),
    javob_vaqt timestamptz
);

create index if not exists idx_baholash_holat on baholashlar(holat);
create index if not exists idx_baholash_mijoz on baholashlar(mijoz_id);

-- ============================================================
-- QO'SHIMCHA: Google Sheets'dan aniqlangan kompaniya nomini mijozga saqlash uchun
alter table mijozlar add column if not exists kompaniya_nomi text;

-- ============================================================
-- QO'SHIMCHA: kompaniya nomi endi HAR BIR ZAYAVKAning o'zida saqlanadi
-- (mijozning umumiy yozuvida emas) — shunda bir kishi turli INN bilan
-- turli kompaniyalar nomidan murojaat qilsa ham, eski murojaatlar
-- noto'g'ri qayta yozilib ketmaydi
-- ============================================================
alter table zayavkalar add column if not exists inn text;
alter table zayavkalar add column if not exists kompaniya_nomi text;

-- ============================================================
-- QO'SHIMCHA: "Telefonni ko'tarmadi" — necha marta urinilganini hisoblash uchun
-- ============================================================
alter table zayavkalar add column if not exists qongiroq_soni integer not null default 0;

-- ============================================================
-- QO'SHIMCHA: mijoz botni "start" qilmagani uchun yetkazib bo'lmagan shaxsiy xabarni
-- vaqtincha saqlab turish uchun — start bosgan zahoti avtomatik yetkaziladi
-- ============================================================
alter table mijozlar add column if not exists kutayotgan_xabar text;

-- ============================================================
-- QO'SHIMCHA: mijoz xabarini TAHRIRLAGANDA to'g'ri almashtirish uchun
-- zayavkadagi har bir xabarning (ID, matn) ro'yxati saqlanadi
-- ============================================================
alter table zayavkalar add column if not exists xabarlar jsonb not null default '[]'::jsonb;
NOTIFY pgrst, 'reload schema';
