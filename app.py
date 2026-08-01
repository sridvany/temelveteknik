import streamlit as st
import requests
import pandas as pd
import io
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="Ücretsiz Temel ve Teknik Analiz", page_icon="📊", layout="wide")

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


st.title("Ücretsiz Temel ve Teknik Analiz")
st.caption(
    "Eğitim amaçlıdır. Yatırım tavsiyesi içermez. Veri kaynakları "
    '<a href="https://finance.yahoo.com/" target="_blank">Yahoo Finance</a>'
    " ve "
    '<a href="https://www.tradingview.com/screener/" target="_blank">'
    "Tradingview</a>'dir.",
    unsafe_allow_html=True,
)
st.divider()

st.header("📊 Temel Analiz")


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
        kriter["nakit"] = cfo_nk >= 1
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

#### Yıldız nasıl hesaplanıyor? (⭐ 0–7)

Her sağlanan kriter 1 yıldız:

1. ROE ≥ %15 (kalite)
2. ROIC ≥ %10 (kaldıraçsız kalite)
3. CFO/Net Kâr ≥ 1 (kâr nakde dönüşüyor)
4. FCF Verimi > 0 (yatırımlar sonrası da nakit üretiyor)
5. Borç/Özkaynak ≤ 1 (bilanço sağlığı)
6. EPS büyümesi (YY) > 0 (kâr erimiyor — değer tuzağı freni)
7. F/K **ve** FD/FAVÖK kendi sektör medyanının altında (göreli ucuzluk)

Verisi eksik kriter değerlendirme dışı bırakılır ve o yıldız
kazanılamaz (ör. bankalarda FD/FAVÖK yoktur — en fazla 6 yıldız
alabilirler). En az 4 geçerli kriteri olmayan şirkete yıldız
verilmez ("—"). ⭐⭐⭐⭐⭐⭐⭐ "al" demek değildir; kalite + nakit +
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
| ⭐⭐⭐⭐⭐⭐⭐ | 85 | Kaliteli **ve** sektörünün yıldızı |
| ⭐⭐⭐☆☆☆☆ | 90 | Sektörünün en iyisi ama sektör zayıf (tuzak olabilir) |
| ⭐⭐⭐⭐⭐☆☆ | 40 | İyi şirket ama sektöründe daha cazibi var |

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
| **CFO/Net Kâr** | Faaliyet nakit akışı / Net kâr | Kâr gerçekten kasaya giriyor mu | 🔼 Yüksek (≥ 1) — sürekli < 1 ise kâr kağıt üzerinde olabilir |
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

    st.markdown(
        """
        **Ticker sembolünü öğrenmek için:**  
        <a href="https://finance.yahoo.com/lookup" target="_blank">
            finance.yahoo.com/lookup
        </a>
        """,
        unsafe_allow_html=True,
    )

    ta_ticker = st.text_input("Ticker Sembolü", "")

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


# Yıllık finansallar: istikrar kontrolü için (yıldız/skor hesabına GİRMEZ).
# yfinance genelde son 4 mali yılı verir; bazı sembollerde eksik/boş gelir.
# Satır adları yfinance sürümüne göre değişebildiği için her satırda
# alternatif isim listesi tutulur; ilk bulunan kullanılır.
# fmt: para / yuzde / kat / birim
YILLIK_GRUPLAR = [
    ("Gelir Tablosu", "fin", [
        ("Gelir", ["Total Revenue", "Operating Revenue"], "para"),
        ("Brüt Kâr", ["Gross Profit"], "para"),
        ("Faaliyet Kârı", ["Operating Income"], "para"),
        ("FAVÖK", ["EBITDA", "Normalized EBITDA"], "para"),
        ("Faiz Gideri", ["Interest Expense"], "para"),
        ("Vergi Öncesi Kâr", ["Pretax Income"], "para"),
        ("Vergi Karşılığı", ["Tax Provision"], "para"),
        ("Net Kâr", ["Net Income", "Net Income Common Stockholders"], "para"),
        ("Seyreltilmiş EPS", ["Diluted EPS", "Basic EPS"], "birim"),
        ("Ort. Hisse Sayısı",
         ["Diluted Average Shares", "Basic Average Shares"], "para"),
    ]),
    ("Bilanço", "bs", [
        ("Toplam Varlıklar", ["Total Assets"], "para"),
        ("Nakit ve Benzerleri",
         ["Cash And Cash Equivalents",
          "Cash Cash Equivalents And Short Term Investments"], "para"),
        ("Stoklar", ["Inventory"], "para"),
        ("Ticari Alacaklar", ["Accounts Receivable", "Receivables"], "para"),
        ("Toplam Borç", ["Total Debt"], "para"),
        ("Uzun Vadeli Borç", ["Long Term Debt"], "para"),
        ("Özkaynaklar",
         ["Stockholders Equity", "Total Equity Gross Minority Interest"],
         "para"),
        ("Dağıtılmamış Kârlar", ["Retained Earnings"], "para"),
    ]),
    ("Nakit Akışı", "cf", [
        ("Faaliyet Nakit Akışı",
         ["Operating Cash Flow", "Total Cash From Operating Activities"],
         "para"),
        ("Yatırım Harcaması (CapEx)", ["Capital Expenditure"], "para"),
        ("Serbest Nakit Akışı", ["Free Cash Flow"], "para"),
        ("Ödenen Temettü",
         ["Cash Dividends Paid", "Common Stock Dividend Paid"], "para"),
        ("Hisse Geri Alımı", ["Repurchase Of Capital Stock"], "para"),
        ("Alınan Borç", ["Issuance Of Debt"], "para"),
        ("Ödenen Borç", ["Repayment Of Debt"], "para"),
    ]),
]

# Ham satırlardan türetilenler: (ad, fmt, hesap fonksiyonu)
# h(ad) -> ilgili ham satır serisi (yoksa NaN serisi)
YILLIK_TURETILMIS = [
    ("Brüt Marj %", "yuzde",
     lambda h: 100 * h("Brüt Kâr") / h("Gelir")),
    ("Faaliyet Marjı %", "yuzde",
     lambda h: 100 * h("Faaliyet Kârı") / h("Gelir")),
    ("Net Marj %", "yuzde",
     lambda h: 100 * h("Net Kâr") / h("Gelir")),
    ("ROE %", "yuzde",
     lambda h: 100 * h("Net Kâr") / h("Özkaynaklar").where(h("Özkaynaklar") > 0)),
    ("ROA %", "yuzde",
     lambda h: 100 * h("Net Kâr") / h("Toplam Varlıklar").where(
         h("Toplam Varlıklar") > 0)),
    ("FAVÖK / Faiz Gideri", "kat",
     lambda h: h("FAVÖK") / h("Faiz Gideri").abs()),
    ("CFO / Net Kâr", "kat",
     lambda h: h("Faaliyet Nakit Akışı") / h("Net Kâr").where(h("Net Kâr") > 0)),
    ("Net Borç / FAVÖK", "kat",
     lambda h: (h("Toplam Borç") - h("Nakit ve Benzerleri"))
     / h("FAVÖK").where(h("FAVÖK") > 0)),
    ("Borç / Özkaynak", "kat",
     lambda h: h("Toplam Borç") / h("Özkaynaklar").where(h("Özkaynaklar") > 0)),
]

# İstikrar uyarısı verilecek satırlar (negatifse dikkat)
YILLIK_NEGATIF_UYARI = ("Net Kâr", "Faaliyet Nakit Akışı",
                        "Serbest Nakit Akışı", "Özkaynaklar")


def _yillik_seri(tablo, adaylar) -> pd.Series | None:
    if tablo is None or getattr(tablo, "empty", True):
        return None
    for aday in adaylar:
        if aday in tablo.index:
            seri = tablo.loc[aday]
            if isinstance(seri, pd.DataFrame):    # tekrar eden index adı
                seri = seri.iloc[0]
            return pd.to_numeric(seri, errors="coerce")
    return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_yillik_finansallar(symbol: str):
    """(gruplar, formatlar) döndürür. gruplar: {grup_adı: DataFrame}"""
    try:
        t = yf.Ticker(symbol)
        tablolar = {"fin": t.financials, "bs": t.balance_sheet, "cf": t.cashflow}
    except Exception:
        return {}, {}

    ham, fmtler, gruplar = {}, {}, {}
    for grup_ad, kaynak, satirlar in YILLIK_GRUPLAR:
        bulunan = {}
        for ad, adaylar, fmt in satirlar:
            seri = _yillik_seri(tablolar.get(kaynak), adaylar)
            if seri is None:
                continue
            # CapEx / temettü / geri alım muhasebede negatif (nakit çıkışı)
            if ad in ("Yatırım Harcaması (CapEx)", "Ödenen Temettü",
                      "Hisse Geri Alımı", "Ödenen Borç"):
                seri = seri.abs()
            bulunan[ad] = seri
            ham[ad] = seri
            fmtler[ad] = fmt
        if bulunan:
            gruplar[grup_ad] = bulunan

    if not ham:
        return {}, {}

    yillar = sorted({pd.to_datetime(c).year
                     for seri in ham.values() for c in seri.index})

    def _hizala(seri):
        s = seri.copy()
        s.index = [pd.to_datetime(c).year for c in s.index]
        s = s[~s.index.duplicated()]
        return s.reindex(yillar)

    ham_h = {ad: _hizala(s) for ad, s in ham.items()}
    bos = pd.Series(np.nan, index=yillar)

    def h(ad):
        return ham_h.get(ad, bos)

    turetilmis = {}
    for ad, fmt, hesap in YILLIK_TURETILMIS:
        try:
            deger = hesap(h).replace([np.inf, -np.inf], np.nan)
        except Exception:
            continue
        if deger.notna().any():
            turetilmis[ad] = deger
            fmtler[ad] = fmt

    cikti = {}
    for grup_ad, bulunan in gruplar.items():
        cikti[grup_ad] = pd.DataFrame(
            {ad: _hizala(s) for ad, s in bulunan.items()}
        ).T.dropna(axis=1, how="all")
    if turetilmis:
        cikti["Türetilmiş Oranlar"] = pd.DataFrame(turetilmis).T.dropna(
            axis=1, how="all"
        )
    return cikti, fmtler


def kisa_sayi(v) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    a = abs(v)
    if a >= 1e12:
        return f"{v / 1e12:,.2f} Tn"
    if a >= 1e9:
        return f"{v / 1e9:,.2f} Mr"
    if a >= 1e6:
        return f"{v / 1e6:,.2f} Mn"
    if a >= 1e3:
        return f"{v / 1e3:,.1f} B"
    return f"{v:,.0f}"


def yillik_bicim(v, fmt: str) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    if fmt == "yuzde":
        return f"{v:,.1f}%"
    if fmt == "kat":
        return f"{v:,.2f}x"
    if fmt == "birim":
        return f"{v:,.2f}"
    return kisa_sayi(v)


def yillik_tablo_goster(tablo: pd.DataFrame, fmtler: dict):
    gorunum = tablo.apply(
        lambda satir: satir.map(
            lambda v: yillik_bicim(v, fmtler.get(satir.name, "para"))
        ),
        axis=1,
    )
    st.dataframe(gorunum, use_container_width=True)


PLOTLY_CONFIG = dict(scrollZoom=True, displayModeBar=True,
    modeBarButtonsToAdd=["pan2d", "zoomIn2d", "zoomOut2d", "resetScale2d"],
    modeBarButtonsToRemove=["lasso2d", "select2d"])


def sub_layout(height=250):
    return dict(template="plotly_dark", height=height, margin=dict(t=30, b=30), dragmode="pan")


# ============================================================
# 8. ANA MANTIK
# ============================================================
if ta_calistir and ta_ticker:
    _fin_gruplar, _fin_fmt = fetch_yillik_finansallar(ta_ticker)
    with st.expander(
        f"📅 {ta_ticker} — Yıllık Finansallar (istikrar kontrolü)", expanded=False
    ):
        if not _fin_gruplar:
            st.caption(
                "Yahoo Finance bu sembol için yıllık finansal tablo vermiyor."
            )
        else:
            # Negatif yıl uyarıları (istikrar): tüm gruplarda ara
            _uyari = []
            for _tablo in _fin_gruplar.values():
                for _ad in YILLIK_NEGATIF_UYARI:
                    if _ad in _tablo.index:
                        _satir = _tablo.loc[_ad]
                        _neg = [str(y) for y in _satir.index
                                if pd.notna(_satir[y]) and _satir[y] < 0]
                        if _neg:
                            _uyari.append(f"**{_ad}** negatif: {', '.join(_neg)}")
            if _uyari:
                st.warning("⚠️ " + "  \n".join(_uyari))
            else:
                st.success(
                    "✅ Net kâr, nakit akışları ve özkaynak tablodaki tüm "
                    "yıllarda pozitif."
                )

            for _grup_ad, _tablo in _fin_gruplar.items():
                st.markdown(f"**{_grup_ad}**")
                yillik_tablo_goster(_tablo, _fin_fmt)

            st.caption(
                "Yıldız ve Sektör Skoru hesabına girmez — istikrarı gözle "
                "değerlendirmek için. Boş satırlar (—) Yahoo Finance'ın o "
                "sembol için vermediği kalemlerdir; bankalarda FAVÖK/CapEx "
                "gibi kalemler tanımlı değildir. Kaynak: Yahoo Finance "
                "yıllık tabloları."
            )

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
| **0.0%** | Kırmızı | Swing dibi (pivot) | Swing dibi (hedef) |
| **23.6%** | Turuncu | Hafif geri çekilme — güçlü trendde tepki beklenir | Zayıf direnç |
| **38.2%** | Sarı | Normal correction seviyesi | Orta direnç |
| **50.0%** | Yeşil | Psikolojik seviye (Fib değil ama eklenmiştir) | Psikolojik direnç |
| **61.8%** | Mavi | Altın oran — en önemli destek | Altın oran — en önemli direnç |
| **78.6%** | Mor | Derin geri çekilme — trend zayıflıyor | Trend dönüş yakın |
| **100.0%** | Kırmızı | Swing tepesi | Swing tepesi (pivot) |

