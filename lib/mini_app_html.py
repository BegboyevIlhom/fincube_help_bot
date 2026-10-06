# Bu fayl xodimlar (va owner/super_user) uchun Telegram Mini App sahifasini saqlaydi
#
# Bo'limlar (barcha rollarga ko'rinadi: xodim, owner, super_user):
#   1) Joriy mijozim (shaxsiy) — agar band bo'lsa
#   2) Bugungi qisqa statistika (3 raqamli karta)
#   3) Navbatda kutayotganlar — "Qabul qildim" tugmasi bilan
#   4) Consultatsiya jarayonda (BARCHA xodimlar bo'yicha, kim band ekani bilan)
#   5) 20 daqiqada o'tib ketgan mijozlar (bugungi)
#
# FAQAT owner va super_user uchun qo'shimcha bo'limlar:
#   6) Xodimlar holati (kim band, kim bo'sh) — super_user bu ro'yxatda ko'rsatilmaydi
#   7) Analitika, 8) Reyting, 9) Yo'nalishlar statistikasi, 10) Oylik hisobot, 11) Kompaniyalar statistikasi
#
# Dizayn: barcha ranglar CSS o'zgaruvchilari (custom properties) orqali berilgan —
# shunda Telegram foydalanuvchining OCH yoki QORONG'U rejimiga avtomatik moslashadi
# (JS orqali tg.colorScheme tekshirilib, "tema-och" klassi qo'shiladi/qo'shilmaydi).
# Ikonkalar — o'z chizilgan SVG ikonkalarimiz (emoji emas), shunda barcha qurilma/brauzerlarda
# bir xil, tekis va professional ko'rinadi.
#
# Tahrirlash huquqi (Qabul qildim / Consultatsiya berdim tugmalari):
#   xodim va super_user — bor;  owner — yo'q (faqat ko'radi)

