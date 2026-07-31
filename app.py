import streamlit as st
import requests
import pandas as pd
import io
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="Temel Analiz", page_icon="📊", layout="wide")

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
}

_KULLANILMAYAN_PIYASALAR = {
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
    ("close", "Son Fiyat"),
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
     "Piyasa Değeri", "Son Fiyat", "7G Değişim %", "30G Değişim %",
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
    start, adim = 0, 500
    while True:
        payload = {
            "columns": api_alanlari,
            "markets": [market],
            "filter": filtreler,
            "range": [start, start + adim],
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
        if len(data) < adim:
            break
        start += adim
    df_son = pd.DataFrame(all_rows, columns=gosterim_adlari)
    # Olası çift kolon adlarını temizle
    df_son = df_son.loc[:, ~df_son.columns.duplicated()]
    return df_son, son_hata


st.title("📊 Temel Analiz")


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
            lambda s: "—" if pd.isna(s) else "⭐" * int(s) + "☆" * (7 - int(s))
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


# ============================================================
#  BÖLÜM 2 — TEKNİK ANALİZ
# ============================================================
st.divider()
st.header("📈 Teknik Analiz")
st.caption("Yukarıda temel analizle firma seç, solda ticker'ını yazıp Analiz Et'e bas. "
           "YATIRIM TAVSİYESİ İÇERMEZ.")

# ============================================================
# SESSION STATE VARSAYILANLARI
# ============================================================
_defaults = {
    "sma_short":     20,
    "sma_long":      200,
    "rsi_period":    14,
    "rsi_lower":     30,
    "rsi_upper":     70,
    "rsi_trend_period": 200,
    "bb_period":     20,
    "bb_std":        2.0,
    "macd_fast":     12,
    "macd_slow":     26,
    "macd_signal":   9,
    "adx_period":    14,
    "adx_threshold": 25,
    "st_period":     10,
    "st_multiplier": 3.0,
    "lrc_period":    50,
    "lrc_std_mult":  2.0,
    "wt_n1":         10,
    "wt_n2":         21,
    "obv_short":     10,
    "obv_long":      30,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================
# 2. YAN PANEL
# ============================================================
with st.sidebar:
    st.header("⚙️ Teknik Analiz Ayarları")
    ta_ticker = st.text_input("Ticker Sembolü (örn. ASELS.IS, AAPL, GC=F):", "")
    if st.button("🔍 Analiz Et", type="primary", use_container_width=True):
        st.session_state["ta_aktif"] = True
        st.session_state["ta_ticker_secili"] = ta_ticker
    # Buton bir kez basıldıktan sonra slider değişikliklerinde de analiz açık kalsın.
    ta_calistir = st.session_state.get("ta_aktif", False)
    ta_ticker = st.session_state.get("ta_ticker_secili", ta_ticker)

    period = st.selectbox(
        "Toplam Veri Süresi (Period):",
        options=["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
        index=6,
    )

    if period in ["1d", "5d"]:
        interval_options = ["1m", "2m", "5m", "15m", "30m", "60m", "1h", "1d"]
        default_int_idx = 0
    elif period == "1mo":
        interval_options = ["2m", "5m", "15m", "30m", "60m", "1h", "4h", "1d"]
        default_int_idx = 6
    else:
        interval_options = ["1h", "4h", "8h", "1d", "1wk", "1mo"]
        default_int_idx = 3

    interval = st.selectbox(
        "Mum Aralığı (Interval):", options=interval_options, index=default_int_idx
    )
    st.write("---")
    chart_type = st.radio("📊 Grafik Tipi:", ["Mum", "Çizgi"], horizontal=True)
    show_vp = st.checkbox("Fiyat Hacimlerini Göster", value=True)

    st.write("---")
    st.subheader("Sabit Parametreler")
    ss = st.session_state
    sma_short        = st.slider("SMA Kısa Periyot:",        5,   50,  value=ss["sma_short"])
    sma_long         = st.slider("SMA Uzun Periyot:",        50,  300, value=ss["sma_long"])
    rsi_period       = st.slider("RSI Periyodu:",            7,   21,  value=ss["rsi_period"])
    rsi_lower        = st.slider("RSI Alt Eşik:",            20,  40,  value=ss["rsi_lower"])
    rsi_upper        = st.slider("RSI Üst Eşik:",            60,  80,  value=ss["rsi_upper"])
    rsi_ma_period    = st.slider("RSI MA Periyodu:",         5,   50,  14)
    bb_period        = st.slider("BB Periyodu:",             10,  50,  value=ss["bb_period"])
    bb_std           = st.slider("BB Standart Sapma:",       1.0, 3.0, value=ss["bb_std"],        step=0.5)
    macd_fast        = st.slider("MACD Hızlı EMA:",          5,   20,  value=ss["macd_fast"])
    macd_slow        = st.slider("MACD Yavaş EMA:",          15,  40,  value=ss["macd_slow"])
    macd_signal      = st.slider("MACD Sinyal:",             5,   15,  value=ss["macd_signal"])
    obv_short        = st.slider("OBV Kısa SMA:",            5,   20,  value=ss["obv_short"])
    obv_long         = st.slider("OBV Uzun SMA:",            15,  50,  value=ss["obv_long"])
    adx_period       = st.slider("ADX Periyodu:",            7,   30,  value=ss["adx_period"])
    adx_threshold    = st.slider("ADX Trend Eşiği:",        15,  35,  value=ss["adx_threshold"])
    atr_period       = st.slider("ATR Periyodu:",            7,   30,  14)
    stoch_rsi_period = st.slider("Stoch RSI Periyodu:",      7,   21,  14)
    stoch_d_period   = st.slider("Stoch RSI %D Smoothing:",  2,   5,   3)
    stoch_lower      = st.slider("Stoch RSI Alt Eşik:",      5,   30,  20)
    stoch_upper      = st.slider("Stoch RSI Üst Eşik:",      70,  95,  80)
    ichi_tenkan      = st.slider("Tenkan-sen:",              5,   20,  9,
        help="⚠️ Ichimoku'da klasik değer 9'dur (Hosoda 1930'lar). Değiştirmek önerilmez — "
             "9-26-52 Schelling noktasıdır, dünya çapında bu değerler izlenir.")
    ichi_kijun       = st.slider("Kijun-sen:",               20,  40,  26,
        help="⚠️ Ichimoku'da klasik değer 26'dır. Değiştirmek önerilmez.")
    ichi_senkou_b    = st.slider("Senkou Span B:",           40,  65,  52,
        help="⚠️ Ichimoku'da klasik değer 52'dir. Değiştirmek önerilmez.")
    st_period        = st.slider("SuperTrend ATR Periyodu:", 5,   20,  value=ss["st_period"])
    st_multiplier    = st.slider("SuperTrend Çarpan:",       1.0, 5.0, value=ss["st_multiplier"], step=0.5)
    kama_period      = st.slider("KAMA Etkinlik Periyodu:",  5,   20,  10)
    kama_fast        = st.slider("KAMA Hızlı EMA:",          2,   5,   2)
    kama_slow        = st.slider("KAMA Yavaş EMA:",          20,  40,  30)
    lrc_period       = st.slider("LRC Periyodu:",            20,  100, value=ss["lrc_period"])
    lrc_std_mult     = st.slider("LRC Standart Sapma:",      1.0, 3.0, value=ss["lrc_std_mult"],  step=0.5)
    vwap_band_pct    = st.slider("VWAP Nötr Bant (%):",     0.0, 1.0, 0.1, step=0.05)

    st.write("---")
    st.subheader("📐 Fibonacci Ayarları")
    fib_lookback = st.slider("Fibonacci Lookback (bar):", 20, 300, 100)

    st.write("---")
    st.subheader("〰️ WaveTrend Ayarları")
    wt_n1 = st.slider("WaveTrend Kanal (n1):",    5,  20,  value=ss["wt_n1"])
    wt_n2 = st.slider("WaveTrend Ortalama (n2):", 10, 40,  value=ss["wt_n2"])
    wt_ob = st.slider("WaveTrend Aşırı Alım:",    40, 80,  60)
    wt_os = st.slider("WaveTrend Aşırı Satım:",  -80, -20, -60)

    st.write("---")
    st.subheader("🔀 Divergence Ayarları")
    div_window = st.slider("Divergence Pivot Pencere:", 3, 10, 5)

    # ── Destek/Direnç ve Trend Çizgisi Ayarları ───────────────
    st.write("---")
    st.subheader("📊 Destek / Direnç Ayarları")
    swing_window  = st.slider("S/R Pivot Pencere:",    3,  20, 10,
        help="Tepe/dip tespiti için her yönde bakılacak bar sayısı")
    swing_touches = st.slider("Min. Dokunuş Sayısı:", 1,   5,  1,
        help="1 = tek pivotlu seviyeler de gösterilir (daha fazla çizgi, zayıf güç)")
    swing_atr_k   = st.slider("ATR Tolerans Çarpanı:", 0.2, 2.0, 0.5, step=0.1,
        help="Seviye birleştirme toleransı = bu değer × ATR / fiyat. "
             "Volatil enstrümanlarda yükselt, sakin enstrümanlarda düşür.")
    swing_tol     = 0.003  # fallback (ATR yoksa kullanılır)

    st.write("---")
    st.subheader("📐 Trend Çizgisi Ayarları")
    tl_pivot_window = st.slider("TL Pivot Pencere:",       5,  20,  10,
        help="Trend çizgisi pivot tespiti için pencere genişliği")
    tl_max_lines    = st.slider("Max Çizgi Sayısı:",       1,   5,   3,
        help="Her yönde (destek/direnç) gösterilecek maksimum çizgi")
    tl_tolerance    = st.slider("TL Tolerans (%):",        0.3, 2.0, 1.2, step=0.1,
        help="Pivotun çizgiye dokundu sayılması için fiyat toleransı") / 100
    tl_show_channel = st.checkbox("Kanalları Göster", value=True,
        help="Paralel destek+direnç kanallarını dolgulu göster")
    # ──────────────────────────────────────────────────────────

    st.write("---")
    st.info("İpucu: 1 dakikalık analizler için Periyot: 5d, Mum Aralığı: 1m seçiniz.")


# ============================================================
# 4. YARDIMCI FONKSİYONLAR
# ============================================================
def safe_scalar(value):
    if isinstance(value, (pd.Series, np.ndarray)):
        return float(value.iloc[0]) if len(value) > 0 else np.nan
    try:
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        unique_tickers = df.columns.get_level_values(1).unique()
        if len(unique_tickers) <= 1:
            df.columns = df.columns.get_level_values(0)
        else:
            df.columns = [f"{col[1]}_{col[0]}" for col in df.columns]
    return df


def calc_adx(high, low, close, period=14):
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low  - close.shift(1)).abs()
    tr  = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    up_move   = high - high.shift(1)
    down_move = low.shift(1) - low
    plus_dm   = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm  = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    plus_dm   = pd.Series(plus_dm,  index=high.index, dtype=float)
    minus_dm  = pd.Series(minus_dm, index=high.index, dtype=float)
    alpha     = 1.0 / period
    atr_s     = tr.ewm(alpha=alpha, min_periods=period, adjust=False).mean()
    sp        = plus_dm.ewm(alpha=alpha, min_periods=period, adjust=False).mean()
    sm        = minus_dm.ewm(alpha=alpha, min_periods=period, adjust=False).mean()
    plus_di   = 100 * (sp / atr_s.replace(0, np.nan))
    minus_di  = 100 * (sm / atr_s.replace(0, np.nan))
    dx        = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan))
    adx       = dx.ewm(alpha=alpha, min_periods=period, adjust=False).mean()
    return adx, plus_di, minus_di


def calc_kama(close, period=10, fast=2, slow=30):
    """Kaufman Adaptive Moving Average — KAMA + Efficiency Ratio.
    ER (0..1): yön etkinliği. 1=mükemmel trend, 0=tam gürültü.
    Returns (kama_series, er_series).
    """
    ca   = close.values.astype(float)
    kama = np.full(len(ca), np.nan)
    er_a = np.full(len(ca), np.nan)
    kama[period - 1] = ca[period - 1]
    fsc = 2.0 / (fast + 1)
    ssc = 2.0 / (slow + 1)
    for i in range(period, len(ca)):
        direction  = abs(ca[i] - ca[i - period])
        volatility = np.sum(np.abs(np.diff(ca[i - period:i + 1])))
        er  = 0.0 if volatility == 0 else direction / volatility
        er_a[i] = er
        sc  = (er * (fsc - ssc) + ssc) ** 2
        kama[i] = kama[i - 1] + sc * (ca[i] - kama[i - 1])
    return pd.Series(kama, index=close.index), pd.Series(er_a, index=close.index)


def calc_supertrend(high, low, close, period=10, multiplier=3.0):
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low  - close.shift(1)).abs()
    tr  = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    hl2 = (high + low) / 2
    ub  = (hl2 + multiplier * atr).values.astype(float)
    lb  = (hl2 - multiplier * atr).values.astype(float)
    ca  = close.values.astype(float)
    ubf = ub.copy()
    lbf = lb.copy()
    direction  = np.ones(len(ca), dtype=float)
    supertrend = np.full(len(ca), np.nan)
    for i in range(1, len(ca)):
        if np.isnan(ubf[i-1]) or np.isnan(lbf[i-1]):
            ubf[i] = ub[i]
            lbf[i] = lb[i]
        else:
            ubf[i] = ub[i] if (ub[i] < ubf[i-1] or ca[i-1] > ubf[i-1]) else ubf[i-1]
            lbf[i] = lb[i] if (lb[i] > lbf[i-1] or ca[i-1] < lbf[i-1]) else lbf[i-1]
        if   ca[i] > ubf[i-1]: direction[i] = 1
        elif ca[i] < lbf[i-1]: direction[i] = -1
        else:                   direction[i] = direction[i-1]
        supertrend[i] = lbf[i] if direction[i] == 1 else ubf[i]
    return (pd.Series(supertrend, index=close.index), pd.Series(direction, index=close.index),
            pd.Series(lbf, index=close.index),        pd.Series(ubf, index=close.index))


