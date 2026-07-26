import streamlit as st
import requests
import pandas as pd
import io

st.set_page_config(page_title="TradingView Screener", page_icon="📊")

# Sekme yazı stili
st.markdown("""
<style>
.stTabs button[data-baseweb="tab"] p {
    font-weight: 700 !important;
}
</style>
""", unsafe_allow_html=True)

# TradingView sektör adları -> Türkçe
SEKTOR_TR = {
    "Commercial Services": "Ticari Hizmetler",
    "Communications": "İletişim",
    "Consumer Durables": "Dayanıklı Tüketim",
    "Consumer Non-Durables": "Tüketim (Dayanıksız)",
    "Consumer Services": "Tüketici Hizmetleri",
    "Distribution Services": "Dağıtım Hizmetleri",
    "Electronic Technology": "Elektronik Teknoloji",
    "Energy Minerals": "Enerji Madenleri",
    "Finance": "Finans",
    "Government": "Devlet",
    "Health Services": "Sağlık Hizmetleri",
    "Health Technology": "Sağlık Teknolojisi",
    "Industrial Services": "Endüstriyel Hizmetler",
    "Miscellaneous": "Çeşitli",
    "Non-Energy Minerals": "Enerji Dışı Madenler",
    "Process Industries": "İşlenebilen Endüstriler",
    "Producer Manufacturing": "Üretici İmalatı",
    "Retail Trade": "Perakende Ticaret",
    "Technology Services": "Teknoloji Hizmetleri",
    "Transportation": "Taşımacılık",
    "Utilities": "Elektrik, Su, Gaz Hizmetleri",
}

# Türkçe isim -> (TradingView market kodu, country alanındaki İngilizce isim)
PIYASALAR = {
    "Türkiye": ("turkey", "Turkey"),
    "ABD": ("america", "United States"),
    "Almanya": ("germany", "Germany"),
    "Arjantin": ("argentina", "Argentina"),
    "Avustralya": ("australia", "Australia"),
    "Avusturya": ("austria", "Austria"),
    "BAE": ("uae", "United Arab Emirates"),
    "Bahreyn": ("bahrain", "Bahrain"),
    "Bangladeş": ("bangladesh", "Bangladesh"),
    "Belçika": ("belgium", "Belgium"),
    "Birleşik Krallık": ("uk", "United Kingdom"),
    "Brezilya": ("brazil", "Brazil"),
    "Çek Cumhuriyeti": ("czech", "Czech Republic"),
    "Çin": ("china", "China"),
    "Danimarka": ("denmark", "Denmark"),
    "Endonezya": ("indonesia", "Indonesia"),
    "Estonya": ("estonia", "Estonia"),
    "Filipinler": ("philippines", "Philippines"),
    "Finlandiya": ("finland", "Finland"),
    "Fransa": ("france", "France"),
    "Güney Afrika": ("rsa", "South Africa"),
    "Güney Kore": ("korea", "South Korea"),
    "Hindistan": ("india", "India"),
    "Hollanda": ("netherlands", "Netherlands"),
    "Hong Kong": ("hongkong", "Hong Kong"),
    "İspanya": ("spain", "Spain"),
    "İsrail": ("israel", "Israel"),
    "İsveç": ("sweden", "Sweden"),
    "İsviçre": ("switzerland", "Switzerland"),
    "İtalya": ("italy", "Italy"),
    "İzlanda": ("iceland", "Iceland"),
    "Japonya": ("japan", "Japan"),
    "Kanada": ("canada", "Canada"),
    "Katar": ("qatar", "Qatar"),
    "Kenya": ("kenya", "Kenya"),
    "Kıbrıs": ("cyprus", "Cyprus"),
    "Kolombiya": ("colombia", "Colombia"),
    "Kuveyt": ("kuwait", "Kuwait"),
    "Letonya": ("latvia", "Latvia"),
    "Litvanya": ("lithuania", "Lithuania"),
    "Lüksemburg": ("luxembourg", "Luxembourg"),
    "Macaristan": ("hungary", "Hungary"),
    "Malezya": ("malaysia", "Malaysia"),
    "Meksika": ("mexico", "Mexico"),
    "Mısır": ("egypt", "Egypt"),
    "Nijerya": ("nigeria", "Nigeria"),
    "Norveç": ("norway", "Norway"),
    "Pakistan": ("pakistan", "Pakistan"),
    "Peru": ("peru", "Peru"),
    "Polonya": ("poland", "Poland"),
    "Portekiz": ("portugal", "Portugal"),
    "Romanya": ("romania", "Romania"),
    "Rusya": ("russia", "Russia"),
    "Singapur": ("singapore", "Singapore"),
    "Sırbistan": ("serbia", "Serbia"),
    "Slovakya": ("slovakia", "Slovakia"),
    "Sri Lanka": ("srilanka", "Sri Lanka"),
    "Suudi Arabistan": ("ksa", "Saudi Arabia"),
    "Şili": ("chile", "Chile"),
    "Tayland": ("thailand", "Thailand"),
    "Tayvan": ("taiwan", "Taiwan"),
    "Tunus": ("tunisia", "Tunisia"),
    "Venezuela": ("venezuela", "Venezuela"),
    "Vietnam": ("vietnam", "Vietnam"),
    "Yeni Zelanda": ("newzealand", "New Zealand"),
    "Yunanistan": ("greece", "Greece"),
}


