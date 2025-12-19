import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, date, time, timedelta

st.set_page_config(page_title="Top 2000 zoekapp", layout="wide")

CSV_FILE = "top2000.csv"
CSV_SEP = ";"

# mogelijke kolomnamen (pas gerust aan)
DATETIME_COLS = ["datetime", "datumtijd", "start", "starttijd", "uitzendmoment"]
DATE_COLS = ["datum", "date", "dag"]
TIME_COLS = ["tijd", "time", "uur", "start_uur"]

def pick_col(df, candidates):
    cols_lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in cols_lower:
            return cols_lower[cand.lower()]
    return None

def load_data():
    path = Path(CSV_FILE)
    if not path.exists():
        st.error(f"Bestand niet gevonden: {CSV_FILE}")
        st.stop()

    df = pd.read_csv(path, sep=CSV_SEP, dtype=str, keep_default_na=False).fillna("")
    return df

def add_datetime_column(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    dt_col = pick_col(df, DATETIME_COLS)
    d_col = pick_col(df, DATE_COLS)
    t_col = pick_col(df, TIME_COLS)

    if dt_col:
        # probeer automatisch te parsen (ondersteunt o.a. "2025-12-19 13:00" en "19-12-2025 13:00")
        df["_dt"] = pd.to_datetime(df[dt_col], errors="coerce", dayfirst=True)
        return df

    if d_col and t_col:
        # combineer datum + tijd
        combo = (df[d_col].astype(str).str.strip() + " " + df[t_col].astype(str).str.strip()).str.strip()
        df["_dt"] = pd.to_datetime(combo, errors="coerce", dayfirst=True)
        return df

    # geen bruikbare kolommen gevonden
    df["_dt"] = pd.NaT
    return df

df = load_data()
df = add_datetime_column(df)

st.title("Top 2000 – zoekapp")

left, mid, right = st.columns([1.1, 1.1, 2.0])

with left:
    modus = st.radio(
        "Weergave",
        ["Zoeken", "Komend uur"],
        horizontal=True,
    )

with mid:
    # datum+tijd keuze
    gekozen_datum = st.date_input("Datum", value=date.today())
    gekozen_tijd = st.time_input("Tijd", value=datetime.now().time().replace(second=0, microsecond=0))

with right:
    st.caption(f"Bronbestand: {CSV_FILE}")

# algemene zoekbalk blijft bruikbaar
zoekterm = st.text_input("Zoek (alles doorzoekbaar)", "")

resultaat = df.copy()

# filter: komend uur
if modus == "Komend uur":
    if resultaat["_dt"].isna().all():
        st.error(
            "Ik kan 'Komend uur' niet tonen, omdat ik geen datum/tijd-kolom in je CSV kan vinden.\n\n"
            "Zorg voor óf één kolom zoals: datetime / datumtijd / start, óf twee kolommen: datum + tijd."
        )
        st.stop()

    start_dt = datetime.combine(gekozen_datum, gekozen_tijd)
    end_dt = start_dt + timedelta(hours=1)

    mask = (resultaat["_dt"] >= start_dt) & (resultaat["_dt"] < end_dt)
    resultaat = resultaat[mask].copy()

# filter: zoekterm (kan óók bovenop 'Komend uur' werken)
if zoekterm.strip():
    term = zoekterm.lower()
    mask = pd.Series(False, index=resultaat.index)
    for col in resultaat.columns:
        if col == "_dt":
            continue
        mask = mask | resultaat[col].str.lower().str.contains(term, na=False)
    resultaat = resultaat[mask].copy()

# opschonen
for kolom in ["positie", "jaartal"]:
    if kolom in resultaat.columns:
        resultaat[kolom] = resultaat[kolom].str.replace(".0", "", regex=False)

# sorteer logisch als _dt bestaat
if not resultaat["_dt"].isna().all():
    resultaat = resultaat.sort_values("_dt", ascending=True)

resultaat = resultaat.reset_index(drop=True)

st.write(f"Aantal resultaten: {len(resultaat)}")

# toon datetime netjes als er een bronkolom was
if "_dt" in resultaat.columns and not resultaat["_dt"].isna().all():
    resultaat["_dt"] = resultaat["_dt"].dt.strftime("%d-%m-%Y %H:%M")

st.dataframe(resultaat.drop(columns=["_dt"], errors="ignore"), use_container_width=True, hide_index=True)