def calc_linear_regression_channel(close, period=50, std_mult=2.0):
    """Linear Regression Channel — Raff 1996.

    Her bar için son `period` kapanışına OLS regresyon uygulanır.
    Returns (mid, upper, lower, slope, r2):
      - mid    : son tahmin (regresyon çizgisinin son noktası)
      - upper  : mid + std_mult × rezidüel_std
      - lower  : mid - std_mult × rezidüel_std
      - slope  : regresyon eğimi (birim: fiyat/bar)
      - r2     : R² (0..1) — regresyonun veriye uyum kalitesi
    """
    n = len(close)
    mid   = np.full(n, np.nan)
    upper = np.full(n, np.nan)
    lower = np.full(n, np.nan)
    slope_a = np.full(n, np.nan)
    r2_a    = np.full(n, np.nan)
    for i in range(period - 1, n):
        y = close.values[i - period + 1:i + 1].astype(float)
        x = np.arange(period)
        sl, ic = np.polyfit(x, y, 1)
        yp  = sl * x + ic
        resid = y - yp
        std = np.std(resid)
        mid[i]   = yp[-1]
        upper[i] = yp[-1] + std_mult * std
        lower[i] = yp[-1] - std_mult * std
        slope_a[i] = sl
        # R² = 1 - SS_res / SS_tot
        ss_tot = np.sum((y - y.mean()) ** 2)
        r2_a[i] = 1.0 - (np.sum(resid ** 2) / ss_tot) if ss_tot > 0 else np.nan
    return (pd.Series(mid, index=close.index),  pd.Series(upper, index=close.index),
            pd.Series(lower, index=close.index), pd.Series(slope_a, index=close.index),
            pd.Series(r2_a, index=close.index))


def calc_vwap_daily(high, low, close, volume):
    tp = (high + low + close) / 3
    dk = pd.Series(close.index.date, index=close.index)
    return (tp * volume).groupby(dk).cumsum() / volume.groupby(dk).cumsum().replace(0, np.nan)


# ── YENİ: Swing Destek/Direnç ─────────────────────────────────────────────────
def find_swing_levels(high, low, close, window=10, min_touches=2, tolerance=0.003,
                      atr_series=None, atr_k=0.5):
    """
    Swing High/Low bazlı otomatik destek/direnç tespiti.
    - atr_series verilirse tolerans = atr_k * ATR / fiyat (dinamik, volatiliteye uyumlu)
    - Aksi halde sabit 'tolerance' yüzdesi kullanılır (geriye uyumluluk)
    - Her seviyenin 'broken' alanı vardır: son kapanış seviyeyi kırmışsa True
    """
    n      = len(close)
    levels = []

    for i in range(window, n - window):
        if high.iloc[i] == high.iloc[i - window: i + window + 1].max():
            levels.append(("R", float(high.iloc[i]), i))
        if low.iloc[i] == low.iloc[i - window: i + window + 1].min():
            levels.append(("S", float(low.iloc[i]), i))

    # Dinamik tolerans: her pivot için kendi ATR'sine göre yüzde tolerans
    def _tol_for(price, bar_idx):
        if atr_series is not None and bar_idx < len(atr_series):
            atr_val = float(atr_series.iloc[bar_idx]) if hasattr(atr_series, "iloc") else float(atr_series[bar_idx])
            if not np.isnan(atr_val) and price > 0:
                return max(atr_k * atr_val / price, 0.0005)  # minimum %0.05 taban
        return tolerance

    merged = []
    used   = set()
    for idx, (typ, price, bar) in enumerate(levels):
        if idx in used:
            continue
        tol         = _tol_for(price, bar)
        touches     = [price]
        touch_bars  = [bar]
        for jdx, (typ2, price2, bar2) in enumerate(levels):
            if jdx != idx and jdx not in used:
                if abs(price2 - price) / price < tol:
                    touches.append(price2)
                    touch_bars.append(bar2)
                    used.add(jdx)
        used.add(idx)
        avg_price  = float(np.mean(touches))
        last_touch = max(touch_bars)

        # ── Break detection & role reversal ──
        # Fiyat bir direnci kırıp yukarı geçerse o seviye artık "destek"
        # Fiyat bir desteği kırıp aşağı inerse o seviye artık "direnç"
        last_close = float(close.iloc[-1])
        tol_now = _tol_for(avg_price, n - 1)
        if typ == "R":
            if last_close > avg_price * (1 + tol_now):
                typ = "S"           # direnç kırıldı, destek oldu
                broken = False      # yeni rolüyle aktif
            else:
                broken = False
        else:  # "S"
            if last_close < avg_price * (1 - tol_now):
                typ = "R"           # destek kırıldı, direnç oldu
                broken = False
            else:
                broken = False

        # ── Recency: son dokunuşun yakınlığı (0-1, yeni olan yüksek) ──
        recency = last_touch / max(n - 1, 1)

        # ── Güç skoru: dokunuş sayısı × recency ağırlığı ──
        strength = len(touches) * (0.5 + 0.5 * recency)

        merged.append({
            "type":       typ,
            "price":      avg_price,
            "touches":    len(touches),
            "last_touch": last_touch,
            "broken":     broken,
            "strength":   strength,
        })

    merged = [m for m in merged if m["touches"] >= min_touches]
    merged = sorted(merged, key=lambda x: -x["strength"])[:10]
    return merged
# ──────────────────────────────────────────────────────────────────────────────


