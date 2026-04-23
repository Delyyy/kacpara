"""
Vatan Bilgisayar'dan elektronik urun fiyatlarini ceker. (Scrapling refactor)
18 kategoriden 100+ urun.
Cikti: otomatik_elektronik.json

Cari HTTP: Scrapling Fetcher (TLS impersonation).
Cari parse: CSS selectors (regex yerine).
"""
import json
import sys
import re
import time
import random
import html as htmllib
from datetime import datetime

from scrapling.fetchers import Fetcher

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# (url_slug, emoji, kategori_isim, kac_urun_alinacak)
KATEGORILER = [
    ("notebook",           "💻", "Laptop",              14),
    ("televizyon",         "📺", "Televizyon",          14),
    ("tabletler",          "📱", "Tablet",              10),
    ("fotograf-makinesi",  "📷", "Fotoğraf Makinesi",   10),
    ("akilli-saatler",     "⌚", "Akıllı Saat",         10),
    ("bluetooth-hoparlor", "🔊", "Bluetooth Hoparlör",   8),
    ("yazici",             "🖨️", "Yazıcı",               8),
    ("klavye",             "⌨️", "Klavye",               8),
    ("hoparlor",           "🔈", "Hoparlör",             8),
    ("ekran-kartlari",     "🎮", "Ekran Kartı",          8),
    ("islemciler",         "🧠", "İşlemci",              8),
    ("anakart",            "🔌", "Anakart",              6),
    ("gaming-mouse",       "🖱️", "Gaming Mouse",         8),
    ("router",             "📡", "Router",               6),
    ("mikrofon",           "🎤", "Mikrofon",             8),
    ("kulakici-kulaklik",  "🎧", "Kulaklık",            10),
    ("drone",              "🚁", "Drone",                6),
    ("oyun-konsollari",    "🕹️", "Oyun Konsolu",         6),
]


def temizle_isim(s):
    """HTML entity ve fazla bosluklari temizle."""
    s = htmllib.unescape(s or "").strip()
    s = re.sub(r'\s+', ' ', s)
    return s


def fiyat_parse(s):
    """'15.999' -> 15999.0  |  '15.999,50' -> 15999.50"""
    if not s:
        return None
    s = s.strip()
    if ',' in s:
        integer, decimal = s.rsplit(',', 1)
        integer = integer.replace('.', '').replace(' ', '')
        try:
            return float(f'{integer}.{decimal}')
        except Exception:
            return None
    else:
        s = s.replace('.', '').replace(' ', '')
        try:
            return float(s)
        except Exception:
            return None


def kategori_urunleri(slug, emoji, kategori_adi, limit):
    """Kategori sayfasindan urun kartlarini CSS selector ile al."""
    url = f"https://www.vatanbilgisayar.com/{slug}/"
    try:
        page = Fetcher.get(url, impersonate="chrome", timeout=15)
        if page.status != 200:
            print(f"  X {kategori_adi:20s} HTTP {page.status}")
            return []

        urunler = []
        gorulen = set()

        # Vatan'da her urun karti .product-list-link ile sarili
        # (hem .product-list--fourth grid'i hem .product-list--list-page listesi icin calisir)
        for card in page.css('.product-list-link'):
            isim = temizle_isim(card.css('.product-list__product-name h3::text').get())
            if not isim or isim in gorulen:
                continue

            fiyat_str = card.css('.product-list__price::text').get()
            fiyat = fiyat_parse(fiyat_str)
            if not fiyat or fiyat < 50:
                continue

            # Lazy-load: data-src gercek gorseli tutuyor (src = placeholder)
            gorsel = card.css('img::attr(data-src)').get()

            gorulen.add(isim)
            urun = {
                "emoji": emoji,
                "isim": isim,
                "bilgi": f"Vatan Bilgisayar · {kategori_adi}",
                "fiyat": fiyat,
                "kategori": kategori_adi,
            }
            if gorsel:
                urun["gorsel"] = gorsel
            urunler.append(urun)

            if len(urunler) >= limit:
                break

        print(f"  OK {kategori_adi:20s} {len(urunler)} urun")
        return urunler
    except Exception as e:
        print(f"  X {kategori_adi:20s} HATA: {e}")
        return []


def main():
    print("Vatan Bilgisayar'dan elektronik fiyatlari cekiliyor (Scrapling)...")
    print("-" * 60)

    tum_urunler = []
    for slug, emoji, ad, limit in KATEGORILER:
        urunler = kategori_urunleri(slug, emoji, ad, limit)
        tum_urunler.extend(urunler)
        time.sleep(random.uniform(0.25, 0.45))  # nazik ol, jitter ile

    tum_urunler.sort(key=lambda x: x["fiyat"])

    sonuc = {
        "guncelleme": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "kaynak": "vatanbilgisayar.com",
        "toplam_urun": len(tum_urunler),
        "urunler": tum_urunler,
    }

    with open("otomatik_elektronik.json", "w", encoding="utf-8") as f:
        json.dump(sonuc, f, ensure_ascii=False, indent=2)

    print("-" * 60)
    print(f"OK Toplam {len(tum_urunler)} elektronik urunu kaydedildi")
    print(f"OK Dosya: otomatik_elektronik.json")


if __name__ == "__main__":
    main()
