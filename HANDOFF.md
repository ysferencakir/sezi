# Sezi — Fable 5 Devir Notu

**Amaç:** Bu doküman, projeyi Fable 5'e (veya başka bir modele/oturuma) devrederken hızlı bağlam kazandırmak için yazıldı. `README.md` daha genel/kalıcı dokümantasyon, `PLAN.md` başlangıç (Mayıs 2026) planı — ikisi de artık gerçek koddan geride kalmış durumda. Bu dosya **güncel gerçek durumu** yansıtıyor (2026-07-19 itibarıyla).

---

## Projenin Amacı

Sezi, kullanıcının kendi hayatındaki görünmez örüntüleri (sağlık, takvim, harcama, alışkanlık, ulaşım) gözlemlemesini sağlayan **kişisel veri toplama ve yansıtma sistemi**. Optimizasyon/gamification/koçluk yapmıyor — sadece veriyi topluyor, düzenli özetler (günlük/haftalık) çıkarıyor, yorumu kullanıcıya bırakıyor.

Temel ilkeler (README'den, hâlâ geçerli):
- Zayıf dil: korelasyon evet, nedensellik iddiası yok
- Obsesyon önleme: gerçek zamanlı alert yok, sadece günlük/haftalık/aylık özetler
- Kullanıcı yorumluyor, sistem sadece gösteriyor

---

## Teknik Yapı (mevcut hal)

- **Backend:** Python 3.12.7 + FastAPI, `api/main.py` üzerinden lifespan ile modüller ve scheduler başlatılıyor
- **DB:** PostgreSQL, async SQLAlchemy 2.0 (`core/database.py`)
- **Scheduler:** APScheduler, tüm cron işleri **Europe/Istanbul** saatinde (`core/scheduler.py`)
- **Bildirim:** Telegram bot (`core/telegram_bot.py`) + ntfy.sh fallback (`core/notifier.py`)
- **Modül sistemi:** `core/base_module.py` → `BaseModule.fetch()/process()/run()/schedules()`; `core/module_loader.py` otomatik keşif yapıyor, `modules/` altına yeni klasör atmak yeterli
- **Deploy:** Render.com hedefi, `da4f385` ile deploy workflow eklendi (detay için `DEPLOYMENT.md`)

---

## Mevcut Modüller (kod → gerçek durum)

README'nin "Future Roadmap" bölümü **eski** — şu modüller zaten kodda mevcut ve çalışır durumda görünüyor:

| Modül | Konum | Ne yapıyor |
|---|---|---|
| **health** | `modules/health/` | Google Fit: adım, kalori, aktif dakika, kalp atışı, uyku |
| **calendar** | `modules/calendar/` | Google Calendar: günlük toplantı sayısı/süresi, tatil bilgisi, kategori |
| **context** | `modules/context/` | Haftalık yansıma formu (POST/GET /api/context), Pazar 18:00 hatırlatma |
| **currency** | `modules/currency/` | Frankfurter API ile döviz kuru takibi |
| **weather** | `modules/weather/` | Open-Meteo: hava durumu, hava kalitesi, gün doğumu/batımı, konum servisi |
| **smoking** | `modules/smoking/` | Sigara alışkanlığı takibi (servis katmanı var) |
| **spotify** | `modules/spotify/` | Son çalınan şarkılar, OAuth token yönetimi |
| **notion** | `modules/notion/` | Günlük özetleri bir Notion veritabanına yazma |
| **digest** | `modules/digest/` | Sabah/akşam özetlerini modüllerden toplayıp birleştiren konsolide modül |
| **transit** | `modules/transit/` | İzmir ESHOT otobüs/durak bilgisi scraping, rota/varış verisi, yakınlık ikonları |

**Henüz yok:** Bank/finance modülü, yatırım modülü, React dashboard, query/filter endpoint'leri, email digest, Samsung Health/Health Connect entegrasyonu (hâlâ Google Fit kullanılıyor).

---

## Sıradaki Hedef: Web Arayüzü → Android App (2026-07-19'da başlandı)

Kullanıcı şu anda **dashboard/frontend web sitesi** üretmek istiyor, ardından bunu bir **Android uygulaması olarak görüntülemeyi** planlıyor (muhtemelen WebView sarmalama veya benzeri bir yaklaşımla — henüz teknoloji seçimi netleşmedi).

**Neden:** Backend/modül tarafı olgunlaştı (10 modül çalışıyor), ama kullanıcıya dönük hiçbir görsel arayüz yok — şu an tek etkileşim kanalı Telegram bot ve ham API endpoint'leri (`static/index.html` var ama kapsamı sınırlı, kontrol edilmeli).

**Nasıl uygulanmalı:**

- Mevcut `api/routers/dashboard.py` ve `api/routers/context.py` endpoint'leri zaten özet/context verisi döndürüyor — web arayüzü muhtemelen bunların üzerine kurulacak.
- README/PLAN'daki eski React planı (Vercel deploy) referans alınabilir ama mimari kararları (hangi framework, hangi hosting) kullanıcıyla netleştirilmeli, PLAN.md'deki varsayımlar (Neon/Vercel) güncel değil.
- Android'e taşıma yöntemi henüz belirsiz: native WebView wrapper mı (Capacitor/Cordova tarzı), yoksa PWA mı — bu erken bir karar noktası, kullanıcıya sorulmalı.

---

## Son Commit'lerden Çıkan Bağlam (en yeniden eskiye)

1. **Rota varış formatlaması** — okunabilirlik için yeniden düzenleme, benzersiz varış listeleri, proximity ikonları (`8767368`)
2. **Rota varış çekme iyileştirmesi** — hata yönetimi, formatlama, proximity ikonları (`428b185`)
3. **Google Fit/Spotify auth URL** — query parametreleri artık `urlencode` ile kuruluyor (güvenlik/doğruluk düzeltmesi) (`c0bd155`)
4. **Deploy workflow eklendi** (`da4f385`)
5. **Transit modülleri retry logic** — ağ isteklerinde hata yönetimi ve tekrar deneme (`321b7b4`)
6. **eshot_scraper** — İzmir Transit modülü yerine ESHOT scraper'a geçildi, `hat_yon` alanı eklendi (`14be3ff`)
7. **Büyük modül eklemesi** — smoking evening reminder kaldırıldı → digest modülüne taşındı; weather'a hava kalitesi eklendi; digest, notion, spotify, transit modülleri ilk kez eklendi (`22c1b54`)

**Çıkarım:** Son dönemdeki çalışma ağırlıklı olarak **transit (İzmir otobüs) modülü** üzerine — scraping güvenilirliği, hata yönetimi/retry, ve kullanıcıya sunulan format (proximity ikonları, benzersiz varış listesi) üzerinde ilerliyor.

---

## Bilinen Tutarsızlıklar / Dikkat Edilecekler

- `README.md`'deki "Future Roadmap" tablosu **2026-07-13** tarihli ve büyük ölçüde güncelliğini yitirmiş — currency, smoking, spotify, notion, transit, digest modülleri listede yok ama kodda var. Fable 5'e geçilince bu tablo güncellenmeli veya bu dosyaya yönlendirilmeli.
- `PLAN.md` tamamen **Neon + Vercel + GitHub Actions** mimarisini varsayıyor (Mayıs 2026 planı); gerçek deploy hedefi Render.com göründüğü için PLAN.md'nin altyapı bölümleri artık referans değil, sadece tarihsel not.
- `venv/` repo kökünde duruyor — muhtemelen `.gitignore`'da ama kontrol edilmedi.

---

## Gelecek Planı (2026-07-19'da gündeme alındı)

### 1. Google Fit → yeni sağlık API'si geçişi (SON TARİH: 2026 sonu)

Health modülü Google Fit REST API kullanıyor; Google bu API'yi **2026 sonuna kadar** destekleyecek (yeni kayıtlar zaten Mayıs 2024'te kapandı). Geçilmezse health modülü 2027'de veri alamaz hale gelir.