# ── YENİ: Diyagonal Trend Çizgileri ───────────────────────────────────────────
def find_trendlines(high, low, close, pivot_window=10, max_lines=3, tolerance=0.012):
    """
    Gelişmiş otomatik trend çizgisi tespiti.
    - Swing high/low pivotları tespit edilir
    - Her ikili kombinasyon için çizgi skoru hesaplanır
       (dokunuş sayısı + yenilik + ihlal cezası)
    - Benzer eğimli çizgiler tekilleştirilir
    - Paralel destek+direnç çiftleri kanal olarak işaretlenir
    Döndürür: (lines, channels)
      lines   : list of dict  {type, x0,y0,x1,y1,slope,touches,last_touch}
      channels: list of dict  {support, resistance}
    """
    n     = len(close)
    dates = close.index

    # Pivot tespiti
    pivot_highs, pivot_lows = [], []
    for i in range(pivot_window, n - pivot_window):
        if high.iloc[i] == high.iloc[i - pivot_window: i + pivot_window + 1].max():
            pivot_highs.append((i, float(high.iloc[i])))
        if low.iloc[i] == low.iloc[i - pivot_window: i + pivot_window + 1].min():
            pivot_lows.append((i, float(low.iloc[i])))

    def _score_line(p1, p2, pivots, violation_series):
        x1, y1 = p1;  x2, y2 = p2
        if x2 == x1: return 0, []
        slope     = (y2 - y1) / (x2 - x1)
        intercept = y1 - slope * x1
        touches   = []
        violations = 0
        for xi in range(min(x1, x2), n):
            y_line = slope * xi + intercept
            y_act  = float(violation_series.iloc[xi])
            rel    = (y_act - y_line) / (abs(y_line) + 1e-9)
            # Dokunuş: pivot bu çizgiye yeterince yakın mı?
            for (px, py) in pivots:
                if px == xi and abs(py - y_line) / (abs(y_line) + 1e-9) < tolerance:
                    touches.append((xi, py))
            # İhlal: fiyat destek/direnç çizgisini kırdı mı?
            if slope >= 0 and rel < -tolerance * 3:   violations += 1
            if slope < 0  and rel >  tolerance * 3:   violations += 1
        score = len(touches) - violations * 0.5
        return score, touches

    def _best_lines(pivots, violation_series, line_type):
        if len(pivots) < 2:
            return []
        candidates = []
        for i in range(len(pivots)):
            for j in range(i + 1, len(pivots)):
                p1, p2 = pivots[i], pivots[j]
                score, touches = _score_line(p1, p2, pivots, violation_series)
                if score < 1.5 or len(touches) < 2:
                    continue
                x1, y1 = p1;  x2, y2 = p2
                slope     = (y2 - y1) / (x2 - x1)
                intercept = y1 - slope * x1
                y_end     = slope * (n - 1) + intercept
                last_bar  = max(t[0] for t in touches)
                candidates.append({
                    "type":       line_type,
                    "x0":         x1,         "y0": y1,
                    "x1":         n - 1,      "y1": y_end,
                    "slope":      slope,
                    "intercept":  intercept,
                    "touches":    len(touches),
                    "last_touch": last_bar,
                    "score":      score,
                })
        # Sırala: skor desc, yenilik desc
        candidates.sort(key=lambda c: (-c["score"], -c["last_touch"]))
        # Benzer eğimli çizgileri tekilleştir
        unique = []
        for c in candidates:
            dup = any(
                abs(c["slope"] - u["slope"]) / (abs(u["slope"]) + 1e-9) < 0.08
                for u in unique
            )
            if not dup:
                unique.append(c)
            if len(unique) >= max_lines:
                break
        return unique

    support_lines    = _best_lines(pivot_lows,  low,  "support")
    resistance_lines = _best_lines(pivot_highs, high, "resistance")

    # Kanal tespiti: yaklaşık paralel destek + direnç çiftleri
    channels = []
    for sl in support_lines:
        for rl in resistance_lines:
            sdiff = abs(sl["slope"] - rl["slope"]) / (abs(sl["slope"]) + 1e-9)
            if sdiff < 0.12:
                channels.append({"support": sl, "resistance": rl})

    return support_lines + resistance_lines, channels, dates
# ──────────────────────────────────────────────────────────────────────────────


