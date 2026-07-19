# Sezi Bridge (Android)

Samsung Health → Health Connect → Sezi köprüsü. Telefondaki Health Connect deposundan
kararlı 1.1.0 istemcisinin desteklediği tüm aktivite, vücut ölçümü, beslenme, uyku,
yaşamsal bulgu ve döngü takibi kayıtlarını okur; 6 saatte bir
`POST /api/health/ingest`'e gönderir. Google Fit REST API'nin 2026 sonunda kapanmasına
karşı geçiş yolu (bkz. kök dizindeki `HANDOFF.md` → Gelecek Planı).

## Dağıtım — imzalı GitHub Release (önerilen)

Kalıcı imza Secrets kurulumu bir kez tamamlandıktan sonra `main` dalındaki her Android
kod değişikliği:

1. Aynı release anahtarıyla imzalanmış yeni bir APK üretir.
2. Sürüm kodunu otomatik artırır.
3. APK ve SHA-256 dosyasını yeni bir
   [GitHub Release](https://github.com/ysferencakir/sezi/releases) olarak yayınlar.
4. Obtainium'un telefonda yeni sürümü bulmasını sağlar.

### Tek seferlik imza kurulumu

JDK 17 kurulu bir Windows bilgisayarda repo kökünden:

```powershell
.\bridge-android\scripts\prepare-signing-key.ps1
```

Komut kalıcı `sezi-release.jks` dosyasını kullanıcı dizininin altındaki
`sezi-signing` klasöründe oluşturur ve base64 değerini panoya kopyalar. GitHub
**Settings → Secrets and variables → Actions** bölümüne şu repository secret'ları ekle:

- `ANDROID_KEYSTORE_BASE64`
- `ANDROID_KEYSTORE_PASSWORD`
- `ANDROID_KEY_ALIAS`
- `ANDROID_KEY_PASSWORD`

JKS dosyasını ve parolaları güvenli, çevrimdışı ikinci bir yerde yedekle. Bu anahtar
kaybolursa mevcut kurulumların üzerine imzalı güncelleme yayınlanamaz.

İlk kalıcı imzalı release APK'sına geçerken eski debug APK son kez kaldırılmalıdır.
Bu ilk geçişten sonra URL, token ve izinler sonraki güncellemelerde korunur.

### Obtainium

Obtainium'da **Add App** seçeneğine şu adresi ver:

`https://github.com/ysferencakir/sezi`

Kaynak olarak GitHub Releases'ı ve APK filtresi olarak `sezi-bridge-*.apk` desenini
seç. Bundan sonraki sürümler uygulamayı kaldırmadan mevcut kurulumun üzerine yüklenir;
Android yalnız güncelleme kurulumu için onay isteyebilir.

## CI doğrulaması — debug artifact

`bridge-android/` altında bir değişiklik push'landığında **Build Bridge APK** akışı
ayrıca kodun derlendiğini doğrular. Buradaki `sezi-bridge-debug-ci-only` artifact'i
geçici debug anahtarı taşır ve telefona kalıcı kurulum için kullanılmamalıdır.

Telefona kurulacak dosya her zaman GitHub **Releases** sayfasındaki
`sezi-bridge-v*.apk` dosyasıdır.

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
  (`awake/light/deep/rem`, backend'in beklediği adlarla) + nabız örnekleri (~300'e
  seyreltilmiş) ve desteklenen tüm kayıt türlerinin kayıpsız JSON alanları.
- `SyncWorker` — WorkManager periyodik iş (6 saat, yalnız ağ varken; hata → otomatik retry).
- `ApiClient` — OkHttp, `X-Ingest-Token` başlığıyla POST.
- Backend günlük özetleri ve ham kayıtları upsert, uyku/nabız verisini dedupe ettiği
  için aynı verinin tekrar gönderilmesi zararsızdır;
  Google Fit senkronuyla paralel çalışabilir (bkz. `api/routers/ingest.py`).

## Güncelleme dağıtımı

- Release keystore yalnız GitHub Secrets ve kullanıcının güvenli yedeğinde tutulur.
- `Publish Bridge APK` aynı imzayla release APK üretip GitHub Releases'a yükler.
- Obtainium yeni sürümleri takip eder; ilk imza geçişinden sonra APK kaldırılmadan
  güncellenir ve uygulama ayarları korunur.
