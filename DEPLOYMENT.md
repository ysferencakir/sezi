# Sezi — Deployment Planı

**Durum:** Render'dan VPS'e geçiş planlanıyor — VPS henüz sipariş edilmedi.
**Hedef:** `sezi.ysferencakir.info.tr` üzerinde 7/24 çalışan bir prod ortamı.

---

## Neden VPS (Render değil)

Sezi'nin iki bileşeni **sürekli çalışan bir process** gerektiriyor:
- Telegram bot (`core/telegram_bot.py`) — long-polling ile mesaj dinliyor
- APScheduler (`core/scheduler.py`) — günlük senkronlar + akşam hatırlatmaları için cron job'ları

Render'a geçmiştik ama **otobüs takip özelliği** (`modules/transit/eshot_scraper.py`) `eshot.gov.tr`'yi scrape ediyor ve bu site bulut sağlayıcıların (Render dahil) datacenter IP aralıklarını engelliyor. Çözüm olarak ScraperAPI proxy'si denendi (çalıştı) ama ücretsiz deneme 7 günlük — sonrası ücretli. Türkiye IP'li bir VPS bu sorunu **kökten** çözüyor: proxy'ye hiç gerek kalmıyor, `eshot_scraper.py` doğrudan çalışır.

VPS'in eskiden vazgeçilme sebebi (manuel deploy yükü) **GitHub Actions ile SSH auto-deploy** kurularak çözülüyor — böylece Render'daki "push'ta otomatik deploy" deneyimi büyük ölçüde korunuyor.

**Seçilen plan:** TR-VPS-1 — 1 CPU, 512MB RAM, 20GB SSD, 500GB trafik, ~230 TL/ay. Veritabanı zaten Neon'da (VPS dışında) çalıştığı için VPS'in yükü sadece FastAPI + Caddy + Telegram bot.

---

## Adım 1 — VPS Siparişi ve İlk Erişim

- [ ] TR-VPS-1 planını sipariş et
- [ ] İşletim sistemi: **Ubuntu 24.04 LTS** seç (mevcut değilse 22.04)
- [ ] Sipariş sonrası: sunucu IP adresi + root şifresi (ya da SSH key)

## Adım 2 — Sunucu Temel Kurulumu

```bash
apt update && apt upgrade -y
apt install -y python3.12 python3.12-venv python3-pip git ufw caddy
```

- [ ] 1GB swap dosyası oluştur (RAM dar olduğu için güvenlik payı):
  ```bash
  fallocate -l 1G /swapfile && chmod 600 /swapfile
  mkswap /swapfile && swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
  ```
- [ ] Firewall (ufw): sadece 22 (SSH), 80, 443 açık
  ```bash
  ufw allow OpenSSH && ufw allow 80 && ufw allow 443 && ufw enable
  ```
- [ ] Ayrıcalıksız bir sistem kullanıcısı oluştur (root olarak çalıştırmamak için):
  ```bash
  adduser --system --group --home /opt/sezi sezi
  ```

## Adım 3 — Repo ve Ortam

- [ ] Repo'yu sunucuya çek: `git clone https://github.com/ysferencakir/sezi.git /opt/sezi`
- [ ] `/opt/sezi` sahipliğini `sezi` kullanıcısına ver: `chown -R sezi:sezi /opt/sezi`
- [ ] Venv oluştur, bağımlılıkları kur:
  ```bash
  cd /opt/sezi && python3.12 -m venv .venv
  .venv/bin/pip install -r requirements.txt
  ```
- [ ] `.env` dosyasını sunucuda oluştur (yerel `.env` içeriğiyle aynı, **iki farkla**):
  - `GOOGLE_REDIRECT_URI=https://sezi.ysferencakir.info.tr/auth/google/callback`
  - `APP_ENV=production`
  - `SCRAPERAPI_KEY` **eklenmeyecek** — VPS zaten Türkiye IP'li olduğu için gerek yok, `eshot_scraper.py` otomatik olarak proxy'siz direkt bağlanır
- [ ] Google Cloud Console'da OAuth client'a yeni redirect URI'yi ekle (eski localhost URI'sini silme, ikisi birlikte durabilir)

## Adım 4 — systemd Servisi

`/etc/systemd/system/sezi.service`:
```ini
[Unit]
Description=Sezi FastAPI app
After=network.target

[Service]
Type=simple
User=sezi
WorkingDirectory=/opt/sezi
ExecStart=/opt/sezi/.venv/bin/python main.py
Restart=always
RestartSec=5
EnvironmentFile=/opt/sezi/.env
Environment=PORT=8000

[Install]
WantedBy=multi-user.target
```