💡 Karar matrisinde Fibonacci satırında **trend yönü** (bull/bear/range) ve **en yakın seviye** gösterilir.

---

### 🎯 Yatay Destek / Direnç

Swing pivot tespiti + ATR tabanlı gruplama ile otomatik çiziliyor.

| Görünüm | Anlamı |
|---|---|
| **Yeşil yatay çizgi** | Aktif **destek** (fiyatın altında) |
| **Kırmızı yatay çizgi** | Aktif **direnç** (fiyatın üstünde) |
| **Gri yatay çizgi** | Kırılmış seviye — artık aktif değil, referans için duruyor |

**Kalınlık/stil dokunuş sayısını söyler:**
- **İnce, dash** (— —) → 1 dokunuş (zayıf)
- **Orta, dashdot** (—·—·) → 2 dokunuş (orta)
- **Kalın, solid** (———) → 3+ dokunuş (güçlü)

**🔄 Role-Reversal (Rol Değişimi):**
- Fiyat eski bir direnci kırıp yukarı geçerse → o seviye **destek** rolüne geçer (yeşile döner)
- Fiyat eski bir desteği kırıp aşağı inerse → o seviye **direnç** rolüne geçer (kırmızıya döner)
- Klasik teknik analiz prensibi: "eski direnç yeni destektir"

---

### 📏 Diyagonal Trend Çizgileri (Legend'dan aç/kapa)

Pivot high'ları birleştirince **direnç TL**, pivot low'ları birleştirince **destek TL** oluşur. Legend başlığı "Trend Çizgileri" altında:

| Görünüm | Anlamı |
|---|---|
| **↗ Destek TL (xN)** yeşil | Yükselen trend çizgisi, N dokunuşla doğrulanmış |
| **↘ Direnç TL (xN)** kırmızı | Düşen trend çizgisi, N dokunuşla doğrulanmış |
| **Mavimsi dolgu alan** | Paralel kanal — fiyatın içinde hareket etmesi beklenen koridor |

Dokunuş sayısı (xN) arttıkça çizgi daha kalın çizilir. 5+ dokunuşlu bir trend çizgisinin kırılması çok anlamlıdır.

---

### 🔻 Divergence İşaretleri

| Sembol | Renk | Anlamı |
|---|---|---|
| **🔺 Bullish Div** | Yeşil üçgen (mumun altında) | Fiyat daha düşük dip yaptı **ama** RSI veya MACD daha yüksek dip yaptı → gizli güç, dönüş sinyali |
| **🔻 Bearish Div** | Kırmızı üçgen (mumun üstünde) | Fiyat daha yüksek tepe yaptı **ama** RSI veya MACD daha düşük tepe yaptı → zayıflama, düşüş uyarısı |

💡 Divergence tek başına giriş sinyali değildir — başka teyitlerle birlikte değerlendir.

---

### 📦 Volume Profile (Sağ Panel) & POC

Grafiğin sağında yatay hacim çubukları var. Her çubuk, o fiyat seviyesinde geçmişte **ne kadar hacim** gerçekleştiğini gösterir.

| Element | Renk | Anlamı |
|---|---|---|
| **POC (Point of Control)** | Turuncu kesikli yatay çizgi + etiket | En yüksek hacimli fiyat seviyesi — piyasanın "adil değer"i kabul edilir |
| **Mavi-yeşil tonlu çubuklar** | Yoğunluğa göre renk | Hacim arttıkça daha doygun yeşile kayar |
| **Son fiyat etiketi** | Yeşil (POC üstünde) / Kırmızı (POC altında) | Fiyatın POC'a göre konumu |

**Nasıl yorumlanır?**
- Fiyat POC'un **altında** → piyasa ucuza düşmüş, alıcılar devreye girebilir
- Fiyat POC'un **üstünde** → değerinin üstünde, satış baskısı gelebilir
- **Boş hacim bölgeleri** (az çubuk) = fiyat hızlı geçiyor, güçlü hareket zonu
- **Dolu hacim bölgeleri** = konsolidasyon, güçlü destek/direnç

---

### 💡 Hepsini Birlikte Nasıl Okumalı?

Görsel bir **çoklu-teyit sistemi** olarak tasarlanmış. Tek bir sinyale değil, **birbiriyle örtüşen** sinyallere güvenin:

1. **Büyük resim:** Fiyat EMA200'ün neresinde? Trend mi yatay mı?
2. **Rejim:** SuperTrend ne diyor? Kısa MA uzun MA'nın neresinde?
3. **Seviye:** Fiyat hangi Fib / LRC / S/R seviyesinde?
4. **Momentum:** Mum rengi ne? Cyan/Yeşil mi, Sarı/Kırmızı mı?
5. **Uyarı:** Divergence var mı? Kırılmış seviyeler hangileri?
6. **Hacim:** POC'un neresinde? Volume profile dağılımı nasıl?

Üç veya daha fazla sinyal **aynı yönü gösteriyorsa** konfidans yüksektir. Çelişiyorsa → **bekle**.

> ⚠️ **Not:** Bu rehber sadece grafik elementlerini açıklar. Alt sekmelerdeki göstergelerin (RSI, MACD, ADX vb.) detaylı yorumu her sekmenin kendi "📖 Nasıl Okunur?" bölümündedir.
""")

        # ============================================================
        # ALT GRAFİKLER
        # ============================================================
        tab_bb, tab_adx, tab_ichi, tab_kama, tab_st, tab_stoch, tab_wt, tab_rsi, tab_macd, tab_obv, tab_div = st.tabs([
            "Bollinger Bands", "ADX", "Ichimoku", "KAMA & LRC", "SuperTrend",
            "Stoch RSI", "WaveTrend", "RSI", "MACD", "OBV", "Divergence"])

        # Eski tab1..tab11 değişken isimlerini koru (içerik bloklarını değiştirmemek için)
        tab1  = tab_rsi
        tab2  = tab_macd
        tab3  = tab_adx
        tab4  = tab_obv
        tab5  = tab_stoch
        tab6  = tab_ichi
        tab7  = tab_st
        tab8  = tab_kama
        tab10 = tab_wt
        tab11 = tab_div

        with tab1:
            f = go.Figure()
            f.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI",
                line=dict(color="rgba(0,200,100,0.9)", width=1.5),
                fill="tozeroy", fillcolor="rgba(0,200,100,0.15)"))
            f.add_trace(go.Scatter(x=df.index, y=df["RSI_MA"],
                name=f"RSI MA({rsi_ma_period})", line=dict(color="yellow", width=1.5, dash="dot")))
            f.add_hline(y=p_rsi["rsi_lower"], line_dash="dash", line_color="lime",
                annotation_text=f"Aşırı Satım ({p_rsi['rsi_lower']})")
            f.add_hline(y=p_rsi["rsi_upper"], line_dash="dash", line_color="red",
                annotation_text=f"Aşırı Alım ({p_rsi['rsi_upper']})")
            f.add_hline(y=50, line_dash="dot", line_color="gray")
            bull_div_rsi = df["Div_RSI"] == 1
            bear_div_rsi = df["Div_RSI"] == -1
            if bull_div_rsi.any():
                f.add_trace(go.Scatter(x=df.index[bull_div_rsi], y=df["RSI"][bull_div_rsi],
                    name="Bullish Div", mode="markers",
                    marker=dict(color="lime", size=10, symbol="triangle-up")))
            if bear_div_rsi.any():
                f.add_trace(go.Scatter(x=df.index[bear_div_rsi], y=df["RSI"][bear_div_rsi],
                    name="Bearish Div", mode="markers",
                    marker=dict(color="red", size=10, symbol="triangle-down")))
            f.update_layout(**sub_layout())
            st.plotly_chart(f, use_container_width=True, config=PLOTLY_CONFIG)
            with st.expander("📖 RSI Nasıl Okunur?"):
                st.markdown("""
**RSI (Relative Strength Index)** — 0–100 arasında salınan momentum göstergesidir.

| Bölge | Anlam |
|---|---|
| RSI < Aşırı Satım eşiği | 🟢 Aşırı satılmış → potansiyel AL sinyali |
| RSI > Aşırı Alım eşiği | 🔴 Aşırı alınmış → potansiyel SAT sinyali |
| RSI ~ 50 | ⚪ Nötr bölge |

- **RSI MA (sarı noktalı):** RSI'nın hareketli ortalaması. RSI bu çizgiyi yukarı keserse momentum güçleniyor demektir.
- **Bullish Divergence 🔺:** Fiyat düşük dip yaparken RSI yüksek dip yapıyor → güçlü dönüş sinyali.
- **Bearish Divergence 🔻:** Fiyat yüksek tepe yaparken RSI alçak tepe yapıyor → zayıflama uyarısı.
                """)

        with tab2:
            f = go.Figure()
            f.add_trace(go.Scatter(x=df.index, y=df["MACD"], name="MACD", line=dict(color="cyan")))
            f.add_trace(go.Scatter(x=df.index, y=df["MACD_S"], name="Sinyal", line=dict(color="orange")))
            hist = df["MACD"] - df["MACD_S"]
            f.add_trace(go.Bar(x=df.index, y=hist, name="Histogram",
                marker_color=["lime" if v >= 0 else "red" for v in hist], opacity=0.5))
            bull_div_macd = df["Div_MACD"] == 1
            bear_div_macd = df["Div_MACD"] == -1
            if bull_div_macd.any():
                f.add_trace(go.Scatter(x=df.index[bull_div_macd], y=df["MACD"][bull_div_macd],
                    name="Bullish Div", mode="markers",
                    marker=dict(color="lime", size=10, symbol="triangle-up")))
            if bear_div_macd.any():
                f.add_trace(go.Scatter(x=df.index[bear_div_macd], y=df["MACD"][bear_div_macd],
                    name="Bearish Div", mode="markers",
                    marker=dict(color="red", size=10, symbol="triangle-down")))
            f.update_layout(**sub_layout())
            st.plotly_chart(f, use_container_width=True, config=PLOTLY_CONFIG)
            with st.expander("📖 MACD Nasıl Okunur?"):
                st.markdown("""
**MACD (Moving Average Convergence Divergence)** — trend yönü ve momentumu ölçer.

| Unsur | Anlam |
|---|---|
| MACD > Sinyal çizgisi | 🟢 Yukarı momentum → AL eğilimi |
| MACD < Sinyal çizgisi | 🔴 Aşağı momentum → SAT eğilimi |
| Histogram yeşil & büyüyor | 🟢 Momentum güçleniyor |
| Histogram kırmızı & büyüyor | 🔴 Momentum zayıflıyor |

- **Sıfır çizgisi geçişi:** MACD sıfırı yukarı kesiyor = güçlü boğa sinyali; aşağı kesiyor = ayı sinyali.
- **Bullish Divergence 🔺:** Fiyat düşük dip, MACD yüksek dip → trend dönüş öncüsü.
- **Bearish Divergence 🔻:** Fiyat yüksek tepe, MACD alçak tepe → zirve uyarısı.
                """)

        with tab3:
            f = go.Figure()
            f.add_trace(go.Scatter(x=df.index, y=df["ADX"],      name="ADX", line=dict(color="yellow", width=2)))
            f.add_trace(go.Scatter(x=df.index, y=df["PLUS_DI"],  name="+DI", line=dict(color="lime", dash="dot")))
            f.add_trace(go.Scatter(x=df.index, y=df["MINUS_DI"], name="-DI", line=dict(color="red",  dash="dot")))
            f.add_hline(y=p_adx["adx_threshold"], line_dash="dash", line_color="white",
                annotation_text=f"Trend Eşiği ({p_adx['adx_threshold']})")
            f.update_layout(**sub_layout())
            st.plotly_chart(f, use_container_width=True, config=PLOTLY_CONFIG)
            with st.expander("📖 ADX Nasıl Okunur?"):
                st.markdown("""
**ADX (Average Directional Index)** — trendin gücünü ölçer (yön değil, sadece güç).

| ADX Değeri | Trend Gücü |
|---|---|
| < 20 | Zayıf / yatay piyasa |
| 20–25 | Trend oluşuyor |
| > 25 | Güçlü trend |
| > 40 | Çok güçlü trend |

- **+DI (yeşil):** Yukarı yönlü hareketin gücü.
- **-DI (kırmızı):** Aşağı yönlü hareketin gücü.
- **+DI > -DI ve ADX > eşik:** 🟢 Güçlü yükseliş trendi.
- **-DI > +DI ve ADX > eşik:** 🔴 Güçlü düşüş trendi.
- ADX düşükken verilen sinyaller güvenilmezdir.
                """)

        with tab4:
            f = go.Figure()
            f.add_trace(go.Scatter(x=df.index, y=df["OBV"], name="OBV", line=dict(color="dodgerblue")))
            f.add_trace(go.Scatter(x=df.index, y=obv_sma_short,
                name=f"OBV SMA {obv_short}", line=dict(color="orange", dash="dot")))
            f.add_trace(go.Scatter(x=df.index, y=obv_sma_long,
                name=f"OBV SMA {obv_long}", line=dict(color="cyan", dash="dot")))
            bull_div_obv = df["Div_OBV"] == 1
            bear_div_obv = df["Div_OBV"] == -1
            if bull_div_obv.any():
                f.add_trace(go.Scatter(x=df.index[bull_div_obv], y=df["OBV"][bull_div_obv],
                    name="Bullish Div", mode="markers",
                    marker=dict(color="lime", size=10, symbol="triangle-up")))
            if bear_div_obv.any():
                f.add_trace(go.Scatter(x=df.index[bear_div_obv], y=df["OBV"][bear_div_obv],
                    name="Bearish Div", mode="markers",
                    marker=dict(color="red", size=10, symbol="triangle-down")))
            f.update_layout(**sub_layout())
            st.plotly_chart(f, use_container_width=True, config=PLOTLY_CONFIG)
            with st.expander("📖 OBV Nasıl Okunur?"):
                st.markdown("""
**OBV (On-Balance Volume)** — hacim akışını kümülatif olarak izler; fiyat hareketini önceden haber verebilir.

