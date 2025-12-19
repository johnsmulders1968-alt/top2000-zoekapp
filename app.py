import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, date, timedelta

st.set_page_config(page_title="Top 2000 zoekapp", layout="wide")

CSV_FILE = "top2000.csv"
CSV_SEP = ";"

def load_data():
    path = Path(CSV_FILE)
    if not path.exists():
        st.error(f"Bestand niet gevonden: {CSV_FILE}")
        st.stop()
    df = pd.read_csv(path, sep=CSV_SEP, dtype=str, keep_default_na=False).fillna("")
    return df

def parse_datetime_from_columns(df, dt_col, date_col, time_col):
    df = df.copy()

    if dt_col and dt_col != "(geen)":
        df["_dt"] = pd.to_datetime(df[dt_col], errors="coerce", dayfirst=True)
        return df

    if date_col and time_col and date_col != "(geen)" and time_col != "(geen)":
        combo = (df[date_col].astype(str).str.strip() + " " + df[time_col].astype(str).str.strip()).str.strip()
        df["_dt"] = pd.to_datetime(combo, errors="coerce", dayfirst=True)
        return df

    df["_dt"] = pd.NaT
    return df

df = load_data()

st.title("Top 2000 – zoekapp")

# bediening
col1, col2, col3 = st.columns([1.1, 1.1, 2.0])
with col1:
    modus = st.radio("Weergave", ["Zoeken", "Komend uur"], horizontal=True)
with col2:
    gekozen_datum = st.date_input("Datum", value=date.today())
    gekozen_tijd = st.time_input("Tijd", value=datetime.now().time().replace(second=0, microsecond=0))
with col3:
    st.caption(f"Bronbestand: {CSV_FILE}")

# kolomkeuze in sidebar
st.sidebar.header("Datum/tijd instellingen")

st.sidebar.caption("Kolommen in je CSV:")
st.sidebar.write(list(df.columns))

options = ["(geen)"] + list(df.columns)

dt_col = st.sidebar.selectbox("1 kolom met datum+tijd (optioneel)", options, index=0)

date_col = st.sidebar.selectbox("Datum-kolom (als je geen datum+tijd kolom hebt)", options, index=0)
time_col = st.sidebar.selectbox("Tijd-kolom (als je geen datum+tijd kolom hebt)", options, index=0)

df = parse_datetime_from_columns(df, dt_col, date_col, time_col)

zoekterm = st.text_input("Zoek (alles doorzoekbaar)", "")

resultaat = df.copy()

# filter: komend uur
if modus == "Komend uur":
    if resultaat["_dt"].isna().all():
        st.error(
            "Ik kan 'Komend uur' niet tonen omdat ik geen geldige datum/tijd kan maken.\n\n"
            "Kies in de sidebar óf een kolom met datum+tijd, óf een datum-kolom + tijd-kolom."
        )
        st.stop()

    start_dt = datetime.combine(gekozen_datum, gekozen_tijd)
    end_dt = start_dt + timedelta(hours=1)

    resultaat = resultaat[(resultaat["_dt"] >= start_dt) & (resultaat["_dt"] < end_dt)].copy()

# filter: zoekterm
if zoekterm.strip():
    term = zoekterm.lower()
    mask = pd.Series(False, index=resultaat.index)
    for col in resultaat.columns:
        if col == "_dt":
            continue
        mask = mask | resultaat[col].astype(str).str.lower().str.contains(term, na=False)
    resultaat = resultaat[mask].copy()

# opschonen
for kolom in ["positie", "jaartal"]:
    if kolom in resultaat.columns:
        resultaat[kolom] = resultaat[kolom].str.replace(".0", "", regex=False)

# sorteren op tijd als beschikbaar
if not resultaat["_dt"].isna().all():
    resultaat = resultaat.sort_values("_dt", ascending=True)

resultaat = resultaat.reset_index(drop=True)

st.write(f"Aantal resultaten: {len(resultaat)}")
st.dataframe(resultaat.drop(columns=["_dt"], errors="ignore"), use_container_width=True, hide_index=True)
