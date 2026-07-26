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
    ("Perf.W", "7G Değişim %"),
    ("Perf.1M", "30G Değişim %"),
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
    ("earnings_release_date", "Son Bilanço"),
    ("earnings_release_next_date", "Sonraki Bilanço"),
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
# yon: sektör medyanına göre hangi taraf iyi ("dusuk" / "yuksek").
# (oran_adi, sektör_kolon_adi, sadece_pozitif, yon)
OZET_ORANLAR = [
    ("F/K (FKO)", "F/K (Sekt.)", True, "dusuk"),
    ("PD/DD", "PD/DD (Sekt.)", True, "dusuk"),
    ("ROE %", "ROE (Sekt.)", False, "yuksek"),
    ("ROIC %", "ROIC (Sekt.)", False, "yuksek"),
    ("FD/FAVÖK", "FD/FAVÖK (Sekt.)", True, "dusuk"),
    ("CFO/Net Kâr", "CFO/NK (Sekt.)", False, "yuksek"),
    ("Cari Oran", "Cari (Sekt.)", False, "yuksek"),
    ("Asit-Test Oranı", "Asit-Test (Sekt.)", False, "yuksek"),
    ("PEG", "PEG (Sekt.)", True, "dusuk"),
    ("FD/Gelir", "FD/Gelir (Sekt.)", True, "dusuk"),
    ("ROA %", "ROA (Sekt.)", False, "yuksek"),
    ("Tem. Verimi %", "Tem. (Sekt.)", False, "yuksek"),
    ("Net Borç/FAVÖK", "NB/FAVÖK (Sekt.)", False, "dusuk"),
    ("FCF Verimi %", "FCF Ver. (Sekt.)", False, "yuksek"),
]

# Aykırı değer sınırları: payda sıfıra yaklaşınca mekanik olarak patlayan
# oranlar (ör. net kârı ~0 şirkette F/K 620). Sınırı aşan değer ekranda
# görünür ama medyan / Sektör Skoru / Yıldız hesaplarına katılmaz.
AYKIRI_SINIRLAR = {
    "F/K (FKO)": 200,
    "PD/DD": 100,
    "FD/FAVÖK": 200,
    "FD/Gelir": 100,
    "PEG": 50,
    "CFO/Net Kâr": 20,
    "Net Borç/FAVÖK": 50,
    "FCF Verimi %": 100,
}