| Durum | Anlam |
|---|---|
| OBV yükseliyor, fiyat yükseliyor | 🟢 Trend onaylanıyor |
| OBV yükseliyor, fiyat düşüyor | 🟢 Gizli birikim → potansiyel yukarı kırılım |
| OBV düşüyor, fiyat yükseliyor | 🔴 Dağıtım var → zayıflama uyarısı |
| OBV düşüyor, fiyat düşüyor | 🔴 Trend onaylanıyor |

- **Kısa SMA (turuncu) > Uzun SMA (cyan):** OBV momentumu pozitif → AL eğilimi.
- **Kısa SMA < Uzun SMA:** OBV momentumu negatif → SAT eğilimi.
- **Bullish Divergence 🔺:** Fiyat yeni dip yaparken OBV yapmıyor → satıcı tükenmesi, dönüş habercisi.
- **Bearish Divergence 🔻:** Fiyat yeni tepe yaparken OBV yapmıyor → alıcı yorgunluğu, zayıflama.
- OBV'nin mutlak değeri değil, eğimi önemlidir.
                """)

        with tab5:
            f = go.Figure()
            f.add_trace(go.Scatter(x=df.index, y=df["StochRSI_K"], name="%K", line=dict(color="magenta")))
            f.add_trace(go.Scatter(x=df.index, y=df["StochRSI_D"], name="%D", line=dict(color="orange", dash="dot")))
            f.add_hline(y=stoch_lower, line_dash="dash", line_color="lime",
                annotation_text=f"Aşırı Satım ({stoch_lower})")
            f.add_hline(y=stoch_upper, line_dash="dash", line_color="red",
                annotation_text=f"Aşırı Alım ({stoch_upper})")
            f.update_layout(**sub_layout())
            st.plotly_chart(f, use_container_width=True, config=PLOTLY_CONFIG)
            with st.expander("📖 Stochastic RSI Nasıl Okunur?"):
                st.markdown("""
**Stochastic RSI** — RSI'ya uygulanan Stochastic göstergesidir. RSI'dan daha hassas ve hızlıdır.

| Bölge | Anlam |
|---|---|
| %K < Aşırı Satım eşiği | 🟢 Aşırı satılmış → AL bölgesi |
| %K > Aşırı Alım eşiği | 🔴 Aşırı alınmış → SAT bölgesi |

- **%K (mor):** Hızlı çizgi — anlık sinyal verir.
- **%D (turuncu noktalı):** %K'nın ortalaması — yavaş, daha güvenilir.
- **%K, %D'yi aşırı satım bölgesinde yukarı kesiyor:** 🟢 Güçlü AL sinyali.
- **%K, %D'yi aşırı alım bölgesinde aşağı kesiyor:** 🔴 Güçlü SAT sinyali.
- RSI aşırı bölgelerde değilken Stoch RSI sinyalleri daha az güvenilirdir.
                """)

        with tab6:
            f = go.Figure()
            f.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"],
                low=df["Low"], close=df["Close"], name="Fiyat"))
            f.add_trace(go.Scatter(x=df.index, y=df["Tenkan"], name="Tenkan-sen", line=dict(color="cyan",  width=1)))
            f.add_trace(go.Scatter(x=df.index, y=df["Kijun"],  name="Kijun-sen",  line=dict(color="red",   width=1)))
            f.add_trace(go.Scatter(x=df.index, y=df["Chikou"], name="Chikou Span",
                line=dict(color="rgba(120,180,255,0.7)", width=1, dash="dash")))

            # Senkou A ve B çizgileri (görsel referans)
            f.add_trace(go.Scatter(x=df.index, y=df["Senkou_A"], name="Senkou A",
                line=dict(color="rgba(0,255,100,0.6)", width=0.5, dash="dot")))
            f.add_trace(go.Scatter(x=df.index, y=df["Senkou_B"], name="Senkou B",
                line=dict(color="rgba(255,80,80,0.6)", width=0.5, dash="dot")))

            # ── Koşullu renkli bulut (Kumo) ──
            # Senkou A > Senkou B → YEŞİL (bullish)
            # Senkou A < Senkou B → KIRMIZI (bearish)
            # Plotly'de koşullu fill için her noktada "max" ve "min" çizip maskelemek gerekiyor
            sa = df["Senkou_A"].values
            sb = df["Senkou_B"].values
            # Bullish maske (A > B)
            sa_bull = np.where(sa >= sb, sa, np.nan)
            sb_bull = np.where(sa >= sb, sb, np.nan)
            # Bearish maske (A < B)
            sa_bear = np.where(sa < sb,  sa, np.nan)
            sb_bear = np.where(sa < sb,  sb, np.nan)

            # Yeşil bulut (bullish)
            f.add_trace(go.Scatter(x=df.index, y=sb_bull, name="Yeşil Bulut (A>B)",
                line=dict(width=0), showlegend=False, hoverinfo="skip"))
            f.add_trace(go.Scatter(x=df.index, y=sa_bull, name="Yeşil Bulut 🟢",
                line=dict(width=0), fill="tonexty",
                fillcolor="rgba(0,255,100,0.18)", hoverinfo="skip",
                legendgroup="kumo_bull"))
            # Kırmızı bulut (bearish)
            f.add_trace(go.Scatter(x=df.index, y=sb_bear, name="Kırmızı Bulut (A<B)",
                line=dict(width=0), showlegend=False, hoverinfo="skip"))
            f.add_trace(go.Scatter(x=df.index, y=sa_bear, name="Kırmızı Bulut 🔴",
                line=dict(width=0), fill="tonexty",
                fillcolor="rgba(255,80,80,0.18)", hoverinfo="skip",
                legendgroup="kumo_bear"))

            f.update_layout(**sub_layout(height=350), xaxis_rangeslider_visible=False)
            st.plotly_chart(f, use_container_width=True, config=PLOTLY_CONFIG)
            with st.expander("📖 Ichimoku Nasıl Okunur?"):
                st.markdown("""
**Ichimoku Kinko Hyo** — trend yönü, destek/direnç ve momentum'u tek grafikte gösterir.
Goichi Hosoda'nın 1930'larda geliştirdiği klasik 5'li set kullanılır.

| Unsur | Renk | Anlam |
|---|---|---|
| Tenkan-sen | Cyan | Kısa vadeli denge çizgisi (9 bar) |
| Kijun-sen | Kırmızı | Orta vadeli denge çizgisi (26 bar) |
| Senkou Span A | Yeşil | Bulutun üst sınırı |
| Senkou Span B | Kırmızı | Bulutun alt sınırı |
| **Chikou Span** | **Mavi (kesikli)** | **Kapanışın 26 bar geriye kaydırılmış hali — trend teyit çizgisi** |

**Okuma Kuralları:**
- **Fiyat bulutun üstünde:** 🟢 Yükseliş trendi.
- **Fiyat bulutun altında:** 🔴 Düşüş trendi.
- **Fiyat bulut içinde:** ⚪ Konsolidasyon.
- **Tenkan > Kijun:** 🟢 Kısa vadeli momentum pozitif.
- **Yeşil bulut (Span A > Span B):** Boğa piyasası.
- **Kırmızı bulut (Span B > Span A):** Ayı piyasası.
- **Chikou geçmiş fiyatların üstünde:** 🟢 Trend teyitli — bugünkü kapanış 26 bar öncesinden yüksek.
- **Chikou geçmiş fiyatların altında:** 🔴 Trend teyitli — bugünkü kapanış 26 bar öncesinden düşük.

