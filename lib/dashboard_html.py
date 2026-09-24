# Bu fayl rahbarlar paneli (dashboard) uchun tayyor HTML sahifani saqlaydi
# Sahifa hech qanday tashqi kutubxonaga bog'liq emas (hammasi bitta faylda) —
# shunday qilib Vercel'da ishlashi kafolatlanadi

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FINCUBE Support — jonli panel</title>
<style>
    /* umumiy ko'rinish sozlamalari — qora fon, oq matn, zamonaviy shrift */
    body {
        background: #0f1115;
        color: #e6e6e6;
        font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif;
        margin: 0;
        padding: 24px;
    }
    h1 { font-size: 20px; margin-bottom: 4px; }
    .yangilangan { color: #888; font-size: 13px; margin-bottom: 24px; }

    /* yuqoridagi 3 ta katta raqamli kartalar uchun panjara (grid) */
    .kartalar {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 14px;
        margin-bottom: 28px;
    }
    .karta {
        background: #1a1d24;
        border-radius: 12px;
        padding: 18px;
        border: 1px solid #262a33;
    }
    .karta .son { font-size: 32px; font-weight: 700; }
    .karta .nom { color: #9aa0aa; font-size: 13px; margin-top: 4px; }

    .bolim-sarlavha { font-size: 15px; color: #9aa0aa; margin: 24px 0 10px; }

    /* xodimlar ro'yxati uchun kartalar */
    .xodimlar { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; }
    .xodim-karta {
        background: #1a1d24;
        border-radius: 10px;
        padding: 14px;
        border: 1px solid #262a33;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .nuqta { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
    .nuqta.bosh { background: #22c55e; }   /* yashil — bo'sh */
    .nuqta.band { background: #ef4444; }   /* qizil — band */
    .xodim-ism { font-weight: 600; }
    .xodim-holat { color: #9aa0aa; font-size: 12px; }
</style>
</head>
<body>
    <h1>🟢 FINCUBE Support — jonli panel</h1>
    <div class="yangilangan" id="yangilangan-vaqt">Yuklanmoqda...</div>

    <div class="kartalar">
        <div class="karta">
            <div class="son" id="hozir-consultatsiyada">—</div>
            <div class="nom">Hozir consultatsiyada</div>
        </div>
        <div class="karta">
            <div class="son" id="navbatda">—</div>
            <div class="nom">Navbatda kutmoqda</div>
        </div>
        <div class="karta">
            <div class="son" id="bugun-jami">—</div>
            <div class="nom">Bugun jami murojaat</div>
        </div>
        <div class="karta">
            <div class="son" id="bugun-tugallandi">—</div>
            <div class="nom">Bugun consultatsiya berildi</div>
        </div>
        <div class="karta">
            <div class="son" id="bugun-qolib-ketdi">—</div>
            <div class="nom">Bugun qolib ketdi (20 daq)</div>
        </div>
    </div>

    <div class="bolim-sarlavha">XODIMLAR HOLATI</div>
    <div class="xodimlar" id="xodimlar-royxati">Yuklanmoqda...</div>

<script>
// bu funksiya /api/dashboard manzilidan ma'lumot olib, sahifani yangilaydi
async function yangila() {
    try {
        const javob = await fetch('/api/dashboard');   // bizning statistika manzilimizga so'rov yuboramiz
        const malumot = await javob.json();            // kelgan JSON'ni o'qiymiz

        // yuqoridagi 5 ta raqamli kartani yangilaymiz
        document.getElementById('hozir-consultatsiyada').textContent = malumot.hozir_consultatsiyada;
        document.getElementById('navbatda').textContent = malumot.navbatda_kutmoqda;
        document.getElementById('bugun-jami').textContent = malumot.bugun_jami_murojaat;
        document.getElementById('bugun-tugallandi').textContent = malumot.bugun_consultatsiya_berildi;
        document.getElementById('bugun-qolib-ketdi').textContent = malumot.bugun_qolib_ketdi;

        // xodimlar ro'yxatini yangidan chizamiz
        const royxat = document.getElementById('xodimlar-royxati');
        royxat.innerHTML = '';  // eskisini tozalaymiz
        malumot.xodimlar.forEach(xodim => {
            const karta = document.createElement('div');
            karta.className = 'xodim-karta';
            const holatMatni = xodim.holat === 'bosh' ? "Bo'sh — mijoz kuta oladi" : "Band — mijoz bilan gaplashmoqda";
            karta.innerHTML = `
                <div class="nuqta ${xodim.holat}"></div>
                <div>
                    <div class="xodim-ism">${xodim.ism_familiya}</div>
                    <div class="xodim-holat">${holatMatni}</div>
                </div>`;
            royxat.appendChild(karta);
        });

        // "oxirgi yangilangan vaqt" yozuvini yangilaymiz
        const hozir = new Date();
        document.getElementById('yangilangan-vaqt').textContent =
            'Oxirgi yangilanish: ' + hozir.toLocaleTimeString('uz-UZ');
    } catch (xato) {
        document.getElementById('yangilangan-vaqt').textContent = 'Xatolik: ma\\'lumot olinmadi';
    }
}

yangila();                    // sahifa ochilganda darhol bir marta yangilaymiz
setInterval(yangila, 5000);   // keyin har 5 soniyada avtomatik yangilab turamiz
</script>
</body>
</html>
"""
