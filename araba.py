"""
Arabam.com'dan sifir km araba fiyatlarini ceker. (Scrapling refactor)
~25 markanin model listesi, JSON-LD (schema.org/Car) uzerinden.
Cikti: otomatik_araba.json

Cari HTTP: Scrapling Fetcher (TLS impersonation).
Cari parse: JSON-LD script tag'i (regex yerine).
"""
import json
import sys
import time
import random
from datetime import datetime

from scrapling.fetchers import Fetcher

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# Arabam.com sifir-km sayfasindaki markalar
BRANDS = [
    "renault", "fiat", "hyundai", "volkswagen", "toyota", "peugeot",
    "skoda", "honda", "bmw", "ford", "mercedes-benz", "opel", "kia",
    "audi", "chery", "citroen", "dacia", "nissan", "seat", "volvo",
    "cupra", "suzuki", "togg", "tesla", "jeep",
]

# bodyType -> emoji eslemesi (JSON-LD kategori etiketleri)
BODY_EMOJI = {
    "SUV/Arazi":    "🚙",
    "Sedan":        "🚗",
    "Hatchback":    "🚗",
    "Station":      "🚙",
    "Stationwagon": "🚙",
    "Coupe":        "🏎️",
    "Cabrio":       "🏎️",
    "Ticari":       "🚐",
    "Pickup":       "🛻",
    "Kamyonet":     "🛻",
    "Panelvan":     "🚐",
    "MPV":          "🚐",
}
DEFAULT_EMOJI = "🚗"


def marka_modelleri(brand):
    """Bir markanin tum model listesini JSON-LD'den donder."""
    url = f"https://www.arabam.com/sifir-km/{brand}-fiyat-listesi"
    try:
        page = Fetcher.get(url, impersonate="chrome", timeout=15)
        if page.status != 200:
            print(f"  X {brand:15s} HTTP {page.status}")
            return []

        ld_txt = page.css('script[type="application/ld+json"]::text').get()
        if not ld_txt:
            print(f"  X {brand:15s} JSON-LD yok")
            return []

        try:
            ld = json.loads(ld_txt)
        except json.JSONDecodeError as e:
            print(f"  X {brand:15s} JSON parse: {e}")
            return []

        if not isinstance(ld, list):
            ld = [ld]

        urunler = []
        gorulen = set()
        for item in ld:
            if not isinstance(item, dict) or item.get("@type") != "Car":
                continue

            isim = (item.get("name") or "").strip()
            if not isim or isim in gorulen:
                continue

            offers = item.get("offers") or {}
            try:
                fiyat = float(offers.get("price") or 0)
            except (TypeError, ValueError):
                continue
            if fiyat < 100000:  # saglama
                continue

            gorsel = item.get("image") or ""
            body = (item.get("bodyType") or "").strip()
            emoji = BODY_EMOJI.get(body, DEFAULT_EMOJI)

            bilgi_parcalari = ["Sıfır km"]
            if body:
                bilgi_parcalari.append(body)
            bilgi = " · ".join(bilgi_parcalari)

            gorulen.add(isim)
            urunler.append({
                "emoji": emoji,
                "isim": isim,
                "bilgi": bilgi,
                "fiyat": fiyat,
                "kategori": "Araba",
                "gorsel": gorsel,
            })

        print(f"  OK {brand:15s} {len(urunler):2d} model")
        return urunler
    except Exception as e:
        print(f"  X {brand:15s} HATA: {e}")
        return []


def main():
    print("Arabam.com'dan sifir km araba fiyatlari cekiliyor (Scrapling)...")
    print("-" * 60)

    tum = []
    for brand in BRANDS:
        tum.extend(marka_modelleri(brand))
        time.sleep(random.uniform(0.2, 0.4))

    tum.sort(key=lambda x: x["fiyat"])

    sonuc = {
        "guncelleme": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "kaynak": "arabam.com/sifir-km",
        "not": "Fiyatlar baslangic (min) versiyon fiyatidir",
        "toplam_urun": len(tum),
        "urunler": tum,
    }

    with open("otomatik_araba.json", "w", encoding="utf-8") as f:
        json.dump(sonuc, f, ensure_ascii=False, indent=2)

    print("-" * 60)
    print(f"OK Toplam {len(tum)} araba modeli kaydedildi")
    print(f"OK Dosya: otomatik_araba.json")


if __name__ == "__main__":
    main()
