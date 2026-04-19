import requests
import json
import sys
from datetime import datetime
from statistics import median

# Windows konsolu UTF-8 yap (emoji sorunu icin)
if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

print("Market fiyatlari cekiliyor, bekleyin...")
print("-" * 50)

API_URL = "https://api.marketfiyati.org.tr/api/v2/search"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Origin": "https://marketfiyati.org.tr",
    "Referer": "https://marketfiyati.org.tr/",
    "Content-Type": "application/json",
    "Accept-Language": "tr-TR,tr;q=0.9",
}

# Her urun icin:
# q        : API'ye gonderilecek arama
# emoji    : oyun emoji
# isim     : oyunda gorunecek isim
# bilgi    : aciklama satiri
# istenen  : baslikta BULUNMASI gereken kelimeler (virgulle, hepsi lazim)
# istenmeyen: baslikta BULUNMAMASI gereken kelimeler (virgulle)
URUNLER = [
    # Sebze-Meyve (hepsi 1 kg)
    {"q":"domates 1 kg","emoji":"🍅","isim":"1 kg domates","bilgi":"Taze","istenen":"domates,1 kg","istenmeyen":"konserve,salca,kurutulmus,sos,suyu,cherry,kiraz,kokteyl,turuncu,atistirmalik,eko"},
    {"q":"salatalik 1 kg","emoji":"🥒","isim":"1 kg salatalık","bilgi":"Taze","istenen":"salatalik,1 kg","istenmeyen":"tursu,konserve"},
    {"q":"patlican","emoji":"🍆","isim":"1 kg patlıcan","bilgi":"Taze","istenen":"patlican,kg","istenmeyen":"konserve,kurutulmus,sos,kiz"},
    {"q":"sivri biber","emoji":"🌶️","isim":"1 kg sivri biber","bilgi":"Taze","istenen":"sivri biber,kg","istenmeyen":"kurutulmus,tursu,konserve,sos,kapya,dolmalik,carliston"},
    {"q":"muz","emoji":"🍌","isim":"1 kg muz","bilgi":"Taze","istenen":"muz,kg","istenmeyen":"kurutulmus,cips,gofret,aromali,sut"},
    {"q":"elma","emoji":"🍎","isim":"1 kg elma","bilgi":"Taze","istenen":"elma,kg","istenmeyen":"kurutulmus,suyu,cips,aromali"},
    {"q":"limon","emoji":"🍋","isim":"1 kg limon","bilgi":"Taze","istenen":"limon,kg","istenmeyen":"suyu,sosu,tuzu,aromali,kolonya"},
    {"q":"sogan","emoji":"🧅","isim":"1 kg soğan","bilgi":"Taze","istenen":"sogan,kg","istenmeyen":"kurutulmus,toz,pul,halka,arpacik"},
    {"q":"karpuz","emoji":"🍉","isim":"1 kg karpuz","bilgi":"Taze","istenen":"karpuz,kg","istenmeyen":"cekirdek,aromali,dilim,sekeri"},

    # Temel Gida
    {"q":"baldo pirinc","emoji":"🍚","isim":"Baldo pirinç 1 kg","bilgi":"Market","istenen":"pirinc,1 kg","istenmeyen":"yasemin,jasmine,basmati"},
    {"q":"un 1 kg","emoji":"🌾","isim":"Un 1 kg","bilgi":"Market","istenen":"un,1 kg","istenmeyen":"bademli,cavdar,misir,nohut,yulaf,bebek,kekik,kabartma"},
    {"q":"bulgur","emoji":"🌾","isim":"Bulgur 1 kg","bilgi":"Market","istenen":"bulgur,1 kg","istenmeyen":"kofte"},
    {"q":"toz seker 1 kg","emoji":"🍬","isim":"Toz şeker 1 kg","bilgi":"Market","istenen":"seker,1 kg","istenmeyen":"esmer,icec,kup,kesme,vanilya,pudra,aromali"},
    {"q":"zeytinyagi 1 lt","emoji":"🫒","isim":"Zeytinyağı 1 L","bilgi":"Sızma","istenen":"zeytinyagi,1 lt","istenmeyen":"sabun"},
    {"q":"barilla makarna 500","emoji":"🍝","isim":"Barilla makarna 500 gr","bilgi":"Market","istenen":"barilla,500","istenmeyen":"tricolore,whole"},

    # Sut Urunleri
    {"q":"pinar sut 1 lt","emoji":"🥛","isim":"Pınar süt 1 L","bilgi":"Tam yağlı","istenen":"pinar,sut,1 lt","istenmeyen":"bebek,cilek,kakaolu,muz,laktozsuz,yarim,sutlac"},
    {"q":"sek sut 1 lt","emoji":"🥛","isim":"SEK süt 1 L","bilgi":"Tam yağlı","istenen":"sek,sut,1 lt","istenmeyen":"bebek,cilek,kakaolu,muz,laktozsuz,yarim,sutlac"},
    {"q":"yumurta 30","emoji":"🥚","isim":"30'lu yumurta","bilgi":"Market","istenen":"yumurta,30","istenmeyen":"cikolata,disi,cevap"},
    {"q":"beyaz peynir 400","emoji":"🧀","isim":"Beyaz peynir 400 gr","bilgi":"Market","istenen":"beyaz peynir,400","istenmeyen":"tulum,lor,kasar"},
    {"q":"kasar peynir 500","emoji":"🧀","isim":"Kaşar peyniri 500 gr","bilgi":"Market","istenen":"kasar,500","istenmeyen":"beyaz,tulum,lor,tost,dilim"},
    {"q":"tereyag 250 gr","emoji":"🧈","isim":"Tereyağı 250 gr","bilgi":"Market","istenen":"tereyag,250","istenmeyen":"margarin,bebek"},
    {"q":"yogurt 1 kg","emoji":"🥣","isim":"Yoğurt 1 kg","bilgi":"Market","istenen":"yogurt,1 kg","istenmeyen":"bebek,meyveli,cilek,muzlu,aromali,dondurma"},
    {"q":"ayran 1 lt","emoji":"🥤","isim":"Ayran 1 L","bilgi":"Market","istenen":"ayran,1 lt","istenmeyen":"sade koy"},

    # Icecek-Atistirmalik
    {"q":"coca cola 1 lt","emoji":"🥤","isim":"Coca-Cola 1 L","bilgi":"PET şişe","istenen":"coca,1 lt","istenmeyen":"zero,light,diyet,cherry,limon"},
    {"q":"red bull","emoji":"⚡","isim":"Red Bull 250 ml","bilgi":"Market","istenen":"red bull,250","istenmeyen":"sugar free,zero,ramune"},
    {"q":"caykur rize 1 kg","emoji":"🫖","isim":"Çaykur Rize çay 1 kg","bilgi":"Market","istenen":"rize,1 kg","istenmeyen":"poset,demlik,earl,bergamot,yesil"},
    {"q":"nescafe gold 100 gr","emoji":"☕","isim":"Nescafe Gold 100 gr","bilgi":"Market","istenen":"nescafe,gold,100","istenmeyen":"multipack,stick,sutlu,kremali,2 gr"},
    {"q":"milka cikolata 100","emoji":"🍫","isim":"Milka çikolata 100 gr","bilgi":"Market","istenen":"milka,100","istenmeyen":"bonibon,mini,kek"},
    {"q":"eti cin 300","emoji":"🍪","isim":"Eti Cin bisküvi","bilgi":"Market","istenen":"eti,cin","istenmeyen":"mini"},

    # Et
    {"q":"tavuk gogus","emoji":"🍗","isim":"Tavuk göğsü (1 adet)","bilgi":"Fileto · market","istenen":"tavuk gogsu","istenmeyen":"dondurulmus,baharatli,marine,dr oetker,129 gr,ikili,2 adet"},

    # Temizlik
    {"q":"ariel toz deterjan","emoji":"🧺","isim":"Ariel toz deterjan","bilgi":"Market","istenen":"ariel","istenmeyen":"sivi,jel,kapsul"},
    {"q":"fairy tablet","emoji":"🧼","isim":"Fairy bulaşık tableti","bilgi":"Market","istenen":"fairy,tablet","istenmeyen":"sivi"},
    {"q":"elidor sampuan 400","emoji":"🧴","isim":"Elidor şampuan 400 ml","bilgi":"Market","istenen":"elidor,400","istenmeyen":"erkek,bebek,krem"},
]

