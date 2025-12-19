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
    try:
        return pd.to_datetime(s, dayfirst=True, errors="coerce").strftime("%d-%m-%Y")
    except Exception:
        return ""

df = load_data()

DATE_COL = "datum"
SLOT_COL = "tijdsvak"

if DATE_COL not in df.columns or SLOT_COL not in df.columns:
    st.error("Vereiste kolommen ontbreken: datum en/of tijdsvak")
    st.stop()

df["_datum_dag"] = df[DATE_COL].apply(norm_date_str)

st.title("Top 2000 – zoekapp")

# ---------- bediening ----------
col1, col2, col3 = st.columns([1.2, 2.0, 1.2])

with col1:
    gekozen_datum = st.date_input("Datum", value=date.today())

with col3:
    st.caption(f"Bronbestand: {CSV_FILE}")

# zoekveld + wis knop
zoek_col, wis_col = st.columns([5, 1])
with zoek_col:
    zoekterm = st.text_input("Zoek (alles doorzoekbaar)", "")
with wis_col:
    wis = st.button("Wis")

if wis:
    st.session_state.clear()
    st.rerun()

# ---------- LOGICA ----------
# ALS er een zoekterm is → GEEN datum / tijdsvak filters
if zoekterm.strip():
    resultaat = df.copy()

else:
    # filter op datum
    gekozen_datum_str = gekozen_datum.strftime("%d-%m-%Y")
    df_dag = df[df["_datum_dag"] == gekozen_datum_str].copy()

    # tijdsvakken voor deze datum
    tijdsvakken = sorted(
        [x for x in df_dag[SLOT_COL].unique().tolist() if str(x).strip()]
    )

    if tijdsvakken:
        gekozen_tijdsvak = st.selectbox("Tijdsvak", tijdsvakken)
        resultaat = df_dag[
            df_dag[SLOT_COL].astype(str).str.strip()
            == str(gekozen_tijdsvak).strip()
        ].copy()
    else:
        st.warning("Geen tijdsvakken gevonden voor deze datum.")
        resultaat = df_dag.iloc[0:0].copy()

# ---------- ZOEKFILTER ----------
if zoekterm.strip():
    term = zoekterm.lower()
    mask = pd.Series(False, index=resultaat.index)
    for col in resultaat.columns:
        if col == "_datum_dag":
            continue
        mask = mask | resultaat[col].astype(str).str.lower().str.contains(term, na=False)
    resultaat = resultaat[mask].copy()

# ---------- OPSCHONEN ----------
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
