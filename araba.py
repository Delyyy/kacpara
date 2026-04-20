"""
Arabam.com'dan sifir km araba fiyatlarini ceker.
~25 markanin seri/model kirilimi, minPrice (baslangic fiyati) kullanilir.
Cikti: otomatik_araba.json
"""
import requests
import json
import sys
import re
import time
import html as htmllib
from datetime import datetime

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "tr-TR,tr;q=0.9",
}

# Arabam.com sifir-km sayfasindaki markalar
BRANDS = [
    "renault", "fiat", "hyundai", "volkswagen", "toyota", "peugeot",
    "skoda", "honda", "bmw", "ford", "mercedes-benz", "opel", "kia",
    "audi", "chery", "citroen", "dacia", "nissan", "seat", "volvo",
    "cupra", "suzuki", "togg", "tesla", "jeep",
]

# subName -> emoji eslemesi (Arabam.com kategori etiketleri)
SUBNAME_EMOJI = {
    "SUV/Arazi":   "🚙",
    "Sedan":       "🚗",
    "Hatchback":   "🚗",
    "Station":     "🚙",
    "Stationwagon":"🚙",
    "Coupe":       "🏎️",
    "Cabrio":      "🏎️",
    "Ticari":      "🚐",
    "Pickup":      "🛻",
    "Kamyonet":    "🛻",
    "Panelvan":    "🚐",
    "MPV":         "🚐",
}
DEFAULT_EMOJI = "🚗"

# JSON blob icinde her seri kaydi icin regex
# "listPhotoUrl":"...","name":"Renault Clio","subName":"Hatchback",...,"minPrice":1695000,"maxPrice":1996000
URUN_RE = re.compile(
    r'"listPhotoUrl":"([^"]+)",'
    r'"name":"([^"]+)",'
    r'"subName":"([^"]+)",'
    r'"brand":"[^"]+"[^{}]*?'
    r'"modelCount":(\d+),'
    r'"minPrice":(\d+),'
    r'"maxPrice":(\d+)'
)

PHOTO_SIZE = "393x226"


def marka_modelleri(brand):
    """Bir markanin tum model/seri listesini donder."""
    url = f"https://www.arabam.com/sifir-km/{brand}-fiyat-listesi"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"  X {brand:15s} HTTP {r.status_code}")
            return []
        html = r.text

        urunler = []
        gorulen = set()
        for m in URUN_RE.finditer(html):
            photo_tmpl = m.group(1)
            isim = htmllib.unescape(m.group(2)).strip()
            subname = htmllib.unescape(m.group(3)).strip()
            model_count = int(m.group(4))
            min_price = int(m.group(5))
            max_price = int(m.group(6))

            if isim in gorulen:
                continue
            gorulen.add(isim)

            # Fiyat: baslangic (min) fiyati - en yaygin bilinen fiyat.
            fiyat = min_price
            if fiyat < 100000:  # saglama
                continue

            # Fotograf URL'sinde {0} sablonu var
            gorsel = photo_tmpl.replace("{0}", PHOTO_SIZE)

            emoji = SUBNAME_EMOJI.get(subname, DEFAULT_EMOJI)

            # bilgi: "Sifir km · SUV/Arazi · 4 versiyon"
            bilgi_parcalari = ["Sıfır km", subname]
            if model_count > 1:
                bilgi_parcalari.append(f"{model_count} versiyon")
            bilgi = " · ".join(bilgi_parcalari)

            urunler.append({
                "emoji": emoji,
                "isim": isim,
                "bilgi": bilgi,
                "fiyat": float(fiyat),
                "kategori": "Araba",
                "gorsel": gorsel,
            })

        print(f"  OK {brand:15s} {len(urunler):2d} model")
        return urunler
    except Exception as e:
        print(f"  X {brand:15s} HATA: {e}")
        return []


def main():
    print("Arabam.com'dan sifir km araba fiyatlari cekiliyor...")
    print("-" * 60)

    tum = []
    for brand in BRANDS:
        tum.extend(marka_modelleri(brand))
        time.sleep(0.25)

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
