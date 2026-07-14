# Sezi — Deployment Planı

**Durum:** Planlama aşaması — Render servisi henüz oluşturulmadı.
**Hedef:** `sezi.ysferencakir.info.tr` üzerinde 7/24 çalışan bir prod ortamı.

---

## Neden Render (VPS değil)

Sezi'nin iki bileşeni **sürekli çalışan bir process** gerektiriyor:
- Telegram bot (`core/telegram_bot.py`) — long-polling ile mesaj dinliyor
- APScheduler (`core/scheduler.py`) — günlük senkronlar + akşam hatırlatmaları için cron job'ları

Bunlar FastAPI app'in `lifespan` fonksiyonunda aynı process içinde başlatılıyor (`api/main.py`). Aynı process HTTP de sunuyor (dashboard, `/api/*`, Google OAuth callback), bu yüzden Render'da **Web Service** olarak deploy edilmeli — Background Worker değil, çünkü Background Worker'ın public URL'i yok ve OAuth callback / dashboard'a erişilemez.

VPS + systemd + Caddy planından vazgeçildi (kurulum/yönetim yükü fazla geldi). Render'da:
- **Hobby plan** ($0/mo, workspace ücreti) — bireysel proje için yeterli, takım özelliklerine gerek yok
- **+ Starter compute instance** (~$7/ay) — Web Service'i her zaman açık tutar, ücretsiz instance'ın 15 dakika inaktivite sonrası uyuması sorununu (bot/scheduler'ı öldüren asıl problem) ortadan kaldırır

Veritabanı zaten Neon'da (Render dışında) çalıştığı için Render'ın tek işi FastAPI + Telegram bot + scheduler'ı ayakta tutmak.

---

## Adım 1 — Render'da Web Service Oluştur

- [ ] [render.com](https://render.com) → New → **Web Service**
- [ ] GitHub reposunu bağla (`ysferencakir/sezi`)
- [ ] Ayarlar:
  - **Runtime:** Python 3
  - **Build Command:** `pip install -r requirements.txt`
  - **Start Command:** `python main.py` (main.py zaten `$PORT` ortam değişkenini uvicorn'a geçiriyor olmalı — kontrol et, yoksa `uvicorn api.main:app --host 0.0.0.0 --port $PORT` olarak güncelle)
  - **Instance Type:** **Starter** ($7/mo) — Free seçilirse 15 dakika inaktivitede uyur, bot/scheduler ölür
  - **Region:** Frankfurt (Avrupa'ya en yakın, TR'ye düşük gecikme)

## Adım 2 — Ortam Değişkenleri

Render dashboard → Environment sekmesinde `.env` dosyasındaki tüm değişkenleri tek tek ekle, **iki farkla**:
- [ ] `GOOGLE_REDIRECT_URI=https://sezi.ysferencakir.info.tr/auth/google/callback`
- [ ] `APP_ENV=production`
- [ ] Diğerleri birebir aynı: `DATABASE_URL` (Neon), `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, Google OAuth client id/secret vb.
- [ ] Google Cloud Console'da OAuth client'a yeni redirect URI'yi ekle (eski localhost URI'sini silme, ikisi birlikte durabilir — test için işe yarayabilir)

## Adım 3 — Custom Domain

- [ ] Render dashboard → Settings → Custom Domain → `sezi.ysferencakir.info.tr` ekle
- [ ] Render'ın verdiği CNAME kaydını domain sağlayıcısında (`ysferencakir.info.tr`) `sezi` subdomain'i için tanımla
- [ ] Render otomatik Let's Encrypt sertifikası sağlıyor — DNS yayıldıktan sonra ek işlem gerekmez (`dig sezi.ysferencakir.info.tr` ile doğrulanabilir)

## Adım 4 — Deploy ve Doğrulama

- [ ] İlk deploy'u tetikle (push sonrası otomatik olur, ya da dashboard'dan "Manual Deploy")
- [ ] Logs sekmesinden başlangıç loglarını izle — Telegram bot'un polling'e başladığını, scheduler'ın job'ları yüklediğini doğrula
- [ ] `https://sezi.ysferencakir.info.tr/health` → `{"status":"ok"}`
- [ ] `https://sezi.ysferencakir.info.tr/` → dashboard açılıyor
- [ ] `/auth/google/authorize` ile prod ortamda yeniden yetkilendirme (yeni redirect_uri ile)
- [ ] Telegram bot'a `/context` veya `/sigara` yazıp yanıt geldiğini doğrula (bot artık Render'dan polling yapıyor — **yerel makinede `python main.py` bir daha çalıştırılmamalı**, ikisi birden çalışırsa Telegram "409 Conflict" hatası verir)
- [ ] Bir modülü manuel tetikleyip (`POST /modules/health/run`) uçtan uca çalıştığını doğrula

## Sonradan Yapılacak / Riskler

- **Otomatik deploy** — Render GitHub push'ta otomatik deploy yapar (VPS'teki manuel `git pull && systemctl restart` derdi yok), bu VPS planına göre net avantaj.
- **Yedekleme** — DB zaten Neon'da (onların kendi yedekleme politikası var). Render'da kalıcı veri yok (kod hariç), servis kaybı kritik değil — yeniden deploy edilebilir.
- **Maliyet** — Hobby ($0) + Starter compute (~$7/ay ≈ 230-250 TL, kura bağlı) — TR-VPS-1 planına (~230 TL/ay) yakın, yönetim yükü çok daha düşük.
- **Telegram bot çakışması** — yerel makinede test amaçlı `python main.py` çalıştırılırsa prod bot ile aynı anda polling yapmaya çalışıp hata verir. Test ederken Render servisini durdurmak (Suspend) ya da ayrı bir test bot token'ı kullanmak gerekir.
- **Cold start yok** — Starter instance sürekli açık olduğu için free tier'daki "ilk istek yavaş" sorunu da ortadan kalkar.
