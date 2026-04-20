"""
IKEA Turkiye'den mobilya fiyatlarini ceker.
26 kategoriden ~150+ urun, her kategori 6-8 urun.
Cikti: otomatik_mobilya.json
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
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "tr-TR,tr;q=0.9",
}

# (url_slug, emoji, kategori_adi, limit)
KATEGORILER = [
    ("karyolalar",                    "🛏️",  "Karyola",             8),
    ("yatak-odasi-mobilyalari",       "🛏️",  "Yatak Odası",         8),
    ("gardiroplar",                   "🚪", "Gardırop",             6),
    ("komodinler",                    "🗄️",  "Komodin",              5),
    ("sifonyerler",                   "🗄️",  "Şifonyer",             6),
    ("makyaj-masalari",               "💄", "Makyaj Masası",        8),
    ("pax-gardiroplar",               "🚪", "PAX Gardırop",         3),
    ("hurclar",                       "📦", "Hurç",                 5),
    ("kitapliklar",                   "📚", "Kitaplık",             4),
    ("oturma-odasi-mobilyalari",      "🛋️",  "Oturma Odası",         8),
    ("koltuklar",                     "🛋️",  "Koltuk",               3),
    ("sehpalar",                      "🪑", "Sehpa",                8),
    ("tv-uniteleri",                  "📺", "TV Ünitesi",           8),
    ("masa-takimlari",                "🍽️",  "Yemek Masası",         5),
    ("calisma-masalari",              "💻", "Çalışma Masası",       8),
    ("calisma-sandalyeleri",          "💺", "Çalışma Sandalyesi",   8),
    ("sandalyeler",                   "🪑", "Sandalye",             6),
    ("aydinlatma",                    "💡", "Aydınlatma",           8),
    ("masa-lambalari",                "💡", "Masa Lambası",         3),
    ("halilar",                       "🟦", "Halı",                 8),
    ("kilimler",                      "🟨", "Kilim",                5),
    ("perdeler",                      "🪟", "Perde",                6),
    ("aynalar",                       "🪞", "Ayna",                 5),
    ("bebek-mobilyalari",             "🍼", "Bebek Mobilyası",      5),
    ("cocuk-mobilyalari",             "🧸", "Çocuk Mobilyası",      6),
    ("dis-mekan-urunleri",            "🌳", "Dış Mekan",            6),
]


def temizle(s):
    s = htmllib.unescape(s)
    # Replace HTML tags with space (not empty!) so "AD<span>aciklama</span>"
    # does not become "ADaciklama"
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


def _is_brand_token(w):
    """IKEA brand/model/olcu token'i mi?
    - Slash iceren (HEMNES/LUROY, PAX/MERAKER)
    - Sadece sayi (2025, model no)
    - Olcu (120x80, 140x200x30)
    - 2+ karakter buyuk harf (UNDVIKA, STOCKHOLM)
    Tek karakter (L, U) korunur: 'L koltuk' gibi ifadeleri bozmayalim.
    """
    if '/' in w:
        return True
    if w.isdigit():
        return True
    if re.fullmatch(r'\d+[xX]\d+(?:[xX]\d+)?', w):
        return True
    if len(w) >= 2 and not re.search(r'[a-zçşğüiöı]', w):
        return True
    return False


def basitlestir_isim(raw_isim, kategori_adi):
    """IKEA ham isim -> urun tipine odakli temiz isim.

    "UNDVIKA köşe koruyucu, beyaz"                 -> "Köşe koruyucu"
    "STOCKHOLM 2025 yan sehpa, meşe-koyu kahve"    -> "Yan sehpa"
    "HEMNES/LURÖY çift kişilik karyola, beyaz"     -> "Çift kişilik karyola"
    "PAX/MERÅKER PAX gardırop, ağartılmış meşe"    -> "Gardırop"
    "SCHOTTIS"                                     -> kategori adi
    """
    s = raw_isim.strip()
    # Virgul sonrasini at (renk / malzeme / olcu varyasyon bilgisi)
    if ',' in s:
        s = s.split(',', 1)[0].strip()
    # Bas taraftan brand/model/olcu token'larini sil
    words = s.split()
    i = 0
    while i < len(words) and _is_brand_token(words[i]):
        i += 1
    rest = ' '.join(words[i:]).strip()
    if not rest:
        # Sadece marka vardi (SCHOTTIS, LILL gibi) -> kategori ismini kullan
        return kategori_adi
    # Ilk harfi buyuk yap
    return rest[0].upper() + rest[1:]


def fiyat_parse(s):
    """'23.999' -> 23999.0  |  '4.999,50' -> 4999.50"""
    s = s.strip().replace('&nbsp;', '').replace(' ', '')
    if ',' in s:
        integer, decimal = s.rsplit(',', 1)
        integer = integer.replace('.', '')
        try:
            return float(f'{integer}.{decimal}')
        except:
            return None
    else:
        s = s.replace('.', '')
        try:
            return float(s)
        except:
            return None


# Her urun icin: href, bu href'den sonraki ilk fiyat
URUN_URL_RE = re.compile(
    r'<a[^>]+href="(https://www\.ikea\.com\.tr/urun/([^"/]+))"[^>]*target="_self"[^>]*>(.*?)</a>',
    re.DOTALL
)

# Fiyat: class="new" veya class="price" icinde sayi, ondan sonra "TL" span
FIYAT_RE = re.compile(r'class="(?:new|price)[^"]*"[^>]*>\s*([\d.,]+)\s*<span[^>]*class="tl"', re.DOTALL)

# Detay sayfasi icin: og:title ve og:image meta etiketleri
OG_TITLE_RE = re.compile(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"')
OG_IMAGE_RE = re.compile(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"')
# "- NNNNNNNN | IKEA" sonekini temizle
SONEK_RE = re.compile(r'\s*-\s*\d+\s*\|\s*IKEA\s*$')


def urun_detay(urun_url):
    """Urun sayfasindan (og:title, og:image) al.
    og:title: "SANDSBERG siyah plastik sandalye - 30605423 | IKEA"
              -> sonek temizlenir -> "SANDSBERG siyah plastik sandalye"
    og:image: yuksek cozunurluklu beyaz zeminli urun gorseli.
    """
    try:
        r = requests.get(urun_url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return None, None
        html = r.text
        tm = OG_TITLE_RE.search(html)
        im = OG_IMAGE_RE.search(html)
        baslik = None
        if tm:
            baslik = htmllib.unescape(tm.group(1)).strip()
            baslik = SONEK_RE.sub('', baslik).strip()
        gorsel = im.group(1) if im else None
        return baslik, gorsel
    except Exception:
        return None, None


def kategori_urunleri(slug, emoji, kategori_adi, limit):
    url = f"https://www.ikea.com.tr/kategori/{slug}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"  X {kategori_adi:22s} HTTP {r.status_code}")
            return []

        html = r.text
        urunler = []
        gorulen = set()

        # Her urun URL'sini tara; ardindan gelen fiyat ve resmi yakala
        for m in URUN_URL_RE.finditer(html):
            urun_url = m.group(1)
            slug_part = m.group(2)
            link_icerik = m.group(3)

            # Link icerigi: urun adi ve acıklama (span icinde)
            # Ornek: HEMNES/LURÖY<span>çift kişilik karyola, beyaz vernik</span>
            # veya: IDANÄS
            inner_text = temizle(link_icerik)
            if not inner_text:
                continue

            # Ayni urun tekrarini onle
            if slug_part in gorulen:
                continue

            # Fiyat: bu URL'den sonraki ilk 1500 karakterde fiyat ara
            sonrasi = html[m.end():m.end()+1500]
            fm = FIYAT_RE.search(sonrasi)
            if not fm:
                continue
            fiyat = fiyat_parse(fm.group(1))
            if not fiyat or fiyat < 10:
                continue

            # Detay sayfasindan tam baslik + og:image al
            # (Kategori sayfasinda bazi urunlerde acıklama gozukmuyor -
            # sadece marka gorulur. Detay sayfasi tam bilgi verir.)
            detay_baslik, detay_gorsel = urun_detay(urun_url)
            time.sleep(0.15)  # nazik ol

            # Ham isim: detay varsa oradan, yoksa kategori sayfasindaki metin
            ham_isim = detay_baslik or inner_text
            isim = basitlestir_isim(ham_isim, kategori_adi)

            # Ayni urunun farkli varyantlari cikabiliyor; ayni isim varsa atla
            isim_key = isim.lower()
            if isim_key in gorulen:
                continue
            gorulen.add(slug_part)
            gorulen.add(isim_key)

            urun = {
                "emoji": emoji,
                "isim": isim,
                "bilgi": f"IKEA · {kategori_adi}",
                "fiyat": fiyat,
                "kategori": kategori_adi,
            }
            if detay_gorsel:
                urun["gorsel"] = detay_gorsel
            urunler.append(urun)

            if len(urunler) >= limit:
                break

        print(f"  OK {kategori_adi:22s} {len(urunler)} urun")
        return urunler
    except Exception as e:
        print(f"  X {kategori_adi:22s} HATA: {e}")
        return []


def main():
    print("IKEA Turkiye'den mobilya fiyatlari cekiliyor...")
    print("-" * 60)

    tum = []
    for slug, emoji, ad, limit in KATEGORILER:
        tum.extend(kategori_urunleri(slug, emoji, ad, limit))
        time.sleep(0.3)

    tum.sort(key=lambda x: x["fiyat"])

    sonuc = {
        "guncelleme": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "kaynak": "ikea.com.tr",
        "toplam_urun": len(tum),
        "urunler": tum,
    }

    with open("otomatik_mobilya.json", "w", encoding="utf-8") as f:
        json.dump(sonuc, f, ensure_ascii=False, indent=2)

    print("-" * 60)
    print(f"OK Toplam {len(tum)} mobilya urunu kaydedildi")
    print(f"OK Dosya: otomatik_mobilya.json")


if __name__ == "__main__":
    main()
