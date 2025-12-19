import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Top 2000 zoekapp", layout="wide")

CSV_FILE = "top2000.csv"
CSV_SEP = ";"

def load_data():
    path = Path(CSV_FILE)
    if not path.exists():
        st.error(f"Bestand niet gevonden: {CSV_FILE}")
        st.stop()

    df = pd.read_csv(path, sep=CSV_SEP, dtype=str, keep_default_na=False)
    df = df.fillna("")
    return df

st.title("Top 2000 – zoekapp")

col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    st.caption(f"Bronbestand: {CSV_FILE}")
with col2:
    st.caption(f"Laatst gewijzigd: {Path(CSV_FILE).stat().st_mtime if Path(CSV_FILE).exists() else 'onbekend'}")
with col3:
    st.caption("Tip: update je CSV op GitHub en refresh deze pagina.")

df = load_data()

zoekterm = st.text_input("Zoek (alles doorzoekbaar)", "")

if zoekterm.strip():
    term = zoekterm.lower()
    mask = pd.Series(False, index=df.index)
    for col in df.columns:
        mask = mask | df[col].str.lower().str.contains(term, na=False)
    resultaat = df[mask].copy()
else:
    resultaat = df.copy()

for kolom in ["positie", "jaartal"]:
    if kolom in resultaat.columns:
        resultaat[kolom] = resultaat[kolom].str.replace(".0", "", regex=False)

resultaat = resultaat.reset_index(drop=True)

st.write(f"Aantal resultaten: {len(resultaat)}")
st.dataframe(resultaat, use_container_width=True, hide_index=True)
