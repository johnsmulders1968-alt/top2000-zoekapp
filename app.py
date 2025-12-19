import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date

st.set_page_config(page_title="Top 2000 zoekapp", layout="wide")

CSV_FILE = "top2000.csv"
CSV_SEP = ";"

def load_data():
    path = Path(CSV_FILE)
    if not path.exists():
        st.error(f"Bestand niet gevonden: {CSV_FILE}")
        st.stop()
    return pd.read_csv(path, sep=CSV_SEP, dtype=str, keep_default_na=False).fillna("")

def norm_date_str(s: str) -> str:
    s = str(s).strip()
    if not s:
        return ""
    dt = pd.to_datetime(s, errors="coerce", dayfirst=True)
    if pd.isna(dt):
        return ""
    return dt.strftime("%d-%m-%Y")

def to_date_obj(dmy: str):
    dt = pd.to_datetime(dmy, errors="coerce", dayfirst=True)
    if pd.isna(dt):
        return None
    return dt.date()

df = load_data()

DATE_COL = "datum"
SLOT_COL = "tijdsvak"

if DATE_COL not in df.columns or SLOT_COL not in df.columns:
    st.error("Vereiste kolommen ontbreken: datum en/of tijdsvak")
    st.stop()

df["_datum_dag"] = df[DATE_COL].apply(norm_date_str)

available_dmy = sorted([d for d in df["_datum_dag"].unique().tolist() if d])
available_dates = [to_date_obj(d) for d in available_dmy]
available_dates = [d for d in available_dates if d]

if not available_dates:
    st.error("Geen geldige datums gevonden in de CSV.")
    st.stop()

DEFAULT_DATE = min(available_dates)

# --- Session state defaults ---
if "gekozen_datum" not in st.session_state:
    st.session_state.gekozen_datum = DEFAULT_DATE
if "zoekterm" not in st.session_state:
    st.session_state.zoekterm = ""
if "tijdsvak" not in st.session_state:
    st.session_state.tijdsvak = None

def reset_app():
    st.session_state.gekozen_datum = DEFAULT_DATE
    st.session_state.zoekterm = ""
    st.session_state.tijdsvak = None
    st.rerun()

st.title("Top 2000 – zoekapp")

top_left, top_right = st.columns([6, 1])
with top_left:
    st.caption("Tip: gebruik Reset om weer terug te gaan naar Datum + Tijdsvak.")
with top_right:
    st.button("Reset (F5)", on_click=reset_app)

col1, col2, col3 = st.columns([1.2, 2.0, 1.2])

with col1:
    gekozen_datum = st.date_input("Datum", value=st.session_state.gekozen_datum, key="gekozen_datum")

with col3:
    st.caption(f"Bronbestand: {CSV_FILE}")

zoekterm = st.text_input("Zoek (alles doorzoekbaar)", key="zoekterm")

# ALS er een zoekterm is: toon zoekresultaten over alles + melding + reset knop bovenin
if zoekterm.strip():
    resultaat = df.copy()

else:
    gekozen_datum_str = gekozen_datum.strftime("%d-%m-%Y")
    df_dag = df[df["_datum_dag"] == gekozen_datum_str].copy()

    tijdsvakken = sorted([x for x in df_dag[SLOT_COL].unique().tolist() if str(x).strip()])

    if tijdsvakken:
        default_index = 0
        if st.session_state.tijdsvak in tijdsvakken:
            default_index = tijdsvakken.index(st.session_state.tijdsvak)

        gekozen_tijdsvak = st.selectbox("Tijdsvak", tijdsvakken, index=default_index, key="tijdsvak")
        resultaat = df_dag[df_dag[SLOT_COL].astype(str).str.strip() == str(gekozen_tijdsvak).strip()].copy()
    else:
        st.warning("Geen tijdsvakken gevonden voor deze datum.")
        resultaat = df_dag.iloc[0:0].copy()

# zoekfilter toepassen (alleen als zoekterm ingevuld)
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

if "datum" in resultaat.columns:
    resultaat["datum"] = (
        pd.to_datetime(resultaat["datum"], errors="coerce", dayfirst=True)
        .dt.strftime("%d-%m-%Y")
    )

resultaat = resultaat.reset_index(drop=True)

st.write(f"Aantal resultaten: {len(resultaat)}")
st.dataframe(
    resultaat.drop(columns=["_datum_dag"], errors="ignore"),
    use_container_width=True,
    hide_index=True,
)
