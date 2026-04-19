"""
Her urun icin Pixabay API'den net, arka plani temiz urun fotografi ceker
ve resimler.json dosyasina kaydeder.

Pixabay: bedava, saatte 5000 istek, stok fotograf kalitesi.
Fiyat etiketi yok, urunun dogru gorseli.
"""
import requests
import json
import sys
import time
import os

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# API key: ortam degiskeni yoksa hardcoded'dan al
PIXABAY_KEY = os.environ.get("PIXABAY_KEY", "55511269-034a8b0f4a3983450465f76da")
API = "https://pixabay.com/api/"

# Her urun: (anahtar, arama_terimi_Ingilizce)
# Pixabay Ingilizce'de cok iyi calisiyor
URUNLER = {
    # Doviz & Altin
    "USD":                  "dollar banknote",
    "EUR":                  "euro banknote",
    "GBP":                  "pound sterling banknote",
    "CHF":                  "swiss franc banknote",
    "SAR":                  "saudi riyal currency",
    "GRA":                  "gold bar bullion",
    "HAS":                  "gold bar bullion fine",
    "CEYREKALTIN":          "gold coin shiny",
    "YARIMALTIN":           "gold coin",
    "TAMALTIN":             "gold coin stack",
    "CUMHURIYETALTINI":     "gold coin antique",
    "GUMUS":                "silver bar bullion",

    # Market - Sebze/Meyve
    "1 kg domates":         "fresh tomatoes red",
    "1 kg salatalık":       "fresh cucumber green",
    "1 kg patlıcan":        "eggplant purple",
    "1 kg sivri biber":     "green chili pepper",
    "1 kg muz":             "banana yellow fresh",
    "1 kg elma":            "red apple fresh",
    "1 kg limon":           "lemon yellow citrus",
    "1 kg soğan":           "onion white",
    "1 kg karpuz":          "watermelon red",

    # Market - Temel gida
    "Baldo pirinç 1 kg":    "rice white grain",
    "Un 1 kg":              "flour white wheat",
    "Bulgur 1 kg":          "bulgur wheat grain",
    "Toz şeker 1 kg":       "white sugar granulated",
    "Zeytinyağı 1 L":       "olive oil bottle",
    "Barilla makarna 500 gr": "barilla pasta",

    # Market - Sut urunleri
    "Pınar süt 1 L":        "milk carton fresh",
    "SEK süt 1 L":          "milk carton white",
    "30'lu yumurta":        "eggs carton fresh",
    "Beyaz peynir 400 gr":  "feta cheese white block",
    "Kaşar peyniri 500 gr": "yellow cheese block",
    "Tereyağı 250 gr":      "butter block yellow",
    "Yoğurt 1 kg":          "yogurt white cup",
    "Ayran 1 L":            "ayran white drink glass",

    # Market - Icecek/Atistirmalik
    "Coca-Cola 1 L":        "coca cola bottle",
    "Red Bull 250 ml":      "red bull energy drink can",
    "Çaykur Rize çay 1 kg": "black tea loose leaf",
    "Nescafe Gold 100 gr":  "nescafe gold coffee jar",
    "Milka çikolata 100 gr": "milka chocolate bar",

    # Market - Temizlik
    "Ariel toz deterjan":   "ariel detergent powder box",
    "Fairy bulaşık tableti": "dishwasher tablets pack",
    "Elidor şampuan 400 ml": "shampoo bottle",

    # Sabit liste
    "Bir somun ekmek":      "bread loaf fresh white",
    "Eti Crax 100 gr":      "crackers snack pack",
    "Starbucks latte (grande)": "starbucks latte coffee cup",
    "Efes Pilsen 50 cl":    "beer can cold",
    "1 L benzin":           "gasoline pump fuel",
    "Domino's orta pizza":  "pizza whole cheese",
    "Tavuk döner dürüm":    "doner kebab wrap",
    "Marlboro Red paket":   "cigarette pack red",
    "iPhone 16 Pro 256 GB": "iphone pro smartphone",
    "MacBook Air M4 13\"":  "macbook air laptop",
    "AirPods 4":            "airpods white earbuds",
}


def resim_bul(arama):
    """Pixabay'den urun fotografina en uygun gorsel.
    10 sonuc ceker, kare/dikey oranli (lifestyle degil, urun odakli) gorsel tercih eder.
    Cok genis panoramik fotolar (ratio>1.8) lifestyle sahne olur, onlari atlar.
    """
    try:
        params = {
            "key": PIXABAY_KEY,
            "q": arama,
            "image_type": "photo",
            "per_page": 10,
            "safesearch": "true",
            "order": "popular",
            "min_width": 400,
            "min_height": 400,
        }
        r = requests.get(API, params=params, timeout=15)
        if r.status_code != 200:
            return None
        data = r.json()
        hits = data.get("hits", [])
        if not hits:
            return None

        # Kare veya dikey oranda gorsel sec (0.5 - 1.8 arasi)
        # Cok genis (>1.8) = panoramik/sahne, genelde lifestyle
        for h in hits:
            w = h.get("imageWidth", 1)
            hh = h.get("imageHeight", 1)
            ratio = w / hh if hh else 1
            if 0.5 <= ratio <= 1.8:
                url = h.get("webformatURL") or h.get("largeImageURL")
                if url:
                    return url

        # Uygun oran bulunamazsa ilk sonucu ver
        return hits[0].get("webformatURL") or hits[0].get("largeImageURL")
    except Exception:
        return None


print("Pixabay'den resimler cekiliyor...")
print("-" * 60)
resimler = {}
bulunamadi = []

for anahtar, arama in URUNLER.items():
    url = resim_bul(arama)
    if url:
        resimler[anahtar] = url
        print(f"  OK  {anahtar:28s} [{arama:28s}] -> {url.split('/')[-1][:30]}")
    else:
        bulunamadi.append(anahtar)
        print(f"  X   {anahtar:28s} [{arama}] (bulunamadi)")
    # Pixabay rate limit: 100/60sec serbest, yine de nazik olalim
    time.sleep(0.1)

out = {
    "toplam": len(resimler),
    "kaynak": "pixabay.com",
    "resimler": resimler,
}
with open("resimler.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print("-" * 60)
print(f"OK {len(resimler)} resim kaydedildi (hedef: {len(URUNLER)})")
if bulunamadi:
    print(f"!  Bulunamadi: {', '.join(bulunamadi)}")
print(f"OK Dosya: resimler.json")
