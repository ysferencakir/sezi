from fastapi import APIRouter, HTTPException
from loguru import logger

from modules.barcode import camgoz_client

router = APIRouter(prefix="/api/barcode", tags=["barcode"])


@router.get("/{code}")
async def lookup_barcode(code: str):
    """Barkod numarasına göre ürün adı/fiyat/market bilgisini döner (camgoz.net)."""
    try:
        result = await camgoz_client.lookup(code)
    except Exception as exc:
        logger.error(f"[barcode] lookup failed for {code}: {exc}")
        raise HTTPException(status_code=502, detail="Barkod servisine ulaşılamadı")

    if result is None:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    return result