def normalize(s):
    """Karsilastirma icin: kucuk harf + turkce/aksanli karakter donusumu."""
    s = s.lower()
    tr = str.maketrans("çğıöşüâîéèêëáàäóòôúùûñ", "cgiosuaieeeeaaaooouuun")
    return s.translate(tr)

def fiyat_bul(urun):
    """Bir urun icin uygun fiyati bulur. Medyan fiyat doner."""
    try:
        r = requests.post(API_URL, headers=HEADERS, json={"keywords": urun["q"], "pages": 0, "size": 20}, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        products = data.get("content", [])
        if not products:
            return None

        istenen = [normalize(k.strip()) for k in urun.get("istenen", "").split(",") if k.strip()]
        istenmeyen = [normalize(k.strip()) for k in urun.get("istenmeyen", "").split(",") if k.strip()]

        for p in products:
            t = normalize(p["title"])
            # Istenmeyen kelime varsa atla
            if any(bad in t for bad in istenmeyen):
                continue
            # Istenen kelimelerin HEPSI bulunmali
            if istenen and not all(req in t for req in istenen):
                continue
            # Depot listesinden tum fiyatlar
            depot_list = p.get("productDepotInfoList", [])
            fiyatlar = [d.get("price") for d in depot_list if d.get("price") and d.get("price") > 0]
            if not fiyatlar:
                continue
            # Medyan fiyat (uc degerleri elemeye yarar)
            med_fiyat = round(median(fiyatlar), 2)
            marketler = sorted(set(d.get("marketAdi","") for d in depot_list))
            return {
                "emoji": urun["emoji"],
                "isim": urun["isim"],
                "bilgi": urun["bilgi"],
                "fiyat": med_fiyat,
                "kac_market": len(marketler),
                "api_baslik": p["title"],
            }
        return None
    except Exception:
        return None

fiyatlar = []
basarisiz = []
for urun in URUNLER:
    sonuc = fiyat_bul(urun)
    if sonuc:
        fiyatlar.append(sonuc)
        print(f"  {sonuc['emoji']} {sonuc['isim']:30s} {sonuc['fiyat']:>7.2f} TL  ({sonuc['kac_market']} market)")
    else:
        basarisiz.append(urun["isim"])
        print(f"  X  {urun['isim']:30s} (bulunamadi)")

sonuc_data = {
    "guncelleme": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "kaynak": "marketfiyati.org.tr (A101, BIM, Migros, Carrefour, SOK, TK)",
    "not": "Her urunun fiyati: o urunu satan marketlerin medyanidir",
    "toplam_urun": len(fiyatlar),
    "urunler": fiyatlar,
}

with open("otomatik_market.json", "w", encoding="utf-8") as f:
    json.dump(sonuc_data, f, ensure_ascii=False, indent=2)

print("-" * 50)
print(f"OK {len(fiyatlar)} urun kaydedildi (hedef: {len(URUNLER)})")
if basarisiz:
    print(f"!  {len(basarisiz)} urun bulunamadi: {', '.join(basarisiz[:5])}{'...' if len(basarisiz)>5 else ''}")
print(f"OK Dosya: otomatik_market.json")