# ============================================================
# FİBONACCİ, WAVETREND, DIVERGENCE
# ============================================================
def calc_fibonacci(high, low, close, lookback=100, swing_window=5):
    """Fibonacci Retracement — trend yönü ve swing-tabanlı pivot ile.

    Klasik Fibonacci kullanımı:
    - Yükseliş trendinde: swing LOW → swing HIGH yönünde çizilir.
      Seviyeler retracement (geri çekilme) seviyeleri olur — destek olarak görev yapar.
    - Düşüş trendinde:    swing HIGH → swing LOW yönünde çizilir.
      Seviyeler tepki seviyeleri olur — direnç olarak görev yapar.

    Algoritma:
    1. Trend yönü: son lookback barın ilk %25'i ile son %25'inin ortalama
       fiyatları kıyaslanır. Son ortalama yüksekse trend yukarı.
    2. Swing pivotu: lookback içindeki gerçek swing high/low (fractal pivot)
       seçilir; trend yönüne göre **en derin/en yüksek** pivot kullanılır
       (major swing yakalama — kısa vade gürültüsü yerine asıl trend hareketi):
       - Yukarı trend: en derin swing LOW (lookback içindeki en düşük pivot)
                       + ardından gelen en yüksek HIGH
       - Aşağı trend: en yüksek swing HIGH (lookback içindeki en yüksek pivot)
                      + ardından gelen en düşük LOW
    3. Seviyeler statik kalır (mevcut major swing range içinde sabit).

    Returns: (levels_dict, swing_high, swing_low, direction)
      direction: "up" / "down" / "none"
    """
    if len(close) < lookback:
        lookback = len(close)
    if lookback < swing_window * 4:
        # Yetersiz veri için basit min-max'a düş
        recent_high = float(high.iloc[-lookback:].max())
        recent_low  = float(low.iloc[-lookback:].min())
        diff = recent_high - recent_low
        if diff == 0:
            return {}, recent_high, recent_low, "none"
        levels = {
            "0.0%":   recent_low,   "23.6%":  recent_low + 0.236 * diff,
            "38.2%":  recent_low + 0.382 * diff, "50.0%":  recent_low + 0.500 * diff,
            "61.8%":  recent_low + 0.618 * diff, "78.6%":  recent_low + 0.786 * diff,
            "100.0%": recent_high,
        }
        return levels, recent_high, recent_low, "none"

    # 1) Trend yönü tespiti
    seg = close.iloc[-lookback:]
    q   = max(lookback // 4, 5)
    avg_first = float(seg.iloc[:q].mean())
    avg_last  = float(seg.iloc[-q:].mean())
    if avg_last > avg_first * 1.005:    # %0.5 üstü → yukarı trend
        direction = "up"
    elif avg_last < avg_first * 0.995:  # %0.5 altı → aşağı trend
        direction = "down"
    else:
        direction = "none"

    # 2) Swing pivotları (lookback penceresi içinde fractal high/low)
    h_seg = high.iloc[-lookback:].reset_index(drop=True)
    l_seg = low.iloc[-lookback:].reset_index(drop=True)
    swing_highs = []  # (index_in_seg, price)
    swing_lows  = []
    n_seg = len(h_seg)
    for i in range(swing_window, n_seg - swing_window):
        if h_seg.iloc[i] == h_seg.iloc[i - swing_window:i + swing_window + 1].max():
            swing_highs.append((i, float(h_seg.iloc[i])))
        if l_seg.iloc[i] == l_seg.iloc[i - swing_window:i + swing_window + 1].min():
            swing_lows.append((i, float(l_seg.iloc[i])))

    swing_high = swing_low = None

    if direction == "up" and swing_lows:
        # Trend yukarı: lookback içindeki EN DÜŞÜK swing LOW (anlamlı major dip)
        # ve sonrasında oluşan EN YÜKSEK HIGH
        deepest = min(swing_lows, key=lambda x: x[1])
        deepest_idx, deepest_price = deepest
        after = h_seg.iloc[deepest_idx:]
        swing_high = float(after.max())
        swing_low  = deepest_price
    elif direction == "down" and swing_highs:
        # Trend aşağı: lookback içindeki EN YÜKSEK swing HIGH (anlamlı major tepe)
        # ve sonrasında oluşan EN DÜŞÜK LOW
        highest = max(swing_highs, key=lambda x: x[1])
        highest_idx, highest_price = highest
        after = l_seg.iloc[highest_idx:]
        swing_low  = float(after.min())
        swing_high = highest_price
    else:
        # Yön belirsiz: lookback range'inin global high/low'u
        swing_high = float(h_seg.max())
        swing_low  = float(l_seg.min())

    diff = swing_high - swing_low
    if diff == 0:
        return {}, swing_high, swing_low, direction

    # 3) Seviyeler — retracement her iki yön için aynı oranlarda hesaplanır
    # Görsel/yorum yön bilgisiyle yapılır (dokümantasyonda)
    levels = {
        "0.0%":   swing_low,
        "23.6%":  swing_low + 0.236 * diff,
        "38.2%":  swing_low + 0.382 * diff,
        "50.0%":  swing_low + 0.500 * diff,
        "61.8%":  swing_low + 0.618 * diff,
        "78.6%":  swing_low + 0.786 * diff,
        "100.0%": swing_high,
    }
    return levels, swing_high, swing_low, direction


def calc_wavetrend(high, low, close, n1=10, n2=21):
    ap  = (high + low + close) / 3
    esa = ap.ewm(span=n1, adjust=False).mean()
    d   = (ap - esa).abs().ewm(span=n1, adjust=False).mean()
    ci  = (ap - esa) / (0.015 * d.replace(0, np.nan))
    wt1 = ci.ewm(span=n2, adjust=False).mean()
    wt2 = wt1.rolling(4).mean()
    return wt1, wt2


def detect_divergence(price, indicator, window=5):
    n      = len(price)
    result = np.zeros(n)
    pv     = price.values.astype(float)
    iv     = indicator.values.astype(float)
    for i in range(window * 2, n):
        seg_p = pv[max(0, i - window * 4):i + 1]
        seg_i = iv[max(0, i - window * 4):i + 1]
        m     = len(seg_p)
        lows_p = []; lows_i = []
        for j in range(window, m - window):
            if seg_p[j] == np.min(seg_p[j - window:j + window + 1]):
                lows_p.append(seg_p[j])
                lows_i.append(seg_i[j])
        if len(lows_p) >= 2:
            if lows_p[-1] < lows_p[-2] and lows_i[-1] > lows_i[-2]:
                result[i] = 1
        highs_p = []; highs_i = []
        for j in range(window, m - window):
            if seg_p[j] == np.max(seg_p[j - window:j + window + 1]):
                highs_p.append(seg_p[j])
                highs_i.append(seg_i[j])
        if len(highs_p) >= 2:
            if highs_p[-1] > highs_p[-2] and highs_i[-1] < highs_i[-2]:
                result[i] = -1
    return pd.Series(result, index=price.index)


# ============================================================
# 5. SİNYAL FONKSİYONLARI
# ============================================================
def sig_sma(close, sma_s=20, sma_l=100):
    """SMA Crossover — hiyerarşi onaylı.
    AL  : SMA_short > SMA_long  VE  Fiyat > SMA_short
    SAT : SMA_short < SMA_long  VE  Fiyat < SMA_short
    Diğer tüm durumlar (fiyat kısa MA'nın yanlış tarafında) → NÖTR.
    Bu, kısa MA'nın altına/üstüne sarkan ama crossover henüz dönmemiş
    çelişkili durumlarda whipsaw'ı azaltır.
    """
    sh  = close.rolling(sma_s, min_periods=sma_s).mean()
    sl  = close.rolling(sma_l, min_periods=sma_l).mean()
    buy  = (sh > sl) & (close > sh)
    sell = (sh < sl) & (close < sh)
    sig = np.where(buy, 1, np.where(sell, -1, 0))
    sig = np.where(sh.isna() | sl.isna(), 0, sig)
    return pd.Series(sig, index=close.index), sh, sl


def sig_rsi_fn(close, rsi_period, rsi_lower=30, rsi_upper=70, trend_period=200):
    """RSI sinyali — Wilder EWM + SMA trend filtreli + RSI 50 çıkış.

    Hesaplama:
    - Wilder RSI: EWM(alpha=1/period) — TradingView/Bloomberg ile tutarlı.
    - SMA(trend_period) trend filtresi: catching a falling knife önlemi.
      AL yalnızca fiyat SMA üzerinde, SAT yalnızca fiyat SMA altında geçerli.
    - Giriş: RSI < rsi_lower → AL, RSI > rsi_upper → SAT.
    - Çıkış: Long için RSI 50'yi yukarı geçince kapat (Connors standardı).
             Short için RSI 50'yi aşağı geçince kapat.
    """
    d     = close.diff()
    gain  = d.where(d > 0, 0.0)
    loss  = (-d.where(d < 0, 0.0))
    # Wilder smoothing: ilk değer SMA, sonrası EWM (adjust=False, alpha=1/period)
    alpha = 1.0 / rsi_period
    avg_g = gain.ewm(alpha=alpha, min_periods=rsi_period, adjust=False).mean()
    avg_l = loss.ewm(alpha=alpha, min_periods=rsi_period, adjust=False).mean()
    rsi   = 100 - (100 / (1 + avg_g / avg_l.replace(0, np.nan)))

    # Giriş sinyalleri
    rsi_v   = rsi.values
    entry   = np.where(rsi_v < rsi_lower, 1, np.where(rsi_v > rsi_upper, -1, 0))

    # RSI 50 çıkış: long pozisyon RSI 50 yukarı geçince SAT,
    #               short pozisyon RSI 50 aşağı geçince AL
    cross_above_50 = (rsi_v >= 50) & (np.concatenate(([50], rsi_v[:-1])) < 50)
    cross_below_50 = (rsi_v <= 50) & (np.concatenate(([50], rsi_v[:-1])) > 50)

    sig      = np.zeros(len(rsi_v), dtype=float)
    position = 0
    for i in range(len(rsi_v)):
        if position == 0:
            if entry[i] == 1:  position = 1;  sig[i] = 1
            elif entry[i] == -1: position = -1; sig[i] = -1
        elif position == 1:
            if cross_above_50[i]: position = 0; sig[i] = -1  # long kapat
            else: sig[i] = 1
        elif position == -1:
            if cross_below_50[i]: position = 0; sig[i] = 1   # short kapat
            else: sig[i] = -1

    # Trend filtresi: SMA(trend_period)
    trend_sma = close.rolling(trend_period, min_periods=trend_period).mean()
    above = (close > trend_sma).values
    below = (close < trend_sma).values
    valid = trend_sma.notna().values
    sig = np.where(valid & (sig == 1)  & above, 1,
          np.where(valid & (sig == -1) & below, -1,
          np.where(~valid, sig, 0)))
    return pd.Series(sig, index=close.index), rsi


def sig_bb(close, bb_period, bb_std_val=2.0, trend_period=200):
    """Bollinger Bands sinyali — SMA trend filtreli mean reversion.

    Hesaplama:
    - Orta çizgi: SMA(bb_period)
    - Üst/alt bantlar: orta ± bb_std_val * std
    - Giriş: fiyat alt bandın altında → AL, üst bandın üstünde → SAT
    - Trend filtresi: SMA(trend_period)
      AL yalnızca fiyat trend SMA üstündeyse geçerli (yükselen trendde dip alımı).
      SAT yalnızca fiyat trend SMA altındaysa geçerli (düşen trendde tepe satışı).
      Bu, BB mean reversion'un trendli piyasada whipsaw yapmasını önler.
    """
    mid = close.rolling(bb_period).mean()
    std = close.rolling(bb_period).std()
    up  = mid + bb_std_val * std
    lo  = mid - bb_std_val * std
    sig = np.where(close < lo, 1, np.where(close > up, -1, 0))

    # Trend filtresi: SMA(trend_period)
    trend_sma = close.rolling(trend_period, min_periods=trend_period).mean()
    above = (close > trend_sma).values
    below = (close < trend_sma).values
    valid = trend_sma.notna().values
    sig = np.where(valid & (sig == 1)  & above, 1,
          np.where(valid & (sig == -1) & below, -1,
          np.where(~valid, sig, 0)))
    return pd.Series(sig, index=close.index), mid, up, lo


def sig_macd(close, macd_fast=12, macd_slow=26, macd_sig_p=9):
    ef   = close.ewm(span=macd_fast, adjust=False).mean()
    es   = close.ewm(span=macd_slow, adjust=False).mean()
    macd = ef - es
    ms   = macd.ewm(span=macd_sig_p, adjust=False).mean()
    sig  = np.where(macd > ms, 1, -1)
    sig  = np.where(macd.isna() | ms.isna(), 0, sig)
    return pd.Series(sig, index=close.index), macd, ms


def sig_obv(close, volume, obv_short, obv_long):
    obv = (volume * np.sign(close.diff()).fillna(0)).cumsum()
    s   = obv.rolling(obv_short, min_periods=obv_short).mean()
    l   = obv.rolling(obv_long,  min_periods=obv_long).mean()
    sig = np.where(s > l, 1, -1)
    sig = np.where(s.isna() | l.isna(), 0, sig)
    return pd.Series(sig, index=close.index), obv, s, l


def sig_adx_fn(high, low, close, adx_period, adx_threshold=25):
    adx_v, pdi, mdi = calc_adx(high, low, close, period=adx_period)
    sig = np.where(adx_v > adx_threshold, np.where(pdi > mdi, 1, -1), 0)
    return pd.Series(sig, index=close.index), adx_v, pdi, mdi


def sig_stochrsi(close, rsi_series, rsi_ma_series, srsi_period, sd_period, sl, su):
    """Stoch RSI — bölge + %K/%D kesişim + RSI MA momentum filtreli sinyal.
    - Aşırı satım (K < sl) VE yukarı dönüş (K > D) VE RSI > RSI_MA → AL (+1)
    - Aşırı alım  (K > su) VE aşağı dönüş (K < D) VE RSI < RSI_MA → SAT (-1)
    - Aksi halde nötr (0)

    Çift teyit:
    1. Bölgede olmak yetmez — K/D kesişimi dönüş teyidi şarttır.
    2. RSI > RSI_MA: kısa-vadeli momentum yukarı eğimli → AL'lar geçerli.
       RSI < RSI_MA: kısa-vadeli momentum aşağı eğimli → SAT'lar geçerli.
       Bu filtre RSI ekosistemi ile tutarlılık sağlar; trend dönüşü henüz
       teyitlenmemişken erken sinyalleri eler.
    """
    rmin = rsi_series.rolling(srsi_period, min_periods=srsi_period).min()
    rmax = rsi_series.rolling(srsi_period, min_periods=srsi_period).max()
    k    = ((rsi_series - rmin) / (rmax - rmin).replace(0, np.nan) * 100).fillna(50).clip(0, 100)
    d    = k.rolling(sd_period).mean()

    # RSI MA momentum filtresi
    rsi_ma_v = rsi_ma_series.values
    rsi_v    = rsi_series.values
    momentum_up   = rsi_v > rsi_ma_v
    momentum_down = rsi_v < rsi_ma_v
    valid_ma      = ~np.isnan(rsi_ma_v)

    # Kesişim teyitli + momentum filtreli sinyal
    bull = (k < sl) & (k > d)   # Aşırı satımda yukarı dönüş
    bear = (k > su) & (k < d)   # Aşırı alımda aşağı dönüş
    sig  = np.where(valid_ma & bull & momentum_up,   1,
           np.where(valid_ma & bear & momentum_down, -1, 0))
    return pd.Series(sig, index=close.index), k, d


def sig_ichimoku(high, low, close, it, ik, isb):
    """Ichimoku Kinko Hyo — klasik 5'li set, üçlü teyitli sinyal (Hosoda).

    Bileşenler:
    - Tenkan-sen   : Kısa vade denge çizgisi (it bar)
    - Kijun-sen    : Orta vade denge çizgisi (ik bar)
    - Senkou A/B   : Bulut sınırları (ik bar İLERİ kaydırılır)
    - Chikou Span  : Kapanışın ik bar GERİ kaydırılmış hali (trend teyidi)

    Sinyal — üç koşul birden gerekli (Hosoda klasiği):
    1. TK Cross           : Tenkan > Kijun (AL) / Tenkan < Kijun (SAT)
    2. Fiyat-Bulut        : close > cloud_top (AL) / close < cloud_bottom (SAT)
    3. Chikou onayı       : close > close.shift(ik) (AL) / close < close.shift(ik) (SAT)
    """
    tenkan   = (high.rolling(it).max()  + low.rolling(it).min())  / 2
    kijun    = (high.rolling(ik).max()  + low.rolling(ik).min())  / 2
    senkou_a = ((tenkan + kijun) / 2).shift(ik)
    senkou_b = ((high.rolling(isb).max() + low.rolling(isb).min()) / 2).shift(ik)
    chikou   = close.shift(-ik)  # Bugünün kapanışı, ik bar geriye

    # Chikou teyidi: bugünün kapanışı, ik bar önceki kapanıştan yüksek mi?
    # (Hosoda: Chikou geçmiş fiyatların üstünde → boğa, altında → ayı)
    chikou_bull = close > close.shift(ik)
    chikou_bear = close < close.shift(ik)

    ct = pd.concat([senkou_a, senkou_b], axis=1).max(axis=1)
    cb = pd.concat([senkou_a, senkou_b], axis=1).min(axis=1)
    sig = np.where((tenkan > kijun) & (close > ct) & chikou_bull,  1,
                   np.where((tenkan < kijun) & (close < cb) & chikou_bear, -1, 0))
    return pd.Series(sig, index=close.index), tenkan, kijun, senkou_a, senkou_b, chikou


def sig_kama_fn(close, kp, kf, ks, er_threshold=0.30, slope_window=3):
    """KAMA sinyali — Kaufman'ın felsefesine uygun: eğim + ER filtresi.

    Cross değil, eğim:
    - KAMA son `slope_window` barda yukarı eğimli VE ER yeterli → AL
    - KAMA son `slope_window` barda aşağı eğimli VE ER yeterli → SAT
    - ER < threshold → trendsiz, sinyal sıfırla (ATR filtresine gerek yok;
      ER zaten yön kalitesini doğrudan ölçüyor)

    Notlar:
    - ATR filtresi kaldırıldı: ATR mutlak volatiliteyi ölçer, KAMA için
      kritik olan yön etkinliği (ER). Yüksek ATR + düşük ER = yatay zikzak.
    - Eğim 1-bar diff yerine `slope_window` barlık fark: tek bar gürültüsünü
      filtreler, küçük yatay dalgalanmalarda sinyal çıkmaz.
    """
    kama, er = calc_kama(close, period=kp, fast=kf, slow=ks)
    slope    = kama.diff(slope_window)

    sig = np.where((slope > 0) & (er >= er_threshold),  1,
          np.where((slope < 0) & (er >= er_threshold), -1, 0))
    sig = np.where(kama.isna() | er.isna(), 0, sig)
    return pd.Series(sig, index=close.index), kama, er


def sig_supertrend_fn(high, low, close, stp, stm):
    """SuperTrend — flip-based event sinyali.

    Klasik ATR-trailing yapı (Seban 2008) state machine olarak çalışır:
    yön değişimi yalnızca fiyat bandı kırınca olur.

    Sinyal mantığı:
    - direction[t] != direction[t-1] AND direction[t] == 1  → AL  (+1, flip-up)
    - direction[t] != direction[t-1] AND direction[t] == -1 → SAT (-1, flip-down)
    - aksi halde 0 (yön korunuyor, yeni sinyal yok)

    Notlar:
    - ATR filtresi KALDIRILDI: SuperTrend zaten ATR-bazlı bir göstergedir
      (band genişliği = ATR × multiplier). Düşük volatilitede band daralır,
      flip nadir olur — ek ATR filtresi çift filtre olur.
    - Eski "her bar direction" davranışı SMA200 trend filtresi gibi çalışıyordu;
      bu sürüm SuperTrend'in özgün event-based karakterini ortaya çıkarır.
    - Yön bilgisi (direction serisi) ayrıca döndürülür — grafik renklendirme,
      trailing stop kullanımı ve rejim göstergesi olarak ihtiyaç var.
    """
    st, std, lb, ub = calc_supertrend(high, low, close, period=stp, multiplier=stm)
    d = std.values
    flip = np.zeros(len(d), dtype=float)
    for i in range(1, len(d)):
        if not np.isnan(d[i]) and not np.isnan(d[i-1]) and d[i] != d[i-1]:
            flip[i] = d[i]   # +1 flip-up, -1 flip-down
    flip = np.where(st.isna(), 0, flip)
    return pd.Series(flip, index=close.index), st, std, lb, ub


def sig_lrc(close, lrc_period, lrc_std_mult=2.0):
    """LR Channel sinyali — slope-aware mean reversion.

    Klasik bant dokunma + slope filtresi:
    - slope >= 0 (yükselen/yatay regresyon):
        close < lower  → AL  (trend yönünde dip alımı)
        close > upper  → 0   (trend yönüne ters mean reversion — ele)
    - slope < 0 (düşen regresyon):
        close > upper  → SAT (trend yönünde tepe satışı)
        close < lower  → 0   (trend yönüne ters — ele)

    Felsefe:
    LRC'nin gücü "kanalın eğimli" olmasıdır. Slope yönü zaten bir trend filtresidir.
    Trende ters mean reversion sinyalleri (yükselen kanalda üst banda dokunma → SAT)
    whipsaw üretir; bu sürüm onları siler.
    """
    mid, up, lo, slope, r2 = calc_linear_regression_channel(
        close, period=lrc_period, std_mult=lrc_std_mult)
    cv = close.values
    sl_v = slope.values
    up_v = up.values
    lo_v = lo.values

    bullish_trend = sl_v >= 0
    bearish_trend = sl_v <  0

    # AL: yükselen/yatay kanalda alt banda dokunma
    bull_signal = bullish_trend & (cv < lo_v)
    # SAT: düşen kanalda üst banda dokunma
    bear_signal = bearish_trend & (cv > up_v)

    sig = np.where(bull_signal,  1, np.where(bear_signal, -1, 0))
    sig = np.where(mid.isna() | slope.isna(), 0, sig)
    return pd.Series(sig, index=close.index), mid, up, lo, slope, r2


def sig_vwap_fn(high, low, close, volume, vwap_band_pct):
    vwap = calc_vwap_daily(high, low, close, volume)
    band = vwap * (vwap_band_pct / 100)
    sig  = np.where(close > vwap + band, 1, np.where(close < vwap - band, -1, 0))
    sig  = np.where(vwap.isna(), 0, sig)
    return pd.Series(sig, index=close.index), vwap


def sig_wavetrend_fn(high, low, close, rsi_series, rsi_ma_series, n1=10, n2=21, ob=60, os_=-60):
    """WaveTrend (LazyBear 2014) — bölge + cross + RSI MA momentum filtreli sinyal.

    Çift teyit (klasik):
    1. Aşırı satım (WT1 < os_) VE WT1 yukarı kesti WT2'yi → AL bölge sinyali
    2. Aşırı alım  (WT1 > ob)  VE WT1 aşağı kesti WT2'yi → SAT bölge sinyali

    Üçüncü teyit (RSI MA momentum filtresi):
    - AL  yalnızca RSI > RSI_MA ise geçerli (momentum yukarı eğimli)
    - SAT yalnızca RSI < RSI_MA ise geçerli (momentum aşağı eğimli)

    Felsefe:
    WaveTrend salt mean reversion göstergesi olarak trendli piyasada whipsaw üretir.
    StochRSI'da uyguladığımız aynı RSI_MA filtresi WaveTrend'e de uygulanır —
    iki gösterge artık simetrik mimaride: farklı veri kaynağından (RSI vs fiyat)
    aynı kalite filtresinden geçen mean reversion sinyalleri.
    """
    wt1, wt2   = calc_wavetrend(high, low, close, n1=n1, n2=n2)
    cross_up   = (wt1 > wt2) & (wt1.shift(1) <= wt2.shift(1))
    cross_down = (wt1 < wt2) & (wt1.shift(1) >= wt2.shift(1))

    # Klasik bölge + cross sinyalleri
    bull = cross_up   & (wt1 < os_)
    bear = cross_down & (wt1 > ob)

    # RSI MA momentum filtresi
    rsi_ma_v = rsi_ma_series.values
    rsi_v    = rsi_series.values
    momentum_up   = rsi_v > rsi_ma_v
    momentum_down = rsi_v < rsi_ma_v
    valid_ma      = ~np.isnan(rsi_ma_v)

    sig = np.where(valid_ma & bull & momentum_up,   1,
          np.where(valid_ma & bear & momentum_down, -1, 0))
    return pd.Series(sig, index=close.index), wt1, wt2


# ============================================================
# 7. VERİ ÇEKME
# ============================================================
@st.cache_data(ttl=300, show_spinner=False)
def fetch_live_data(symbol, p, i):
    try:
        fetch_i = "1h" if i in ("4h", "8h") else i
        data = yf.download(symbol, period=p, interval=fetch_i, progress=False)
        if data is None or data.empty:
            return pd.DataFrame()
        if i in ("4h", "8h"):
            if isinstance(data.columns, pd.MultiIndex):
                uniq = data.columns.get_level_values(1).unique()
                data.columns = (data.columns.get_level_values(0)
                                if len(uniq) <= 1
                                else [f"{c[1]}_{c[0]}" for c in data.columns])
            rule = "4h" if i == "4h" else "8h"
            data = (
                data.resample(rule)
                .agg({"Open": "first", "High": "max", "Low": "min",
                      "Close": "last", "Volume": "sum"})
                .dropna()
            )
        return data
    except Exception as e:
        st.error(f"Veri çekme hatası: {e}")
        return pd.DataFrame()


PLOTLY_CONFIG = dict(scrollZoom=True, displayModeBar=True,
    modeBarButtonsToAdd=["pan2d", "zoomIn2d", "zoomOut2d", "resetScale2d"],
    modeBarButtonsToRemove=["lasso2d", "select2d"])


def sub_layout(height=250):
    return dict(template="plotly_dark", height=height, margin=dict(t=30, b=30), dragmode="pan")


# ============================================================
# 8. ANA MANTIK
# ============================================================
if ta_calistir and ta_ticker:
    df = fetch_live_data(ta_ticker, period, interval)

    if not df.empty:
        df = flatten_columns(df)
        df = df.dropna(subset=["Open", "High", "Low", "Close", "Volume"])
        missing = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c not in df.columns]
        if missing:
            st.error(f"Eksik sütunlar: {missing}.")
            st.stop()

        close     = df["Close"].squeeze()
        high      = df["High"].squeeze()
        low       = df["Low"].squeeze()
        volume    = df["Volume"].squeeze()
        close_arr = close.values
        n_bars    = len(close)

        indicator_min_reqs = {
            "SMA Crossover":    sma_long,
            "Bollinger Bands":  bb_period,
            "RSI":              rsi_period * 2,
            "MACD":             macd_slow + macd_signal,
            "OBV":              obv_long,
            "ADX":              adx_period * 3,
            "Stoch RSI":        rsi_period + stoch_rsi_period,
            "Ichimoku":         ichi_senkou_b + ichi_kijun,
            "KAMA":             kama_period + kama_slow,
            "SuperTrend":       st_period * 2,
            "LR Channel":       lrc_period,
            "WaveTrend":        wt_n1 + wt_n2,
        }

        affected = [
            f"{name} (min {req} mum)"
            for name, req in indicator_min_reqs.items()
            if n_bars < req
        ]

        min_req = max(150, adx_period * 3, ichi_senkou_b)
        if n_bars < min_req:
            if affected:
                st.warning(
                    f"⚠️ Yeterli veri yok: **{n_bars} mum** mevcut, en az **{min_req}** gerekli.\n\n"
                    f"**Etkilenen indikatörler:** {', '.join(affected)}"
                )
            else:
                st.warning(f"Yeterli veri yok: {n_bars} mum, en az {min_req} gerekli.")

        is_intraday = interval in ["1m", "2m", "5m", "15m", "30m", "60m", "1h"]

        # ATR
        tr1        = high - low
        tr2        = (high - close.shift(1)).abs()
        tr3        = (low  - close.shift(1)).abs()
        tr         = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr_series = tr.ewm(alpha=1.0 / atr_period, min_periods=atr_period, adjust=False).mean()
        atr_ma     = atr_series.rolling(atr_period, min_periods=atr_period).mean()
        atr_high   = (atr_series > atr_ma).values

        # ── YENİ: 200 EMA ─────────────────────────────────────────
        df["EMA200"] = close.ewm(span=200, adjust=False).mean()
        # ──────────────────────────────────────────────────────────

        # ── Swing Destek/Direnç (yatay) ───────────────────────────
        swing_levels = find_swing_levels(
            high, low, close,
            window=swing_window,
            min_touches=swing_touches,
            tolerance=swing_tol,
            atr_series=atr_series,
            atr_k=swing_atr_k,
        )

        # ── Diyagonal Trend Çizgileri ──────────────────────────────
        trendlines, tl_channels, tl_dates = find_trendlines(
            high, low, close,
            pivot_window=tl_pivot_window,
            max_lines=tl_max_lines,
            tolerance=tl_tolerance,
        )
        # ──────────────────────────────────────────────────────────

        p_sma  = {"sma_s": sma_short,   "sma_l": sma_long}
        p_rsi  = {"rsi_period": rsi_period, "rsi_lower": rsi_lower, "rsi_upper": rsi_upper}
        p_bb   = {"bb_period": bb_period,   "bb_std": bb_std}
        p_macd = {"macd_fast": macd_fast,   "macd_slow": macd_slow, "macd_signal": macd_signal}
        p_adx  = {"adx_period": adx_period, "adx_threshold": adx_threshold}
        p_st   = {"st_period": st_period,   "st_multiplier": st_multiplier}
        p_lrc  = {"lrc_period": lrc_period, "lrc_std_mult": lrc_std_mult}
        p_wt   = {"wt_n1": wt_n1,           "wt_n2": wt_n2}

        df["Sig_SMA"], df["SMA_SHORT"], df["SMA_LONG"] = sig_sma(
            close, p_sma["sma_s"], p_sma["sma_l"])

        # SMA 200 (EMA 200 ile karşılaştırma için — daha yavaş, daha stabil)
        df["SMA200"] = close.rolling(200, min_periods=200).mean()

        df["Sig_RSI"], df["RSI"] = sig_rsi_fn(
            close, p_rsi["rsi_period"], p_rsi["rsi_lower"], p_rsi["rsi_upper"])
        df["RSI_MA"] = df["RSI"].rolling(rsi_ma_period).mean()

        df["Sig_BB"], df["Mid"], df["Up"], df["Low_BB"] = sig_bb(
            close, p_bb["bb_period"], p_bb["bb_std"])

        df["Sig_MACD"], df["MACD"], df["MACD_S"] = sig_macd(
            close, p_macd["macd_fast"], p_macd["macd_slow"], p_macd["macd_signal"])

        df["Sig_OBV"], df["OBV"], obv_sma_short, obv_sma_long = sig_obv(
            close, volume, obv_short, obv_long)

        df["Sig_ADX"], df["ADX"], df["PLUS_DI"], df["MINUS_DI"] = sig_adx_fn(
            high, low, close, p_adx["adx_period"], p_adx["adx_threshold"])

        df["Sig_StochRSI"], df["StochRSI_K"], df["StochRSI_D"] = sig_stochrsi(
            close, df["RSI"], df["RSI_MA"], stoch_rsi_period, stoch_d_period, stoch_lower, stoch_upper)

        df["Sig_Ichimoku"], df["Tenkan"], df["Kijun"], df["Senkou_A"], df["Senkou_B"], df["Chikou"] = sig_ichimoku(
            high, low, close, ichi_tenkan, ichi_kijun, ichi_senkou_b)

        df["Sig_KAMA"], df["KAMA"], df["KAMA_ER"] = sig_kama_fn(
            close, kama_period, kama_fast, kama_slow)

        df["Sig_SuperTrend"], df["SuperTrend"], df["ST_Direction"], df["ST_Lower"], df["ST_Upper"] = sig_supertrend_fn(
            high, low, close, p_st["st_period"], p_st["st_multiplier"])

        df["Sig_LRC"], df["LRC_Mid"], df["LRC_Upper"], df["LRC_Lower"], df["LRC_Slope"], df["LRC_R2"] = sig_lrc(
            close, p_lrc["lrc_period"], p_lrc["lrc_std_mult"])

        df["ATR"]      = atr_series
        df["ATR_High"] = atr_high

        if is_intraday:
            df["Sig_VWAP"], df["VWAP"] = sig_vwap_fn(high, low, close, volume, vwap_band_pct)
        else:
            df["Sig_VWAP"] = 0
            df["VWAP"]     = np.nan

        df["Sig_WaveTrend"], df["WT1"], df["WT2"] = sig_wavetrend_fn(
            high, low, close, df["RSI"], df["RSI_MA"],
            p_wt["wt_n1"], p_wt["wt_n2"], wt_ob, wt_os)

        fib_levels, fib_high, fib_low, fib_direction = calc_fibonacci(
            high, low, close, lookback=fib_lookback)

        df["Div_RSI"]  = detect_divergence(close, df["RSI"],  window=div_window)
        df["Div_MACD"] = detect_divergence(close, df["MACD"], window=div_window)
        df["Div_OBV"]  = detect_divergence(close, df["OBV"],  window=div_window)

        # ============================================================
        # ANA GRAFİK + VRP
        # ============================================================
        from plotly.subplots import make_subplots

        bull_st = df["ST_Direction"] == 1
        bear_st = df["ST_Direction"] == -1

        st_dir_shifted = df["ST_Direction"].shift(1).fillna(0)
        st_buy_signal  = (df["ST_Direction"] == 1)  & (st_dir_shifted != 1)
        st_sell_signal = (df["ST_Direction"] == -1) & (st_dir_shifted != -1)

        lp = float(close.iloc[-1])
        pp = float(close.iloc[-2]) if len(close) > 1 else lp

        vrp_bins     = 40
        if show_vp:
            price_min    = float(low.min())
            price_max    = float(high.max())
            bin_edges    = np.linspace(price_min, price_max, vrp_bins + 1)
            bin_centers  = (bin_edges[:-1] + bin_edges[1:]) / 2
            vol_at_price = np.zeros(vrp_bins)
            for i in range(len(df)):
                lo_i  = float(low.iloc[i])
                hi_i  = float(high.iloc[i])
                vol_i = float(volume.iloc[i])
                if hi_i == lo_i:
                    idx = np.clip(np.searchsorted(bin_edges, lo_i, side="right") - 1, 0, vrp_bins - 1)
                    vol_at_price[idx] += vol_i
                else:
                    for b in range(vrp_bins):
                        overlap = min(hi_i, bin_edges[b+1]) - max(lo_i, bin_edges[b])
                        if overlap > 0:
                            vol_at_price[b] += vol_i * overlap / (hi_i - lo_i)

            poc_idx   = int(np.argmax(vol_at_price))
            poc_price = bin_centers[poc_idx]
            max_vol   = vol_at_price.max()
            bar_colors = [
                "rgba(255,165,0,1.0)" if b == poc_idx
                else f"rgba(100,{int(80 + 175*(v/max_vol)) if max_vol > 0 else 200},255,0.85)"
                for b, v in enumerate(vol_at_price)
            ]

        if show_vp:
            fig = make_subplots(
                rows=2, cols=2,
                row_heights=[0.20, 0.80],
                column_widths=[0.85, 0.15],
                shared_xaxes=True,
                shared_yaxes=True,
                horizontal_spacing=0.0,
                vertical_spacing=0.02,
            )
        else:
            fig = make_subplots(
                rows=2, cols=1,
                row_heights=[0.20, 0.80],
                shared_xaxes=True,
                vertical_spacing=0.02,
            )

        # ── ÜST MİNİ PANEL: WT_CROSS_LB (bilgi amaçlı, saf cross) ─────
        # df["WT1"], df["WT2"] line ~2109'da zaten hesaplandı; yeniden hesaplamıyoruz.
        # Buradaki cross noktaları BÖLGE FİLTRESİZ — LazyBear orijinal davranışı.
        _wt1 = df["WT1"]; _wt2 = df["WT2"]
        _wt_cu = (_wt1 > _wt2) & (_wt1.shift(1) <= _wt2.shift(1))
        _wt_cd = (_wt1 < _wt2) & (_wt1.shift(1) >= _wt2.shift(1))
        # OB/OS yatay çizgileri (referans)
        fig.add_hline(y=wt_ob, line=dict(color="rgba(255,80,80,0.35)", width=1, dash="dot"), row=1, col=1)
        fig.add_hline(y=wt_os, line=dict(color="rgba(80,255,80,0.35)", width=1, dash="dot"), row=1, col=1)
        fig.add_hline(y=0,     line=dict(color="rgba(150,150,150,0.25)", width=1), row=1, col=1)
        # WT çizgileri
        fig.add_trace(go.Scatter(x=df.index, y=_wt1, name="WT1",
            line=dict(color="#00e5ff", width=1.4), showlegend=False,
            hovertemplate="WT1: %{y:.2f}<extra></extra>"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=_wt2, name="WT2",
            line=dict(color="#ff9800", width=1.2, dash="dot"), showlegend=False,
            hovertemplate="WT2: %{y:.2f}<extra></extra>"), row=1, col=1)
        # Cross noktaları (filtresiz — tüm kesişimler)
        if _wt_cu.any():
            fig.add_trace(go.Scatter(x=df.index[_wt_cu], y=_wt2[_wt_cu],
                mode="markers", name="WT bull cross",
                marker=dict(color="#00e676", size=6, line=dict(color="#003d20", width=0.5)),
                showlegend=False, hoverinfo="skip"), row=1, col=1)
        if _wt_cd.any():
            fig.add_trace(go.Scatter(x=df.index[_wt_cd], y=_wt2[_wt_cd],
                mode="markers", name="WT bear cross",
                marker=dict(color="#ff5252", size=6, line=dict(color="#3d0000", width=0.5)),
                showlegend=False, hoverinfo="skip"), row=1, col=1)
        # Panel başlığı (sol üst köşe, küçük)
        fig.add_annotation(
            xref="x domain", yref="y domain", x=0.005, y=0.92,
            text="<b>WT_CROSS_LB</b>", showarrow=False,
            font=dict(color="rgba(200,200,200,0.65)", size=9, family="monospace"),
            row=1, col=1,
        )
        # ──────────────────────────────────────────────────────────────

        if chart_type == "Mum":
            # ── Sinyal bazlı mum renklendirme ─────────────────────
            _rsi_mid    = (rsi_lower + rsi_upper) / 2
            cyan_raw   = (df["ST_Direction"] == 1) & (df["Sig_OBV"] == 1) & (df["RSI"] < rsi_upper)
            cyan_mask  = cyan_raw & ~cyan_raw.shift(1).fillna(False)
            yellow_mask = (~cyan_mask) & (df["ADX"] < adx_threshold) & (df["RSI"] >= _rsi_mid - 5) & (df["RSI"] <= _rsi_mid + 5)
            red_mask   = (~cyan_mask) & (~yellow_mask) & (df["Close"] < df["Open"]) & (df["MACD"] < df["MACD_S"])
            green_mask = ~cyan_mask & ~yellow_mask & ~red_mask

            _color_defs = [
                ("Cyan AL",  cyan_mask,   "#00ffff"),
                ("Yeşil",    green_mask,  "#00cc66"),
                ("Sarı",     yellow_mask, "#ffcc00"),
                ("Ayı",      red_mask,    "#ff4444"),
            ]
            for _lbl, _mask, _color in _color_defs:
                _rising  = _mask & (df["Close"] >= df["Open"])
                _falling = _mask & (df["Close"] <  df["Open"])
                for _m, _fill, _trace_lbl in [
                    (_rising,  _color,   _lbl + " ↑"),
                    (_falling, "#111111", _lbl + " ↓"),
                ]:
                    if _m.any():
                        fig.add_trace(go.Candlestick(
                            x=df.index[_m],
                            open=df["Open"][_m], high=df["High"][_m],
                            low=df["Low"][_m],   close=df["Close"][_m],
                            name=_trace_lbl,
                            increasing_fillcolor=_fill, increasing_line_color=_color,
                            decreasing_fillcolor=_fill, decreasing_line_color=_color,
                            showlegend=False,
                        ), row=2, col=1)

            # ── Divergence marker katmanı (ana grafik) ────────────
            bull_div = (df["Div_RSI"] == 1) | (df["Div_MACD"] == 1) | (df["Div_OBV"] == 1)
            bear_div = (df["Div_RSI"] == -1) | (df["Div_MACD"] == -1) | (df["Div_OBV"] == -1)
            if bull_div.any():
                fig.add_trace(go.Scatter(
                    x=df.index[bull_div], y=df["Low"][bull_div] * 0.998,
                    mode="markers", name="Bullish Div 🔺",
                    marker=dict(symbol="triangle-up", color="lime", size=10),
                ), row=2, col=1)
            if bear_div.any():
                fig.add_trace(go.Scatter(
                    x=df.index[bear_div], y=df["High"][bear_div] * 1.002,
                    mode="markers", name="Bearish Div 🔻",
                    marker=dict(symbol="triangle-down", color="red", size=16),
                ), row=2, col=1)
        else:
            fig.add_trace(go.Scatter(x=df.index, y=close, name="Fiyat",
                line=dict(color="orange", width=1.5)), row=2, col=1)

        # ── Mum renk legend girişleri (dummy scatter) ─────────────
        if chart_type == "Mum":
            for _leg_name, _leg_color in [
                ("🔴 Ayı",         "#ff4444"),
                ("🟡 Kararsız",    "#ffcc00"),
                ("🟢 Boğa",        "#00cc66"),
                ("🔵 Güçlü Boğa",  "#00ffff"),
            ]:
                fig.add_trace(go.Scatter(
                    x=[None], y=[None], mode="markers",
                    name=_leg_name,
                    marker=dict(symbol="square", size=24, color=_leg_color),
                    showlegend=True,
                ), row=2, col=1)

        fig.add_trace(go.Scatter(x=df.index, y=df["SMA_SHORT"],
            name=f"SMA {p_sma['sma_s']}",
            line=dict(color="orange")), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["SMA_LONG"],
            name=f"SMA {p_sma['sma_l']}",
            line=dict(color="cyan")), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["KAMA"],
            name="KAMA", line=dict(color="violet", width=1.5),
            visible="legendonly"), row=2, col=1)

        # ── YENİ: 200 EMA trace ───────────────────────────────────
        fig.add_trace(go.Scatter(
            x=df.index, y=df["EMA200"],
            name="EMA 200",
            line=dict(color="yellow", width=2, dash="dot"),
            visible="legendonly",
        ), row=2, col=1)
        # SMA 200 — daha stabil, EMA'ya göre yavaş, uzun vade referansı
        fig.add_trace(go.Scatter(
            x=df.index, y=df["SMA200"],
            name="SMA 200",
            line=dict(color="gold", width=2, dash="solid"),
        ), row=2, col=1)
        # ──────────────────────────────────────────────────────────

        fig.add_trace(go.Scatter(
            x=df.index[bull_st], y=df["SuperTrend"][bull_st],
            name="SuperTrend (Boğa çizgi)", mode="lines",
            line=dict(color="rgba(0,255,100,0.5)", width=1.5),
            visible=False, showlegend=False), row=2, col=1)
        fig.add_trace(go.Scatter(
            x=df.index[bear_st], y=df["SuperTrend"][bear_st],
            name="SuperTrend (Ayı çizgi)", mode="lines",
            line=dict(color="rgba(255,60,60,0.5)", width=1.5),
            visible=False, showlegend=False), row=2, col=1)

        if st_buy_signal.any():
            fig.add_trace(go.Scatter(
                x=df.index[st_buy_signal],
                y=df["SuperTrend"][st_buy_signal],
                name="SuperTrend AL",
                mode="markers+text",
                marker=dict(symbol="square", color="#00c853", size=18, line=dict(color="#00c853", width=0)),
                text="AL",
                textfont=dict(color="white", size=8, family="Arial Black"),
                textposition="middle center",
                visible="legendonly",
            ), row=2, col=1)

        if st_sell_signal.any():
            fig.add_trace(go.Scatter(
                x=df.index[st_sell_signal],
                y=df["SuperTrend"][st_sell_signal],
                name="SuperTrend SAT",
                mode="markers+text",
                marker=dict(symbol="square", color="#d50000", size=18, line=dict(color="#d50000", width=0)),
                text="SAT",
                textfont=dict(color="white", size=8, family="Arial Black"),
                textposition="middle center",
                visible="legendonly",
            ), row=2, col=1)

        fig.add_trace(go.Scatter(x=df.index, y=df["LRC_Mid"],
            name="LRC Orta", visible=False, showlegend=False,
            line=dict(color="white", width=1, dash="dash")), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["LRC_Upper"],
            name="LRC Üst", visible=False, showlegend=False,
            line=dict(color="rgba(200,200,200,0.5)", width=1, dash="dot")), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["LRC_Lower"],
            name="LRC Alt", visible=False, showlegend=False,
            line=dict(color="rgba(200,200,200,0.5)", width=1, dash="dot"),
            fill="tonexty", fillcolor="rgba(150,150,150,0.05)"), row=2, col=1)

        if is_intraday:
            fig.add_trace(go.Scatter(x=df.index, y=df["VWAP"],
                name="VWAP", visible="legendonly",
                line=dict(color="yellow", dash="dash", width=1.5)), row=2, col=1)

        FIB_COLORS = {
            "0.0%":   "rgba(128,128,128,0.7)",
            "23.6%":  "rgba(255,165,0,0.8)",
            "38.2%":  "rgba(255,215,0,0.9)",
            "50.0%":  "rgba(255,255,255,0.9)",
            "61.8%":  "rgba(255,215,0,0.9)",
            "78.6%":  "rgba(255,165,0,0.8)",
            "100.0%": "rgba(128,128,128,0.7)",
        }
        for lvl_name, lvl_price in fib_levels.items():
            fig.add_hline(
                y=lvl_price,
                line_dash="dot",
                line_color=FIB_COLORS.get(lvl_name, "gray"),
                line_width=1,
                annotation_text=f"  Fib {lvl_name} {lvl_price:.2f}",
                annotation_font=dict(color=FIB_COLORS.get(lvl_name, "gray"), size=9, family="monospace"),
                annotation_position="top left",
                row=2, col=1,
            )

        # ── Yatay S/R çizgileri (legend toggle destekli, güce göre kalınlık) ──
        # Hepsi "Swing S/R" legend grubu altında — tek yerden aç/kapa
        x_start = df.index[0]
        x_end   = df.index[-1]
        _swing_first = True
        for lvl in swing_levels:
            is_support = lvl["type"] == "S"
            t          = lvl["touches"]
            broken     = lvl.get("broken", False)

            # Kalınlık: dokunuş sayısına göre
            width = 1 if t <= 1 else (2 if t == 2 else 3)
            # Çizgi stili
            dash  = "dash" if t <= 1 else ("dashdot" if t == 2 else "solid")
            # Opaklık
            alpha = min(0.40 + 0.15 * t, 0.80)

            if broken:
                color = f"rgba(160,160,160,{alpha*0.6:.2f})"
                status = " [kırık]"
            else:
                color = (f"rgba(0,255,100,{alpha:.2f})" if is_support
                         else f"rgba(255,80,80,{alpha:.2f})")
                status = ""

            sr_label = (f"{'🟢 Destek' if is_support else '🔴 Direnç'} "
                        f"{lvl['price']:.2f} (x{t}){status}")

            fig.add_trace(go.Scatter(
                x=[x_start, x_end],
                y=[lvl["price"], lvl["price"]],
                mode="lines",
                name=sr_label,
                line=dict(color=color, width=width, dash=dash),
                visible=False,
                showlegend=False,
                legendgroup="swing_sr",
                legendgrouptitle_text="Swing S/R" if _swing_first else None,
                hovertemplate=f"{sr_label}<extra></extra>",
            ), row=2, col=1)
            _swing_first = False

        # ── Diyagonal Trend Çizgileri (legend toggle destekli) ────
        for tl in trendlines:
            is_sup  = tl["type"] == "support"
            color   = "rgba(0,255,120,0.9)" if is_sup else "rgba(255,80,80,0.9)"
            width   = 1 if tl["touches"] <= 2 else (2 if tl["touches"] <= 4 else 3)
            label   = f"{'↗ Destek' if is_sup else '↘ Direnç'} TL (x{tl['touches']})"
            x0_date = tl_dates[tl["x0"]]
            x1_date = tl_dates[tl["x1"]]
            fig.add_trace(go.Scatter(
                x=[x0_date, x1_date],
                y=[tl["y0"], tl["y1"]],
                mode="lines",
                name=label,
                line=dict(color=color, width=width, dash="solid"),
                visible="legendonly",
                legendgroup="trendlines",
                legendgrouptitle_text="Trend Çizgileri" if tl == trendlines[0] else None,
            ), row=2, col=1)

        # ── Kanal dolgusu (legend toggle destekli) ────────────────
        if tl_show_channel:
            for ci, ch in enumerate(tl_channels):
                sl   = ch["support"];  rl = ch["resistance"]
                xi0  = max(sl["x0"], rl["x0"])
                xi1  = sl["x1"]
                xs   = [tl_dates[xi0], tl_dates[xi1],
                        tl_dates[xi1], tl_dates[xi0], tl_dates[xi0]]
                y_s0 = sl["slope"] * xi0 + sl["intercept"]
                y_s1 = sl["slope"] * xi1 + sl["intercept"]
                y_r0 = rl["slope"] * xi0 + rl["intercept"]
                y_r1 = rl["slope"] * xi1 + rl["intercept"]
                ys   = [y_s0, y_s1, y_r1, y_r0, y_s0]
                fig.add_trace(go.Scatter(
                    x=xs, y=ys,
                    fill="toself",
                    fillcolor="rgba(100,180,255,0.07)",
                    line=dict(width=0),
                    mode="lines",
                    name=f"Kanal {ci+1}",
                    visible="legendonly",
                    legendgroup="trendlines",
                    showlegend=True,
                ), row=2, col=1)
        # ──────────────────────────────────────────────────────────

        if show_vp:
            fig.add_trace(go.Bar(
                x=vol_at_price, y=bin_centers,
                orientation="h",
                marker_color=bar_colors,
                name="Hacim Profili",
                showlegend=False,
                hovertemplate="Fiyat: %{y:.2f}<br>Hacim: %{x:,.0f}<extra></extra>",
            ), row=2, col=2)

            fig.add_hline(y=poc_price, line_dash="dash", line_color="orange",
                annotation_text=f"POC {poc_price:.2f}",
                annotation_font=dict(color="orange", size=10, family="monospace"),
                annotation_bgcolor="rgba(255,165,0,0.15)",
                annotation_position="top right", row=2, col=2)
            fig.add_hline(y=lp, line_dash="dot", line_color="lime" if lp >= pp else "red",
                annotation_text=f"  {lp:.2f}",
                annotation_font=dict(color="lime" if lp >= pp else "red", size=12, family="monospace"),
                annotation_bgcolor="rgba(0,255,0,0.12)" if lp >= pp else "rgba(255,0,0,0.12)",
                annotation_position="bottom right", row=2, col=2)
        else:
            # VP kapalı → son fiyat etiketi ana grafiğin sağ kenarında
            fig.add_hline(y=lp, line_dash="dot", line_color="lime" if lp >= pp else "red",
                annotation_text=f" {lp:.2f}",
                annotation_font=dict(color="black", size=12, family="monospace"),
                annotation_bgcolor="lime" if lp >= pp else "red",
                annotation_bordercolor="rgba(0,0,0,0.6)",
                annotation_position="right", row=2, col=1)

        _layout_common = dict(
            template="plotly_dark", height=720,
            dragmode="pan",
            legend=dict(
                orientation="v",
                x=-0.02, y=1,
                xanchor="right", yanchor="top",
                bgcolor="rgba(0,0,0,0)",
                font=dict(size=11),
                itemwidth=30,
                itemsizing="constant",
                tracegroupgap=4,
            ),
            margin=dict(l=110, r=10, t=30, b=30),
        )
        if show_vp:
            fig.update_layout(
                **_layout_common,
                # row=1, col=1 → WT mini panel
                xaxis=dict(showgrid=True, showticklabels=False, rangeslider_visible=False),
                yaxis=dict(showgrid=False, tickfont=dict(size=9), zeroline=False),
                # row=1, col=2 → boş köşe
                xaxis2=dict(showgrid=False, showticklabels=False, visible=False),
                yaxis2=dict(showgrid=False, showticklabels=False, visible=False),
                # row=2, col=1 → ana grafik
                xaxis3=dict(rangeslider_visible=False),
                # row=2, col=2 → hacim profili
                xaxis4=dict(showgrid=False, showticklabels=False),
                yaxis4=dict(showticklabels=False),
            )
        else:
            fig.update_layout(
                **_layout_common,
                # row=1, col=1 → WT mini panel (skala sağda)
                xaxis=dict(showgrid=True, showticklabels=False, rangeslider_visible=False),
                yaxis=dict(showgrid=False, tickfont=dict(size=9), zeroline=False, side="right"),
                # row=2, col=1 → ana grafik (fiyat skalası sağda)
                xaxis2=dict(rangeslider_visible=False),
                yaxis2=dict(side="right"),
            )

        _hdr_last_close = float(df["Close"].iloc[-1])
        _hdr_prev_close = float(df["Close"].iloc[-2]) if len(df) > 1 else _hdr_last_close
        _hdr_diff = _hdr_last_close - _hdr_prev_close
        _hdr_pct  = (_hdr_diff / _hdr_prev_close * 100) if _hdr_prev_close else 0.0
        if _hdr_diff > 0:
            _hdr_color, _hdr_arrow, _hdr_sign = "#00c853", "▲", "+"
        elif _hdr_diff < 0:
            _hdr_color, _hdr_arrow, _hdr_sign = "#ff4b4b", "▼", ""
        else:
            _hdr_color, _hdr_arrow, _hdr_sign = "#bbbbbb", "▬", ""
        st.markdown(
            f"## {ta_ticker} &nbsp;·&nbsp; "
            f"<span style='color:{_hdr_color}'>{_hdr_last_close:.2f}</span> &nbsp;&nbsp; "
            f"<span style='color:{_hdr_color};font-size:0.7em'>"
            f"{_hdr_arrow} {_hdr_sign}{_hdr_diff:.2f} ({_hdr_sign}{_hdr_pct:.2f}%)</span>"
            f" &nbsp;&nbsp;&nbsp;&nbsp; "
            f"<span style='color:#888;font-size:0.55em;font-family:monospace'>"
            f"{period.upper()} · {interval.upper()}</span>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

        # ============================================================
        # ANA GRAFİK REHBERİ (Expander)
        # ============================================================
        with st.expander("📖 Ana Grafikte Ne Ne Anlama Geliyor? (Detaylı Rehber)", expanded=False):
            st.markdown("""
### 🕯️ Mum Renkleri

Her mum 4 kategoriden birine atanır. Hiyerarşik sıralama: önce **Cyan** kontrol edilir, olmazsa **Sarı**, olmazsa **Kırmızı**, kalanlar **Yeşil**.

| Renk | Anlamı | Tetikleyici |
|---|---|---|
| 🔵 **Cyan (Güçlü Boğa)** | Taze AL sinyali | SuperTrend yukarı **VE** OBV birikim **VE** RSI aşırı alım değil **VE** önceki barda bu koşul yoktu |
| 🟢 **Yeşil (Boğa)** | Normal yükseliş bağlamı | Diğer üç kategoriye girmeyen mumlar (varsayılan) |
| 🟡 **Sarı (Kararsız)** | Yatay/düşük momentum | ADX zayıf **VE** RSI nötr bölgede (eşiklerin ortası ±5) |
| 🔴 **Kırmızı (Ayı)** | Momentumlu düşüş | Düşüş mumu **VE** MACD negatif |

**Gövde dolgu farkı:** Yükselen mumlar (Close ≥ Open) kategori renginde **dolu**. Düşen mumlar (Close < Open) **içi siyah**, kenarı kategori renginde. Böylece hem renk kategorisi hem yön tek bakışta görünür.

---

### 📈 Hareketli Ortalamalar & Trend

| Çizgi | Renk/Stil | Neyi Gösterir |
|---|---|---|
| **SMA Kısa** | Turuncu | Kısa vadeli trend ortalaması (varsayılan 20 bar). Fiyat altındaysa zayıflık, üstündeyse güç |
| **SMA Uzun** | Cyan | Orta vadeli ortalama (varsayılan 200 bar). Trend yönü anchor'ı |
| **KAMA** | Mor | Kaufman Adaptif MA — volatiliteye göre hız değiştirir. Yatayda düz, trend başlayınca hızlanır |
| **EMA 200** | Sarı, noktalı | Uzun vadeli trend filtresi. Fiyat üstündeyse "boğa piyasası", altındaysa "ayı piyasası" |
| **SuperTrend çizgisi** | Yeşil (boğa) / Kırmızı (ayı) | ATR tabanlı trend takip. Çizginin rengi mevcut rejimi söyler |
| **🔼 SuperTrend AL** | Yeşil kare, beyaz "AL" yazısı | ST rejimi AYI'dan BOĞA'ya geçti — trend değişim sinyali |
| **🔽 SuperTrend SAT** | Kırmızı kare, beyaz "SAT" yazısı | ST rejimi BOĞA'dan AYI'ya geçti |

💡 **İpucu:** SMA kısa > SMA uzun → "altın haç" (golden cross) bağlamı. EMA200 üstünde kalan bir fiyat, SMA ve KAMA'nın da yukarı eğimiyle birleşirse **çok katmanlı trend teyidi** vardır.

---

### 📊 Kanallar & Zarflar

| Element | Renk | Neyi Gösterir |
|---|---|---|
| **LRC Orta** | Beyaz kesikli | Linear Regression Channel — periyoda göre fiyatın istatistiksel orta çizgisi |
| **LRC Üst** | Gri noktalı | Orta + N standart sapma. Fiyat burada = kanalın üst sınırı, olası SAT bölgesi |
| **LRC Alt** | Gri noktalı | Orta - N standart sapma. Fiyat burada = kanalın alt sınırı, olası AL bölgesi |

---

### 📐 Fibonacci Seviyeleri

**Trend yönüne göre dinamik çizilir:**
- **Yükseliş trendinde** (📈 bull retracement): Son swing LOW pivotundan sonraki swing HIGH'a kadar çizilir.
  Seviyeler **destek** olarak görev yapar — fiyat geri çekilince bu seviyelerden tepki bekler.
- **Düşüş trendinde** (📉 bear retracement): Son swing HIGH pivotundan sonraki swing LOW'a kadar çizilir.
  Seviyeler **direnç** olarak görev yapar — fiyat tepki yaparken bu seviyelerden satıcı bekler.
- **Yatay/range piyasada**: Lookback range'inin global high-low'u kullanılır (geleneksel davranış).

Trend tespiti: Son `fib_lookback` barın ilk %25 ortalama fiyatı ile son %25 ortalaması karşılaştırılır.
%0.5'ten büyük fark varsa yön belirlenir.

**Yedi seviye:**

| Seviye | Renk (tipik) | Bull retracement (destek) | Bear retracement (direnç) |
|---|---|---|---|
| **0.0%** | Kırmızı | Swing dibi (pivot) | Swing di