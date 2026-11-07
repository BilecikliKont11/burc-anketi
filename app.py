import os
import random
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, abort
from pymongo import MongoClient

yol = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(yol)

# .env içinde hangi isim kullanıldıysa onu bulur
MONGO_URI = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI")

client = MongoClient(MONGO_URI)
katilimlar = client["burc_anketi"]["katilimlar"]

BURCLAR = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak",
           "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]

# Her seçenek, listelenen burçlara +1 puan verir
SORULAR = [
    {"id": "q1", "metin": "Cumartesi gecesi planın ne olur?", "secenekler": [
        {"metin": "Kalabalık bir arkadaş buluşması", "burclar": ["Koç", "İkizler", "Aslan", "Yay"]},
        {"metin": "Evde film ve battaniye", "burclar": ["Yengeç", "Boğa", "Balık", "Oğlak"]},
        {"metin": "Yeni bir yer keşfetmek", "burclar": ["Yay", "Kova", "İkizler", "Terazi"]},
        {"metin": "Kitap ve tek başına zaman", "burclar": ["Başak", "Akrep", "Oğlak", "Kova"]},
    ]},
    {"id": "q2", "metin": "Bir tartışmada nasılsın?", "secenekler": [
        {"metin": "Hemen cevap veririm, geri adım atmam", "burclar": ["Koç", "Aslan", "Akrep", "Boğa"]},
        {"metin": "Soğukkanlı dinler, mantıkla cevap veririm", "burclar": ["Başak", "Kova", "İkizler", "Terazi"]},
        {"metin": "Ortayı bulmaya çalışırım", "burclar": ["Terazi", "Balık", "Yengeç", "Yay"]},
        {"metin": "Susar, içime atarım", "burclar": ["Yengeç", "Akrep", "Oğlak", "Balık"]},
    ]},
    {"id": "q3", "metin": "Arkadaş grubundaki rolün hangisi?", "secenekler": [
        {"metin": "Espri yapan, ortamı neşelendiren", "burclar": ["İkizler", "Yay", "Aslan", "Koç"]},
        {"metin": "Plan yapan, organize eden", "burclar": ["Başak", "Oğlak", "Boğa", "Terazi"]},
        {"metin": "Dinleyen, dert ortağı", "burclar": ["Yengeç", "Balık", "Terazi", "Başak"]},
        {"metin": "Gizemli, az konuşan", "burclar": ["Akrep", "Kova", "Oğlak", "Balık"]},
    ]},
    {"id": "q4", "metin": "Hangi tatili seçersin?", "secenekler": [
        {"metin": "Macera ve doğa sporları", "burclar": ["Koç", "Yay", "Aslan", "Kova"]},
        {"metin": "Lüks otel, havuz başı", "burclar": ["Boğa", "Aslan", "Terazi", "Balık"]},
        {"metin": "Şehir gezisi, müze, kafe", "burclar": ["İkizler", "Başak", "Terazi", "Kova"]},
        {"metin": "Sakin bir deniz kenarı köyü", "burclar": ["Yengeç", "Balık", "Oğlak", "Akrep"]},
    ]},
    {"id": "q5", "metin": "Seni en çok ne rahatsız eder?", "secenekler": [
        {"metin": "Belirsizlik ve plansızlık", "burclar": ["Başak", "Oğlak", "Boğa", "Akrep"]},
        {"metin": "Sıkıcılık ve rutin", "burclar": ["İkizler", "Yay", "Koç", "Kova"]},
        {"metin": "Kaba ve düşüncesiz davranışlar", "burclar": ["Terazi", "Yengeç", "Balık", "Aslan"]},
        {"metin": "Yalan ve ihanet", "burclar": ["Akrep", "Aslan", "Boğa", "Oğlak"]},
    ]},
    {"id": "q6", "metin": "Bir hedefe nasıl ulaşırsın?", "secenekler": [
        {"metin": "Hemen harekete geçerim", "burclar": ["Koç", "Aslan", "Yay", "İkizler"]},
        {"metin": "Adım adım, sabırla", "burclar": ["Boğa", "Oğlak", "Başak", "Yengeç"]},
        {"metin": "Sezgilerime güvenirim", "burclar": ["Balık", "Akrep", "Yengeç", "Kova"]},
        {"metin": "Başkalarıyla işbirliği yaparım", "burclar": ["Terazi", "Kova", "İkizler", "Aslan"]},
    ]},
]

app = Flask(__name__)


def kayit_getir(id):
    try:
        k = katilimlar.find_one({"_id": ObjectId(id)})
    except InvalidId:
        abort(404)
    if k is None:
        abort(404)
    return k


@app.route("/")
def ana():
    return render_template("anket.html", sorular=SORULAR)


@app.route("/tahmin", methods=["POST"])
def tahmin_et():
    skorlar = {b: 0 for b in BURCLAR}
    cevaplar = {}
    for s in SORULAR:
        try:
            idx = int(request.form[s["id"]])
            secenek = s["secenekler"][idx]
        except (KeyError, ValueError, IndexError):
            return redirect(url_for("ana"))
        cevaplar[s["id"]] = idx
        for b in secenek["burclar"]:
            skorlar[b] += 1

    en_yuksek = max(skorlar.values())
    tahmin = random.choice([b for b, p in skorlar.items() if p == en_yuksek])

    sonuc = katilimlar.insert_one({
        "cevaplar": cevaplar,
        "skorlar": skorlar,
        "tahmin": tahmin,
        "gercek_burc": None,
        "tarih": datetime.now(timezone.utc),
    })
    return redirect(url_for("sonuc", id=sonuc.inserted_id))


@app.route("/sonuc/<id>")
def sonuc(id):
    k = kayit_getir(id)
    siralama = sorted(k["skorlar"].items(), key=lambda x: x[1], reverse=True)[:3]
    return render_template("sonuc.html", k=k, siralama=siralama, burclar=BURCLAR)


@app.route("/gercek/<id>", methods=["POST"])
def gercek(id):
    k = kayit_getir(id)
    burc = request.form.get("gercek")
    if burc in BURCLAR:
        katilimlar.update_one({"_id": k["_id"]}, {"$set": {"gercek_burc": burc}})
    return redirect(url_for("sonuc", id=id))


@app.route("/analiz")
def analiz():
    toplam = katilimlar.count_documents({})
    kayitlar = list(katilimlar.find({"gercek_burc": {"$ne": None}}))
    n = len(kayitlar)
    dogru = sum(1 for k in kayitlar if k["tahmin"] == k["gercek_burc"])
    satirlar = []
    for b in BURCLAR:
        grup = [k for k in kayitlar if k["gercek_burc"] == b]
        d = sum(1 for k in grup if k["tahmin"] == b)
        satirlar.append({
            "burc": b,
            "n": len(grup),
            "dogru": d,
            "oran": round(d * 100 / len(grup), 1) if grup else 0,
        })
    genel = round(dogru * 100 / n, 1) if n else 0
    return render_template("analiz.html", toplam=toplam, n=n, genel=genel, satirlar=satirlar)


if __name__ == "__main__":
    app.run(debug=True)