param(
    [string]$Alias = "sezi-release",
    [string]$OutputDirectory = (Join-Path $HOME "sezi-signing")
)

$ErrorActionPreference = "Stop"

$keytool = Get-Command keytool -ErrorAction SilentlyContinue
if (-not $keytool -and $env:JAVA_HOME) {
    $candidate = Join-Path $env:JAVA_HOME "bin\keytool.exe"
    if (Test-Path -LiteralPath $candidate) {
        $keytool = Get-Item -LiteralPath $candidate
    }
}
if (-not $keytool) {
    throw "keytool bulunamadı. Önce JDK 17 kur veya JAVA_HOME değişkenini ayarla."
}

New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$keystorePath = Join-Path $OutputDirectory "sezi-release.jks"
if (Test-Path -LiteralPath $keystorePath) {
    throw "Dosya zaten var: $keystorePath. Mevcut kalıcı anahtarı silmek yerine yedekle ve kullan."
}

Write-Host "Kalıcı Sezi release anahtarı oluşturuluyor."
Write-Host "Sorulan parolaları güvenli bir parola yöneticisine kaydet; kaybolursa uygulama aynı imzayla güncellenemez."
& $keytool.Source `
    -genkeypair `
    -v `
    -keystore $keystorePath `
    -alias $Alias `
    -keyalg RSA `
    -keysize 4096 `
    -validity 10000

if ($LASTEXITCODE -ne 0) {
    throw "keytool anahtar oluşturamadı."
}

$base64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($keystorePath))
Set-Clipboard -Value $base64

Write-Host ""
Write-Host "Anahtar oluşturuldu: $keystorePath"
Write-Host "Base64 değeri panoya kopyalandı."
Write-Host ""
Write-Host "GitHub > Settings > Secrets and variables > Actions altında şunları ekle:"
Write-Host "  ANDROID_KEYSTORE_BASE64  (panodaki değer)"
Write-Host "  ANDROID_KEYSTORE_PASSWORD"
Write-Host "  ANDROID_KEY_ALIAS        ($Alias)"
Write-Host "  ANDROID_KEY_PASSWORD"
Write-Host ""
Write-Host "JKS dosyasını ve parolaları ayrıca güvenli, çevrimdışı bir yerde yedekle."
