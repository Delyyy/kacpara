"""
Vatan Bilgisayar'dan elektronik urun fiyatlarini ceker.
100+ urun, her kategori icin ~25-34 urun.
Cikti: otomatik_elektronik.json
"""
import requests
import json
import sys
import re
import time
import html as htmllib
from datetime import datetime

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}

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

# HTML'den urunleri ayikla: product-list--fourth bloklari
URUN_REGEX = re.compile(
    r'<div class="product-list product-list--fourth">.*?'
    r'<img[^>]+data-src="([^"]+)"[^>]+title="([^"]*)".*?'
    r'<h3>(.*?)</h3>.*?'
    r'<span class="product-list__price">(.*?)</span>',
    re.DOTALL
)

# Daha esnek fallback (sadece isim + fiyat)
URUN_REGEX_BASIT = re.compile(
    r'<div class="product-list__product-name">\s*<h3>(.*?)</h3>.*?'
    r'<span class="product-list__price">(.*?)</span>',
    re.DOTALL
)


def temizle_isim(s):
    """HTML entity ve fazla bosluklari temizle"""
    s = htmllib.unescape(s).strip()
    s = re.sub(r'\s+', ' ', s)
    return s


def fiyat_parse(s):
    """'15.999' -> 15999.0  |  '15.999,50' -> 15999.50"""
    s = s.strip()
    # Turk formati: nokta binlik, virgul ondalik
    if ',' in s:
        # virgul ondalik
        integer, decimal = s.rsplit(',', 1)
        integer = integer.replace('.', '').replace(' ', '')
        try:
            return float(f'{integer}.{decimal}')
        except:
            return None
    else:
        s = s.replace('.', '').replace(' ', '')
        try:
            return float(s)
        except:
            return None


def kategori_urunleri(slug, emoji, kategori_adi, limit):
    """Bir kategori sayfasindan urun listesi cek.
    Basit regex (isim + fiyat) kullanir, gorsel url'si de opsiyonel bulunur."""
    url = f"https://www.vatanbilgisayar.com/{slug}/"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"  X {kategori_adi:20s} HTTP {r.status_code}")
            return []

        html = r.text
        urunler = []
        gorulen = set()

        # Her urunun isim bloguna yakin fiyat ve resim bul
        # Strateji: her h3 name'i bul, ondan sonraki ilk price'i ve oncesindeki ilk img'yi al
        name_iter = list(re.finditer(
            r'<div class="product-list__product-name">\s*<h3>(.*?)</h3>',
            html, re.DOTALL
        ))

        for nm in name_iter:
            isim = temizle_isim(nm.group(1))
            if not isim or isim in gorulen:
                continue

            # Bu isimden sonraki ilk fiyat
            sonrasi = html[nm.end():nm.end()+2000]
            fm = re.search(r'<span class="product-list__price">([^<]+)</span>', sonrasi)
            if not fm:
                continue
            fiyat = fiyat_parse(fm.group(1))
            if not fiyat or fiyat < 50:
                continue

            # Bu ismin ONCESI'ndeki (son 2000 karakterde) img data-src
            oncesi = html[max(0, nm.start()-2000):nm.start()]
            im = None
            for m in re.finditer(r'data-src="(https?://[^"]+\.jpg[^"]*)"', oncesi):
                im = m.group(1)
            # im = en sonuncu = en yakin = bu urunun resmi

            gorulen.add(isim)
            urun = {
                "emoji": emoji,
                "isim": isim,
                "bilgi": f"Vatan Bilgisayar · {kategori_adi}",
                "fiyat": fiyat,
                "kategori": kategori_adi,
            }
            if im:
                urun["gorsel"] = im
            urunler.append(urun)
            if len(urunler) >= limit:
                break

        print(f"  OK {kategori_adi:20s} {len(urunler)} urun")
        return urunler
    except Exception as e:
        print(f"  X {kategori_adi:20s} HATA: {e}")
        return []


def main():
    print("Vatan Bilgisayar'dan elektronik fiyatlari cekiliyor...")
    print("-" * 60)

    tum_urunler = []
    for slug, emoji, ad, limit in KATEGORILER:
        urunler = kategori_urunleri(slug, emoji, ad, limit)
        tum_urunler.extend(urunler)
        time.sleep(0.3)  # nazik ol, rate-limit olma

    # Fiyatlara gore sirala (oyun icin gorsel dengeli dagilim)
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