# Kolon grupları: (api_alani, gosterim_adi)
ORTAK_KOLONLAR = [
    ("name", "Hisse"),
    ("description", "Şirket"),
    ("country", "Ülke"),
    ("exchange", "Borsa"),
    ("currency", "Para Birimi"),
    ("sector", "Sektör"),
    ("market_cap_basic", "Piyasa Değeri"),
]

GELIR_KOLONLARI = [
    ("total_revenue_ttm", "Gelir (TTM)"),
    ("total_revenue_yoy_growth_ttm", "Gelir Büyüme YY % (TTM)"),
    ("gross_profit_ttm", "Brüt Kar (TTM)"),
    ("oper_income_ttm", "Faaliyet Geliri (TTM)"),
    ("ebitda_ttm", "FAVÖK (TTM)"),
    ("net_income_ttm", "Net Kar (TTM)"),
    ("earnings_per_share_basic_ttm", "EPS Temel (TTM)"),
    ("earnings_per_share_diluted_ttm", "EPS Seyreltilmiş (TTM)"),
    ("earnings_per_share_diluted_yoy_growth_ttm", "EPS Büyüme YY % (TTM)"),
    ("gross_margin_ttm", "Brüt Marj % (TTM)"),
    ("operating_margin_ttm", "Faaliyet Marjı % (TTM)"),
    ("net_margin_ttm", "Net Marj % (TTM)"),
    ("price_earnings_ttm", "F/K (FKO)"),
    ("price_book_fq", "PD/DD"),
    ("return_on_equity_fq", "ROE %"),
    ("return_on_invested_capital_fq", "ROIC %"),
    ("enterprise_value_ebitda_ttm", "FD/FAVÖK"),
    ("price_earnings_growth_ttm", "PEG"),
    ("enterprise_value_to_revenue_ttm", "FD/Gelir"),
    ("return_on_assets_fq", "ROA %"),
    ("dividend_yield_recent", "Tem. Verimi %"),
]

BILANCO_KOLONLARI = [
    ("total_assets_fq", "Toplam Varlıklar"),
    ("total_current_assets_fq", "Dönen Varlıklar"),
    ("cash_n_short_term_invest_fq", "Nakit ve Kısa Vad. Yatırımlar"),
    ("total_liabilities_fq", "Toplam Yükümlülükler"),
    ("total_current_liabilities_fq", "Kısa Vad. Yükümlülükler"),
    ("total_debt_fq", "Toplam Borç"),
    ("long_term_debt_fq", "Uzun Vad. Borç"),
    ("total_equity_fq", "Özkaynaklar"),
    ("book_value_per_share_fq", "Defter Değeri / Hisse"),
    ("current_ratio_fq", "Cari Oran"),
    ("quick_ratio_fq", "Asit-Test Oranı"),
    ("debt_to_equity_fq", "Borç / Özkaynak"),
    ("net_debt_fq", "Net Borç"),
]

NAKIT_KOLONLARI = [
    ("cash_f_operating_activities_ttm", "Faaliyet Nakit Akışı (TTM)"),
    ("cash_f_investing_activities_ttm", "Yatırım Nakit Akışı (TTM)"),
    ("cash_f_financing_activities_ttm", "Finansman Nakit Akışı (TTM)"),
    ("free_cash_flow_ttm", "Serbest Nakit Akışı (TTM)"),
    ("capital_expenditures_ttm", "Yatırım Harcamaları / CapEx (TTM)"),
]