# Özet sekmesinde gösterilecek kolonlar: her oranın yanında sektör medyanı
OZET_ADLARI = (
    ["Hisse", "Şirket", "Yıldız", "Sektör Skoru", "Sektör",
     "Piyasa Değeri", "7G Değişim %", "30G Değişim %",
     "FAVÖK (TTM)", "Son Bilanço", "Sonraki Bilanço"]
    + [ad for oran, sekt, _, _ in OZET_ORANLAR for ad in (oran, sekt)]
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

        # Bilanço tarihleri: unix timestamp -> tarih. 7 gün içinde bilanço
        # açıklayacaklara ⏰ rozeti (oranlar yakında değişecek uyarısı).
        bugun = pd.Timestamp.now().normalize()
        sonraki_ts = pd.to_datetime(
            df["Sonraki Bilanço"], unit="s", errors="coerce"
        ).dt.normalize()
        yakin = sonraki_ts.between(bugun, bugun + pd.Timedelta(days=7))
        for kolon in ("Son Bilanço", "Sonraki Bilanço"):
            df[kolon] = pd.to_datetime(
                df[kolon], unit="s", errors="coerce"
            ).dt.strftime("%Y-%m-%d")
        df.loc[yakin, "Sonraki Bilanço"] = (
            "⏰ " + df.loc[yakin, "Sonraki Bilanço"]
        )

        yakin_sayi = int(yakin.sum())
        if yakin_sayi:
            yakin_hisseler = ", ".join(
                df.loc[yakin, "Hisse"].astype(str).sort_values()
            )
            st.info(
                f"⏰ Önümüzdeki 7 günde bilanço açıklayacak "
                f"**{yakin_sayi} şirket** var: **{yakin_hisseler}** — "
                f"bu şirketlerin oranları, Yıldız ve Sektör Skoru "
                f"bilanço sonrası değişebilir."
            )

        # Türetilmiş oran: kârın nakde dönüşümü (sadece pozitif net kârda anlamlı)
        df["CFO/Net Kâr"] = (
            df["Faaliyet Nakit Akışı (TTM)"] / df["Net Kar (TTM)"]
        ).where(df["Net Kar (TTM)"] > 0).round(2)

        # Türetilmiş oran: Net Borç/FAVÖK (FAVÖK <= 0 ise anlamsız -> boş)
        df["Net Borç/FAVÖK"] = (
            df["Net Borç"] / df["FAVÖK (TTM)"]
        ).where(df["FAVÖK (TTM)"] > 0).round(2)

        # Türetilmiş oran: FCF Verimi = Serbest Nakit Akışı / Piyasa Değeri.
        # Negatif değerler anlamlıdır (yatırım fazı / nakit yakma) ve
        # medyana katılır.
        df["FCF Verimi %"] = (
            100 * df["Serbest Nakit Akışı (TTM)"] / df["Piyasa Değeri"]
        ).where(df["Piyasa Değeri"] > 0).round(2)

        # Hesaplarda kullanılacak temiz değer: pozitiflik şartı + aykırı sınır.
        # Ekrandaki ham değer değişmez; sadece hesap dışı kalır.
        def oran_temiz(oran: str, sadece_poz: bool) -> pd.Series:
            deger = df[oran].where(df[oran] > 0) if sadece_poz else df[oran]
            sinir = AYKIRI_SINIRLAR.get(oran)
            if sinir is not None:
                deger = deger.where(deger.abs() <= sinir)
            return deger

        # Her oran için sektör medyanı kolonu.
        # sadece_pozitif=True olanlarda negatifler medyan dışı bırakılır;
        # NaN'lar (ör. temettü vermeyenler) medyana zaten katılmaz.
        # Sektörde geçerli verisi olan en az 3 şirket yoksa medyan boş
        # bırakılır (tek şirketli sektörde medyan = kendisi olurdu).
        for oran, sekt_ad, sadece_poz, _ in OZET_ORANLAR:
            deger = oran_temiz(oran, sadece_poz)
            df[sekt_ad] = deger.groupby(df["Sektör"]).transform(
                lambda s: s.median() if s.count() >= 3 else float("nan")
            ).round(2)

        # Sektör Skoru (0-100): her oran kendi sektör medyanıyla doğru
        # yönde kıyaslanır (düşük-iyi / yüksek-iyi). Verisi eksik oran
        # sayılmaz; skor = kazanılan / geçerli oran sayısı x 100.
        # En az 3 geçerli oran yoksa skor boş bırakılır.
        skor_kazanilan = pd.Series(0, index=df.index)
        skor_gecerli = pd.Series(0, index=df.index)
        for oran, sekt_ad, sadece_poz, yon in OZET_ORANLAR:
            deger = oran_temiz(oran, sadece_poz)
            gecerli_o = deger.notna() & df[sekt_ad].notna()
            if yon == "dusuk":
                kazandi = deger <= df[sekt_ad]
            else:
                kazandi = deger >= df[sekt_ad]
            skor_kazanilan += (kazandi & gecerli_o).astype(int)
            skor_gecerli += gecerli_o.astype(int)
        df["Sektör Skoru"] = (
            (100 * skor_kazanilan / skor_gecerli.where(skor_gecerli >= 3))
            .round().astype("Int64")
        )

        # Yıldız: 7 kriter, her sağlanan kriter 1 yıldız (★ 0-7).
        # Kalite kriterleri mutlak eşik, değerleme sektör-göreli.
        # En az 4 geçerli kriter yoksa yıldız verilmez ("—").
        cfo_nk = oran_temiz("CFO/Net Kâr", False)
        fcf_ver = oran_temiz("FCF Verimi %", False)
        kriter = pd.DataFrame(index=df.index)
        kriter["roe"] = df["ROE %"] >= 15
        kriter["roic"] = df["ROIC %"] >= 10
        kriter["nakit"] = cfo_nk >= 0.8
        kriter["fcf"] = fcf_ver > 0
        kriter["borc"] = df["Borç / Özkaynak"] <= 1
        kriter["buyume"] = df["EPS Büyüme YY % (TTM)"] > 0
        fk_poz = oran_temiz("F/K (FKO)", True)
        fd_poz = oran_temiz("FD/FAVÖK", True)
        kriter["deger"] = (
            (fk_poz <= df["F/K (Sekt.)"]) & (fd_poz <= df["FD/FAVÖK (Sekt.)"])
        )
        gecerli = pd.DataFrame({
            "roe": df["ROE %"].notna(),
            "roic": df["ROIC %"].notna(),
            "nakit": cfo_nk.notna(),
            "fcf": fcf_ver.notna(),
            "borc": df["Borç / Özkaynak"].notna(),
            "buyume": df["EPS Büyüme YY % (TTM)"].notna(),
            "deger": (
                fk_poz.notna() & fd_poz.notna()
                & df["F/K (Sekt.)"].notna() & df["FD/FAVÖK (Sekt.)"].notna()
            ),
        })
        puan = (kriter & gecerli).sum(axis=1)
        gecerli_sayisi = gecerli.sum(axis=1)
        yildiz_sayi = puan.where(gecerli_sayisi >= 4)
        df["Yıldız"] = yildiz_sayi.map(
            lambda s: "—" if pd.isna(s) else "★" * int(s) + "☆" * (7 - int(s))
        )

        ortak_adlar = [k[1] for k in ORTAK_KOLONLAR]
        df_ozet = df[OZET_ADLARI]
        df_gelir = df[ortak_adlar + [k[1] for k in GELIR_KOLONLARI]]
        df_bilanco = df[ortak_adlar + [k[1] for k in BILANCO_KOLONLARI]]
        df_nakit = df[ortak_adlar + [k[1] for k in NAKIT_KOLONLARI]]

        sek_ozet, sek2, sek3, sek4 = st.tabs(
            ["Özet", "Gelir Tablosu", "Bilanço", "Nakit Akışı"]
        )
        with sek_ozet:
            st.dataframe(df_ozet, use_container_width=True)
        with sek2:
            st.dataframe(df_gelir, use_container_width=True)
        with sek3:
            st.dataframe(df_bilanco, use_container_width=True)
        with sek4:
            st.dataframe(df_nakit, use_container_width=True)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df_ozet.to_excel(writer, index=False, sheet_name="Özet")
            df_gelir.to_excel(writer, index=False, sheet_name="Gelir Tablosu")
            df_bilanco.to_excel(writer, index=False, sheet_name="Bilanço")
            df_nakit.to_excel(writer, index=False, sheet_name="Nakit Akışı")
        st.download_button(
            label="📥 Excel Dosyasını İndir",
            data=buffer.getvalue(),
            file_name=f"{market}_Finansallar.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        with st.expander("📖 Yıldız ve Sektör Skoru Nasıl Çalışır?"):
            st.markdown("""
*(Oranların tek tek anlamı için alttaki "Tüm Oranlar" bölümüne bak.)*

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

#### Yıldız nasıl hesaplanıyor? (★ 0–7)

Her sağlanan kriter 1 yıldız:

1. ROE ≥ %15 (kalite)
2. ROIC ≥ %10 (kaldıraçsız kalite)
3. CFO/Net Kâr ≥ 0.8 (kâr nakde dönüşüyor)
4. FCF Verimi > 0 (yatırımlar sonrası da nakit üretiyor)
5. Borç/Özkaynak ≤ 1 (bilanço sağlığı)
6. EPS büyümesi (YY) > 0 (kâr erimiyor — değer tuzağı freni)
7. F/K **ve** FD/FAVÖK kendi sektör medyanının altında (göreli ucuzluk)

Verisi eksik kriter değerlendirme dışı bırakılır ve o yıldız
kazanılamaz (ör. bankalarda FD/FAVÖK yoktur — en fazla 6 yıldız
alabilirler). En az 4 geçerli kriteri olmayan şirkete yıldız
verilmez ("—"). ★★★★★★★ "al" demek değildir; kalite + nakit +
büyüme + ucuzluk kombinasyonunun mekanik bir özetidir. Yatırım
tavsiyesi değildir. Not: FCF kriteri sermaye-yoğun sektörlerde
(havayolu, enerji, telekom) yatırım fazındaki sağlıklı şirketlere
de yıldız kaybettirebilir — FCF Ver. (Sekt.) kolonuyla birlikte oku.

#### Sektör Skoru nasıl hesaplanıyor? (0–100)

Yıldız **mutlak** kaliteyi ölçer ("iyi şirket mi?"), Sektör Skoru
**göreli** konumu ölçer ("sektöründe nerede?"). Özet'teki 14 oranın
her biri kendi sektör medyanıyla doğru yönde kıyaslanır:

- **Düşük iyi:** F/K, PD/DD, FD/FAVÖK, FD/Gelir, PEG, Net Borç/FAVÖK
- **Yüksek iyi:** ROE, ROIC, ROA, CFO/Net Kâr, Cari, Asit-Test, Temettü,
  FCF Verimi

Skor = medyanı geçen oran sayısı / geçerli oran sayısı × 100.
Verisi eksik oran hesaba katılmaz.

Birlikte okuma:

| Yıldız | Skor | Yorum |
|---|---|---|
| ★★★★★★★ | 85 | Kaliteli **ve** sektörünün yıldızı |
| ★★★☆☆☆☆ | 90 | Sektörünün en iyisi ama sektör zayıf (tuzak olabilir) |
| ★★★★★☆☆ | 40 | İyi şirket ama sektöründe daha cazibi var |

#### Güvenlik kuralları

- **Aykırı değer filtresi:** Payda sıfıra yaklaşınca patlayan oranlar
  (ör. F/K > 200, CFO/Net Kâr > 20) ekranda görünür ama medyan, Skor
  ve Yıldız hesaplarına katılmaz.
- **En az 3 şirket:** Sektörde geçerli verisi olan 3'ten az şirket
  varsa o oranın sektör medyanı boş bırakılır (tek şirketli sektörde
  medyan şirketin kendisi olurdu — skor otomatik şişerdi).
- **En az 4 kriter / 3 oran:** 4'ten az geçerli kriteri olan şirkete
  yıldız verilmez ("—"); 3'ten az geçerli oranı olana Sektör Skoru
  verilmez. Bir-iki kriterden yüksek yıldız çıkmasını engeller.
""")

        with st.expander("📚 Tüm Oranlar: Ne Anlama Gelir, Yüksek mi Düşük mü İyi?"):
            st.markdown("""
#### Değerleme oranları — 🔽 düşük iyi

| Oran | Formül (özü) | Anlamı | İyi olan |
|---|---|---|---|
| **F/K (FKO)** | Fiyat / Hisse başı kâr | 1 birim kâr için kaç birim ödüyorsun | 🔽 Düşük — ama sektörüne göre; negatifse (zarar) anlamsız |
| **PD/DD** | Piyasa değeri / Özkaynak | Özkaynağın kaç katını ödüyorsun | 🔽 Düşük — ROE yüksekse prim normaldir |
| **FD/FAVÖK** | (Piyasa değeri + Net borç) / FAVÖK | Borç dahil şirket fiyatı / faaliyet kârı | 🔽 Düşük — F/K'dan farkı borcu da katması; bankalarda hesaplanmaz |
| **FD/Gelir** | Firma değeri / Satışlar | Satışların kaç katını ödüyorsun | 🔽 Düşük — zarar eden şirketlerde de çalışır |
| **PEG** | F/K / Kâr büyüme hızı | Fiyat, büyümeye göre pahalı mı | 🔽 Düşük — ~1 makul, < 1 büyümeye göre ucuz; negatif büyümede anlamsız |

#### Kârlılık oranları — 🔼 yüksek iyi

| Oran | Formül (özü) | Anlamı | İyi olan |
|---|---|---|---|
| **ROE %** | Net kâr / Özkaynak | Ortağın parası ne kadar kâr üretiyor | 🔼 Yüksek (≥ %15) — ama borçla şişirilebilir, ROIC ile birlikte oku |
| **ROIC %** | Faaliyet kârı / Yatırılan sermaye | Borç + özkaynak toplamının kârlılığı | 🔼 Yüksek (≥ %10) — ROE'nin kaldıraçsız, daha dürüst hali |
| **ROA %** | Net kâr / Toplam varlıklar | Tüm varlıkların kârlılığı | 🔼 Yüksek — kaldıraçtan en az etkilenen kârlılık ölçüsü |

#### Kâr kalitesi ve borç — yönü karışık

| Oran | Formül (özü) | Anlamı | İyi olan |
|---|---|---|---|
| **CFO/Net Kâr** | Faaliyet nakit akışı / Net kâr | Kâr gerçekten kasaya giriyor mu | 🔼 Yüksek (≥ 0.8) — sürekli < 1 ise kâr kağıt üzerinde olabilir |
| **FCF Verimi %** | Serbest nakit akışı / Piyasa değeri | Yatırımlar sonrası kalan nakdin fiyata oranı | 🔼 Yüksek — negatifse şirket nakit yakıyor; sermaye-yoğun sektörlerde yapısal olarak düşüktür, sektörüne göre oku |
| **Net Borç/FAVÖK** | (Borç − Nakit) / FAVÖK | Borç kaç yıllık faaliyet kârı eder | 🔽 Düşük (≤ 2-3) — **negatif = net nakit**, en sağlamı |
| **Borç/Özkaynak** | Toplam borç / Özkaynak | Bilanço kaldıracı | 🔽 Düşük (≤ 1) — yüksekse ROE'ye güvenme |

#### Likidite oranları — 🔼 yüksek iyi

| Oran | Formül (özü) | Anlamı | İyi olan |
|---|---|---|---|
| **Cari Oran** | Dönen varlık / Kısa vadeli borç | 1 yıl içindeki borç ödeme gücü | 🔼 Yüksek (≥ 1) — ama çok yüksekse para atıl duruyor olabilir |
| **Asit-Test** | (Dönen varlık − Stok) / KV borç | Stok satmadan borç ödeme gücü | 🔼 Yüksek (≥ 1) — Cari'nin muhafazakâr hali |

#### Temettü — 🔼 yüksek iyi (şartlı)

| Oran | Formül (özü) | Anlamı | İyi olan |
|---|---|---|---|
| **Tem. Verimi %** | Yıllık temettü / Fiyat | Fiyata göre nakit getiri | 🔼 Yüksek — ama aşırı yüksekse (≥ %15) sürdürülemez olabilir veya fiyat çökmüştür; boşsa temettü vermiyor |

#### Genel uyarılar

- Hiçbir oran tek başına karar verdirmez; **aynı sektördeki (Sekt.)
  medyanıyla** kıyasla.
- Sektörler yapısal olarak farklıdır: bankada PD/DD ~1 normalken
  yazılımda 5+ olabilir; FD/FAVÖK finans şirketlerinde hesaplanmaz.
- Uç değerler (F/K 500 gibi) genelde şirketin harika olduğunu değil,
  paydanın (kârın) sıfıra yaklaştığını gösterir.
""")
