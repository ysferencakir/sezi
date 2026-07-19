# Sezi Bridge (Android)

Samsung Health → Health Connect → Sezi köprüsü. Telefondaki Health Connect deposundan
adım/mesafe/kalori/egzersiz süresi, uyku evreleri ve nabız verisini okur; 6 saatte bir
`POST /api/health/ingest`'e gönderir. Google Fit REST API'nin 2026 sonunda kapanmasına
karşı geçiş yolu (bkz. kök dizindeki `HANDOFF.md` → Gelecek Planı).

## Derleme — Yol 1: GitHub Actions (önerilen, lokal kurulum gerekmez)

`bridge-android/` altında bir değişiklik push'landığında (veya Actions sekmesinden
**Build Bridge APK → Run workflow** ile elle) APK bulutta derlenir:

1. GitHub → repo → **Actions** → "Build Bridge APK" çalışmasının sayfası
2. Sayfanın altındaki **Artifacts** bölümünden `sezi-bridge-apk` dosyasını indir
   (telefonun tarayıcısından da indirilebilir — GitHub'a giriş gerekir; zip içinden `app-debug.apk` çıkar)

## Derleme — Yol 2: Android Studio (lokal)

1. Android Studio'yu aç → **Open** → bu `bridge-android/` klasörünü seç (repo kökünü değil).
2. Gradle sync bitince: **Build → Build App Bundle(s) / APK(s) → Build APK(s)**.
3. APK çıktısı: `app/build/outputs/apk/debug/app-debug.apk` (release da olur, debug imzalı).

Not: `androidx.health.connect:connect-client` sürümü çözülmezse
[sürüm sayfasından](https://developer.android.com/jetpack/androidx/releases/health-connect)
günceline yükselt (`app/build.gradle.kts`).

## Telefona kurulum

1. APK'yı telefona at (USB, Drive, Telegram Saved Messages…) ve aç — "bilinmeyen kaynak"
   iznini onayla (Play Store yok, bilinçli tercih).
2. Uygulamayı aç:
   - **Sunucu adresi**: `https://sezi.ysferencakir.info.tr` (varsayılan dolu gelir)
   - **Ingest token**: VPS'teki `/opt/sezi/.env` içindeki `HEALTH_INGEST_TOKEN` değeri
     (lokal repo `.env`'inde de aynı değer var)
   - **Kaydet ve 6 saatlik senkronu kur**
3. **Health Connect İzni İste** → açılan ekranda tüm okuma izinlerini ver.
4. **Şimdi Gönder** ile ilk senkronu test et — "Gönderildi ✓" ve sunucu özeti görünmeli.
5. Doğrulama: `https://sezi.ysferencakir.info.tr` → Trendler sekmesinde veriler akmalı.

## Ön koşullar

- Android 9+ (Android 14+'ta Health Connect sistemde gömülü; öncesinde Play Store'dan kurulur)
- Samsung Health → Ayarlar → Health Connect bağlantısı açık (veri oraya yazılıyor olmalı)

## Mimari notlar

- `HealthReader` — Health Connect aggregate API'siyle gün bazlı özet + uyku evreleri
  (`awake/light/deep/rem`, backend'in beklediği adlarla) + nabız örnekleri (~300'e seyreltilmiş).
- `SyncWorker` — WorkManager periyodik iş (6 saat, yalnız ağ varken; hata → otomatik retry).
- `ApiClient` — OkHttp, `X-Ingest-Token` başlığıyla POST.
- Backend upsert + dedupe yaptığı için aynı verinin tekrar gönderilmesi zararsızdır;
  Google Fit senkronuyla paralel çalışabilir (bkz. `api/routers/ingest.py`).
