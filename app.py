import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, date, time, timedelta

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

def norm_date_str(s: str) -> str:
    s = str(s).strip()
    if not s:
        return ""
    # accepteer "25-12-2025 00:00" en "25-12-2025"
    try:
        dt = pd.to_datetime(s, errors="coerce", dayfirst=True)
        if pd.isna(dt):
            return s
        return dt.strftime("%d-%m-%Y")
    except Exception:
        return s

def parse_tijdsvak_start_end(tijdsvak: str):
    # verwacht iets als "20.00 - 21.00" of "20:00 - 21:00"
    tv = str(tijdsvak).strip()
    if not tv:
        return None, None
    tv = tv.replace("–", "-").replace("—", "-")
    parts = [p.strip() for p in tv.split("-")]
    if len(parts) < 2:
        return None, None
    start_s = parts[0].replace(".", ":")
    end_s = parts[1].replace(".", ":")
    try:
        start_t = pd.to_datetime(start_s, errors="coerce").to_pydatetime().time()
        end_t = pd.to_datetime(end_s, errors="coerce").to_pydatetime().time()
        return start_t, end_t
    except Exception:
        return None, None

def format_tijdsvak_from_time(t: time):
    # maakt "HH.00 - HH+1.00"
    h = int(t.hour)
    start = f"{h:02d}.00"
    end = f"{(h + 1) % 24:02d}.00"
    return f"{start} - {end}"

df = load_data()

# kolommen (pas aan als jouw CSV anders heet)
DATE_COL = "datum"
SLOT_COL = "tijdsvak"

if DATE_COL not in df.columns or SLOT_COL not in df.columns:
    st.error(f"Ik mis kolommen. Vereist: '{DATE_COL}' en '{SLOT_COL}'.")
    st.stop()

# extra kolom voor datum (alleen dag, als tekst)
df["_datum_dag"] = df[DATE_COL].apply(norm_date_str)

st.title("Top 2000 – zoekapp")

col1, col2, col3 = st.columns([1.2, 1.2, 2.0])

with col1:
    modus = st.radio("Weergave", ["Zoeken", "Kies tijdsvak", "Komend uur"], horizontal=True)

with col2:
    gekozen_datum = st.date_input("Datum", value=date.today())
    gekozen_tijd = st.time_input("Tijd", value=datetime.now().time().replace(second=0, microsecond=0))

with col3:
    st.caption(f"Bronbestand: {CSV_FILE}")

zoekterm = st.text_input("Zoek (alles doorzoekbaar)", "")

# datumfilter (op tekstdag)
gekozen_datum_str = gekozen_datum.strftime("%d-%m-%Y")
df_dag = df[df["_datum_dag"] == gekozen_datum_str].copy()

# tijdsvak selectie (op tekst)
tijdsvakken = sorted([x for x in df_dag[SLOT_COL].unique().tolist() if str(x).strip()])

gekozen_tijdsvak = None

if modus == "Kies tijdsvak":
    if not tijdsvakken:
        st.warning("Geen tijdsvakken gevonden voor deze datum.")
    else:
        gekozen_tijdsvak = st.selectbox("Tijdsvak", tijdsvakken)

if modus == "Komend uur":
    if not tijdsvakken:
        st.warning("Geen tijdsvakken gevonden voor deze datum.")
    else:
        target = format_tijdsvak_from_time(gekozen_tijd)
        # probeer exacte match, anders fuzzy: tijdsvakken die met startuur beginnen
        if target in tijdsvakken:
            gekozen_tijdsvak = target
        else:
            start_prefix = f"{int(gekozen_tijd.hour):02d}."
            candidates = [tv for tv in tijdsvakken if tv.strip().startswith(start_prefix)]
            gekozen_tijdsvak = candidates[0] if candidates else None

resultaat = df.copy()

# pas datumfilter toe voor tijdsvak-modi
if modus in ["Kies tijdsvak", "Komend uur"]:
    resultaat = df_dag
    if gekozen_tijdsvak:
        resultaat = resultaat[resultaat[SLOT_COL].astype(str).str.strip() == str(gekozen_tijdsvak).strip()].copy()
    else:
        resultaat = resultaat.iloc[0:0].copy()

# zoekfilter (bovenop alles)
if zoekterm.strip():
    term = zoekterm.lower()
    mask = pd.Series(False, index=resultaat.index)
    for col in resultaat.columns:
        if col == "_datum_dag":
            continue
        mask = mask | resultaat[col].astype(str).str.lower().str.contains(term, na=False)
    resultaat = resultaat[mask].copy()

# opschonen
for kolom in ["positie", "jaartal"]:
    if kolom in resultaat.columns:
        resultaat[kolom] = resultaat[kolom].str.replace(".0", "", regex=False)

# sorteer binnen dag op tijdsvak (starttijd), als dat lukt
if not resultaat.empty and SLOT_COL in resultaat.columns:
    starts = []
    for tv in resultaat[SLOT_COL].tolist():
        st_t, _ = parse_tijdsvak_start_end(tv)
        starts.append(st_t)
    resultaat["_starttijd"] = starts
    if resultaat["_starttijd"].notna().any():
        resultaat = resultaat.sort_values(["_starttijd"], ascending=True)
    resultaat = resultaat.drop(columns=["_starttijd"], errors="ignore")

resultaat = resultaat.reset_index(drop=True)

st.write(f"Aantal resultaten: {len(resultaat)}")
st.dataframe(resultaat.drop(columns=["_datum_dag"], errors="ignore"), use_container_width=True, hide_index=True)
