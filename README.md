# 📊 Temel ve Teknik Analiz Terminali

İki aşamalı bir hisse senedi analiz uygulaması. Üstte **temel analizle** uluslararası piyasalardan firma elenir; altta seçilen firmanın ticker'ı girilerek **teknik analiz** yapılır. Streamlit üzerinde tek dosyada çalışır.

> ⚠️ **Yatırım tavsiyesi içermez. Yalnızca araştırma ve eğitim amaçlıdır.** Tüm skorlar ve sinyaller mekanik hesaplamalardır.

---

## İçindekiler

- [Genel Bakış](#genel-bakış)
- [Kurulum](#kurulum)
- [Çalıştırma](#çalıştırma)
- [Bölüm 1 — Temel Analiz](#bölüm-1--temel-analiz)
- [Bölüm 2 — Teknik Analiz](#bölüm-2--teknik-analiz)
- [Veri Kaynakları ve Gecikme](#veri-kaynakları-ve-gecikme)
- [Sık Karşılaşılan Sorunlar](#sık-karşılaşılan-sorunlar)
- [Bilinen Sınırlamalar](#bilinen-sınırlamalar)

---

## Genel Bakış

Uygulama iki bölümden oluşur ve tek sayfada, yukarıdan aşağıya bir iş akışı sunar:

1. **Temel Analiz (üst):** Bir ülke/piyasa seçilir, o piyasadaki tüm şirketler TradingView tarayıcısından çekilir. Her şirket için değerleme, kârlılık, borç ve nakit oranları hesaplanır; iki puanlama sistemi (Yıldız ve Sektör Skoru) ile sıralama yapılır.
2. **Teknik Analiz (alt):** Temel analizle beğenilen firmanın ticker'ı elle girilip "Analiz Et" butonuna basılınca, yfinance'ten fiyat geçmişi çekilir ve 15+ teknik gösterge, otomatik destek/direnç, Fibonacci ve bir karar özeti üretilir.

İki bölüm birbirinden bağımsız çalışır: teknik analiz, butona basılana kadar hiç çalışmaz ve üstteki taramayı yavaşlatmaz.

---

## Kurulum

Python 3.9+ gereklidir.

```bash
pip install -r requirements.txt
```

`requirements.txt` içeriği:

```
streamlit
requests
pandas
numpy
yfinance
plotly
xlsxwriter
```

---

## Çalıştırma

```bash
streamlit run app.py
```

Tarayıcıda otomatik olarak `http://localhost:8501` açılır.

---

## Bölüm 1 — Temel Analiz

### Nasıl kullanılır

1. Açılır menüden bir **piyasa (ülke)** seç.
2. İstersen "Sadece bu ülkenin şirketleri" kutusunu işaretle (yabancı/ETF/çapraz kotlu enstrümanları eler).
3. **"Piyasayı Tara ve Verileri Getir"** butonuna bas.
4. Sonuçlar dört sekmede gelir: **Özet, Gelir Tablosu, Bilanço, Nakit Akışı**.
5. İstersen tüm veriyi **Excel** olarak indir.

### Özet tablosundaki kolonlar

Kimlik ve durum kolonlarının (Hisse, Şirket, Sektör, Piyasa Değeri, 7G/30G Değişim, FAVÖK, Son/Sonraki Bilanço) yanında 14 oranın her biri, hemen yanında o oranın **kendi sektöründeki medyanıyla** birlikte gösterilir.

**Değerleme (düşük iyi):** F/K, PD/DD, FD/FAVÖK, FD/Gelir, PEG
**Kârlılık (yüksek iyi):** ROE, ROIC, ROA
**Kâr kalitesi & borç:** CFO/Net Kâr (yüksek iyi), Net Borç/FAVÖK (düşük iyi), FCF Verimi (yüksek iyi)
**Likidite (yüksek iyi):** Cari Oran, Asit-Test
**Temettü:** Temettü Verimi

Her oranın anlamı ve yönü, uygulama içindeki **"Tüm Oranlar"** açılır bölümünde ayrıntılı açıklanır.

### İki puanlama sistemi

**⭐ Yıldız (0–7) — mutlak kalite.** "Bu iyi bir şirket mi?" sorusunu ölçer. Her sağlanan kriter 1 yıldız:

1. ROE ≥ %15
2. ROIC ≥ %10
3. CFO/Net Kâr ≥ 0.8
4. FCF Verimi > 0
5. Borç/Özkaynak ≤ 1
6. EPS büyümesi (yıllık) > 0
7. F/K **ve** FD/FAVÖK, sektör medyanının altında

Verisi eksik kriter yıldız kazandırmaz (ör. bankalarda FD/FAVÖK olmadığı için tavan 6 yıldızdır). En az 4 geçerli kriteri olmayan şirkete yıldız verilmez ("—").

**📊 Sektör Skoru (0–100) — göreli konum.** "Sektöründe nerede duruyor?" sorusunu ölçer. 14 oranın her biri kendi sektör medyanıyla doğru yönde kıyaslanır; skor = medyanı geçen oran / geçerli oran × 100.

İki metrik birlikte okunur: yüksek Yıldız + yüksek Skor "kaliteli ve sektörünün önünde" demektir; yüksek Skor + düşük Yıldız ise "zayıf bir sektörün en iyisi" (değer tuzağı) olabilir.

### Veri temizleme güvenlikleri

Puanlamaların yanlış pozitif üretmesini önlemek için üç kural uygulanır:

- **Aykırı değer filtresi:** Payda sıfıra yaklaşınca patlayan oranlar (ör. F/K > 200, CFO/Net Kâr > 20) ekranda görünür ama medyan, Skor ve Yıldız hesaplarına katılmaz.
- **En az 3 şirket:** Bir sektörde geçerli verisi olan 3'ten az şirket varsa o oranın sektör medyanı boş bırakılır (tek şirketli sektörde medyan = şirketin kendisi olurdu).
- **En az 4 kriter / 3 oran:** Yeterli verisi olmayan şirkete yıldız/skor verilmez.

### Bilanço takvimi

Özet tablosunda "Son Bilanço" ve "Sonraki Bilanço" tarihleri gösterilir. Önümüzdeki 7 gün içinde bilanço açıklayacak şirketler ⏰ rozetiyle işaretlenir ve tablonun üstünde uyarı olarak listelenir — bu şirketlerin oranları ve skorları bilanço sonrası değişebilir.

---

## Bölüm 2 — Teknik Analiz

### Nasıl kullanılır

1. Sol paneldeki **"Ticker Sembolü"** kutusuna sembolü yaz.
   - BIST hisseleri için `.IS` eki gerekir: `ASELS.IS`, `THYAO.IS`
   - ABD hisseleri eksiz: `AAPL`, `MSFT`
   - Emtia/vadeli: `GC=F` (altın), `CL=F` (petrol)
2. **Periyot** (veri süresi) ve **Mum Aralığı** seç.
3. **"🔍 Analiz Et"** butonuna bas.

> Butona basılana kadar teknik analiz çalışmaz. Bir kez basıldıktan sonra kenar çubuğundaki parametreleri değiştirdiğinde analiz açık kalır (grafik kaybolmaz).

### Sunulan göstergeler

Ana grafik: mum/çizgi, SMA, EMA, KAMA, SuperTrend, Fibonacci seviyeleri, otomatik destek/direnç, trend çizgileri, hacim profili ve WaveTrend tabanlı boğa/ayı işaretleri.

Alt sekmeler her göstergeyi ayrı grafikte gösterir: **Bollinger Bands, ADX, Ichimoku, KAMA & LRC, SuperTrend, Stoch RSI, WaveTrend, RSI, MACD, OBV, Divergence.**

### Algoritmik karar özeti

Grafik altında her gösterge için **AL / SAT / TUT / BİLGİ** kararı ve gerekçesi tablo halinde verilir. Ayrıca hareketli ortalamaların **hiyerarşi** dizilimi (fiyatın MA'lara göre konumu) ve ADX rejimi özetlenir. Bu bir sinyal birleştiricidir, tavsiye değildir.

### Ekonomik takvim

Seçilen ülke için TradingView ekonomik takviminden önümüzdeki günlerin önemli veri açıklamaları (faiz kararları, enflasyon, istihdam vb.) Türkçe başlıklarla listelenir.

### Parametreler

Tüm gösterge parametreleri (SMA/EMA periyotları, RSI eşikleri, Bollinger sapması, MACD, ADX, SuperTrend, Ichimoku, Fibonacci lookback vb.) kenar çubuğundaki kaydırıcılarla ayarlanabilir. Ichimoku'nun klasik 9-26-52 değerleri korunması önerilir (arayüzde uyarı vardır).

---

## Veri Kaynakları ve Gecikme

| Bölüm | Kaynak | Tazelik |
|---|---|---|
| Temel analiz (oranlar, temel veri) | TradingView tarayıcı API'si | Oranlar günlük güncellenir; temel kalemler çeyreklik |
| Temel analiz (fiyat/piyasa değeri) | TradingView | Borsaya göre ~15 dk gecikmeli |
| Teknik analiz (fiyat geçmişi) | yfinance (Yahoo Finance) | Borsaya göre ~15 dk gecikmeli |

Oranların payı ve paydası aynı kaynaktan (TradingView) gelir — bu tutarlılık için önemlidir. Teknik analiz ayrı olarak yfinance kullanır; bu, fiyat geçmişi gerektiren grafikler için doğru kaynaktır.

Uygulama gün içi (intraday) alım-satım için değil, **tarama ve analiz** için tasarlanmıştır.

---

## Sık Karşılaşılan Sorunlar

**Teknik analizde "Veri çekilemedi" hatası**
Ticker formatını kontrol et (BIST için `.IS` eki şart). Yahoo Finance geçici olarak erişilemiyor olabilir; birkaç dakika sonra tekrar dene.

**Grafik dar/sıkışık görünüyor**
Sayfa `layout="wide"` ile açılır; tarayıcı penceresini genişlet. Streamlit Cloud'da bazen ilk yüklemede dar açılır, sayfayı yenile.

**Temel analiz tablosunda bilanço tarihleri veya bazı oranlar boş**
TradingView bazı küçük piyasalar/şirketler için bu alanları vermez. Boş alan, veri yokluğunu gösterir ve hesaplara katılmaz.

**Aynı şirket iki kez görünüyor (ör. İş Bankası B ve C)**
Çift kotasyon TradingView'dan gelir. Likit olmayan sınıfın fiyatı/oranları yanıltıcı olabilir.

---

## Bilinen Sınırlamalar

- Piyasalar TradingView tarayıcısının desteklediği ülkelerle sınırlıdır.
- "Finans" ve "Çeşitli" gibi geniş sektör torbaları farklı iş modellerini (banka, sigorta, holding, faktoring) aynı medyanda toplar; bu sektörlerdeki skorlar dikkatle okunmalıdır.
- Yatırım ortaklıkları (portföy şirketleri) için standart oranlar yanıltıcıdır; doğru metrik NAV iskontosudur ve bu veri mevcut değildir.
- Teknik göstergelerin tümü geçmiş fiyata dayanır; hiçbiri gelecek garantisi vermez.

---

*Bu uygulama eğitim ve araştırma amaçlıdır. Hiçbir çıktısı yatırım tavsiyesi değildir. Yatırım kararları için lisanslı bir danışmana başvurun.*