**KARAR (2026-07-19):** Veri kaynağı Samsung Health → **Health Connect köprüsü** seçildi. Backend tarafı hazır: `POST /api/health/ingest` (`api/routers/ingest.py`, `X-Ingest-Token` header'ı + `HEALTH_INGEST_TOKEN` env ile korunuyor; gün upsert, uyku/nabız dedupe, `health_records` ham veri deposu toplu upsert).

**DURUM (2026-07-19 akşamı): Köprü CANLI ve veri akıyor** — `bridge-android/` uygulaması telefonda kurulu, `health_records`'ta 1400+ ham kayıt (Steps/Speed/Distance/Calories/HeartRate/ExerciseSession). Kalanlar:

- [x] **Uyku çözüldü** (2026-07-19) — veri vardı ama 3 günlük pencerenin dışındaydı; "Geçmişi Gönder (30 gün)" ile 210 evre kaydı geldi (son uyku 15 Temmuz — saatle uyunmayan gecelerde veri oluşmaz)
- [ ] 6 saatlik arka plan senkronunun çalıştığını teyit et (uygulamadaki "Son senkron" saati)
- [ ] Fit ile paralel dönem (birkaç hafta) → veriler tutarlıysa 2026 sonundan önce Fit schedule'ını kapat

**Değerlendirilen iki yol şuydu:**
- **Google Health API** (bulut, `developers.google.com/health`) — mevcut FastAPI backend mimarisine en yakın yol (OAuth2 + REST). Dikkat: Sleep/HRV gibi veriler "restricted scope" — app verification/güvenlik incelemesi gerektirebilir; kişisel kullanımda test-mode OAuth ile yeterli olabilir, doğrulanmalı.
- **Health Connect** (cihaz üstü, Android) — Samsung Health verisini de birleştirir (uzun süredir istenen Samsung entegrasyonunu bedavaya getirir). Ama PWA'dan erişilemez; küçük bir native Android köprü uygulaması/companion gerekir.

**İzlenecek resmi sayfalar (durum kontrolü için):**
- `https://developers.google.com/fit` — Fit deprecation duyuruları ve kapanış tarihi buradan takip edilir (ana kaynak bu)
- `https://developers.google.com/health/migration` — Health API geçiş rehberi
- `https://developer.android.com/health-and-fitness/health-connect/migration/fit` — Fit → Health Connect geçiş SSS'i

**Önerilen zamanlama:** Eylül-Ekim 2026'da geçişe başla (yıl sonu son tarihinden önce 2-3 ay tampon); o zamana kadar çeyrekte bir yukarıdaki Fit sayfasından tarih değişikliği kontrol et.

### 2. Android köprüsü için kalıcı imza ve kolay güncelleme

**Hedef:** Her yeni APK'da uygulamayı kaldırıp URL/token ve Health Connect izinlerini
yeniden kurma zorunluluğunu kaldırmak.

- [x] Gradle'ı yalnız ortam değişkenleriyle sağlanan kalıcı release anahtarını kullanacak şekilde hazırla.
- [x] `Publish Bridge APK` akışıyla sürüm kodunu otomatik artır, imzayı doğrula ve
  APK/SHA-256 dosyalarını GitHub Releases'a ekle.
- [x] Debug artifact'i `ci-only` olarak ayır; telefon dağıtımında kullanılmamasını belgele.
- [x] Keystore üretimi ve base64 hazırlığı için `prepare-signing-key.ps1` ekle.
- [ ] Kalıcı release keystore'u bir kez oluştur; özel anahtarı repoya ekleme.
- [ ] Keystore, alias ve parolaları GitHub Actions Secrets içinde sakla.
- [ ] Telefonda Obtainium ile GitHub Releases kaynağını takip et; yeni sürüm bildirimini
  ve mevcut uygulamanın üzerine kurulabilen güncellemeleri etkinleştir.
- [ ] İlk kalıcı imzalı sürüme geçerken eski debug APK'yı son kez kaldırıp yeniden kur.
  Bu geçişten sonraki güncellemelerde uygulama verileri ve izinler korunmalı.
- [ ] İleride tam otomatik güncelleme istenirse Play Store kapalı test kanalını ve
  Health Connect veri erişimi beyanlarını ayrıca değerlendir.

### 3. Diğer sıradaki işler (öncelik sırasıyla)

1. **Query/filter endpoint'leri** — "10+ toplantılı haftaları göster" tipi sorgular; PWA'ya arama sekmesi olarak eklenebilir.
2. **Yatırım modülü** — rapora göre: altın için goldprice.dev (spot çekirdek) + ayrı prim katmanı; TEFAS için tefas-crawler + cache; BIST için Yapı Kredi API Portal.
3. **Banka modülü** — ertelendi (2026-07-19, veri çekme zorluğu). Gündeme gelirse: Kobaküs sandbox (`reference.kobakus.com`).
4. **Eğlence katmanı** — digest'e NASA APOD / Wikimedia On This Day kartı (düşük maliyet, hızlı kazanım).

---

## Fable 5 İçin Öneriler

1. İlk iş olarak bu dosyayı ve `README.md`'yi karşılaştırıp roadmap tablosunu güncelle.
2. Bank/finance ve yatırım modülleri hâlâ "not started" — kullanıcı bunları öncelikli görüyorsa (bkz. bellek: [Free API Reference](../../.claude/projects/w--Workspace-Projects-GitHub-sezi/memory/reference_free_apis.md) — Nordigen banka API'si değerlendirilmiş) sıradaki büyük iş muhtemelen budur.
3. Git/commit/push işlemlerini kullanıcı kendisi yapmak istiyor — önerme, sadece hazırla (bellek: git_ownership).
