import requests
import json
from datetime import datetime

print("Fiyatlar çekiliyor, bekleyin...")
print("-" * 50)

url = "https://finans.truncgil.com/v4/today.json"

try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
except Exception as e:
    print(f"HATA: {e}")
    exit()

fiyatlar = {}

urun_listesi = {
    "USD": {"isim": "1 ABD Doları", "kategori": "doviz"},
    "EUR": {"isim": "1 Euro", "kategori": "doviz"},
    "GBP": {"isim": "1 İngiliz Sterlini", "kategori": "doviz"},
    "CHF": {"isim": "1 İsviçre Frangı", "kategori": "doviz"},
    "SAR": {"isim": "1 Suudi Riyali", "kategori": "doviz"},
    "GRA": {"isim": "Gram Altın", "kategori": "altin"},
    "HAS": {"isim": "Has Altın", "kategori": "altin"},
    "CEYREKALTIN": {"isim": "Çeyrek Altın", "kategori": "altin"},
    "YARIMALTIN": {"isim": "Yarım Altın", "kategori": "altin"},
    "TAMALTIN": {"isim": "Tam Altın", "kategori": "altin"},
    "CUMHURIYETALTINI": {"isim": "Cumhuriyet Altını", "kategori": "altin"},
    "GUMUS": {"isim": "Gümüş (gram)", "kategori": "altin"}
}

print()
for kod, bilgi in urun_listesi.items():
    if kod in data:
        satis = data[kod].get("Selling")
        if satis:
            fiyat = float(satis)
            fiyatlar[kod] = {
                "isim": bilgi["isim"],
                "kategori": bilgi["kategori"],
                "fiyat": fiyat
            }
            print(f"  {bilgi['isim']}: {fiyat:,.2f} TL")

sonuc = {
    "guncelleme": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "kaynak": "Truncgil Finans",
    "toplam_fiyat": len(fiyatlar),
    "fiyatlar": fiyatlar
}

with open("otomatik_fiyatlar.json", "w", encoding="utf-8") as f:
    json.dump(sonuc, f, ensure_ascii=False, indent=2)

print("-" * 50)
print(f"✓ Toplam {len(fiyatlar)} fiyat kaydedildi!")
print(f"✓ Dosya: otomatik_fiyatlar.json")