# Özet sekmesindeki oranlar. sadece_pozitif=True: medyan yalnızca
# pozitif değerlerden hesaplanır (negatif F/K, PEG vb. anlamsız).
# (oran_adi, sektör_kolon_adi, sadece_pozitif)
OZET_ORANLAR = [
    ("F/K (FKO)", "F/K (Sekt.)", True),
    ("PD/DD", "PD/DD (Sekt.)", True),
    ("ROE %", "ROE (Sekt.)", False),
    ("ROIC %", "ROIC (Sekt.)", False),
    ("FD/FAVÖK", "FD/FAVÖK (Sekt.)", True),
    ("CFO/Net Kâr", "CFO/NK (Sekt.)", False),
    ("Cari Oran", "Cari (Sekt.)", False),
    ("Asit-Test Oranı", "Asit-Test (Sekt.)", False),
    ("PEG", "PEG (Sekt.)", True),
    ("FD/Gelir", "FD/Gelir (Sekt.)", True),
    ("ROA %", "ROA (Sekt.)", False),
    ("Tem. Verimi %", "Tem. (Sekt.)", False),
    ("Net Borç/FAVÖK", "NB/FAVÖK (Sekt.)", False),
]

# Özet sekmesinde gösterilecek kolonlar: her oranın yanında sektör medyanı
OZET_ADLARI = (
    ["Hisse", "Şirket", "Yıldız", "Sektör", "Piyasa Değeri", "FAVÖK (TTM)"]
    + [ad for oran, sekt, _ in OZET_ORANLAR for ad in (oran, sekt)]
)

TUM_KOLONLAR = (
    ORTAK_KOLONLAR + GELIR_KOLONLARI + BILANCO_KOLONLARI + NAKIT_KOLONLARI
)


@st.cache_data(ttl=3600)
def veri_cek_v5(market: str, country: str, sadece_yerli: bool, kolonlar: tuple):
    url = f"https://scanner.tradingview.com/{market}/scan"
    headers = {
        "authority": "scanner.tradingview.com",
        "accept": "application/json",
        "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "origin": "https://www.tradingview.com",
        "referer": "https://www.tradingview.com/",
    }
    api_alanlari = [k[0] for k in kolonlar]
    gosterim_adlari = [k[1] for k in kolonlar]

    filtreler = [{"left": "type", "operation": "equal", "right": "stock"}]
    if sadece_yerli:
        filtreler.append(
            {"left": "country", "operation": "equal", "right": country}
        )

    all_rows = []
    son_hata = None
    for start in range(0, 1500, 150):
        payload = {
            "columns": api_alanlari,
            "markets": [market],
            "filter": filtreler,
            "range": [start, start + 150],
            "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
        }
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        if res.status_code != 200:
            son_hata = f"HTTP {res.status_code}: {res.text[:500]}"
            break
        data = res.json().get("data", [])
        if not data:
            break
        for item in data:
            d = item["d"]
            row = dict(zip(gosterim_adlari, d))
            row["Sektör"] = SEKTOR_TR.get(row.get("Sektör"), row.get("Sektör") or "")
            # CapEx muhasebede negatif gelir (nakit çıkışı) -> mutlak değere çevir
            capex = row.get("Yatırım Harcamaları / CapEx (TTM)")
            if isinstance(capex, (int, float)):
                row["Yatırım Harcamaları / CapEx (TTM)"] = abs(capex)
            all_rows.append(row)
        if len(data) < 150:
            break
    df_son = pd.DataFrame(all_rows, columns=gosterim_adlari)
    # Olası çift kolon adlarını temizle
    df_son = df_son.loc[:, ~df_son.columns.duplicated()]
    return df_son, son_hata


st.title("📊 TradingView Screener")


# Türkçe karakter farkını aşmak için sıralama anahtarı
def tr_key(s: str) -> str:
    return s.translate(str.maketrans("ÇĞİıÖŞÜçğıöşü", "CGIIOSUcgiosu")).lower()

secim = st.selectbox(
    "Piyasa (ülke) seç:",
    options=sorted(PIYASALAR.keys(), key=tr_key),
    index=sorted(PIYASALAR.keys(), key=tr_key).index("Türkiye"),
)
sadece_yerli = st.checkbox(
    "Sadece bu ülkenin şirketleri (yabancı/ETF/çapraz kotluları gizle)",
    value=True,
)

market, country = PIYASALAR[secim]

if st.button("Piyasayı Tara ve Verileri Getir"):
    st.session_state["tarama"] = veri_cek_v5(
        market, country, sadece_yerli, tuple(TUM_KOLONLAR)
    )