**Sinyal Mantığı (Üçlü Teyit — Hosoda klasiği):**
Sistem AL/SAT üretmek için **üç koşulun birden** sağlanmasını ister:
1. Tenkan-Kijun cross (kısa vade momentum)
2. Fiyat-Bulut pozisyonu (uzun vade trend)
3. Chikou onayı (geçmişle kıyas — Hosoda'nın klasik kullanımı)

Bu konservatif yapı sinyali nadir ama güvenilir kılar. Düşük volatilite dönemlerinde
sinyal yine üretilir ama karar matrisinde "düşük vol" uyarısı görürsünüz — kararı
kullanıcı bağlama göre değerlendirir.

⚠️ **Parametreler:** 9-26-52 değerleri Hosoda'nın orijinal ayarlarıdır ve dünya çapında izlenir.
Schelling noktası etkisiyle bu seviyelerde fiyat tepkisi oluşur. Optimize etmek değil, **sabitlemek** doğrudur.
                """)

        with tab7:
            f = go.Figure()
            f.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"],
                low=df["Low"], close=df["Close"], name="Fiyat"))
            f.add_trace(go.Scatter(x=df.index[bull_st], y=df["SuperTrend"][bull_st],
                name="SuperTrend (Boğa)", mode="lines", line=dict(color="lime", width=2)))
            f.add_trace(go.Scatter(x=df.index[bear_st], y=df["SuperTrend"][bear_st],
                name="SuperTrend (Ayı)", mode="lines", line=dict(color="red", width=2)))
            if st_buy_signal.any():
                f.add_trace(go.Scatter(
                    x=df.index[st_buy_signal], y=df["SuperTrend"][st_buy_signal],
                    name="AL", mode="markers+text",
                    marker=dict(symbol="square", color="#00c853", size=18, line=dict(width=0)),
                    text="AL",
                    textfont=dict(color="white", size=8, family="Arial Black"),
                    textposition="middle center"))
            if st_sell_signal.any():
                f.add_trace(go.Scatter(
                    x=df.index[st_sell_signal], y=df["SuperTrend"][st_sell_signal],
                    name="SAT", mode="markers+text",
                    marker=dict(symbol="square", color="#d50000", size=18, line=dict(width=0)),
                    text="SAT",
                    textfont=dict(color="white", size=8, family="Arial Black"),
                    textposition="middle center"))
            f.update_layout(**sub_layout(height=350), xaxis_rangeslider_visible=False)
            st.plotly_chart(f, use_container_width=True, config=PLOTLY_CONFIG)
            with st.expander("📖 SuperTrend Nasıl Okunur?"):
                st.markdown("""
**SuperTrend** (Olivier Seban, 2008) — ATR tabanlı dinamik destek/direnç + trailing stop göstergesidir.

**İki katmanlı bilgi sağlar:**

**1. Rejim (sürekli):** Çizgi rengi mevcut trendi gösterir, her bar günceldir.

| Durum | Anlam |
|---|---|
| Çizgi yeşil (fiyatın altında) | 🟢 Yükseliş rejimi — çizgi destek seviyesi (trailing stop) |
| Çizgi kırmızı (fiyatın üstünde) | 🔴 Düşüş rejimi — çizgi direnç seviyesi |

**2. Sinyal (event-based):** Yalnızca yön değişiminde (flip) üretilir.

| İşaret | Anlam |
|---|---|
| 🟩 AL kutusu | ⚡ Flip-up: ayıdan boğaya geçiş, **yeni** AL sinyali |
| 🟥 SAT kutusu | ⚡ Flip-down: boğadan ayıya geçiş, **yeni** SAT sinyali |

Trend devam ettiği sürece (flip yok) yeni sinyal üretilmez — bu **doğru** davranıştır.
SuperTrend'in özgün gücü "bant kırılımıyla yön değişir" mantığında saklıdır;
her bar AL/SAT üretmek bu güçten faydalanmaz.

**Trailing Stop kullanımı:**
- Boğa modunda → SuperTrend çizgisi = stop loss seviyesi
- Fiyat çizginin altına düşerse → otomatik flip + çıkış sinyali
- Karar matrisinde "Çizgi: X (fiyatın %Y altında)" şeklinde görürsünüz

**Parametreler:**
- **ATR Periyodu:** Volatilite hesabı penceresi (klasik 10).
- **ATR Çarpanı:** Band genişliği. Yüksek değer → az sinyal, az whipsaw, ama geç giriş/çıkış. (klasik 3.0)

**İpuçları:**
- "Flip yakın" uyarısı (çizgi-fiyat mesafesi <%1): pozisyon kapama hazırlığı yap.
- "Flip'ten X bar" göstergesi: trendin ne kadar olgunlaştığını söyler.
- ADX > eşik ile birlikte kullanım sinyal kalitesini artırır.
                """)

        with tab8:
            f = go.Figure()
            f.add_trace(go.Scatter(x=df.index, y=close, name="Fiyat", line=dict(color="white", width=1)))
            f.add_trace(go.Scatter(x=df.index, y=df["KAMA"], name="KAMA", line=dict(color="violet", width=2)))
            f.add_trace(go.Scatter(x=df.index, y=df["LRC_Mid"], name="LRC Orta",
                line=dict(color="white", dash="dash", width=1)))
            f.add_trace(go.Scatter(x=df.index, y=df["LRC_Upper"], name="LRC Üst",
                line=dict(color="rgba(200,200,200,0.6)", dash="dot")))
            f.add_trace(go.Scatter(x=df.index, y=df["LRC_Lower"], name="LRC Alt",
                line=dict(color="rgba(200,200,200,0.6)", dash="dot"),
                fill="tonexty", fillcolor="rgba(150,150,150,0.07)"))
            f.update_layout(**sub_layout(height=350))
            st.plotly_chart(f, use_container_width=True, config=PLOTLY_CONFIG)
            with st.expander("📖 KAMA & LR Channel Nasıl Okunur?"):
                st.markdown("""
**KAMA (Kaufman Adaptive Moving Average)** — Perry Kaufman 1995. Piyasa koşullarına göre hızını adapte eden akıllı ortalama.

**Felsefe:**
KAMA klasik MA gibi **cross sinyali için değil, eğim için** tasarlanmıştır.
"Fiyat KAMA üstünde" SMA'larla zaten ölçülüyor — KAMA'nın değeri **kendi yönü ve ER kalitesidir**.

| Bileşen | Anlam |
|---|---|
| **KAMA eğimi** | Yukarı = trend yukarı, aşağı = trend aşağı, yatay = beklemede |
| **ER (Efficiency Ratio)** | 0–1 arası "yön etkinliği". 1 = mükemmel trend, 0 = tam gürültü |

**Sinyal Mantığı:**
- KAMA son 3 barda yukarı eğimli **VE** ER ≥ 0.30 → 🟢 AL
- KAMA son 3 barda aşağı eğimli **VE** ER ≥ 0.30 → 🔴 SAT
- ER < 0.30 → ⚠️ Yatay/gürültü, sinyal sıfırlanır

**ER yorumu:**
| ER | Anlam |
|---|---|
| > 0.50 | 🔥 Güçlü trend — sinyal çok güvenilir |
| 0.30 – 0.50 | ⚖️ Orta momentum — sinyal geçerli |
| < 0.30 | ⚠️ Yatay/gürültü — KAMA susar |

**Ek bilgi (bağlamsal):**
- Fiyat-KAMA arası yüzde uzaklık trend gücünü gösterir ama tek başına sinyal değildir.
- ATR filtresi yerine ER filtresi kullanılır: ATR mutlak volatiliteyi, ER yön kalitesini ölçer.
  Yüksek ATR + düşük ER = yatay zikzak (KAMA'nın **çıkması gereken** durum).

**LR Channel (Linear Regression Channel)** — Gilbert Raff 1996.

Son N barın kapanışına OLS regresyon uygulanır. Mid çizgisi regresyon tahmini, bantlar rezidüel std ile çizilir.
BB'den farkı: orta çizgi düz değil **eğimlidir** — kanal trendi takip eder.

**Sinyal Mantığı (slope-aware mean reversion):**
- Slope ≥ 0 (yükselen/yatay kanal) **VE** fiyat alt bantta → 🟢 AL (trende uyumlu dip)
- Slope < 0 (alçalan kanal) **VE** fiyat üst bantta → 🔴 SAT (trende uyumlu tepe)
- Trende **ters** mean reversion sinyalleri (yükselen kanalda üst bant dokunma → SAT) silinir.
  Bu whipsaw'ı önler — trend devam ediyorsa sapma sinyal değil, momentum'dur.

**Bağlamsal Bilgiler (karar matrisinde):**

| Bilgi | Anlam |
|---|---|
| **Slope** | Bar başına fiyat değişimi. + → yükselen, − → alçalan, 0 → yatay |
| **R²** | Regresyon kalitesi. Yüksekse veri doğrusal, sinyaller güvenilir |
| **Bant genişliği** | Lokal volatilite ölçüsü. Daralma = squeeze (patlama yakın), genişleme = trend olgunlaşıyor |

**R² yorumu:**
| R² | Anlam |
|---|---|
| > 0.70 | 🔥 Güçlü doğrusal trend — LRC sinyalleri çok güvenilir |
| 0.40 – 0.70 | ⚖️ Orta uyum — sinyaller geçerli |
| < 0.40 | ⚠️ Zayıf uyum — veri zikzaklı, kanal anlamsız |

**LRC vs BB:** LRC'nin orta çizgisi **eğimli** (regresyon), BB'ninki düz (SMA). Trendli piyasada LRC bantları trendle birlikte hareket ettiği için mean reversion sinyalleri **daha doğru** verir. Yatay piyasada ikisi yakınsar.
                """)

        with tab_bb:
            f = go.Figure()
            # Üst-alt bant arası şeffaf mavi dolgu (önce alt bandı ekleyip,
            # üst bandı "tonexty" ile ona doldurmak gerekiyor)
            f.add_trace(go.Scatter(x=df.index, y=df["Low_BB"], name="Alt Band",
                line=dict(color="lime", width=1, dash="dot")))
            f.add_trace(go.Scatter(x=df.index, y=df["Up"], name="Üst Band",
                line=dict(color="red", width=1, dash="dot"),
                fill="tonexty", fillcolor="rgba(80,140,255,0.08)"))
            f.add_trace(go.Scatter(x=df.index, y=df["Mid"], name="Orta (SMA)",
                line=dict(color="gold", width=1.5, dash="dash")))
            f.add_trace(go.Scatter(x=df.index, y=close, name="Fiyat",
                line=dict(color="white", width=1.5)))

            # Üst/alt kırmalar
            bb_break_up   = close > df["Up"]
            bb_break_down = close < df["Low_BB"]
            if bb_break_up.any():
                f.add_trace(go.Scatter(x=df.index[bb_break_up], y=close[bb_break_up],
                    name="Aşırı Alım", mode="markers",
                    marker=dict(color="red", size=7, symbol="circle")))
            if bb_break_down.any():
                f.add_trace(go.Scatter(x=df.index[bb_break_down], y=close[bb_break_down],
                    name="Aşırı Satım", mode="markers",
                    marker=dict(color="lime", size=7, symbol="circle")))

            # Squeeze: bant genişliği son 60 barın p25'inin altındaysa
            bb_width = (df["Up"] - df["Low_BB"]) / df["Mid"]
            if len(bb_width.dropna()) >= 60:
                _wnd = bb_width.rolling(60, min_periods=20)
                _p25 = _wnd.quantile(0.25)
                squeeze_mask = (bb_width <= _p25) & bb_width.notna()
                if squeeze_mask.any():
                    f.add_trace(go.Scatter(
                        x=df.index[squeeze_mask], y=df["Mid"][squeeze_mask],
                        name="Squeeze (sıkışma)", mode="markers",
                        marker=dict(color="orange", size=4, symbol="diamond"),
                        opacity=0.7))

            f.update_layout(**sub_layout(height=350), xaxis_rangeslider_visible=False)
            st.plotly_chart(f, use_container_width=True, config=PLOTLY_CONFIG)

            # Anlık değerler (alt yazı)
            _bb_last_w   = float(bb_width.iloc[-1]) if not bb_width.empty else float("nan")
            _bb_w_med    = float(bb_width.tail(60).median()) if len(bb_width.dropna()) >= 20 else float("nan")
            _bb_pos_text = ""
            _lc = float(close.iloc[-1])
            _lu = float(df["Up"].iloc[-1]) if not df["Up"].empty else float("nan")
            _ll = float(df["Low_BB"].iloc[-1]) if not df["Low_BB"].empty else float("nan")
            _lm = float(df["Mid"].iloc[-1]) if not df["Mid"].empty else float("nan")
            if not (np.isnan(_lu) or np.isnan(_ll) or np.isnan(_lm)):
                if _lc > _lu:
                    _bb_pos_text = f"🔴 Üst bandın **üstünde** ({_lc:.2f} > {_lu:.2f}) — aşırı alım"
                elif _lc < _ll:
                    _bb_pos_text = f"🟢 Alt bandın **altında** ({_lc:.2f} < {_ll:.2f}) — aşırı satım"
                else:
                    _pct_b = (_lc - _ll) / (_lu - _ll) * 100 if (_lu - _ll) > 0 else 50.0
                    _bb_pos_text = f"⚪ Bant **içinde** (%{_pct_b:.0f} pozisyon, orta: {_lm:.2f})"

            _bb_w_pct = (_bb_last_w / _bb_w_med * 100 - 100) if _bb_w_med else 0.0
            _bb_w_label = (
                f"Bant Genişliği: %{_bb_last_w*100:.2f} "
                f"({'+' if _bb_w_pct >= 0 else ''}{_bb_w_pct:.1f}% medyana göre)"
            )
            st.caption(f"{_bb_pos_text} · {_bb_w_label}")

            with st.expander("📖 Bollinger Bands Nasıl Okunur?"):
                st.markdown(f"""
**Bollinger Bands** — fiyatın etrafına çizilen istatistiksel zarftır. Orta çizgi {bb_period} bar SMA, üst/alt bantlar bu ortalamadan **±{bb_std}σ** uzaklıkta. Volatilite ölçer; aynı zamanda mean-reversion ve breakout sinyali verir.

**Bantların yapısı**

| Unsur | Anlam |
|---|---|
| 🟡 Orta çizgi (sarı kesikli) | {bb_period} barlık SMA — fiyatın "denge" noktası |
| 🔴 Üst band (kırmızı kesikli) | SMA + {bb_std}σ — istatistiksel olarak yüksek seviye |
| 🟢 Alt band (yeşil kesikli) | SMA − {bb_std}σ — istatistiksel olarak düşük seviye |
| 🔵 Mavi dolgu | Bantlar arası alan — "normal" hareket aralığı (~%{int((1 - 2*(1 - 0.9772)) * 100) if bb_std == 2.0 else 95}) |

**Sinyal okuma**

| Durum | Yorum |
|---|---|
| 🔴 Fiyat üst bandın üstünde | **Aşırı alım** — istatistiksel olarak nadir bölge. Range piyasasında SAT sinyali; trend piyasasında "trend güçlü" anlamına gelir, hemen satma |
| 🟢 Fiyat alt bandın altında | **Aşırı satım** — Range piyasasında AL sinyali; düşüş trendinde "trend güçlü" |
| ⚪ Fiyat bant içinde | Normal seyir — orta çizgiye yakınlık denge halini gösterir |
| 🟠 Squeeze (turuncu elmaslar) | **Sıkışma** — bant genişliği son 60 barın en düşük %25'inde. Volatilite çökmüş, **breakout yakın** olabilir (yön belirsiz) |

**İki kullanım modu**

- **Mean Reversion (geri dönüş):** Range piyasada üst/alt band kırmaları ters yöne dönüş sinyali. Çoğu zaman geçerli.
- **Squeeze + Breakout:** Bant daralırken bir kırılım gelirse, **trend başlangıcı**. Squeeze sonrası ilk büyük bant dışı hareket güçlü sinyaldir.

⚠️ **Not:** Bollinger tek başına yön söylemez. ADX (trend gücü) ve hacim ile birlikte yorumlanmalı. Güçlü trendde fiyat üst banda yapışıp ilerleyebilir — bu durumda "aşırı alım" yanıltıcıdır.
                """)

        with tab10:
            f = go.Figure()
            f.add_trace(go.Scatter(x=df.index, y=df["WT1"], name="WT1",
                line=dict(color="cyan", width=1.5)))
            f.add_trace(go.Scatter(x=df.index, y=df["WT2"], name="WT2",
                line=dict(color="orange", width=1.5, dash="dot")))
            wt_hist = df["WT1"] - df["WT2"]
            f.add_trace(go.Bar(x=df.index, y=wt_hist, name="WT Histogram",
                marker_color=["lime" if v >= 0 else "red" for v in wt_hist], opacity=0.4))
            f.add_hline(y=wt_ob, line_dash="dash", line_color="red",
                annotation_text=f"Aşırı Alım ({wt_ob})")
            f.add_hline(y=wt_os, line_dash="dash", line_color="lime",
                annotation_text=f"Aşırı Satım ({wt_os})")
            f.add_hline(y=0, line_dash="dot", line_color="gray")
            wt_buy  = df["Sig_WaveTrend"] == 1
            wt_sell = df["Sig_WaveTrend"] == -1
            if wt_buy.any():
                f.add_trace(go.Scatter(x=df.index[wt_buy], y=df["WT1"][wt_buy],
                    name="AL", mode="markers",
                    marker=dict(color="lime", size=10, symbol="triangle-up")))
            if wt_sell.any():
                f.add_trace(go.Scatter(x=df.index[wt_sell], y=df["WT1"][wt_sell],
                    name="SAT", mode="markers",
                    marker=dict(color="red", size=10, symbol="triangle-down")))
            f.update_layout(**sub_layout(height=300))
            st.plotly_chart(f, use_container_width=True, config=PLOTLY_CONFIG)
            with st.expander("📖 WaveTrend Nasıl Okunur?"):
                st.markdown("""
**WaveTrend (WT_CROSS_LB)** — momentum ve aşırı bölge tespiti için kullanılan osilatördür.

| Unsur | Anlam |
|---|---|
| WT1 (cyan) | Hızlı sinyal çizgisi |
| WT2 (turuncu noktalı) | Yavaş sinyal çizgisi |

- **WT1, WT2'yi aşırı satım bölgesinde yukarı kesiyor 🔺:** Güçlü AL sinyali.
- **WT1, WT2'yi aşırı alım bölgesinde aşağı kesiyor 🔻:** Güçlü SAT sinyali.
                """)

        with tab11:
            f = go.Figure()
            f.add_trace(go.Scatter(x=df.index, y=close, name="Fiyat",
                line=dict(color="red", width=1.5)))
            bull_div_r = df["Div_RSI"]  == 1
            bear_div_r = df["Div_RSI"]  == -1
            bull_div_m = df["Div_MACD"] == 1
            bear_div_m = df["Div_MACD"] == -1
            bull_div_o = df["Div_OBV"]  == 1
            bear_div_o = df["Div_OBV"]  == -1
            if bull_div_r.any():
                f.add_trace(go.Scatter(x=df.index[bull_div_r], y=close[bull_div_r],
                    name="RSI Bullish Div", mode="markers",
                    marker=dict(color="lime", size=12, symbol="triangle-up")))
            if bear_div_r.any():
                f.add_trace(go.Scatter(x=df.index[bear_div_r], y=close[bear_div_r],
                    name="RSI Bearish Div", mode="markers",
                    marker=dict(color="red", size=12, symbol="triangle-down")))
            if bull_div_m.any():
                f.add_trace(go.Scatter(x=df.index[bull_div_m], y=close[bull_div_m],
                    name="MACD Bullish Div", mode="markers",
                    marker=dict(color="aquamarine", size=10, symbol="diamond")))
            if bear_div_m.any():
                f.add_trace(go.Scatter(x=df.index[bear_div_m], y=close[bear_div_m],
                    name="MACD Bearish Div", mode="markers",
                    marker=dict(color="salmon", size=10, symbol="diamond")))
            if bull_div_o.any():
                f.add_trace(go.Scatter(x=df.index[bull_div_o], y=close[bull_div_o],
                    name="OBV Bullish Div", mode="markers",
                    marker=dict(color="gold", size=10, symbol="star")))
            if bear_div_o.any():
                f.add_trace(go.Scatter(x=df.index[bear_div_o], y=close[bear_div_o],
                    name="OBV Bearish Div", mode="markers",
                    marker=dict(color="orange", size=10, symbol="star")))
            f.update_layout(**sub_layout(height=350), xaxis_rangeslider_visible=False,
                title_text="Divergence Noktaları (Fiyat Grafiği Üzerinde)")
            st.plotly_chart(f, use_container_width=True, config=PLOTLY_CONFIG)
            with st.expander("📖 Divergence Nasıl Okunur?"):
                st.markdown("""
**Divergence (Uyumsuzluk)** — fiyat hareketi ile indikatör arasındaki zıtlık; trend dönüşünün erken habercisidir.

| Tür | Fiyat | İndikatör | Anlam |
|---|---|---|---|
| Bullish Div 🔺 | Düşük dip | Yüksek dip | 🟢 Satış baskısı azalıyor → yukarı dönüş olabilir |
| Bearish Div 🔻 | Yüksek tepe | Düşük tepe | 🔴 Alış gücü zayıflıyor → aşağı dönüş olabilir |
                """)

        # ============================================================
        # KARAR TABLOSU
        # ============================================================
        last       = df.iloc[-1]
        last_close = safe_scalar(last["Close"])
        last_ath   = bool(last["ATR_High"]) if not pd.isna(last["ATR_High"]) else False

        # ── Son bar indikatör değerleri (hem Kombine Skor hem Teknik Rapor kullanır) ──
        r_close    = safe_scalar(last["Close"])
        r_kama     = safe_scalar(last["KAMA"])
        r_adx      = safe_scalar(last["ADX"])
        r_pdi      = safe_scalar(last["PLUS_DI"])
        r_mdi      = safe_scalar(last["MINUS_DI"])
        r_macd     = safe_scalar(last["MACD"])
        r_macds    = safe_scalar(last["MACD_S"])
        r_rsi      = safe_scalar(last["RSI"])
        r_stk      = safe_scalar(last["StochRSI_K"])
        r_std      = safe_scalar(last["ST_Direction"])
        r_lrc_sig  = safe_scalar(last["Sig_LRC"])
        r_lrc_mid  = safe_scalar(last["LRC_Mid"])
        r_lrc_up   = safe_scalar(last["LRC_Upper"])
        r_lrc_lo   = safe_scalar(last["LRC_Lower"])
        r_vwap     = safe_scalar(last["VWAP"])     if is_intraday else np.nan
        r_vwap_sig = safe_scalar(last["Sig_VWAP"]) if is_intraday else 0
        r_obv_sig  = safe_scalar(last["Sig_OBV"])
        r_div_rsi  = safe_scalar(last["Div_RSI"])
        r_div_mac  = safe_scalar(last["Div_MACD"])
        r_div_obv  = safe_scalar(last["Div_OBV"])
        r_ichi     = safe_scalar(last["Sig_Ichimoku"])
        r_wt1      = safe_scalar(last["WT1"])
        r_atr_hi   = bool(last["ATR_High"]) if not pd.isna(last["ATR_High"]) else False
        r_ema200   = safe_scalar(last["EMA200"])

        # ── ADAPTİF ADX EŞİĞİ ──────────────────────────────────────
        # Volatiliteye göre ADX eşiğini otomatik ayarla.
        # Yüksek volatilitede (gürültülü) trend için daha yüksek eşik iste;
        # düşük volatilitede ise daha düşük eşik yeterli.
        # Kullanıcının manuel eşiği baz alınır, üzerine volatilite düzeltmesi uygulanır.
        r_atr      = safe_scalar(last["ATR"])
        r_atr_ma   = safe_scalar(atr_ma.iloc[-1]) if len(atr_ma) else np.nan
        if not (np.isnan(r_atr) or np.isnan(r_atr_ma)) and r_atr_ma > 0:
            atr_ratio = r_atr / r_atr_ma
        else:
            atr_ratio = 1.0

        # Volatilite düzeltmesi: ATR oranı ±%20'yi aşarsa ±5 puan oynat
        if atr_ratio > 1.2:
            adx_threshold_adaptive = min(adx_threshold + 5, 40)
            adx_regime_note = f"Yüksek vol. (ATR×{atr_ratio:.2f}) → eşik +5"
        elif atr_ratio < 0.8:
            adx_threshold_adaptive = max(adx_threshold - 5, 15)
            adx_regime_note = f"Düşük vol. (ATR×{atr_ratio:.2f}) → eşik -5"
        else:
            adx_threshold_adaptive = adx_threshold
            adx_regime_note = f"Normal vol. (ATR×{atr_ratio:.2f}) → eşik değişmedi"

        if fib_levels:
            r_fib_closest = min(fib_levels.items(), key=lambda x: abs(x[1] - r_close))
        else:
            r_fib_closest = ("N/A", r_close)

        res        = []

        def trend_dec(raw_dec, atr_ok):
            # E sürümü: ATR artık kararı override etmiyor. Düşük volatilite
            # bağlamsal bilgi olarak ayrı (ATR satırında ve Ichimoku gibi
            # bazı satırlarda) gösteriliyor. Karar olduğu gibi geçer.
            return raw_dec

        # ── Hiyerarşi satırı: SMA/EMA/KAMA/Fiyat sıralaması ──
        # Kullanıcıya "her şey nerede" tek bakışta göstersin (bullish/bearish hizalama)
        # A: yön okları, B: golden/death cross uyarısı, D: ADX bağlam, G: yakınlık uyarısı
        hiyerarsi_items = []  # (name, value, slope_arrow, near_price_warn)
        lss_h = safe_scalar(last["SMA_SHORT"])
        lsl_h = safe_scalar(last["SMA_LONG"])
        lk_h  = safe_scalar(last["KAMA"])
        le_h  = safe_scalar(last["EMA200"])
        ls200 = safe_scalar(last["SMA200"]) if "SMA200" in df.columns else np.nan

        # A) Yön oku helper: son 3 barlık fark işareti (↑ ↓ →)
        def _slope_arrow(series_name):
            if series_name not in df.columns or len(df) < 4:
                return ""
            s = df[series_name]
            cur  = safe_scalar(s.iloc[-1])
            prev = safe_scalar(s.iloc[-4])
            if np.isnan(cur) or np.isnan(prev) or prev == 0:
                return ""
            change_pct = (cur - prev) / prev * 100
            if change_pct > 0.05:    return "↑"
            if change_pct < -0.05:   return "↓"
            return "→"

        # G) Fiyat-ortalama yakınlık eşiği: %0.5
        near_price_pct = 0.005
        def _near_price(val):
            return abs(val - last_close) / last_close < near_price_pct if last_close > 0 else False

        if not np.isnan(lss_h):
            hiyerarsi_items.append((f"SMA{p_sma['sma_s']}",  lss_h, _slope_arrow("SMA_SHORT"), _near_price(lss_h)))
        hiyerarsi_items.append(("Fiyat", last_close, "", False))
        if not np.isnan(lsl_h):
            hiyerarsi_items.append((f"SMA{p_sma['sma_l']}",  lsl_h, _slope_arrow("SMA_LONG"),  _near_price(lsl_h)))
        if not np.isnan(lk_h):
            hiyerarsi_items.append(("KAMA",                  lk_h,  _slope_arrow("KAMA"),      _near_price(lk_h)))
        if not np.isnan(ls200):
            hiyerarsi_items.append(("SMA200",                ls200, _slope_arrow("SMA200"),    _near_price(ls200)))
        if not np.isnan(le_h):
            hiyerarsi_items.append(("EMA200",                le_h,  _slope_arrow("EMA200"),    _near_price(le_h)))

        # Değere göre büyükten küçüğe sırala
        hiyerarsi_items.sort(key=lambda x: x[1], reverse=True)

        # Format: "Fiyat (4639) > SMA10 (4625) ↑ ⚠️ > KAMA (4598) ↑ > ..."
        def _fmt(item):
            name, val, arrow, near = item
            txt = f"**{name}** ({val:.2f})" if name == "Fiyat" else f"{name} ({val:.2f})"
            if arrow:  txt += f" {arrow}"
            if near:   txt += " ⚠️"
            return txt
        hiyerarsi_str = " > ".join(_fmt(it) for it in hiyerarsi_items)

        # Tüm ortalamalar fiyatın altında → bullish hizalama (trend yukarı)
        # Tüm ortalamalar fiyatın üstünde → bearish hizalama (trend aşağı)
        fiyat_idx = next((i for i, it in enumerate(hiyerarsi_items) if it[0] == "Fiyat"), -1)
        total     = len(hiyerarsi_items) - 1  # fiyat hariç
        if fiyat_idx == 0:
            hiz_desc = "🟢 Güçlü Bullish hizalama"
        elif fiyat_idx == len(hiyerarsi_items) - 1:
            hiz_desc = "🔴 Güçlü Bearish hizalama"
        elif fiyat_idx <= total / 3:
            hiz_desc = "🟢 Zayıf Bullish hizalama"
        elif fiyat_idx >= 2 * total / 3:
            hiz_desc = "🔴 Zayıf Bearish hizalama"
        else:
            hiz_desc = "⚪ Karışık / geçiş"

        # D) ADX bağlam — hizalama gerçek mi yoksa yatay piyasada tesadüf mü?
        adx_val = safe_scalar(last["ADX"])
        if not np.isnan(adx_val):
            if adx_val > adx_threshold:
                adx_note = f"ADX: {adx_val:.0f} (trend güçlü ✅)"
            elif adx_val < max(adx_threshold - 5, 15):
                adx_note = f"ADX: {adx_val:.0f} (trend zayıf — hizalama yanıltıcı olabilir ⚠️)"
            else:
                adx_note = f"ADX: {adx_val:.0f} (geçiş rejimi)"
            hiz_desc += f" | {adx_note}"

        # G) En yakın ortalama uyarısı (kırılım riski) — desc satırına eklenir
        near_warns = [it for it in hiyerarsi_items if it[3] and it[0] != "Fiyat"]
        if near_warns:
            closest = min(near_warns, key=lambda it: abs(it[1] - last_close))
            dist_pct = abs(closest[1] - last_close) / last_close * 100
            hiz_desc += f" | ⚠️ Fiyat-{closest[0]} mesafesi %{dist_pct:.2f} (kırılım riski)"

        # B) Golden/Death Cross yakın mı? Hareketli ortalamalar arasında %0.5 altı mesafe
        # ve aralarında uygun eğim ilişkisi varsa cross yakındır
        cross_threshold = 0.005
        cross_alerts = []
        ma_pairs = []
        if not np.isnan(lss_h) and not np.isnan(lsl_h):
            ma_pairs.append((f"SMA{p_sma['sma_s']}", lss_h, "SMA_SHORT",
                             f"SMA{p_sma['sma_l']}", lsl_h, "SMA_LONG"))
        if not np.isnan(le_h) and not np.isnan(ls200):
            ma_pairs.append(("EMA200", le_h, "EMA200", "SMA200", ls200, "SMA200"))
        if not np.isnan(lk_h) and not np.isnan(lsl_h):
            ma_pairs.append(("KAMA", lk_h, "KAMA",
                             f"SMA{p_sma['sma_l']}", lsl_h, "SMA_LONG"))

        for short_name, short_val, short_col, long_name, long_val, long_col in ma_pairs:
            if long_val == 0:
                continue
            dist = abs(short_val - long_val) / long_val
            if dist > cross_threshold:
                continue
            # Eğimleri al, yaklaşma yönünü tespit et
            short_arrow = _slope_arrow(short_col)
            long_arrow  = _slope_arrow(long_col)
            # Golden cross: kısa MA, uzun MA'nın altında ama yukarı eğimli
            if short_val < long_val and short_arrow == "↑":
                cross_alerts.append(
                    f"🎯 Golden Cross yaklaşıyor: {short_name} ↔ {long_name} "
                    f"mesafesi %{dist*100:.2f}")
            # Death cross: kısa MA, uzun MA'nın üstünde ama aşağı eğimli
            elif short_val > long_val and short_arrow == "↓":
                cross_alerts.append(
                    f"💀 Death Cross yaklaşıyor: {short_name} ↔ {long_name} "
                    f"mesafesi %{dist*100:.2f}")

        # Hiyerarşi tablo yerine başlık altında markdown olarak gösterilecek
        _hiyerarsi_md = hiyerarsi_str
        _hiz_desc_md  = hiz_desc
        _cross_alert_md = "  \n".join(cross_alerts) if cross_alerts else ""
        # ──────────────────────────────────────────────────────────

        lss = safe_scalar(last["SMA_SHORT"])
        lsl = safe_scalar(last["SMA_LONG"])
        if not (np.isnan(lss) or np.isnan(lsl) or np.isnan(last_close)):
            if lss > lsl and last_close > lss:
                _dec, _why = "AL", "Hiyerarşi: Fiyat > SMA_kısa > SMA_uzun."
            elif lss < lsl and last_close < lss:
                _dec, _why = "SAT", "Hiyerarşi: Fiyat < SMA_kısa < SMA_uzun."
            else:
                _dec, _why = "TUT", "Hiyerarşi çelişkili — fiyat kısa MA'nın yanlış tarafında."
            res.append([trend_dec(_dec, last_ath),
                        f"SMA ({p_sma['sma_s']}/{p_sma['sma_l']})", _why])
        else:
            res.append(["N/A", "SMA Crossover", "Yetersiz veri."])

        lr = safe_scalar(last["RSI"])
        if not np.isnan(lr):
            dec = "AL" if lr < p_rsi["rsi_lower"] else ("SAT" if lr > p_rsi["rsi_upper"] else "TUT")
            res.append([dec, f"RSI ({p_rsi['rsi_period']}) [{p_rsi['rsi_lower']}/{p_rsi['rsi_upper']}]", f"Seviye: {lr:.1f}"])
        else:
            res.append(["N/A", "RSI", "Yetersiz veri."])

        lup = safe_scalar(last["Up"])
        llb = safe_scalar(last["Low_BB"])
        if not any(np.isnan(v) for v in [last_close, llb, lup]):
            dec = "AL" if last_close < llb else ("SAT" if last_close > lup else "TUT")
            res.append([dec, f"Bollinger Bands (σ={p_bb['bb_std']})", "Fiyatın kanaldaki yeri."])
        else:
            res.append(["N/A", "Bollinger Bands", "Yetersiz veri."])

        lm  = safe_scalar(last["MACD"])
        lms = safe_scalar(last["MACD_S"])
        if not (np.isnan(lm) or np.isnan(lms)):
            macd_hist = lm - lms
            hist_color = "🟢 Yeşil" if macd_hist > 0 else ("🔴 Kırmızı" if macd_hist < 0 else "⚪ Sıfır")
            relation   = "MACD > Signal" if lm > lms else ("MACD < Signal" if lm < lms else "MACD = Signal")
            macd_desc  = f"{relation} | Histogram: {macd_hist:+.4f} ({hist_color})"
            res.append([trend_dec("AL" if lm > lms else "SAT", last_ath),
                        f"MACD ({p_macd['macd_fast']},{p_macd['macd_slow']},{macd_signal})", macd_desc])
        else:
            res.append(["N/A", "MACD", "Yetersiz veri."])

        lo = safe_scalar(last["Sig_OBV"])
        if lo != 0 and not np.isnan(lo):
            # Son bar OBV SMA değerleri
            obv_s_last = safe_scalar(obv_sma_short.iloc[-1]) if len(obv_sma_short) else np.nan
            obv_l_last = safe_scalar(obv_sma_long.iloc[-1])  if len(obv_sma_long)  else np.nan

            if not (np.isnan(obv_s_last) or np.isnan(obv_l_last)):
                diff     = obv_s_last - obv_l_last
                # Sayıyı okunabilir formata çevir (milyon/milyar)
                def _fmt_vol(v):
                    av = abs(v)
                    if av >= 1e9:  return f"{v/1e9:+.2f}B"
                    if av >= 1e6:  return f"{v/1e6:+.2f}M"
                    if av >= 1e3:  return f"{v/1e3:+.2f}K"
                    return f"{v:+.2f}"
                relation = "Kısa SMA > Uzun SMA" if diff > 0 else "Kısa SMA < Uzun SMA"
                status   = "Birikim ✅" if lo > 0 else "Dağıtım ❌"
                obv_desc = f"{relation} | Fark: {_fmt_vol(diff)} ({status})"
            else:
                obv_desc = "Birikim ✅" if lo > 0 else "Dağıtım ❌"
            res.append(["AL" if lo > 0 else "SAT", f"OBV ({obv_short}/{obv_long})", obv_desc])
        else:
            res.append(["N/A", f"OBV ({obv_short}/{obv_long})", "Yetersiz veri."])

        la   = safe_scalar(last["ADX"])
        lpd  = safe_scalar(last["PLUS_DI"])
        lmd2 = safe_scalar(last["MINUS_DI"])
        if not np.isnan(la):
            # Adaptif eşiği kullan (volatiliteye göre düzeltilmiş)
            adx_eff_thresh = adx_threshold_adaptive
            # DI+/DI- farkı trend yönünün gücünü gösterir
            if not (np.isnan(lpd) or np.isnan(lmd2)):
                di_diff  = lpd - lmd2
                di_info  = f"| +DI: {lpd:.1f} / -DI: {lmd2:.1f} ({'↑' if di_diff > 0 else '↓'} fark: {abs(di_diff):.1f})"
            else:
                di_info = ""
            strength = "Güçlü" if la > adx_eff_thresh else "Zayıf"
            thresh_info = f"eşik: {adx_eff_thresh}"
            if adx_eff_thresh != adx_threshold:
                thresh_info += f" (kullanıcı: {adx_threshold}, adaptif: {adx_eff_thresh})"
            macd_desc = f"ADX: {la:.1f} ({strength}, {thresh_info}) {di_info}"
            if la > adx_eff_thresh:
                res.append([trend_dec("AL" if lpd > lmd2 else "SAT", last_ath), "ADX", macd_desc])
            else:
                res.append(["TUT", "ADX", macd_desc])
        else:
            res.append(["N/A", "ADX", "Yetersiz veri."])

        if is_intraday:
            lv  = safe_scalar(last["VWAP"])
            lvs = safe_scalar(last["Sig_VWAP"])
            if not np.isnan(lv):
                dec = "AL" if lvs == 1 else ("SAT" if lvs == -1 else "TUT")
                res.append([dec, "VWAP", f"VWAP: {lv:.2f} | bant: ±%{vwap_band_pct:.2f}"])
            else:
                res.append(["N/A", "VWAP", "Yetersiz veri."])
        else:
            res.append(["N/A", "VWAP", "Günlük+ periyotta devre dışı."])

        lsk = float(df["StochRSI_K"].iloc[-1])
        lsd = float(df["StochRSI_D"].iloc[-1]) if "StochRSI_D" in df.columns else np.nan
        lss = safe_scalar(last["Sig_StochRSI"])
        if not np.isnan(lsk):
            # Bölge tespiti
            if   lsk < stoch_lower:  bolge = f"Aşırı Satım 🟢 (<{stoch_lower})"
            elif lsk > stoch_upper:  bolge = f"Aşırı Alım 🔴 (>{stoch_upper})"
            else:                    bolge = f"Nötr ⚪ ({stoch_lower}-{stoch_upper})"

            # K/D ilişkisi
            if not np.isnan(lsd):
                if lsk > lsd:   kd_rel = f"K > D ↑ (K:{lsk:.1f} / D:{lsd:.1f})"
                elif lsk < lsd: kd_rel = f"K < D ↓ (K:{lsk:.1f} / D:{lsd:.1f})"
                else:           kd_rel = f"K = D (K:{lsk:.1f} / D:{lsd:.1f})"
            else:
                kd_rel = f"%K: {lsk:.1f}"

            # Teyit durumu: sinyal sadece bölge + K/D uyumluysa oluşur
            if lss == 1:
                teyit = "✅ AL teyidi (aşırı satım + yukarı dönüş)"
                dec = "AL"
            elif lss == -1:
                teyit = "✅ SAT teyidi (aşırı alım + aşağı dönüş)"
                dec = "SAT"
            else:
                # Bölgede ama kesişim teyidi yok
                if lsk < stoch_lower and not np.isnan(lsd) and lsk < lsd:
                    teyit = "⏸ Aşırı satımda ama K < D (dönüş teyidi bekle)"
                elif lsk > stoch_upper and not np.isnan(lsd) and lsk > lsd:
                    teyit = "⏸ Aşırı alımda ama K > D (dönüş teyidi bekle)"
                else:
                    teyit = "Nötr bölgede"
                dec = "TUT"

            stoch_desc = f"{bolge} | {kd_rel} | {teyit}"
            res.append([dec, f"Stoch RSI ({stoch_rsi_period})", stoch_desc])
        else:
            res.append(["N/A", "Stoch RSI", "Yetersiz veri."])

        # ───────── Ichimoku zenginleştirilmiş satır ─────────
        lis = safe_scalar(last["Sig_Ichimoku"])
        l_tenkan = safe_scalar(last["Tenkan"])
        l_kijun  = safe_scalar(last["Kijun"])
        l_seka   = safe_scalar(last["Senkou_A"])
        l_sekb   = safe_scalar(last["Senkou_B"])

        if any(np.isnan([l_tenkan, l_kijun, l_seka, l_sekb])):
            # Senkou'lar 26 bar ileri kaydırıldığı için başlarda NaN olabilir
            res.append(["N/A", "Ichimoku", "Yetersiz veri (Senkou henüz hesaplanmadı)."])
        else:
            # 1) Tenkan-Kijun ilişkisi
            if l_tenkan > l_kijun:
                tk_rel = f"T:{l_tenkan:.1f} > K:{l_kijun:.1f} ↑"
            elif l_tenkan < l_kijun:
                tk_rel = f"T:{l_tenkan:.1f} < K:{l_kijun:.1f} ↓"
            else:
                tk_rel = f"T:{l_tenkan:.1f} = K:{l_kijun:.1f}"

            # 2) Fiyat - Bulut pozisyonu
            cloud_top    = max(l_seka, l_sekb)
            cloud_bottom = min(l_seka, l_sekb)
            if last_close > cloud_top:
                cloud_pos = "Bulut ÜSTÜNDE ✅"
            elif last_close < cloud_bottom:
                cloud_pos = "Bulut ALTINDA ❌"
            else:
                cloud_pos = "Bulut İÇİNDE ⚪"

            # 3) Bulut rengi (Senkou A vs B)
            cloud_color = "Yeşil 🟢" if l_seka > l_sekb else ("Kırmızı 🔴" if l_seka < l_sekb else "Eşit ⚪")

            # 4) Chikou teyidi: bugünün kapanışı, ik bar önceki kapanışla kıyaslama
            #    (Hosoda: Chikou geçmiş fiyatların üstünde → boğa onayı)
            chikou_ref_idx = -ichi_kijun - 1
            if len(close) >= ichi_kijun + 1:
                close_ref = safe_scalar(close.iloc[chikou_ref_idx])
                if not np.isnan(close_ref):
                    if last_close > close_ref:
                        chikou_note = f"Chikou ↑ (kapanış {ichi_kijun} bar öncesinden yüksek)"
                    elif last_close < close_ref:
                        chikou_note = f"Chikou ↓ (kapanış {ichi_kijun} bar öncesinden düşük)"
                    else:
                        chikou_note = "Chikou ="
                else:
                    chikou_note = "Chikou: yetersiz veri"
            else:
                chikou_note = "Chikou: yetersiz veri"

            # 5) Rejim bazlı dinamik uyarı (ADX'e göre)
            #    Adaptif eşik kullanıyoruz — tutarlılık için
            if not np.isnan(la):
                if la > adx_threshold_adaptive:
                    regime_note = f"✅ Trend piyasa — sinyal güvenilir (ADX: {la:.1f})"
                elif la < max(adx_threshold_adaptive - 5, 15):
                    regime_note = f"⚠️ Yatay piyasada aldatıcı (ADX: {la:.1f})"
                else:
                    regime_note = f"⏸ Geçiş rejimi (ADX: {la:.1f})"
            else:
                regime_note = ""

            # Karar + açıklama birleşimi
            desc = f"{tk_rel} | {cloud_pos} | {cloud_color} | {chikou_note}"
            if regime_note:
                desc += f" | {regime_note}"

            if lis == 1:
                # Düşük volatilite uyarısı (artık otomatik silmiyor, sadece bağlamsal not)
                if not last_ath:
                    res.append(["AL", "Ichimoku", desc + " | ⚠️ Düşük vol — sinyal güvenilirliği azalmış olabilir."])
                else:
                    res.append(["AL", "Ichimoku", desc])
            elif lis == -1:
                if not last_ath:
                    res.append(["SAT", "Ichimoku", desc + " | ⚠️ Düşük vol — sinyal güvenilirliği azalmış olabilir."])
                else:
                    res.append(["SAT", "Ichimoku", desc])
            else:
                res.append(["TUT", "Ichimoku", desc])

        lk = safe_scalar(last["KAMA"])
        if not np.isnan(lk):
            # 1) Fiyat-KAMA ilişkisi + yüzde uzaklık (bağlam bilgisi)
            dist_pct_k = (last_close - lk) / lk * 100
            if last_close > lk:
                rel_k = f"Fiyat {last_close:.2f} > KAMA {lk:.2f} (+%{dist_pct_k:.2f})"
            elif last_close < lk:
                rel_k = f"Fiyat {last_close:.2f} < KAMA {lk:.2f} ({dist_pct_k:+.2f}%)"
            else:
                rel_k = f"Fiyat = KAMA ({lk:.2f})"

            # 2) KAMA eğimi (son 3 barlık fark) — ASIL sinyal kaynağı
            slope_window = 3
            if len(df["KAMA"]) >= slope_window + 1:
                kama_slope = lk - safe_scalar(df["KAMA"].iloc[-slope_window - 1])
                if not np.isnan(kama_slope):
                    if kama_slope > 0:
                        slope_desc = f"KAMA ↑ (+{kama_slope:.2f}, {slope_window} bar)"
                    elif kama_slope < 0:
                        slope_desc = f"KAMA ↓ ({kama_slope:.2f}, {slope_window} bar)"
                    else:
                        slope_desc = "KAMA yatay"
                else:
                    slope_desc = "Eğim: yetersiz veri"
            else:
                slope_desc = "Eğim: yetersiz veri"

            # 3) Efficiency Ratio — sinyal kalite filtresi (df'ten direkt)
            er = safe_scalar(last["KAMA_ER"])
            if not np.isnan(er):
                if er > 0.5:
                    er_desc = f"ER: {er:.2f} (güçlü trend 🔥)"
                elif er > 0.30:
                    er_desc = f"ER: {er:.2f} (orta momentum)"
                else:
                    er_desc = f"ER: {er:.2f} (yatay/gürültü ⚠️ sinyal yok)"
            else:
                er_desc = "ER: yetersiz veri"

            kama_desc = f"{slope_desc} | {er_desc} | {rel_k}"

            # Karar: artık eğim + ER tabanlı (Sig_KAMA)
            lks = safe_scalar(last["Sig_KAMA"])
            if lks == 1:
                kama_dec = "AL"
            elif lks == -1:
                kama_dec = "SAT"
            else:
                kama_dec = "TUT"

            res.append([trend_dec(kama_dec, last_ath),
                        f"KAMA ({kama_period},{kama_fast},{kama_slow})", kama_desc])
        else:
            res.append(["N/A", "KAMA", "Yetersiz veri."])

        lst  = safe_scalar(last["SuperTrend"])
        lstd = safe_scalar(last["ST_Direction"])
        if not np.isnan(lst) and not np.isnan(lstd):
            # 1) Yön
            yon = "YUKARI ↑" if lstd == 1 else "AŞAĞI ↓"

            # 2) Çizgi seviyesi ve fiyata uzaklık
            if last_close > 0:
                dist_pct = abs(lst - last_close) / last_close * 100
                if lstd == 1:
                    # Trend yukarı → çizgi altta (destek)
                    uzak_str = f"fiyatın %{dist_pct:.2f} altında (destek)"
                else:
                    # Trend aşağı → çizgi üstte (direnç)
                    uzak_str = f"fiyatın %{dist_pct:.2f} üstünde (direnç)"
                # Flip yakınlığı uyarısı
                if dist_pct < 1.0:
                    uzak_str += " ⚠️ flip yakın"
            else:
                uzak_str = ""

            # 3) Güncel ATR (volatilite bağlamı)
            r_atr_st = safe_scalar(last["ATR"])
            atr_str  = f"ATR: {r_atr_st:.2f}" if not np.isnan(r_atr_st) else ""

            # 4) Flip'ten bu yana bar sayısı (sinyal olgunluğu)
            st_dir_series = df["ST_Direction"].values
            bars_since_flip = 0
            for i in range(len(st_dir_series) - 1, 0, -1):
                if st_dir_series[i] != st_dir_series[i-1]:
                    break
                bars_since_flip += 1
            if bars_since_flip == 0:
                flip_str = "🆕 Yeni flip!"
            elif bars_since_flip < 3:
                flip_str = f"Flip'ten {bars_since_flip} bar (yeni sinyal)"
            else:
                flip_str = f"Flip'ten {bars_since_flip} bar"

            # Birleştir
            parts = [f"Yön: {yon}", f"Çizgi: {lst:.2f} ({uzak_str})"]
            if atr_str:   parts.append(atr_str)
            parts.append(flip_str)
            st_desc = " | ".join(parts)

            # Karar: flip event-bazlı (Sig_SuperTrend)
            # +1 = flip-up (yeni AL), -1 = flip-down (yeni SAT), 0 = trend devam
            lsts = safe_scalar(last["Sig_SuperTrend"])
            if lsts == 1:
                st_dec = "AL"
            elif lsts == -1:
                st_dec = "SAT"
            else:
                # Flip yok — yön bilgisi mevcut (lstd) ama yeni event yok → TUT
                st_dec = "TUT"

            res.append([trend_dec(st_dec, last_ath),
                        f"SuperTrend ({p_st['st_period']}, x{p_st['st_multiplier']})", st_desc])
        else:
            res.append(["N/A", "SuperTrend", "Yetersiz veri."])

        llrc = safe_scalar(last["Sig_LRC"])
        llm  = safe_scalar(last["LRC_Mid"])
        llu  = safe_scalar(last["LRC_Upper"])
        lll  = safe_scalar(last["LRC_Lower"])
        if not np.isnan(llm) and not np.isnan(llu) and not np.isnan(lll):
            # 1) Kanal içi pozisyon
            if last_close > llu:
                pos_lrc = f"Fiyat {last_close:.2f} ÜST kanal üstünde ({llu:.2f}) ❌ aşırı alım"
            elif last_close < lll:
                pos_lrc = f"Fiyat {last_close:.2f} ALT kanal altında ({lll:.2f}) ✅ aşırı satım"
            else:
                # Kanal içinde — orta çizgiye yakınlık
                if last_close > llm:
                    pct_mid = (last_close - llm) / llm * 100
                    pos_lrc = f"Fiyat {last_close:.2f} kanal içinde (orta üstü, +%{pct_mid:.2f})"
                else:
                    pct_mid = (llm - last_close) / llm * 100
                    pos_lrc = f"Fiyat {last_close:.2f} kanal içinde (orta altı, -%{pct_mid:.2f})"

            # 2) Slope yönü (df'ten direkt — sig_lrc içinde hesaplandı)
            slope = safe_scalar(last["LRC_Slope"])
            if not np.isnan(slope):
                slope_pct = slope / llm * 100 if llm > 0 else 0.0
                if slope > 0:
                    slope_desc = f"Slope: +{slope:.3f} ↗ (yükselen, bar başı +%{slope_pct:.3f})"
                elif slope < 0:
                    slope_desc = f"Slope: {slope:.3f} ↘ (alçalan, bar başı %{slope_pct:.3f})"
                else:
                    slope_desc = "Slope: 0 → (yatay)"
            else:
                slope_desc = ""

            # 3) R² — regresyon kalitesi (LRC sinyallerinin güvenilirliği)
            r2 = safe_scalar(last["LRC_R2"])
            if not np.isnan(r2):
                if r2 > 0.7:
                    r2_desc = f"R²: {r2:.2f} (güçlü doğrusal trend 🔥)"
                elif r2 > 0.4:
                    r2_desc = f"R²: {r2:.2f} (orta uyum)"
                else:
                    r2_desc = f"R²: {r2:.2f} (zayıf uyum ⚠️ kanal anlamsız)"
            else:
                r2_desc = ""

            # 4) Bant genişliği (lokal volatilite — normalize)
            bant_width = llu - lll
            if llm > 0:
                bant_pct = bant_width / llm * 100
                bant_desc = f"Bant: ±{bant_width/2:.2f} (kanal genişliği %{bant_pct:.2f})"
            else:
                bant_desc = f"Bant: ±{bant_width/2:.2f}"

            # Birleştir
            parts = [pos_lrc]
            if slope_desc: parts.append(slope_desc)
            if r2_desc:    parts.append(r2_desc)
            parts.append(bant_desc)
            lrc_desc = " | ".join(parts)

            dec = "AL" if llrc == 1 else ("SAT" if llrc == -1 else "TUT")
            res.append([dec, f"LR Channel (σ={p_lrc['lrc_std_mult']})", lrc_desc])
        else:
            res.append(["N/A", "LR Channel", "Yetersiz veri."])

        la2 = safe_scalar(last["ATR"])
        lam = safe_scalar(atr_ma.iloc[-1])
        if not np.isnan(la2) and not np.isnan(lam):
            # 1) Yüzde fark (MA'ya göre)
            if lam > 0:
                pct_diff = (la2 - lam) / lam * 100
                if last_ath:
                    pct_str = f"Yüksek ↑ (%{abs(pct_diff):.1f} üstü MA'dan)"
                else:
                    pct_str = f"Düşük ↓ (%{abs(pct_diff):.1f} altı MA'dan)"
            else:
                pct_str = "Yüksek ↑" if last_ath else "Düşük ↓"

            # 2) Son 5 bar volatilite yönü (artıyor mu azalıyor mu)
            atr_vals = atr_series.values
            if len(atr_vals) >= 6:
                recent       = atr_vals[-5:]
                older        = atr_vals[-6:-1]
                avg_recent   = float(np.nanmean(recent))
                avg_older    = float(np.nanmean(older))
                if np.isfinite(avg_recent) and np.isfinite(avg_older) and avg_older > 0:
                    change_pct = (avg_recent - avg_older) / avg_older * 100
                    if change_pct > 2:
                        trend_str = "Son 5 bar: yükseliyor ↗ (patlama yakın olabilir)"
                    elif change_pct < -2:
                        trend_str = "Son 5 bar: düşüyor ↘ (sıkışma derinleşiyor)"
                    else:
                        trend_str = "Son 5 bar: stabil →"
                else:
                    trend_str = ""
            else:
                trend_str = ""

            parts = [f"Volatilite: {pct_str}", f"ATR: {la2:.2f}", f"MA: {lam:.2f}"]
            if trend_str:
                parts.append(trend_str)
            atr_desc = " | ".join(parts)
            res.append(["BİLGİ", "ATR Filtre", atr_desc])
        else:
            res.append(["N/A", "ATR Filtre", "Yetersiz veri."])

        lwt1    = safe_scalar(last["WT1"])
        lwt2    = safe_scalar(last["WT2"])
        lwt_sig = safe_scalar(last["Sig_WaveTrend"])
        if not np.isnan(lwt1):
            # 1) Bölge tespiti (eşik değerlerini de göster)
            if lwt1 > wt_ob:
                wt_zone = f"Aşırı Alım 🔴 (>{wt_ob})"
            elif lwt1 < wt_os:
                wt_zone = f"Aşırı Satım 🟢 (<{wt_os})"
            else:
                wt_zone = f"Nötr Bölge ({wt_os}/+{wt_ob})"

            # 2) WT1 / WT2 değerleri + ilişki
            if not np.isnan(lwt2):
                if lwt1 > lwt2:
                    kd_rel = f"WT1: {lwt1:.1f} > WT2: {lwt2:.1f} ↑"
                elif lwt1 < lwt2:
                    kd_rel = f"WT1: {lwt1:.1f} < WT2: {lwt2:.1f} ↓"
                else:
                    kd_rel = f"WT1 = WT2 ({lwt1:.1f})"

                # 3) Histogram (WT1 - WT2) + renk
                wt_hist = lwt1 - lwt2
                hist_color = "🟢 Yeşil" if wt_hist > 0 else ("🔴 Kırmızı" if wt_hist < 0 else "⚪ Sıfır")
                hist_str = f"Histogram: {wt_hist:+.2f} ({hist_color})"

                parts = [kd_rel, wt_zone, hist_str]
            else:
                parts = [f"WT1: {lwt1:.1f}", wt_zone]

            wt_desc = " | ".join(parts)
            wt_dec = "AL" if lwt_sig == 1 else ("SAT" if lwt_sig == -1 else "TUT")
            res.append([wt_dec, f"WaveTrend ({p_wt['wt_n1']}/{p_wt['wt_n2']})", wt_desc])
        else:
            res.append(["N/A", "WaveTrend", "Yetersiz veri."])

        # ── YENİ: EMA200 karar satırı ─────────────────────────────
        lema200 = safe_scalar(last["EMA200"])
        if not np.isnan(lema200):
            ema_dec = trend_dec("AL" if last_close > lema200 else "SAT", last_ath)
            res.append([ema_dec, "EMA 200", f"EMA200: {lema200:.2f} | Fiyat {'üstünde ✅' if last_close > lema200 else 'altında ❌'}"])
        else:
            res.append(["N/A", "EMA 200", "Yetersiz veri (min 200 bar gerekli)."])

        # ── YENİ: Fibonacci + Swing S/R Confluence ────────────────
        # Bağımsız iki teknik (swing pivot + Fib retracement) aynı seviyeye
        # işaret ediyorsa "güçlü destek/direnç bandı" — trader için kritik bilgi.
        # Eşik: %0.5 fiyat mesafesi (çok yakın değil, çok uzak değil)
        if swing_levels and fib_levels and last_close > 0:
            confluence_threshold = 0.005   # %0.5
            confluences = []
            for sw in swing_levels:
                if sw.get("broken"):       # kırılmış seviyeler hariç
                    continue
                sw_price = sw["price"]
                for fib_name, fib_price in fib_levels.items():
                    if fib_name in ("0.0%", "100.0%"):   # uçlar zaten swing
                        continue
                    dist = abs(sw_price - fib_price) / last_close
                    if dist <= confluence_threshold:
                        # Ortalama band: iki seviyenin orta noktası
                        band_mid = (sw_price + fib_price) / 2
                        confluences.append({
                            "type":      sw["type"],
                            "swing":     sw_price,
                            "touches":   sw["touches"],
                            "fib_name":  fib_name,
                            "fib_price": fib_price,
                            "band_mid":  band_mid,
                            "dist_to_price": abs(band_mid - last_close) / last_close,
                        })
            # Fiyata yakınlık sırası, en fazla 3 confluence göster
            confluences.sort(key=lambda x: x["dist_to_price"])
            for c in confluences[:3]:
                role = "Güçlü Destek" if c["type"] == "S" else "Güçlü Direnç"
                lo, hi = sorted([c["swing"], c["fib_price"]])
                desc = (f"{lo:.2f}–{hi:.2f} "
                        f"(Swing {c['type']} [{c['touches']}x dokunuş] + Fib {c['fib_name']})")
                res.append(["🎯 Confluence", role, desc])

        # ── YENİ: En yakın S/R seviyesi karar satırı ──────────────
        if swing_levels:
            closest_sr = min(swing_levels, key=lambda x: abs(x["price"] - last_close))
            dist_pct   = abs(closest_sr["price"] - last_close) / last_close * 100
            sr_label   = "Destek" if closest_sr["type"] == "S" else "Direnç"
            res.append(["BİLGİ", "Swing S/R",
                f"En yakın {sr_label}: {closest_sr['price']:.2f} "
                f"(%{dist_pct:.1f} uzakta, {closest_sr['touches']}x dokunuş)"])
        # ──────────────────────────────────────────────────────────

        last_div_rsi  = safe_scalar(last["Div_RSI"])
        last_div_macd = safe_scalar(last["Div_MACD"])
        last_div_obv  = safe_scalar(last["Div_OBV"])
        if last_div_rsi == 1:
            res.append(["BİLGİ", "Divergence (RSI)", "🔺 Bullish Divergence — güçlü dip sinyali olabilir"])
        elif last_div_rsi == -1:
            res.append(["BİLGİ", "Divergence (RSI)", "🔻 Bearish Divergence — zayıflayan momentum"])
        else:
            res.append(["BİLGİ", "Divergence (RSI)", "Aktif divergence yok"])
        if last_div_macd == 1:
            res.append(["BİLGİ", "Divergence (MACD)", "🔺 Bullish Divergence"])
        elif last_div_macd == -1:
            res.append(["BİLGİ", "Divergence (MACD)", "🔻 Bearish Divergence"])
        else:
            res.append(["BİLGİ", "Divergence (MACD)", "Aktif divergence yok"])
        if last_div_obv == 1:
            res.append(["BİLGİ", "Divergence (OBV)", "🔺 Bullish Divergence — fiyat dip yapıyor, hacim desteği zayıflıyor (alıcı tükenmesi)"])
        elif last_div_obv == -1:
            res.append(["BİLGİ", "Divergence (OBV)", "🔻 Bearish Divergence — fiyat tepe yapıyor, hacim desteklemiyor (satıcı tükenmesi)"])
        else:
            res.append(["BİLGİ", "Divergence (OBV)", "Aktif divergence yok"])

        if fib_levels:
            closest_lvl = min(fib_levels.items(), key=lambda x: abs(x[1] - last_close))
            if fib_direction == "up":
                dir_str = "📈 Bull retracement (destek arıyor)"
            elif fib_direction == "down":
                dir_str = "📉 Bear retracement (direnç test ediyor)"
            else:
                dir_str = "↔️ Yatay (range — yön belirsiz)"
            res.append(["BİLGİ", f"Fibonacci ({fib_lookback} bar)",
                        f"En yakın seviye: {closest_lvl[0]} ({closest_lvl[1]:.2f}) | "
                        f"Swing: {fib_low:.2f} — {fib_high:.2f} | {dir_str}"])

        # ============================================================
        # (Kombine Sinyal Skoru kaldırıldı)

        st.subheader("🔍 Algoritmik Detaylar")
        # Hiyerarşi — tablonun üstünde markdown olarak (bold çalışır, tek satır)
        _hier_block = f"**📊 Hiyerarşi:** {_hiyerarsi_md}  \n{_hiz_desc_md}"
        if _cross_alert_md:
            _hier_block += f"  \n{_cross_alert_md}"
        st.markdown(_hier_block)
        res_df = pd.DataFrame(res, columns=["Karar", "Algoritma", "Durum/Sebep"])

        def color_map(val):
            if val == "AL":    return "color: #00ff00; font-weight: bold"
            if val == "SAT":   return "color: #ff4b4b; font-weight: bold"
            if val == "N/A":   return "color: #ffaa00; font-weight: bold"
            if val == "BİLGİ": return "color: #00bfff; font-weight: bold"
            if "düşük vol." in str(val): return "color: #808495; font-style: italic"
            return "color: #808495; font-weight: bold"

        st.table(res_df.style.map(color_map, subset=["Karar"]))

        # ============================================================
        # 📅 EKONOMİK TAKVİM (TradingView)
        # ============================================================
        st.write("---")
        with st.expander("📅 Ekonomik Takvim", expanded=False):
            TV_CAL_URL = "https://economic-calendar.tradingview.com/events"
            TV_CAL_HEADERS = {
                "accept":     "application/json",
                "origin":     "https://www.tradingview.com",
                "referer":    "https://www.tradingview.com/",
                "user-agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/147.0.0.0 Safari/537.36"
                ),
            }
            CAL_COUNTRIES = {
                "TR": "🇹🇷 Türkiye",
                "US": "🇺🇸 ABD",
                "EU": "🇪🇺 Euro Bölgesi",
                "GB": "🇬🇧 İngiltere",
                "DE": "🇩🇪 Almanya",
                "JP": "🇯🇵 Japonya",
                "CN": "🇨🇳 Çin",
            }

            # Başlık çevirileri — sözlükte olmayanlar orijinal İngilizce kalır.
            TR_EVENT_TITLES = {
                # — Türkiye özel —
                "Economic Confidence Index":                       "Ekonomik Güven Endeksi",
                "Unemployment Rate":                               "İşsizlik Oranı",
                "Participation Rate":                              "İşgücüne Katılım Oranı",
                "Tourism Revenues":                                "Turizm Gelirleri",
                "Tourist Arrivals YoY":                            "Turist Sayısı (Y/Y)",
                "MPC Meeting Summary":                             "PPK Toplantı Özeti",
                "MPC Meeting Minutes":                             "PPK Toplantı Tutanakları",
                "Foreign Exchange Reserves":                       "Döviz Rezervleri",
                "Capacity Utilization":                            "Kapasite Kullanım Oranı",
                "Istanbul Chamber of Industry Manufacturing PMI":  "İSO İmalat PMI",
                "TCMB Interest Rate Decision":                     "TCMB Faiz Kararı",
                "Real Sector Confidence":                          "Reel Kesim Güveni",
                "Manufacturing Confidence":                        "İmalat Güveni",
                "Services Confidence":                             "Hizmet Güveni",
                "Retail Confidence":                               "Perakende Güveni",
                "Construction Confidence":                         "İnşaat Güveni",
                # — Resmi tatiller —
                "Labor and Solidarity Day":                        "Emek ve Dayanışma Günü",
                "Republic Day":                                    "Cumhuriyet Bayramı",
                "Victory Day":                                     "Zafer Bayramı",
                "Democracy and National Unity Day":                "Demokrasi ve Milli Birlik Günü",
                "Commemoration of Atatürk, Youth and Sports Day":  "Atatürk'ü Anma, Gençlik ve Spor Bayramı",
                "National Sovereignty and Children's Day":         "Ulusal Egemenlik ve Çocuk Bayramı",
                "Christmas Day":                                   "Noel",
                "New Year's Day":                                  "Yılbaşı",
                # — Genel makro (tüm ülkeler) —
                "Balance of Trade":          "Dış Ticaret Dengesi",
                "Balance of Trade Final":    "Dış Ticaret Dengesi (Nihai)",
                "Balance of Trade Prel":     "Dış Ticaret Dengesi (Öncü)",
                "Imports":                   "İthalat",
                "Imports Final":             "İthalat (Nihai)",
                "Imports Prel":              "İthalat (Öncü)",
                "Exports":                   "İhracat",
                "Exports Final":             "İhracat (Nihai)",
                "Exports Prel":              "İhracat (Öncü)",
                "Trade Balance":             "Ticaret Dengesi",
                "Current Account":           "Cari İşlemler Dengesi",
                "Inflation Rate YoY":        "Enflasyon Oranı (Y/Y)",
                "Inflation Rate MoM":        "Enflasyon Oranı (A/A)",
                "Core Inflation Rate YoY":   "Çekirdek Enflasyon (Y/Y)",
                "Core Inflation Rate MoM":   "Çekirdek Enflasyon (A/A)",
                "CPI":                       "TÜFE",
                "CPI YoY":                   "TÜFE (Y/Y)",
                "CPI MoM":                   "TÜFE (A/A)",
                "Core CPI YoY":              "Çekirdek TÜFE (Y/Y)",
                "Core CPI MoM":              "Çekirdek TÜFE (A/A)",
                "PPI YoY":                   "ÜFE (Y/Y)",
                "PPI MoM":                   "ÜFE (A/A)",
                "GDP Growth Rate YoY":       "GSYH Büyüme (Y/Y)",
                "GDP Growth Rate QoQ":       "GSYH Büyüme (Ç/Ç)",
                "GDP Growth Rate":           "GSYH Büyüme",
                "GDP YoY":                   "GSYH (Y/Y)",
                "Industrial Production YoY": "Sanayi Üretimi (Y/Y)",
                "Industrial Production MoM": "Sanayi Üretimi (A/A)",
                "Retail Sales YoY":          "Perakende Satışlar (Y/Y)",
                "Retail Sales MoM":          "Perakende Satışlar (A/A)",
                "Manufacturing PMI":         "İmalat PMI",
                "Services PMI":              "Hizmet PMI",
                "Composite PMI":             "Bileşik PMI",
                "Consumer Confidence":       "Tüketici Güveni",
                "Business Confidence":       "İş Dünyası Güveni",
                "Budget Balance":            "Bütçe Dengesi",
                "Government Debt to GDP":    "Devlet Borcu/GSYH",
                "House Price Index YoY":     "Konut Fiyat Endeksi (Y/Y)",
                "House Price Index MoM":     "Konut Fiyat Endeksi (A/A)",
                "Interest Rate Decision":    "Faiz Kararı",
                "Deposit Facility Rate":     "Mevduat Faizi",
                # — ABD —
                "Fed Interest Rate Decision":          "Fed Faiz Kararı",
                "FOMC Minutes":                        "FOMC Toplantı Tutanakları",
                "Fed Chair Powell Speech":             "Fed Başkanı Powell Konuşması",
                "Non Farm Payrolls":                   "Tarım Dışı İstihdam",
                "Initial Jobless Claims":              "Haftalık İşsizlik Başvuruları",
                "Continuing Jobless Claims":           "Devam Eden İşsizlik Başvuruları",
                "Average Hourly Earnings MoM":         "Saatlik Kazançlar (A/A)",
                "Average Hourly Earnings YoY":         "Saatlik Kazançlar (Y/Y)",
                "ADP Employment Change":               "ADP İstihdam Değişimi",
                "JOLTs Job Openings":                  "JOLTS Açık İş Sayısı",
                "ISM Manufacturing PMI":               "ISM İmalat PMI",
                "ISM Services PMI":                    "ISM Hizmet PMI",
                "Durable Goods Orders MoM":            "Dayanıklı Mal Siparişleri (A/A)",
                "Factory Orders MoM":                  "Fabrika Siparişleri (A/A)",
                "Building Permits":                    "Yapı İzinleri",
                "Housing Starts":                      "Konut Başlangıçları",
                "Existing Home Sales":                 "Mevcut Konut Satışları",
                "New Home Sales":                      "Yeni Konut Satışları",
                "Pending Home Sales MoM":              "Bekleyen Konut Satışları (A/A)",
                "Crude Oil Inventories":               "Ham Petrol Stokları",
                "PCE Price Index YoY":                 "PCE Fiyat Endeksi (Y/Y)",
                "PCE Price Index MoM":                 "PCE Fiyat Endeksi (A/A)",
                "Core PCE Price Index YoY":            "Çekirdek PCE (Y/Y)",
                "Core PCE Price Index MoM":            "Çekirdek PCE (A/A)",
                "Personal Income MoM":                 "Kişisel Gelir (A/A)",
                "Personal Spending MoM":               "Kişisel Harcama (A/A)",
                "Michigan Consumer Sentiment":         "Michigan Tüketici Güveni",
                "CB Consumer Confidence":              "CB Tüketici Güveni",
                "Chicago PMI":                         "Chicago PMI",
                "Philadelphia Fed Manufacturing Index":"Philadelphia Fed İmalat Endeksi",
                "NY Empire State Manufacturing Index": "NY Empire State İmalat Endeksi",
                # — ECB / BoE / BoJ / PBoC —
                "ECB Interest Rate Decision":  "ECB Faiz Kararı",
                "BoE Interest Rate Decision":  "BoE Faiz Kararı",
                "BoJ Interest Rate Decision":  "BoJ Faiz Kararı",
                "PBoC Loan Prime Rate 1Y":     "PBoC 1Y LPR",
                "PBoC Loan Prime Rate 5Y":     "PBoC 5Y LPR",
            }

            @st.cache_data(ttl=1800, show_spinner=False)
            def _fetch_economic_calendar(country, days, past_days=30):
                """TradingView ekonomik takvimi → (events_list, error_msg).
                past_days: geriye kaç günlük açıklanmış veri çekilsin."""
                _now = datetime.now(timezone.utc)
                _params = {
                    "from":      (_now - timedelta(days=past_days)).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "to":        (_now + timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "countries": country,
                }
                try:
                    _r = requests.get(TV_CAL_URL, headers=TV_CAL_HEADERS,
                                      params=_params, timeout=15)
                    _r.raise_for_status()
                    _js = _r.json()
                    if _js.get("status") != "ok":
                        return None, f"API status != ok ({_js.get('status')})"
                    return _js.get("result", []), None
                except requests.exceptions.Timeout:
                    return None, "Zaman aşımı — TradingView yanıt vermiyor."
                except requests.exceptions.ConnectionError as _e:
                    return None, f"Bağlantı hatası: {str(_e)[:200]}"
                except requests.exceptions.HTTPError as _e:
                    return None, f"HTTP {_e.response.status_code}"
                except (ValueError, KeyError) as _e:
                    return None, f"Yanıt ayrıştırılamadı ({type(_e).__name__})"
                except Exception as _e:
                    return None, f"{type(_e).__name__}: {str(_e)[:200]}"

            _cc1, _cc2 = st.columns([1, 1])
            with _cc1:
                _cal_country = st.selectbox(
                    "Ülke",
                    options=list(CAL_COUNTRIES.keys()),
                    format_func=lambda k: CAL_COUNTRIES[k],
                    index=0, key="cal_country",
                )
            with _cc2:
                _cal_days = st.slider(
                    "Önümüzdeki gün sayısı",
                    min_value=1, max_value=30, value=7, step=1,
                    key="cal_days",
                )

            _cal_events, _cal_err = _fetch_economic_calendar(_cal_country, _cal_days)

            if _cal_err:
                st.error(f"❌ Takvim çekilemedi — {_cal_err}")
            elif not _cal_events:
                st.info("Bu aralıkta olay bulunamadı.")
            else:
                _TRT = timezone(timedelta(hours=3))
                _IMP_MAP = {1: "YÜK", 0: "ORT", -1: "DÜŞ"}

                # Geçmiş (actual dolu, son 5) + gelecek olarak ayır
                _now_utc = datetime.now(timezone.utc)
                _past, _future = [], []
                for _ev in _cal_events:
                    _d_raw = _ev.get("date", "")
                    try:
                        _edt = datetime.fromisoformat(_d_raw.replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        continue
                    if _edt < _now_utc:
                        if _ev.get("actual") is not None:
                            _past.append(_ev)
                    else:
                        _future.append(_ev)

                _past.sort(key=lambda x: x.get("date", ""), reverse=True)
                _past = list(reversed(_past[:5]))  # son 5, kronolojik
                _cal_events_view = _past + _future

                _cal_rows = []
                for _e in _cal_events_view:
                    _d_str = _e.get("date", "")
                    try:
                        _dt = datetime.fromisoformat(_d_str.replace("Z", "+00:00"))
                        _dt_str = _dt.astimezone(_TRT).strftime("%Y-%m-%d %H:%M")
                    except (ValueError, TypeError):
                        _dt_str = _d_str[:16].replace("T", " ")

                    _unit = _e.get("unit") or ""
                    def _f(v, u=_unit):
                        return f"{v}{u}" if v is not None else "—"

                    _cal_rows.append({
                        "Tarih (TRT)": _dt_str,
                        "Önem":        _IMP_MAP.get(_e.get("importance"), "—"),
                        "Önceki":      _f(_e.get("previous")),
                        "Beklenti":    _f(_e.get("forecast")),
                        "Açıklanan":   _f(_e.get("actual")),
                        "Başlık":      TR_EVENT_TITLES.get(_e.get("title", ""), _e.get("title", "")),
                    })

                _cal_df = pd.DataFrame(_cal_rows)

                def _cal_imp_color(v):
                    if v == "YÜK": return "color: #ff4b4b; font-weight: bold"
                    if v == "ORT": return "color: #ffcc00"
                    if v == "DÜŞ": return "color: #888888"
                    return ""

                _cal_styled = _cal_df.style.map(_cal_imp_color, subset=["Önem"])
                st.caption(
                    f"{CAL_COUNTRIES[_cal_country]} · son {len(_past)} açıklanan + "
                    f"önümüzdeki {_cal_days} gün ({len(_future)} olay) · cache 30dk"
                )
                st.dataframe(_cal_styled, use_container_width=True, hide_index=True)

    else:
        st.error("Veri çekilemedi. Ticker veya internet bağlantısını kontrol edin.")