MINI_APP_HTML = """
<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>FINCUBE — Ish paneli</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
    * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }

    /* ===== RANG O'ZGARUVCHILARI (QORONG'U REJIM — standart) ===== */
    :root {
        --bg: #0a0c10;
        --bg-tint1: rgba(34,197,94,0.07);
        --bg-tint2: rgba(96,165,250,0.06);
        --text: #eef0f2;
        --text-muted: #aab0ba;
        --text-faint: #7d8590;
        --card-bg: #16181e;
        --card-bg-grad1: #1b1e26;
        --card-bg-grad2: #14161b;
        --border: #262a33;
        --border-soft: #1e2128;
        --chip-bg: #23262e;
        --chip-border: #323642;
        --tabbar-bg: rgba(20,22,27,0.94);
        --modal-bg: #0a0c10;
        --table-th: #7d8590;
        --kompaniya-bg: rgba(96,165,250,0.12);
        --kompaniya-text: #93c5fd;
        --card-mening-bg: #17211a;
        --shadow: rgba(0,0,0,0.3);
    }
    /* ===== RANG O'ZGARUVCHILARI (OCH REJIM) — Telegram och tema bo'lsa shu ishlaydi ===== */
    body.tema-och {
        --bg: #f2f4f6;
        --bg-tint1: rgba(34,197,94,0.05);
        --bg-tint2: rgba(59,130,246,0.05);
        --text: #14171a;
        --text-muted: #4b5563;
        --text-faint: #6b7280;
        --card-bg: #ffffff;
        --card-bg-grad1: #ffffff;
        --card-bg-grad2: #f3f4f6;
        --border: #e3e6ea;
        --border-soft: #edeff2;
        --chip-bg: #eef0f3;
        --chip-border: #dde1e6;
        --tabbar-bg: rgba(255,255,255,0.94);
        --modal-bg: #f2f4f6;
        --table-th: #8a94a0;
        --kompaniya-bg: rgba(59,130,246,0.08);
        --kompaniya-text: #1d4ed8;
        --card-mening-bg: #eefcf3;
        --shadow: rgba(15,23,42,0.08);
    }

    body {
        background: var(--bg);
        background-image: radial-gradient(circle at 15% 0%, var(--bg-tint1), transparent 45%),
                           radial-gradient(circle at 85% 10%, var(--bg-tint2), transparent 40%);
        color: var(--text);
        font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif;
        margin: 0;
        padding: 16px;
        padding-bottom: 92px;
        -webkit-font-smoothing: antialiased;
    }

    .ikon-inline { display: inline-flex; vertical-align: -3px; }

    .profil-satr { display: flex; align-items: center; gap: 12px; margin-bottom: 4px; }
    .avatar {
        width: 42px; height: 42px; border-radius: 50%; flex-shrink: 0;
        background: linear-gradient(135deg, #22c55e, #16a34a);
        display: flex; align-items: center; justify-content: center;
        font-weight: 800; font-size: 17px; color: #06210f;
        box-shadow: 0 3px 10px rgba(34,197,94,0.35);
    }
    .avatar.admin { background: linear-gradient(135deg, #f59e0b, #b45309); box-shadow: 0 3px 10px rgba(245,158,11,0.35); color: #2a1500; }
    .avatar.kuzatuvchi { background: linear-gradient(135deg, #6366f1, #4338ca); box-shadow: 0 3px 10px rgba(99,102,241,0.35); color: #eef2ff; }

    h2 { font-size: 17px; margin: 0 0 2px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; font-weight: 800; color: var(--text); }
    .kichik-matn { color: var(--text-faint); font-size: 13px; margin-bottom: 20px; }

    .rol-belgi { font-size: 10.5px; padding: 3px 10px; border-radius: 20px; background: var(--chip-bg); color: var(--text-muted); font-weight: 700; letter-spacing: 0.2px; }
    .rol-belgi.kuzatuvchi { background: rgba(99,102,241,0.16); color: #818cf8; }
    body.tema-och .rol-belgi.kuzatuvchi { color: #4338ca; }
    .rol-belgi.admin { background: rgba(245,158,11,0.16); color: #d97706; }

    .stat-qator { display: grid; grid-template-columns: repeat(3, 1fr); gap: 9px; margin-bottom: 24px; }
    .stat-karta {
        background: linear-gradient(160deg, var(--card-bg-grad1), var(--card-bg-grad2));
        border: 1px solid var(--border); border-radius: 14px; padding: 13px 8px 11px; text-align: center;
        box-shadow: 0 3px 10px var(--shadow); color: var(--text);
    }
    .stat-karta .stat-ikon { color: var(--text-muted); margin-bottom: 3px; }
    .stat-karta .son { font-size: 22px; font-weight: 800; letter-spacing: -0.3px; }
    .stat-karta .nom { font-size: 10px; color: var(--text-faint); margin-top: 3px; line-height: 1.3; }

    .karta {
        background: var(--card-bg);
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 11px;
        border: 1px solid var(--border);
        border-left: 4px solid #22c55e;
        box-shadow: 0 3px 12px var(--shadow);
        color: var(--text);
    }
    .karta.oddiy { border-left-color: var(--border); }
    .karta.mening { border-left-color: #22c55e; background: var(--card-mening-bg); }
    .siz-belgisi { font-size: 10px; background: #22c55e; color: #06210f; padding: 2px 8px; border-radius: 20px; font-weight: 800; letter-spacing: 0.3px; }
    .kompaniya-belgisi {
        display: inline-block; font-size: 11.5px; color: var(--kompaniya-text); background: var(--kompaniya-bg);
        padding: 3px 9px; border-radius: 8px; margin-bottom: 8px; font-weight: 600;
    }

    .chip-qator { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; }
    .chip {
        padding: 8px 14px; border-radius: 20px; font-size: 13px; font-weight: 600;
        background: var(--chip-bg); color: var(--text-muted); cursor: pointer; border: 1px solid var(--chip-border); transition: all 0.15s;
    }
    .chip.tanlangan { background: #22c55e; color: #06210f; border-color: #22c55e; }
    .btn-bekor { background: none !important; border: 1px solid var(--chip-border); color: var(--text-muted); margin-top: 8px; box-shadow: none; }
    .karta .sarlavha { font-weight: 800; margin-bottom: 4px; display: flex; justify-content: space-between; align-items: center; gap: 8px; color: var(--text); }
    .karta .matn { color: var(--text-muted); font-size: 13px; white-space: pre-wrap; margin-bottom: 10px; line-height: 1.45; }
    .karta .kim { font-size: 12px; color: #3b82f6; margin-bottom: 8px; font-weight: 600; }
    body.tema-och .karta .kim { color: #2563eb; }

    .taymer { font-size: 13px; font-weight: 800; font-variant-numeric: tabular-nums; white-space: nowrap; }
    .taymer.yashil { color: #16a34a; }
    .taymer.sariq { color: #ca8a04; }
    .taymer.qizil { color: #dc2626; }
    .taymer.tugagan { color: #991b1b; }
    .davomiylik { font-size: 12px; color: var(--text-faint); font-variant-numeric: tabular-nums; }

    button {
        width: 100%; padding: 13px; border: none; border-radius: 12px;
        font-size: 15px; font-weight: 700; cursor: pointer; transition: opacity 0.15s, transform 0.1s;
    }
    button:active { opacity: 0.8; transform: scale(0.99); }
    .btn-qabul {
        background: linear-gradient(135deg, #22c55e, #16a34a);
        color: #06210f; box-shadow: 0 3px 10px rgba(34,197,94,0.3);
    }
    .btn-tugat {
        background: linear-gradient(135deg, #ef4444, #b91c1c);
        color: #fff; box-shadow: 0 3px 10px rgba(239,68,68,0.3);
    }
    .btn-javobyoq {
        background: var(--chip-bg); color: var(--text-muted);
        border: 1px solid var(--chip-border); box-shadow: none;
    }
    .btn-kutish {
        background: linear-gradient(135deg, #f59e0b, #d97706);
        color: #2b1700; box-shadow: 0 3px 10px rgba(245,158,11,0.3);
    }
    .kutish-vaqti { font-size: 13px; font-weight: 800; color: #d97706; font-variant-numeric: tabular-nums; white-space: nowrap; }
    .urinish-belgisi { font-size: 12px; color: #ca8a04; font-weight: 700; margin-top: 8px; }
    button:disabled { opacity: 0.35; cursor: not-allowed; box-shadow: none; }

    .bolim-sarlavha {
        font-size: 12.5px; color: var(--text-faint); margin: 26px 0 10px;
        text-transform: uppercase; letter-spacing: 0.6px; font-weight: 800;
        display: flex; align-items: center; gap: 7px;
        padding-left: 10px; border-left: 3px solid #22c55e;
    }
    .bosh-holat { text-align: center; color: var(--text-faint); padding: 26px 0; font-size: 13px; }

    .xodim-qator { display: flex; align-items: center; gap: 10px; padding: 11px 2px; border-bottom: 1px solid var(--border-soft); }
    .xodim-qator:last-child { border-bottom: none; }
    .nuqta { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; box-shadow: 0 0 7px currentColor; }
    .nuqta.bosh { background: #22c55e; color: #22c55e; }
    .nuqta.band { background: #ef4444; color: #ef4444; }

    table.analitika { width: 100%; border-collapse: collapse; font-size: 12.5px; color: var(--text); }
    table.analitika th { text-align: left; color: var(--table-th); font-weight: 700; padding: 8px 6px; border-bottom: 1px solid var(--border); font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.3px; }
    table.analitika td { padding: 10px 6px; border-bottom: 1px solid var(--border-soft); }
    table.analitika tr:last-child td { border-bottom: none; }
    table.analitika tr.bosiladi { cursor: pointer; transition: background 0.15s; }
    table.analitika tr.bosiladi:active { background: var(--chip-bg); }
    table.analitika tr.bosiladi td:first-child { color: #3b82f6; font-weight: 700; }
    body.tema-och table.analitika tr.bosiladi td:first-child { color: #2563eb; }
    .oq-belgi { color: var(--text-faint); font-size: 11px; }

    #tafsilot-modal {
        display: none; position: fixed; inset: 0; z-index: 70;
        background: var(--modal-bg);
        overflow-y: auto; padding: 16px; padding-bottom: 48px;
    }
    .orqaga-tugma {
        background: var(--chip-bg) !important; border: 1px solid var(--border); color: var(--text);
        width: auto; padding: 9px 18px; border-radius: 20px; font-size: 13px; margin-bottom: 18px; font-weight: 600;
        box-shadow: none;
    }

    #tab-panel {
        position: fixed; left: 8px; right: 8px; bottom: 8px; z-index: 60;
        display: flex; gap: 4px; background: var(--tabbar-bg); backdrop-filter: blur(10px);
        border: 1px solid var(--border); border-radius: 18px; padding: 6px;
        box-shadow: 0 6px 20px var(--shadow);
        padding-bottom: calc(6px + env(safe-area-inset-bottom, 0px));
    }
    .tab-tugma {
        flex: 1; background: none; border: none; color: var(--text-faint);
        padding: 9px 4px 8px; font-size: 11px; font-weight: 700; line-height: 1.5;
        border-radius: 12px; cursor: pointer; box-shadow: none; transition: all 0.15s;
    }
    .tab-tugma .tab-ikon { display: flex; justify-content: center; margin-bottom: 3px; }
    .tab-tugma.faol { color: #06210f; background: linear-gradient(135deg, #22c55e, #16a34a); }

    /* ===== ANIMATSIYALAR: yuklanish holatini yanada quvnoq/zamonaviy qilish uchun ===== */

    /* Shimmer — kutish paytida "yorug'lik oqib o'tayotgan" ko'rinishdagi skelet-kartalar */
    @keyframes shimmer { 0% { background-position: -450px 0; } 100% { background-position: 450px 0; } }
    .skeleton-karta {
        height: 88px; border-radius: 16px; margin-bottom: 11px;
        background: linear-gradient(90deg, var(--border) 25%, var(--chip-bg) 37%, var(--border) 63%);
        background-size: 900px 100%;
        animation: shimmer 1.5s linear infinite;
    }
    .skeleton-matn {
        display: inline-block; border-radius: 6px;
        background: linear-gradient(90deg, var(--border) 25%, var(--chip-bg) 37%, var(--border) 63%);
        background-size: 900px 100%;
        animation: shimmer 1.5s linear infinite;
    }

    /* Avatar — ma'lumot hali kelmaguncha, sekin "nafas olib" turadi */
    @keyframes nafasOlish { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.55; transform: scale(0.92); } }
    .avatar.yuklanmoqda { animation: nafasOlish 1.3s ease-in-out infinite; }

    /* Har bir karta ekranga chiqqanda, pastdan yumshoq suzib, xiralikdan aniqlikka o'tadi */
    @keyframes paydoBolish { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
    .karta { animation: paydoBolish 0.32s ease-out both; }
</style>
</head>
<body>
    <div class="profil-satr" id="profil-satr">
        <div class="avatar yuklanmoqda" id="avatar">?</div>
        <div>
            <h2><span id="xodim-ismi" class="skeleton-matn" style="width:130px;height:16px"></span></h2>
            <span class="rol-belgi" id="rol-belgi"></span>
        </div>
    </div>
    <div class="kichik-matn" id="xodim-holati"></div>
    <div class="kichik-matn" id="ozim-tafsilot" style="margin-top:-16px;color:#3b82f6;cursor:pointer;display:none" onclick="ozimTafsilot()">
        📋 Bugungi ko'rsatkichlarim ›
    </div>

    <div id="sahifa-ish">
        <div class="stat-qator">
            <div class="stat-karta">
                <div class="stat-ikon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="17" height="17"><path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg></div>
                <div class="son" id="s-jami">—</div><div class="nom">Bugun jami<br>murojaat</div>
            </div>
            <div class="stat-karta">
                <div class="stat-ikon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="17" height="17"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div>
                <div class="son" id="s-tugallandi">—</div><div class="nom">Bugun<br>tugallandi</div>
            </div>
            <div class="stat-karta">
                <div class="stat-ikon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="17" height="17"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div>
                <div class="son" id="s-qolib-ketdi">—</div><div class="nom">20 daq<br>o'tib ketdi</div>
            </div>
        </div>

        <div class="bolim-sarlavha"><span class="ikon-inline"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="15" height="15"><path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg></span> Navbatda kutayotganlar</div>
        <div id="navbat-royxati"><div class="skeleton-karta"></div><div class="skeleton-karta" style="animation-delay:.12s"></div></div>

        <div class="bolim-sarlavha"><span class="ikon-inline"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="15" height="15"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg></span> Consultatsiya jarayonda</div>
        <div id="jarayon-royxati"><div class="skeleton-karta" style="animation-delay:.06s"></div></div>

        <div class="bolim-sarlavha"><span class="ikon-inline"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="15" height="15"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></span> Kutish rejimida (muammo hali hal bo'lmagan)</div>
        <div id="kutish-royxati"><div class="skeleton-karta" style="animation-delay:.12s"></div></div>

        <div class="bolim-sarlavha"><span class="ikon-inline"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="15" height="15"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg></span> Qayta aloqaga chiqish</div>
        <div id="qayta-aloqa-royxati"><div class="skeleton-karta" style="animation-delay:.18s"></div></div>

        <div class="bolim-sarlavha"><span class="ikon-inline"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="15" height="15"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></span> 20 daqiqada o'tib ketgan mijozlar (bugun)</div>
        <div id="otib-ketgan-royxati"><div class="skeleton-karta" style="animation-delay:.24s"></div></div>
    </div>

    <div id="sahifa-boshqaruv" style="display:none">
        <div id="owner-bolimlar"></div>
    </div>

    <div id="tab-panel">
        <button class="tab-tugma faol" id="tab-ish" onclick="sahifaOch('ish')">
            <span class="tab-ikon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="18" height="18"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg></span>Ish
        </button>
        <button class="tab-tugma" id="tab-boshqaruv" onclick="sahifaOch('boshqaruv')" style="display:none">
            <span class="tab-ikon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="18" height="18"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg></span>Boshqaruv
        </button>
    </div>

    <!-- Xodim tafsiloti oynasi (analitikada bosilganda ochiladi) -->
    <div id="tafsilot-modal">
        <button class="orqaga-tugma" onclick="modalniYop()">← Orqaga</button>
        <h2 id="tafsilot-sarlavha"></h2>
        <div class="kichik-matn" id="tafsilot-izoh">Bugun gaplashilgan mijozlar</div>
        <div class="chip-qator" id="tafsilot-tablar"></div>
        <div id="tafsilot-royxat"></div>
    </div>

<script>

const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

// Telegram foydalanuvchining rejimini (och/qorong'u) aniqlab, shunga mos klass qo'shamiz
if (tg.colorScheme === 'light') {
    document.body.classList.add('tema-och');
}

const MUMKIN_YONALISHLAR = ['ZUB', 'Buxgalteriya', 'UNF'];  // serverdagi MUMKIN_YONALISHLAR bilan bir xil bo'lishi shart
const QONGIROQ_MAKS = 3;  // serverdagi QONGIROQ_URINISH_MAKS bilan bir xil bo'lishi shart (faqat ko'rsatish uchun)
let oxirgiMalumot = null;  // eng oxirgi yuklangan to'liq panel ma'lumoti — "Kompaniyalar" oynasini ochish uchun kerak
let joriyTafsilotMalumoti = null;  // xodim tafsilot oynasidagi 3 ta tab (tugallandi/qayta_aloqa/javob_bermadi) ma'lumoti
// MUHIM: quyidagi to'plam hozir "jarayonda" bo'lgan (server javob bermagan) zayavka amallarini saqlaydi —
// shu bilan xodim tugmani tez-tez (bir necha marta ketma-ket) bossa ham, FAQAT BITTA so'rov ketadi,
// qolganlari e'tiborsiz qoldiriladi (bu — "5 ta baholang" yoki "2-3 marta ochilib qolish" xatolarini oldini oladi)
const amalKutilmoqda = new Set();
let tanlashJarayonida = false;  // true bo'lsa, avtomatik yangilanish (poll) vaqtincha to'xtatib turiladi
let joriyTanlovZayavkaId = null;  // hozir yo'nalish tanlanayotgan zayavka IDsi
let joriyTanlov = [];  // hozirgi tanlangan yo'nalishlar (masalan ["ZUB", "UNF"])

// Tizim ichida ishlatiladigan ikonkalar (o'z SVG ikonkalarimiz — barcha qurilmalarda bir xil ko'rinadi)
const IKON = {
    xodimlar: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="15" height="15"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    chart: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="15" height="15"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    star: '<svg viewBox="0 0 24 24" fill="currentColor" width="15" height="15"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
    trend: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="15" height="15"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>',
    briefcase: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="15" height="15"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
    calendar: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="15" height="15"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
};

// XAVFSIZLIK: mijoz yozgan har qanday matn (xabar, ism, kompaniya, izoh) sahifaga qo'yilishidan oldin shu funksiyadan
// o'tishi shart — aks holda mijoz "<img onerror=...>" kabi narsa yozib, xodim/rahbar sahifasida kod ishga tushirishi mumkin
function esc(qiymat) {
    return String(qiymat === null || qiymat === undefined ? '' : qiymat)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

async function so_rov(manzil, usul, gavda) {
    const sozlamalar = { method: usul, headers: { 'Content-Type': 'application/json', 'X-Telegram-Init-Data': tg.initData } };
    if (gavda) sozlamalar.body = JSON.stringify(gavda);

    // MUHIM: agar so'rov hech qachon javob bermay "osilib" qolsa (masalan ba'zi Telegram Desktop
    // versiyalarida uchraydigan muammo), 12 soniyadan keyin majburan to'xtatamiz — aks holda sahifa
    // abadiy "Yuklanmoqda..." holatida qolib ketardi, hech qanday xabar ko'rsatmasdan
    const boshqaruvchi = new AbortController();
    const vaqtchi = setTimeout(() => boshqaruvchi.abort(), 12000);
    sozlamalar.signal = boshqaruvchi.signal;

    try {
        const javob = await fetch(manzil, sozlamalar);
        return await javob.json();
    } catch (xato) {
        // agar server umuman javob bermasa, JSON o'rniga boshqa narsa qaytarsa, yoki vaqt tugasa —
        // bu yerda "ushlab qolamiz" va aniq xabar bilan qaytaramiz
        const matn = (xato.name === 'AbortError')
            ? 'Server javob bermadi (vaqt tugadi). Telegram\\'ni yangilab, qayta urinib ko\\'ring.'
            : 'Server bilan bog\\'lanib bo\\'lmadi: ' + xato.message;
        return { ok: false, xato: matn };
    } finally {
        clearTimeout(vaqtchi);
    }
}

// "Ish" va "Boshqaruv" sahifalari orasida almashtiradi
function sahifaOch(nomi) {
    document.getElementById('sahifa-ish').style.display = nomi === 'ish' ? 'block' : 'none';
    document.getElementById('sahifa-boshqaruv').style.display = nomi === 'boshqaruv' ? 'block' : 'none';
    document.getElementById('tab-ish').classList.toggle('faol', nomi === 'ish');
    document.getElementById('tab-boshqaruv').classList.toggle('faol', nomi === 'boshqaruv');
    window.scrollTo(0, 0);  // sahifa almashganda tepaga qaytaramiz
}

function kompaniyaHtml(z) {
    // agar Google Sheets orqali kompaniya nomi aniqlangan bo'lsa, uni belgi (chip) sifatida ko'rsatamiz
    return z.kompaniya_nomi ? `<div class="kompaniya-belgisi">🏢 ${esc(z.kompaniya_nomi)}</div>` : '';
}

function kartaChiz(z, ichkiQator, oddiymi, tartib) {
    const kechikish = (tartib || 0) * 45;  // har bir keyingi karta bir oz kech chiqadi — "kaskad" effekti
    return `
        <div class="karta ${oddiymi ? 'oddiy' : ''}" data-yaratilgan="${z.yaratilgan_vaqt || ''}" style="animation-delay:${kechikish}ms">
            <div class="sarlavha">
                <span>Mijoz #${z.id}</span>
                ${oddiymi ? '' : '<span class="taymer yashil">20:00</span>'}
            </div>
            ${kompaniyaHtml(z)}
            ${ichkiQator}
            <div class="matn">${esc((z.matn || '').slice(0, 180))}</div>
        </div>`;
}

async function yukla() {
    const m = await so_rov('/api/app/royxat', 'GET');

    const ismJoyi = document.getElementById('xodim-ismi');
    ismJoyi.className = '';  // skelet-shimmer ko'rinishini har doim tozalab qo'yamiz (xato bo'lsa ham, ok bo'lsa ham)
    ismJoyi.style.cssText = '';

    if (!m.ok) {
        ismJoyi.textContent = 'Xatolik';
        document.getElementById('xodim-holati').textContent = m.xato || 'Noma\\'lum xatolik';
        // MUHIM: ro'yxat bo'limlari ham "shimmer" holatida abadiy qolib ketmasin — ularga ham aniq xabar chiqaramiz
        const xabar_html = `<div class="bosh-holat">⚠️ ${m.xato || 'Yuklab bo\\'lmadi'}</div>`;
        ['navbat-royxati', 'jarayon-royxati', 'kutish-royxati', 'qayta-aloqa-royxati', 'otib-ketgan-royxati'].forEach(id => {
            const joy = document.getElementById(id);
            if (joy) joy.innerHTML = xabar_html;
        });
        return;
    }
    oxirgiMalumot = m;  // "Kompaniyalar" oynasi shu yerdan ma'lumot oladi

    const xodim = m.xodim;
    const rol = xodim.rol || 'xodim';
    const kuzatuvchimi = rol === 'owner';
    const ownerKurishHuquqiBormi = (rol === 'owner' || rol === 'super_user');

    // "Boshqaruv" tabini faqat owner/super_user ko'radi; oddiy xodimga umuman ko'rinmaydi
    const boshqaruvTabi = document.getElementById('tab-boshqaruv');
    boshqaruvTabi.style.display = ownerKurishHuquqiBormi ? 'block' : 'none';

    ismJoyi.textContent = xodim.ism_familiya;
    const rolBelgi = document.getElementById('rol-belgi');
    const avatar = document.getElementById('avatar');
    avatar.textContent = (xodim.ism_familiya || '?').trim().charAt(0).toUpperCase();
    if (rol === 'super_user') {
        rolBelgi.textContent = '⭐ Super admin'; rolBelgi.className = 'rol-belgi admin'; avatar.className = 'avatar admin';
    } else if (rol === 'owner') {
        rolBelgi.textContent = '👁 Faqat kuzatish'; rolBelgi.className = 'rol-belgi kuzatuvchi'; avatar.className = 'avatar kuzatuvchi';
    } else {
        rolBelgi.textContent = 'Xodim'; rolBelgi.className = 'rol-belgi'; avatar.className = 'avatar';
    }

    document.getElementById('xodim-holati').textContent = xodim.holat === 'bosh' ? "🟢 Hozir bo'sh" : "🔴 Hozir band";

    // "owner" (faqat kuzatuvchi) uchun bu havola kerak emas — u allaqachon Boshqaruv'da hammasini ko'radi
    document.getElementById('ozim-tafsilot').style.display = (rol === 'owner') ? 'none' : 'block';

    document.getElementById('s-jami').textContent = m.bugun_jami_murojaat ?? 0;
    document.getElementById('s-tugallandi').textContent = m.bugun_consultatsiya_berildi ?? 0;
    document.getElementById('s-qolib-ketdi').textContent = (m.muddati_otganlar || []).length;

    const navbatRoyxat = document.getElementById('navbat-royxati');
    if (!m.navbatdagilar || m.navbatdagilar.length === 0) {
        navbatRoyxat.innerHTML = '<div class="bosh-holat">Hozircha navbatda hech kim yo\\'q 🎉</div>';
    } else {
        const bandmi = xodim.holat !== 'bosh';
        navbatRoyxat.innerHTML = m.navbatdagilar.map((z, idx) => {
            const tugma = kuzatuvchimi ? '' : `<button class="btn-qabul" ${bandmi ? 'disabled' : ''} onclick="qabul(${z.id})">✅ Qabul qildim</button>`;
            return kartaChiz(z, tugma, false, idx);
        }).join('');
    }

    // CONSULTATSIYA JARAYONDA — bu yerda SIZNING joriy mijozingiz ham shu ro'yxat ICHIDA,
    // ajratib (yashil chiziq + "SIZ" belgisi bilan) ko'rsatiladi, alohida bo'lim yo'q
    const jarayonRoyxat = document.getElementById('jarayon-royxati');
    if (!m.jarayondagilar || m.jarayondagilar.length === 0) {
        jarayonRoyxat.innerHTML = '<div class="bosh-holat">Hozir hech kim consultatsiya olmayapti</div>';
    } else {
        jarayonRoyxat.innerHTML = m.jarayondagilar.map(z => {
            const bu_meniki = z.biriktirilgan_xodim_id === xodim.id;  // bu mijoz aynan shu foydalanuvchiniki
            const urinish_belgisi = z.qongiroq_soni ? ` (${z.qongiroq_soni}/${QONGIROQ_MAKS})` : '';
            const amal_html = (bu_meniki && !kuzatuvchimi)
                ? `<div id="amal-${z.id}">
                       <button class="btn-tugat" onclick="tugatishniBoshla(${z.id})">☑️ Consultatsiya berdim</button>
                       <button class="btn-kutish" onclick="kutishgaQoy(${z.id})" style="margin-top:8px">⏳ Kutish rejimi (muammo hal bo'lmadi)</button>
                       <button class="btn-javobyoq" onclick="javobBermadi(${z.id})" style="margin-top:8px">📵 Telefonni ko'tarmadi${urinish_belgisi}</button>
                   </div>`
                : (z.qongiroq_soni ? `<div class="urinish-belgisi">📵 ${z.qongiroq_soni}/${QONGIROQ_MAKS} marta urinilgan</div>` : '');
            return `
                <div class="karta ${bu_meniki ? 'mening' : 'oddiy'}" data-boshlangan="${z.jarayon_boshlangan_vaqt || ''}" data-kutilgan="${z.kutish_jami_soniya || 0}">
                    <div class="sarlavha">
                        <span>Mijoz #${z.id} ${bu_meniki ? '<span class="siz-belgisi">SIZ</span>' : ''}</span>
                        <span class="davomiylik">0:00</span>
                    </div>
                    ${kompaniyaHtml(z)}
                    <div class="kim">👤 ${esc(z.xodim_ismi)}</div>
                    <div class="matn">${esc((z.matn || '').slice(0, 150))}</div>
                    ${amal_html}
                </div>`;
        }).join('');
    }

    // KUTISH REJIMIDA — xodim mijoz bilan gaplashgan, lekin muammo hali hal bo'lmagan. Xodim bo'sh, mijoz esa
    // "Davom ettirish"ni kutmoqda. Bu yerdagi vaqt gaplashish davomiyligiga QO'SHILMAYDI
    const kutishRoyxat = document.getElementById('kutish-royxati');
    if (!m.kutishdagilar || m.kutishdagilar.length === 0) {
        kutishRoyxat.innerHTML = `<div class="bosh-holat">Kutish rejimida mijoz yo'q</div>`;
    } else {
        const bandmi = xodim.holat !== 'bosh';
        kutishRoyxat.innerHTML = m.kutishdagilar.map(z => {
            const bu_meniki = z.biriktirilgan_xodim_id === xodim.id;
            const amal_html = (bu_meniki && !kuzatuvchimi)
                ? `<button class="btn-qabul" ${bandmi ? 'disabled' : ''} onclick="kutishdanDavomEt(${z.id})">▶️ Davom ettirish</button>`
                : '';
            return `
                <div class="karta ${bu_meniki ? 'mening' : 'oddiy'}" data-kutish-boshlangan="${z.kutish_boshlangan_vaqt || ''}" style="border-left-color:#f59e0b">
                    <div class="sarlavha">
                        <span>Mijoz #${z.id} ${bu_meniki ? '<span class="siz-belgisi">SIZ</span>' : ''}</span>
                        <span class="kutish-vaqti">⏳ 0:00</span>
                    </div>
                    ${kompaniyaHtml(z)}
                    <div class="kim">👤 ${esc(z.xodim_ismi)}</div>
                    <div class="matn">${esc((z.matn || '').slice(0, 150))}</div>
                    ${amal_html}
                </div>`;
        }).join('');
    }

    // QAYTA ALOQAGA CHIQISH — "Telefonni ko'tarmadi" bosilib, xodim yana "Qabul qilish"ni
    // bosishini kutayotgan mijozlar (bu 20 daqiqalik taymer bilan bog'liq emas)
    const qaytaAloqaRoyxat = document.getElementById('qayta-aloqa-royxati');
    if (!m.qayta_aloqadagilar || m.qayta_aloqadagilar.length === 0) {
        qaytaAloqaRoyxat.innerHTML = '<div class="bosh-holat">Hozircha qayta aloqaga chiqilayotgan mijoz yo\\'q</div>';
    } else {
        qaytaAloqaRoyxat.innerHTML = m.qayta_aloqadagilar.map(z => {
            const bu_meniki = z.biriktirilgan_xodim_id === xodim.id;
            const amal_html = (bu_meniki && !kuzatuvchimi)
                ? `<button class="btn-qabul" onclick="qaytaQabulQil(${z.id})">🔁 Qabul qilish</button>`
                : '';
            return `
                <div class="karta ${bu_meniki ? 'mening' : 'oddiy'}">
                    <div class="sarlavha">
                        <span>Mijoz #${z.id} ${bu_meniki ? '<span class="siz-belgisi">SIZ</span>' : ''}</span>
                        <span class="urinish-belgisi" style="margin-top:0">📵 ${z.qongiroq_soni || 0}/${QONGIROQ_MAKS}</span>
                    </div>
                    ${kompaniyaHtml(z)}
                    <div class="kim">👤 ${esc(z.xodim_ismi)}</div>
                    <div class="matn">${esc((z.matn || '').slice(0, 150))}</div>
                    ${amal_html}
                </div>`;
        }).join('');
    }

    const otibKetganRoyxat = document.getElementById('otib-ketgan-royxati');
    if (!m.muddati_otganlar || m.muddati_otganlar.length === 0) {
        otibKetganRoyxat.innerHTML = '<div class="bosh-holat">Bugun hech kim qolib ketmagan 👍</div>';
    } else {
        const bandmi = xodim.holat !== 'bosh';
        otibKetganRoyxat.innerHTML = m.muddati_otganlar.map(z => {
            // kech bo'lsa ham, hali qabul qilish mumkin — shuning uchun bu yerga ham tugma qo'yamiz
            const tugma = kuzatuvchimi ? '' : `<button class="btn-qabul" ${bandmi ? 'disabled' : ''} onclick="qabul(${z.id})">✅ Baribir qabul qilaman</button>`;
            return `
                <div class="karta" style="border-left-color:#7f1d1d">
                    <div class="sarlavha"><span>Mijoz #${z.id}</span><span style="color:#ef4444;font-size:12px;font-weight:700">Qolib ketdi</span></div>
                    ${kompaniyaHtml(z)}
                    <div class="matn">${esc((z.matn || '').slice(0, 150))}</div>
                    ${tugma}
                </div>`;
        }).join('');
    }

    const ownerBolim = document.getElementById('owner-bolimlar');
    if (ownerKurishHuquqiBormi && m.xodimlar_holati) {
        const xodimlarHtml = m.xodimlar_holati.map(x => `
            <div class="xodim-qator">
                <div class="nuqta ${x.holat}"></div>
                <div>
                    <div style="font-weight:600">${x.ism_familiya}</div>
                    <div style="font-size:12px;color:#8b93a1">${x.holat === 'bosh' ? "Bo'sh" : 'Band'}</div>
                </div>
            </div>`).join('');

        const analitikaQatorlar = (m.analitika || []).map(a => `
            <tr class="bosiladi" onclick="xodimTafsilot(${a.xodim_id}, '${a.ism_familiya.replace(/'/g, "\\\\'")}')">
                <td>${a.ism_familiya} <span class="oq-belgi">›</span></td>
                <td>${a.consultatsiya_soni} ta</td>
                <td>${a.ortacha_daqiqa} daq</td>
            </tr>`).join('');

        // XODIMLAR REYTINGI — mijozlar bergan yulduzcha bahosi bo'yicha (butun davr bo'yicha)
        const reytingQatorlar = (m.xodimlar_reytingi || []).map(r => `
            <tr>
                <td>${r.ism_familiya}</td>
                <td>${r.ortacha_baho !== null ? '⭐ ' + r.ortacha_baho : '—'}</td>
                <td>${r.baho_soni} ta baho</td>
            </tr>`).join('');

        // YO'NALISHLAR STATISTIKASI — ZUB / Buxgalteriya / UNF qaysi biri eng ko'p so'ralgan
        const yonalishQatorlar = (m.yonalishlar_statistikasi || []).map(y => `
            <tr><td>${y.yonalish}</td><td>${y.soni} ta zayavka</td></tr>`).join('');

        // OYLIK HISOBOT — shu oy (1-kunidan hozirgacha) bo'yicha har bir xodimning umumiy ko'rsatkichlari
        const oylikQatorlar = (m.oylik_hisobot || []).map(o => `
            <tr class="bosiladi" onclick="xodimOylikTafsilot(${o.xodim_id}, '${o.ism_familiya.replace(/'/g, "\\\\'")}')">
                <td>${o.ism_familiya} <span class="oq-belgi">›</span></td>
                <td>${o.mijozlar_soni}</td>
                <td>${o.jami_soat} soat</td>
                <td>${o.izohlar_soni}</td>
                <td style="color:#22c55e">${o.ijobiy_soni}</td>
                <td style="color:#ef4444">${o.salbiy_soni}</td>
                <td>⭐ ${o.yulduzlar_yigindisi}</td>
            </tr>`).join('');

        const kompaniyalarSoni = (m.kompaniyalar_statistikasi || []).length;  // tugmadagi sonni ko'rsatish uchun

        ownerBolim.innerHTML = `
            <div class="bolim-sarlavha">${IKON.xodimlar} Xodimlar holati</div>
            <div class="karta oddiy">${xodimlarHtml}</div>

            <div class="bolim-sarlavha">${IKON.chart} Analitika — bugungi o'rtacha gaplashish vaqti</div>
            <div class="kichik-matn" style="margin-top:-8px;margin-bottom:10px">Tafsilot uchun xodim ustiga bosing</div>
            <div class="karta oddiy">
                <table class="analitika">
                    <tr><th>Xodim</th><th>Soni</th><th>O'rtacha</th></tr>
                    ${analitikaQatorlar || '<tr><td colspan="3" style="color:#6b7280">Bugun hali hech kim yakunlamagan</td></tr>'}
                </table>
            </div>

            <div class="bolim-sarlavha">${IKON.star} Xodimlar reytingi (mijozlar bahosi, butun davr)</div>
            <div class="karta oddiy">
                <table class="analitika">
                    <tr><th>Xodim</th><th>O'rtacha</th><th>Baholar</th></tr>
                    ${reytingQatorlar || '<tr><td colspan="3" style="color:#6b7280">Hali hech kim baholanmagan</td></tr>'}
                </table>
            </div>

            <div class="bolim-sarlavha">${IKON.trend} Yo'nalishlar statistikasi (eng ko'p so'ralgan)</div>
            <div class="karta oddiy">
                <table class="analitika">
                    <tr><th>Yo'nalish</th><th>Soni</th></tr>
                    ${yonalishQatorlar || '<tr><td colspan="2" style="color:#6b7280">Hali ma\\'lumot yo\\'q</td></tr>'}
                </table>
            </div>

            <div class="bolim-sarlavha">${IKON.briefcase} Kompaniyalar bo'yicha statistika</div>
            <div class="karta oddiy" style="cursor:pointer" onclick="kompaniyalarniKorsat()">
                <div class="sarlavha">
                    <span>Barcha kompaniyalar (${kompaniyalarSoni})</span>
                    <span class="oq-belgi">Ko'rish ›</span>
                </div>
                <div class="matn" style="margin-bottom:0">Qaysi kompaniya qaysi yo'nalish bo'yicha ko'proq murojaat qilyapti</div>
            </div>

            <div class="bolim-sarlavha">${IKON.calendar} Oylik hisobot (shu oy boshidan)</div>
            <div class="kichik-matn" style="margin-top:-8px;margin-bottom:10px">
                Har oyning 1-kunidan hozirgi paytgacha yig'ilgan umumiy ko'rsatkichlar
            </div>
            <div class="karta oddiy" style="overflow-x:auto">
                <table class="analitika">
                    <tr><th>Xodim</th><th>Mijoz</th><th>Vaqt</th><th>Izoh</th><th>👍</th><th>👎</th><th>⭐ jami</th></tr>
                    ${oylikQatorlar || '<tr><td colspan="7" style="color:#6b7280">Bu oy hali ma\\'lumot yo\\'q</td></tr>'}
                </table>
            </div>`;
    } else {
        ownerBolim.innerHTML = '';
    }

    taymerlarniYangila();
}

async function qabul(zayavka_id) {
    // agar shu zayavka uchun so'rov ALLAQACHON ketayotgan bo'lsa — qayta yubormaymiz (tez-tez bosishning oldi olinadi)
    if (amalKutilmoqda.has(zayavka_id)) return;
    amalKutilmoqda.add(zayavka_id);
    try {
        const natija = await so_rov('/api/app/qabul', 'POST', { zayavka_id });
        if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred(natija.ok ? 'success' : 'error');
        if (tg.showPopup) tg.showPopup({ message: natija.xabar }); else alert(natija.xabar);
        yukla();
    } finally {
        amalKutilmoqda.delete(zayavka_id);  // so'rov tugadi (muvaffaqiyatli yoki xato) — qayta bosishga ruxsat
    }
}

// "Consultatsiya berdim" bosilganda — DARHOL yakunlamaymiz, avval yo'nalish tanlash chiplarini ko'rsatamiz
function tugatishniBoshla(zayavka_id) {
    tanlashJarayonida = true;  // shu payt avtomatik yangilanishni to'xtatamiz (tanlov "uchib ketmasin")
    joriyTanlovZayavkaId = zayavka_id;
    joriyTanlov = [];  // tanlovni bo'shdan boshlaymiz
    yonalishBlokiniChiz(zayavka_id);
}

// "Telefonni ko'tarmadi" tugmasi bosilganda shu yerga tushadi
async function javobBermadi(zayavka_id) {
    if (amalKutilmoqda.has(zayavka_id)) return;  // allaqachon so'rov ketayapti — qayta yubormaymiz
    amalKutilmoqda.add(zayavka_id);
    try {
        if (tg.HapticFeedback) tg.HapticFeedback.impactOccurred('light');
        const natija = await so_rov('/api/app/javob-bermadi', 'POST', { zayavka_id: zayavka_id });
        if (tg.HapticFeedback) {
            tg.HapticFeedback.notificationOccurred(natija.ok ? 'success' : 'error');
        }
        if (tg.showPopup) {
            tg.showPopup({ message: natija.xabar || '' });
        } else {
            alert(natija.xabar || '');
        }
        yukla();  // panelni yangilaymiz (agar zayavka yopilgan bo'lsa — endi ko'rinmaydi)
    } finally {
        amalKutilmoqda.delete(zayavka_id);
    }
}

// "Qayta aloqaga chiqish" bo'limida "Qabul qilish" qayta bosilganda shu yerga tushadi
async function qaytaQabulQil(zayavka_id) {
    if (amalKutilmoqda.has(zayavka_id)) return;  // allaqachon so'rov ketayapti — qayta yubormaymiz
    amalKutilmoqda.add(zayavka_id);
    try {
        if (tg.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');
        const natija = await so_rov('/api/app/qayta-qabul', 'POST', { zayavka_id: zayavka_id });
        if (tg.HapticFeedback) {
            tg.HapticFeedback.notificationOccurred(natija.ok ? 'success' : 'error');
        }
        if (!natija.ok) {
            if (tg.showPopup) tg.showPopup({ message: natija.xabar || '' }); else alert(natija.xabar || '');
        }
        yukla();  // panelni yangilaymiz — mijoz endi "Consultatsiya jarayonda" bo'limiga o'tadi
    } finally {
        amalKutilmoqda.delete(zayavka_id);
    }
}

// "Kutish rejimi" tugmasi bosilganda: mijoz kutish bo'limiga o'tadi, vaqt hisoblanmaydi, xodim bo'shaydi
async function kutishgaQoy(zayavka_id) {
    if (amalKutilmoqda.has(zayavka_id)) return;  // allaqachon so'rov ketayapti — qayta yubormaymiz
    amalKutilmoqda.add(zayavka_id);
    try {
        if (tg.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');
        const natija = await so_rov('/api/app/kutish', 'POST', { zayavka_id: zayavka_id });
        if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred(natija.ok ? 'success' : 'error');
        if (tg.showPopup) tg.showPopup({ message: natija.xabar || '' }); else alert(natija.xabar || '');
        yukla();
    } finally {
        amalKutilmoqda.delete(zayavka_id);
    }
}

// Kutish rejimidagi mijozda "Davom ettirish" bosilganda: mijoz yana "jarayonda"ga qaytadi
async function kutishdanDavomEt(zayavka_id) {
    if (amalKutilmoqda.has(zayavka_id)) return;
    amalKutilmoqda.add(zayavka_id);
    try {
        if (tg.HapticFeedback) tg.HapticFeedback.impactOccurred('medium');
        const natija = await so_rov('/api/app/kutishdan-davom', 'POST', { zayavka_id: zayavka_id });
        if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred(natija.ok ? 'success' : 'error');
        if (!natija.ok) {
            if (tg.showPopup) tg.showPopup({ message: natija.xabar || '' }); else alert(natija.xabar || '');
        }
        yukla();
    } finally {
        amalKutilmoqda.delete(zayavka_id);
    }
}

// ZUB / Buxgalteriya / UNF chiplarini va tagidagi tugmalarni chizadi (yoki qayta chizadi)
function yonalishBlokiniChiz(zayavka_id) {
    const chiplar = MUMKIN_YONALISHLAR.map(y => {
        const tanlanganmi = joriyTanlov.includes(y);
        return `<span class="chip ${tanlanganmi ? 'tanlangan' : ''}" onclick="chipniAlmashtir('${y}', ${zayavka_id})">${tanlanganmi ? '✅' : ''} ${y}</span>`;
    }).join('');

    const joy = document.getElementById('amal-' + zayavka_id);
    if (!joy) return;  // agar karta ekranda bo'lmasa (kamdan-kam holat), hech narsa qilmaymiz
    joy.innerHTML = `
        <div class="kichik-matn" style="margin-top:10px">Yo'nalishni belgilang (kamida 1, ko'pi bilan 2 ta):</div>
        <div class="chip-qator">${chiplar}</div>
        <button class="btn-tugat" onclick="yonalishniYakunla(${zayavka_id})">☑️ Yakunlash</button>
        <button class="btn-bekor" onclick="yonalishBekorQil()">Bekor qilish</button>`;
}

// bitta chip bosilganda — uni tanlangan/tanlanmagan holatga o'tkazadi
function chipniAlmashtir(yonalish, zayavka_id) {
    if (joriyTanlov.includes(yonalish)) {
        joriyTanlov = joriyTanlov.filter(y => y !== yonalish);  // ro'yxatdan olib tashlaymiz
    } else if (joriyTanlov.length < 2) {
        joriyTanlov.push(yonalish);  // ro'yxatga qo'shamiz (ko'pi bilan 2 tagacha)
    } else {
        if (tg.showPopup) tg.showPopup({ message: "Ko'pi bilan 2 tagacha tanlash mumkin." });
        return;
    }
    yonalishBlokiniChiz(zayavka_id);  // yangilangan holat bilan qayta chizamiz
}

// "Bekor qilish" bosilsa — tanlov rejimidan chiqib, oddiy ro'yxatga qaytamiz
function yonalishBekorQil() {
    tanlashJarayonida = false;
    joriyTanlovZayavkaId = null;
    joriyTanlov = [];
    yukla();  // ro'yxatni yangidan yuklab, asl "Consultatsiya berdim" tugmasini qaytaramiz
}

// "Yakunlash" bosilsa — avval tanlangan yo'nalishlarni saqlaymiz, so'ng zayavkani yakunlaymiz
async function yonalishniYakunla(zayavka_id) {
    if (joriyTanlov.length === 0) {
        if (tg.showPopup) tg.showPopup({ message: "Kamida 1 ta yo'nalish tanlang." });
        return;
    }
    const saqlash = await so_rov('/api/app/yonalish', 'POST', { zayavka_id, yonalishlar: joriyTanlov });
    if (!saqlash.ok) {
        if (tg.showPopup) tg.showPopup({ message: saqlash.xabar }); else alert(saqlash.xabar);
        return;
    }
    tanlashJarayonida = false;  // endi yakunlaymiz, poll'ni qayta yoqamiz
    await tugat(zayavka_id);  // asosiy yakunlash funksiyasi (server tomonda ham tekshiriladi)
}

async function tugat(zayavka_id) {
    if (amalKutilmoqda.has(zayavka_id)) return;  // allaqachon so'rov ketayapti — qayta yubormaymiz
    amalKutilmoqda.add(zayavka_id);
    try {
        const natija = await so_rov('/api/app/tugat', 'POST', { zayavka_id });
        if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred(natija.ok ? 'success' : 'error');
        if (tg.showPopup) tg.showPopup({ message: natija.xabar }); else alert(natija.xabar);
        yukla();
    } finally {
        amalKutilmoqda.delete(zayavka_id);
    }
}

// analitika jadvalida bitta xodim ustiga bosilganda — uning bugungi mijozlari ro'yxatini ochadi
// bitta mijoz kartasini chizadi. izohliMi=true bo'lsa — baho/izoh ko'rsatiladi (faqat "tugallandi" uchun mantiqiy),
// aks holda (hali yakunlanmagan/javob bermagan holatlar uchun) o'rniga urinishlar sonini ko'rsatamiz
function mijozKartasiChiz(mij, izohliMi) {
    let qoshimcha_html = '';
    if (izohliMi) {
        // baho bo'yicha ijobiy/neytral/salbiy deb belgilaymiz (4-5 ijobiy, 3 neytral, 1-2 salbiy)
        let bahoHtml = '<span style="color:var(--text-faint)">Hali baholanmagan</span>';
        if (mij.yulduz) {
            let holatMatni = '😐 Neytral';
            let holatRang = '#eab308';
            if (mij.yulduz >= 4) { holatMatni = '👍 Ijobiy'; holatRang = '#22c55e'; }
            else if (mij.yulduz <= 2) { holatMatni = '👎 Salbiy'; holatRang = '#ef4444'; }
            bahoHtml = `${'⭐'.repeat(mij.yulduz)} <span style="color:${holatRang};font-weight:700">${holatMatni}</span>`;
        }
        // mijozning yozgan izohi (komentariyasi). Bu blok FAQAT rahbarlarga (owner/super_user) chiziladi —
        // oddiy xodim uchun izohliMi=false beriladi (tafsilotTabiniChiz'ga qarang), shuning uchun u buni ko'rmaydi
        const izohHtml = mij.izoh
            ? `<div class="matn" style="margin-top:6px;margin-bottom:0;border-top:1px solid var(--border-soft);padding-top:6px">💬 «${esc(mij.izoh)}»</div>`
            : '';
        qoshimcha_html = `<div style="margin-top:8px;font-size:13px">${bahoHtml}</div>${izohHtml}`;
    } else if (mij.qongiroq_soni) {
        qoshimcha_html = `<div class="urinish-belgisi">📵 ${mij.qongiroq_soni}/${QONGIROQ_MAKS} marta urinilgan</div>`;
    }
    return `
        <div class="karta oddiy">
            <div class="sarlavha">
                <span>${esc(mij.mijoz_ismi)}</span>
                <span class="davomiylik">${(mij.daqiqa !== null && mij.daqiqa !== undefined) ? mij.daqiqa + ' daq' : '—'}</span>
            </div>
            ${mij.kompaniya_nomi ? `<div class="kompaniya-belgisi">🏢 ${esc(mij.kompaniya_nomi)}</div>` : ''}
            <div class="kim">📞 ${esc(mij.mijoz_telefon) || '—'} &nbsp;·&nbsp; 🆔 INN: ${esc(mij.mijoz_inn) || '—'}</div>
            <div class="matn">${esc((mij.matn || 'Sabab yozilmagan').slice(0, 250))}</div>
            ${qoshimcha_html}
        </div>`;
}

// har bir tab qaysi maydonni (tugallandi/qayta_aloqa/javob_bermadi) va qanday ko'rsatilishini belgilaydi
const TAFSILOT_TABLARI = [
    { kalit: 'tugallandi', nom: '✅ Konsultatsiya berildi', izohliMi: true, bosh: 'Hali hech kim bilan gaplashmagan' },
    { kalit: 'qayta_aloqa', nom: '🔁 Qayta aloqaga chiqish', izohliMi: false, bosh: 'Hozircha qayta aloqaga chiqilayotgan mijoz yo\\'q' },
    { kalit: 'javob_bermadi', nom: '📵 Javob bermadi', izohliMi: false, bosh: 'Hali hech kim javob bermay qolmagan' },
];

async function tafsilotniKorsat(manzil, ism, izohMatni) {
    const natija = await so_rov(manzil, 'GET');
    if (!natija.ok) {
        if (tg.showPopup) tg.showPopup({ message: natija.xato }); else alert(natija.xato);
        return;
    }
    joriyTafsilotMalumoti = natija;  // 3 ta ro'yxat ham shu obyekt ichida (tugallandi/qayta_aloqa/javob_bermadi)

    document.getElementById('tafsilot-sarlavha').textContent = ism;
    document.getElementById('tafsilot-izoh').textContent = izohMatni;
    tafsilotTabiniChiz('tugallandi');  // standart holatda birinchi tab ochiladi

    document.getElementById('tafsilot-modal').style.display = 'block';
    window.scrollTo(0, 0);
}

// tafsilot oynasi ichidagi 3 tabdan birini (yoki qayta) chizadi
function tafsilotTabiniChiz(tanlangan_kalit) {
    const m = joriyTafsilotMalumoti;
    if (!m) return;

    // tab tugmalarini (har birida shu toifadagi mijozlar soni bilan) chizamiz
    document.getElementById('tafsilot-tablar').innerHTML = TAFSILOT_TABLARI.map(t => `
        <span class="chip ${t.kalit === tanlangan_kalit ? 'tanlangan' : ''}" onclick="tafsilotTabiniChiz('${t.kalit}')">
            ${t.nom} (${(m[t.kalit] || []).length})
        </span>`).join('');

    // MUHIM: mijozning bahosi/izohi (ayniqsa salbiy bo'lsa) — bu FAQAT rahbarlarga (owner/super_user)
    // ko'rinadi. Oddiy xodim (masalan o'zining "Bugungi ko'rsatkichlarim" havolasidan kirganda)
    // buni ko'rmasligi kerak — aks holda salbiy fikr uni tushkunlikka solib, kayfiyatiga va
    // ishtiyoqiga salbiy ta'sir qilishi mumkin
    const joriyRol = (oxirgiMalumot && oxirgiMalumot.xodim && oxirgiMalumot.xodim.rol) || 'xodim';
    const bahoKorinsinmi = joriyRol !== 'xodim';

    const joriy_tab = TAFSILOT_TABLARI.find(t => t.kalit === tanlangan_kalit);
    const royxat = m[tanlangan_kalit] || [];
    const royxatJoy = document.getElementById('tafsilot-royxat');
    royxatJoy.innerHTML = royxat.length === 0
        ? `<div class="bosh-holat">${joriy_tab.bosh}</div>`
        : royxat.map(mij => mijozKartasiChiz(mij, joriy_tab.izohliMi && bahoKorinsinmi)).join('');
}

// Analitika (bugungi) bo'limida xodim ustiga bosilganda
function xodimTafsilot(xodim_id, ism) {
    tafsilotniKorsat('/api/app/xodim-mijozlari/' + xodim_id, ism, 'Bugungi ko\\'rsatkichlar');
}

// "📋 Bugungi ko'rsatkichlarim" havolasi bosilganda — xodim O'ZINING bugungi ma'lumotini ko'radi
function ozimTafsilot() {
    if (!oxirgiMalumot || !oxirgiMalumot.xodim) return;
    xodimTafsilot(oxirgiMalumot.xodim.id, oxirgiMalumot.xodim.ism_familiya);
}

// Oylik hisobotda xodim ustiga bosilganda
function xodimOylikTafsilot(xodim_id, ism) {
    tafsilotniKorsat('/api/app/xodim-oylik-mijozlari/' + xodim_id, ism, "Shu oy bo'yicha ko'rsatkichlar");
}

// "Kompaniyalar bo'yicha statistika" kartasi bosilganda — xuddi shu oynani, lekin jadval bilan ochamiz
function kompaniyalarniKorsat() {
    const royxat = (oxirgiMalumot && oxirgiMalumot.kompaniyalar_statistikasi) || [];
    document.getElementById('tafsilot-sarlavha').textContent = "Kompaniyalar bo'yicha statistika";
    document.getElementById('tafsilot-izoh').textContent = "Qaysi kompaniya qaysi yo'nalish bo'yicha ko'proq murojaat qilyapti";
    document.getElementById('tafsilot-tablar').innerHTML = '';  // bu oynada tab kerak emas

    const qatorlar = royxat.map(k => `
        <tr>
            <td>${esc(k.kompaniya)}</td>
            <td>${k.jami}</td>
            <td style="color:#3b82f6;font-weight:700">${k.eng_kop_yonalish}</td>
            <td style="font-size:11px;color:var(--text-faint)">ZUB:${k.taqsimot.ZUB} · Bux:${k.taqsimot.Buxgalteriya} · UNF:${k.taqsimot.UNF}</td>
        </tr>`).join('');

    document.getElementById('tafsilot-royxat').innerHTML = `
        <div class="karta oddiy" style="overflow-x:auto">
            <table class="analitika">
                <tr><th>Kompaniya</th><th>Jami</th><th>Eng ko'p</th><th>Taqsimot</th></tr>
                ${qatorlar || '<tr><td colspan="4" style="color:var(--text-faint)">Hali ma\\'lumot yo\\'q</td></tr>'}
            </table>
        </div>`;

    document.getElementById('tafsilot-modal').style.display = 'block';
    window.scrollTo(0, 0);
}

function modalniYop() {
    document.getElementById('tafsilot-modal').style.display = 'none';
}

function taymerlarniYangila() {
    const JAMI_SONIYA = 20 * 60;

    document.querySelectorAll('.karta[data-yaratilgan]:not([data-yaratilgan=""])').forEach(karta => {
        const boshlangan = new Date(karta.dataset.yaratilgan).getTime();
        const otgan = Math.floor((Date.now() - boshlangan) / 1000);
        const qolgan = JAMI_SONIYA - otgan;
        const belgisi = karta.querySelector('.taymer');
        if (!belgisi) return;

        let rang = 'yashil';
        if (qolgan <= 0) rang = 'tugagan';
        else if (otgan >= 15 * 60) rang = 'qizil';
        else if (otgan >= 10 * 60) rang = 'sariq';

        belgisi.className = 'taymer ' + rang;
        karta.style.borderLeftColor = { yashil: '#22c55e', sariq: '#eab308', qizil: '#ef4444', tugagan: '#7f1d1d' }[rang];
        belgisi.textContent = qolgan <= 0 ? 'Muddat tugadi' : `${Math.floor(qolgan / 60)}:${String(qolgan % 60).padStart(2, '0')}`;
    });

    document.querySelectorAll('.karta[data-boshlangan]:not([data-boshlangan=""])').forEach(karta => {
        const boshlangan = new Date(karta.dataset.boshlangan).getTime();
        const kutilgan = parseInt(karta.dataset.kutilgan || '0', 10) || 0;  // kutish rejimida o'tgan soniyalar — hisoblanmaydi
        const otgan = Math.max(0, Math.floor((Date.now() - boshlangan) / 1000) - kutilgan);
        const belgisi = karta.querySelector('.davomiylik');
        if (!belgisi) return;
        belgisi.textContent = `${Math.floor(otgan / 60)}:${String(otgan % 60).padStart(2, '0')} gaplashmoqda`;
    });

    // kutish rejimidagi mijoz qancha vaqtdan beri kutayotganini ko'rsatamiz (unutilib qolmasligi uchun)
    document.querySelectorAll('.karta[data-kutish-boshlangan]:not([data-kutish-boshlangan=""])').forEach(karta => {
        const boshlangan = new Date(karta.dataset.kutishBoshlangan).getTime();
        const otgan = Math.max(0, Math.floor((Date.now() - boshlangan) / 1000));
        const belgisi = karta.querySelector('.kutish-vaqti');
        if (!belgisi) return;
        const soat = Math.floor(otgan / 3600);
        const daqiqa = Math.floor((otgan % 3600) / 60);
        const soniya = String(otgan % 60).padStart(2, '0');
        belgisi.textContent = soat > 0
            ? `⏳ ${soat}:${String(daqiqa).padStart(2, '0')}:${soniya}`
            : `⏳ ${daqiqa}:${soniya}`;
    });
}

yukla();
setInterval(() => { if (!tanlashJarayonida) yukla(); }, 8000);  // tanlash jarayonida "uchib ketmasin" deb to'xtatamiz
setInterval(taymerlarniYangila, 1000);

</script>
</body>
</html>
"""