if "tarama" in st.session_state:
    df, hata = st.session_state["tarama"]
    if df.empty:
        st.error("Veri çekilemedi.")
        if hata:
            st.code(hata)
    else:
        st.success(f"{secim}: {len(df)} şirket çekildi.")

        # Türetilmiş oran: kârın nakde dönüşümü (sadece pozitif net kârda anlamlı)
        df["CFO/Net Kâr"] = (
            df["Faaliyet Nakit Akışı (TTM)"] / df["Net Kar (TTM)"]
        ).where(df["Net Kar (TTM)"] > 0).round(2)

        # Türetilmiş oran: Net Borç/FAVÖK (FAVÖK <= 0 ise anlamsız -> boş)
        df["Net Borç/FAVÖK"] = (
            df["Net Borç"] / df["FAVÖK (TTM)"]
        ).where(df["FAVÖK (TTM)"] > 0).round(2)

        # Her oran için sektör medyanı kolonu.
        # sadece_pozitif=True olanlarda negatifler medyan dışı bırakılır;
        # NaN'lar (ör. temettü vermeyenler) medyana zaten katılmaz.
        for oran, sekt_ad, sadece_poz in OZET_ORANLAR:
            deger = df[oran].where(df[oran] > 0) if sadece_poz else df[oran]
            df[sekt_ad] = (
                deger.groupby(df["Sektör"]).transform("median").round(2)
            )

        # Yıldız: 5 kriter — kalite mutlak eşik, değerleme sektör-göreli.
        # Eksik veride kriter atlanır, puan 5'e orantılanır.
        kriter = pd.DataFrame(index=df.index)
        kriter["roe"] = df["ROE %"] >= 15
        kriter["roic"] = df["ROIC %"] >= 10
        kriter["nakit"] = df["CFO/Net Kâr"] >= 0.8
        kriter["borc"] = df["Borç / Özkaynak"] <= 1
        fk_poz = df["F/K (FKO)"].where(df["F/K (FKO)"] > 0)
        fd_poz = df["FD/FAVÖK"].where(df["FD/FAVÖK"] > 0)
        kriter["deger"] = (
            (fk_poz <= df["F/K (Sekt.)"]) & (fd_poz <= df["FD/FAVÖK (Sekt.)"])
        )
        gecerli = pd.DataFrame({
            "roe": df["ROE %"].notna(),
            "roic": df["ROIC %"].notna(),
            "nakit": df["CFO/Net Kâr"].notna(),
            "borc": df["Borç / Özkaynak"].notna(),
            "deger": fk_poz.notna() & fd_poz.notna(),
        })
        puan = (kriter & gecerli).sum(axis=1)
        gecerli_sayisi = gecerli.sum(axis=1)
        yildiz_sayi = (
            (5 * puan / gecerli_sayisi.where(gecerli_sayisi > 0))
            .round().fillna(0).astype(int)
        )
        df["Yıldız"] = yildiz_sayi.map(lambda s: "★" * s + "☆" * (5 - s))

        ortak_adlar = [k[1] for k in ORTAK_KOLONLAR]
        df_ozet = df[OZET_ADLARI]
        df_genel = df[ortak_adlar]
        df_gelir = df[ortak_adlar + [k[1] for k in GELIR_KOLONLARI]]
        df_bilanco = df[ortak_adlar + [k[1] for k in BILANCO_KOLONLARI]]
        df_nakit = df[ortak_adlar + [k[1] for k in NAKIT_KOLONLARI]]

        sek_ozet, sek1, sek2, sek3, sek4 = st.tabs(
            ["Özet", "Genel", "Gelir Tablosu", "Bilanço", "Nakit Akışı"]
        )
        with sek_ozet:
            st.dataframe(df_ozet, use_container_width=True)
        with sek1:
            st.dataframe(df_genel, use_container_width=True)
        with sek2:
            st.dataframe(df_gelir, use_container_width=True)
        with sek3:
            st.dataframe(df_bilanco, use_container_width=True)
        with sek4:
            st.dataframe(df_nakit, use_container_width=True)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df_ozet.to_excel(writer, index=False, sheet_name="Özet")
            df_genel.to_excel(writer, index=False, sheet_name="Genel")
            df_gelir.to_excel(writer, index=False, sheet_name="Gelir Tablosu")
            df_bilanco.to_excel(writer, index=False, sheet_name="Bilanço")
            df_nakit.to_excel(writer, index=False, sheet_name="Nakit Akışı")
        st.download_button(
            label="📥 Excel Dosyasını İndir",
            data=buffer.getvalue(),
            file_name=f"{market}_Finansallar.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        with st.expander("📖 Oranlar Nasıl Okunmalı? (Yıldız Sistemi)"):
            st.markdown("""
#### Oranların tek başına anlamı

| Oran | Ne ölçer? | İstenen |
|---|---|---|
| **F/K** | Kârın kaç katını ödüyorsun | Düşük (sektörüne göre) |
| **PD/DD** | Özkaynağın kaç katını ödüyorsun | Düşük — ama ROE ile birlikte oku |
| **FD/FAVÖK** | Borç dahil şirket değeri / faaliyet kârı | Düşük; F/K'dan farkı borcu da hesaba katması |
| **ROE %** | Özkaynak kârlılığı | Yüksek (≥ %15) — ama borçla şişirilebilir |
| **ROIC %** | Toplam yatırılan sermayenin kârlılığı | Yüksek (≥ %10) — ROE'nin kaldıraçsız hali |
| **CFO/Net Kâr** | Kâr gerçekten nakde dönüşüyor mu | ≥ 0.8; sürekli < 1 ise kâr kalitesi şüpheli |
| **Borç/Özkaynak** | Bilanço kaldıracı | ≤ 1; yüksekse ROE'ye güvenme |
| **Cari / Asit-Test** | Kısa vadeli borç ödeme gücü | ≥ 1; asit-test stokları saymaz |
| **PEG** | F/K'nın kâr büyümesine oranı | ~1 makul; < 1 büyümeye göre ucuz |
| **FD/Gelir** | Borç dahil şirket değeri / satışlar | Düşük; zarar eden şirketlerde de çalışır |
| **ROA %** | Toplam varlık kârlılığı | Yüksek; kaldıraçtan en az etkilenen kârlılık |
| **Tem. Verimi %** | Yıllık temettü / fiyat | Sürdürülebilirse yüksek; ödeme oranına bak |
| **Net Borç/FAVÖK** | Borcun kaç yıllık faaliyet kârı ettiği | ≤ 2-3; negatifse net nakit pozisyonu |

**(Sekt.) kolonları:** Her oranın yanındaki değer, seçili piyasada aynı
sektördeki şirketlerin **medyanıdır**. F/K, PD/DD, FD/FAVÖK, PEG ve
FD/Gelir medyanı yalnızca pozitif değerlerden hesaplanır; temettü
vermeyenler temettü medyanına katılmaz.

#### Birlikte nasıl okunur?

Tek oran tek başına yanıltır — okuma sırası:

1. **Kalite:** ROE + ROIC + Borç/Özkaynak + CFO/Net Kâr birlikte.
   ROE yüksek ama ROIC düşükse kârlılık borçtan geliyordur.
   CFO/Net Kâr düşükse kâr kağıt üzerindedir.
2. **Değerleme:** F/K + PD/DD + FD/FAVÖK, **aynı sektördeki
   emsallerle** kıyaslanır. Mutlak eşik yok: bankada PD/DD ~1,
   yazılımda 5+ normal olabilir.
3. **Tuzaklar:**
   - Düşük F/K + düşük PD/DD + **düşük ROE** → değer tuzağı
   - Yüksek ROE + çok düşük PD/DD → piyasa bir şey biliyor olabilir
     (tek seferlik kâr, yüksek kaldıraç, kâr kalitesi)
   - Yüksek PD/DD + **sürdürülebilir** yüksek ROE → makul prim

#### Yıldız nasıl hesaplanıyor? (★ 0–5)

Her sağlanan kriter 1 yıldız:

1. ROE ≥ %15 (kalite)
2. ROIC ≥ %10 (kaldıraçsız kalite)
3. CFO/Net Kâr ≥ 0.8 (kâr nakde dönüşüyor)
4. Borç/Özkaynak ≤ 1 (bilanço sağlığı)
5. F/K **ve** FD/FAVÖK kendi sektör medyanının altında (göreli ucuzluk)

Verisi eksik kriter değerlendirme dışı bırakılır, puan 5'e
orantılanır (ör. bankalarda FD/FAVÖK yoktur — kalan kriterlerden
hesaplanır). ★★★★★ "al" demek değildir; kalite + ucuzluk
kombinasyonunun mekanik bir özetidir. Yatırım tavsiyesi değildir.
""")
