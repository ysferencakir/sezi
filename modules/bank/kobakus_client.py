from typing import Any

import httpx

from core.config import settings

_URL = "https://app.kobakus.com/webservice/BankPaymentList.php"

# Kobaküs OAuth kullanmıyor — sabit firmCode/password/channelCode ile kimlik
# doğrulanıyor (bkz. kobakus.com/gelistiriciler). Hesap onayı (production'a geçiş)
# Kobaküs ekibiyle manuel temas gerektiriyor (~72 saat); firmCode/password/channelCode
# ayarlanana kadar bu modül boş sonuç döner.
#
# MALİYET (kobakus.com/fiyatlar, 2026-07-20): sandbox ücretsiz ama canlı AIS erişimi
# ücretli — Silver ₺3.700+KDV/ay (2.000 hesap hareketi dahil) + API erişimi ayrıca
# +₺1.500/ay = min. ~₺6.240 KDV dahil/ay, 12 ay taahhütlü. "Freemium" değil.
#
# NOT: Kobaküs'ün public dokümantasyonu "Accounts" ve "Transactions" endpoint'lerinin
# aynı BankPaymentList.php üzerinden requestMethod parametresiyle ayrıldığını gösteriyor
# ve örnek/sandbox yanıtı account listesi için doğrulandı ({"success","msg","result":
# [{"BankName","Iban","Balance","Currency"}]}). Tam parametre/response şeması API
# Reference'ta (hesap onayından sonra erişilebilir) teyit edilmeli — requestMethod
# değeri burada en olası isimle ("Accounts") varsayılmıştır.


def _configured() -> bool:
    return bool(settings.kobakus_firm_code and settings.kobakus_password and settings.kobakus_channel_code)


async def fetch_accounts() -> list[dict[str, Any]]:
    """Bağlı bankalardaki hesap listesini (IBAN + bakiye) döner."""
    if not _configured():
        return []

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _URL,
            data={
                "firmCode": settings.kobakus_firm_code,
                "password": settings.kobakus_password,
                "channelCode": settings.kobakus_channel_code,
                "requestMethod": "Accounts",
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        body = resp.json()

    if not body.get("success"):
        return []
    return body.get("result", [])
