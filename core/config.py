from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/sezi"
    ntfy_url: str = "https://ntfy.sh"
    ntfy_topic: str = ""
    ntfy_token: str = ""  # boş bırakılırsa auth olmadan gönderir
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    # Google OAuth2
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"
    # Spotify OAuth2
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = "http://localhost:8000/auth/spotify/callback"
    # Notion (internal integration token — OAuth değil)
    notion_token: str = ""
    notion_database_id: str = ""
    # ScraperAPI (scraperapi.com) — eshot.gov.tr Render'ın datacenter IP'sini
    # engelliyor, bu yüzden eshot_scraper.py istekleri Türkiye IP'si üzerinden
    # proxy'leniyor. Boş bırakılırsa proxy kullanılmadan direkt istek atılır
    # (local geliştirmede genelde gerekmez, prod'da/Render'da gerekli).
    scraperapi_key: str = ""
    # Health Connect köprü uygulamasının POST /api/health/ingest için kullandığı
    # paylaşımlı sır. Boş bırakılırsa ingest endpoint'i kapalıdır (503 döner).
    health_ingest_token: str = ""
    # Modül tetikleme (/modules/{name}/run, /trigger) ve context yazma (POST /api/context)
    # uçları için paylaşımlı sır. Boş bırakılırsa bu uçlar kapalıdır (503 döner).
    admin_token: str = ""

    # altinapi.com (Harem Altın verisi) — gram + sarrafiye (çeyrek/yarım/tam/ata) fiyatları
    altinapi_key: str = ""

    # Yahoo Finance (query1.finance.yahoo.com) — auth gerekmez. BIST sembolleri ".IS"
    # suffix'iyle (ör. ISCTR.IS, XU100.IS), virgülle ayrılmış izleme listesi.
    stocks_watchlist: str = "XU100.IS"

    # TEFAS (tefas.gov.tr) — auth gerekmez. Fon kodları, virgülle ayrılmış izleme listesi.
    tefas_watchlist: str = ""

    # Kobaküs Open Banking (kobakus.com) — OAuth değil, sabit kimlik bilgileriyle
    # çalışır. Hesap onayı Kobaküs ekibiyle manuel temas gerektirir (~72 saat).
    kobakus_firm_code: str = ""
    kobakus_password: str = ""
    kobakus_channel_code: str = ""

    # Strava OAuth2 (developer.strava.com → uygulama oluştur; 2026 itibarıyla
    # uygulama oluşturmak için Strava aboneliği gerekiyor)
    strava_client_id: str = ""
    strava_client_secret: str = ""
    strava_redirect_uri: str = "http://localhost:8000/auth/strava/callback"

    # TMDB (themoviedb.org → hesap ayarlarından ücretsiz API key al) — Telegram'a
    # yazılan dizi/film adlarını zenginleştirmek (poster, özet, çıkış tarihi) için.
    tmdb_api_key: str = ""

    # TCMB EVDS (evds2.tcmb.gov.tr) — ücretsiz self-serve kayıt, API key header'da.
    evds_api_key: str = ""

    # camgoz.net Barkod API (JoJ API Marketplace üzerinden) — bireysel kullanım
    # ücretsiz. camgoz.net'e doğrudan istek 400 ile reddediliyor ("Access to this
    # API is restricted to the JOJ API platform only"); jojapi.com/api/product-barcode-api
    # üzerinden key alınınca dashboard'da atanan gerçek gateway base URL'i buraya girilmeli.
    camgoz_api_base: str = "https://camgoz.net"
    camgoz_api_key: str = ""

    # EPİAŞ Şeffaflık Platformu — TGT (CAS ticket) tabanlı kimlik doğrulama,
    # kullanıcı adı/şifre ile hesap oluşturulur (seffaflik.epias.com.tr).
    # Elektrik kesintisi sorgusu için dağıtım şirketi/il kodu gerekir.
    epias_username: str = ""
    epias_password: str = ""
    epias_city_id: str = ""

    # Etkinlik.io RSS — auth gerekmez. Etkinlik başlığı/açıklamasında aranacak
    # şehir anahtar kelimesi (ör. "İzmir"), boşsa filtrelenmeden tüm akış alınır.
    etkinlik_city: str = ""

    app_env: str = "development"
    log_level: str = "INFO"

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"


settings = Settings()