- [ ] `systemctl daemon-reload && systemctl enable --now sezi`
- [ ] `systemctl status sezi` ile doğrula, `journalctl -u sezi -f` ile logları izle

## Adım 5 — Caddy (Reverse Proxy + Otomatik HTTPS)

`/etc/caddy/Caddyfile`:
```
sezi.ysferencakir.info.tr {
    reverse_proxy localhost:8000
}
```

- [ ] `systemctl reload caddy`
- [ ] Caddy, Let's Encrypt sertifikasını otomatik alır — DNS doğru ayarlıysa ek işlem gerekmez

## Adım 6 — DNS

- [ ] Domain sağlayıcısında (`ysferencakir.info.tr`) `sezi` subdomain'i için **A kaydı** → VPS IP adresi
- [ ] DNS yayılımını bekle (`dig sezi.ysferencakir.info.tr` ile kontrol edilebilir)

## Adım 7 — GitHub Actions ile Otomatik Deploy

Render'daki "push'ta otomatik deploy" deneyimini korumak için `main`'e her push'ta VPS'e SSH ile bağlanıp `git pull` + servis restart yapan bir workflow kuruluyor.

- [ ] VPS'te deploy için bir SSH key çifti oluştur (sadece bu iş için, ayrı bir key):
  ```bash
  ssh-keygen -t ed25519 -f ~/.ssh/sezi_deploy -N ""
  cat ~/.ssh/sezi_deploy.pub >> /home/sezi/.ssh/authorized_keys   # sezi kullanıcısına eriş
  ```
- [ ] GitHub repo → Settings → Secrets and variables → Actions → şu secret'ları ekle:
  - `VPS_HOST` — sunucu IP'si
  - `VPS_USER` — `sezi`
  - `VPS_SSH_KEY` — `sezi_deploy` private key'in tam içeriği
- [ ] `.github/workflows/deploy.yml` dosyası repoda hazır (bu commit ile birlikte geliyor) — push'ta otomatik tetiklenir
- [ ] `sezi` kullanıcısının parola sormadan `systemctl restart sezi` çalıştırabilmesi için `visudo` ile bir sudoers kuralı ekle:
  ```
  sezi ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart sezi
  ```

## Adım 8 — Doğrulama

- [ ] `https://sezi.ysferencakir.info.tr/health` → `{"status":"ok"}`
- [ ] `https://sezi.ysferencakir.info.tr/` → dashboard açılıyor
- [ ] `/auth/google/authorize` ile prod ortamda yeniden yetkilendirme (yeni redirect_uri ile)
- [ ] Telegram bot'a `/context` veya `/sigara` yazıp yanıt geldiğini doğrula (bot artık VPS'ten polling yapıyor — **yerel makinede `python main.py` bir daha çalıştırılmamalı**, ikisi birden çalışırsa Telegram "409 Conflict" hatası verir)
- [ ] `/otobus` komutunu dene — artık proxy'siz, doğrudan gerçek mesafe/süre dönmeli
- [ ] Bir test commit'i push'la, GitHub Actions sekmesinden deploy'un otomatik tetiklendiğini doğrula

## Sonradan Yapılacak / Riskler

- **Render servisi** — VPS doğrulandıktan sonra Render'daki "sezi" servisini Suspend/Delete et (aynı Telegram token'ıyla iki yerde polling yapılırsa 409 Conflict çıkar — geçiş sırasında dikkat).
- **ScraperAPI** — artık gerekmiyor, `.env`'e `SCRAPERAPI_KEY` eklenmeyecek. İlerde tekrar bulut sağlayıcıya dönülürse kod zaten hazır (key eklenince otomatik devreye girer).
- **Yedekleme** — DB zaten Neon'da (kendi yedekleme politikaları var). VPS'te kalıcı veri yok (kod hariç), sunucu kaybı kritik değil — yeniden kurulabilir.
- **RAM darlığı** — 512MB dar; ileride modül sayısı artarsa ya da bot yükü artarsa üst plana geçmek gerekebilir.
- **Telegram bot çakışması** — yerel makinede test amaçlı `python main.py` çalıştırılırsa prod bot ile aynı anda polling yapmaya çalışıp hata verir. Test ederken VPS servisini durdurmak (`systemctl stop sezi`) ya da ayrı bir test bot token'ı kullanmak gerekir.
- **GitHub Actions deploy hatası** — deploy script'i `git pull` sırasında conflict/hata verirse workflow kırmızı olur ama servis eski haliyle çalışmaya devam eder (restart adımına gelmez) — sessiz bozulma riski yok.
