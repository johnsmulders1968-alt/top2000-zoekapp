import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Top 2000 zoekapp", layout="wide")

CSV_FILE = "top2000.csv"
CSV_SEP = ";"
DATE_COL = "datum"
SLOT_COL = "tijdsvak"

def load_data():
    path = Path(CSV_FILE)
    if not path.exists():
        st.error(f"Bestand niet gevonden: {CSV_FILE}")
        st.stop()
    return pd.read_csv(path, sep=CSV_SEP, dtype=str, keep_default_na=False).fillna("")

def norm_date_dmy(s: str) -> str:
    s = str(s).strip()
    if not s:
        return ""
    dt = pd.to_datetime(s, errors="coerce", dayfirst=True)
    if pd.isna(dt):
        return ""
    return dt.strftime("%d-%m-%Y")

df = load_data()

if DATE_COL not in df.columns or SLOT_COL not in df.columns:
    st.error(f"Ik mis kolommen. Vereist: '{DATE_COL}' en '{SLOT_COL}'.")
    st.stop()

# hulpkolom: datum als dd-mm-jjjj
df["_datum_dag"] = df[DATE_COL].apply(norm_date_dmy)

# lijst met beschikbare datums (alleen datums die echt in je CSV zitten)
available_dates = sorted([d for d in df["_datum_dag"].unique().tolist() if d])
if not available_dates:
    st.error("Geen geldige datums gevonden in de CSV.")
    st.stop()

# session state defaults
if "zoekterm" not in st.session_state:
    st.session_state.zoekterm = ""
if "gekozen_datum" not in st.session_state:
    st.session_state.gekozen_datum = available_dates[0]
if "gekozen_tijdsvak" not in st.session_state:
    st.session_state.gekozen_tijdsvak = ""

def reset_naar_schema():
    st.session_state.zoekterm = ""
    st.session_state.gekozen_datum = available_dates[0]
    st.session_state.gekozen_tijdsvak = ""
    st.rerun()

st.title("Top 2000 – zoekapp")

top_left, top_right = st.columns([6, 1])
with top_left:
    st.caption("Zoeken is los van datum/tijdvak. Klik Reset om terug te gaan naar Datum + Tijdsvak.")
with top_right:
    st.button("Reset", on_click=reset_naar_schema)

st.caption(f"Bronbestand: {CSV_FILE}")

# zoekveld
st.text_input("Zoek (alles doorzoekbaar)", key="zoekterm")

# als er een zoekterm is: toon alleen zoekresultaten (geen datum/tijdvak filtering)
if st.session_state.zoekterm.strip():
    resultaat = df.copy()

    term = st.session_state.zoekterm.lower()
    mask = pd.Series(False, index=resultaat.index)
    for col in resultaat.columns:
        if col == "_datum_dag":
            continue
        mask = mask | resultaat[col].astype(str).str.lower().str.contains(term, na=False)
    resultaat = resultaat[mask].copy()

else:
    # datum kiezen uit beschikbare datums (altijd raak)
    gekozen_datum = st.selectbox(
        "Datum",
        available_dates,
        index=available_dates.index(st.session_state.gekozen_datum) if st.session_state.gekozen_datum in available_dates else 0,
        key="gekozen_datum",
    )

    df_dag = df[df["_datum_dag"] == gekozen_datum].copy()

    tijdsvakken = sorted([x for x in df_dag[SLOT_COL].unique().tolist() if str(x).strip()])

    if not tijdsvakken:
        st.warning("Geen tijdsvakken gevonden voor deze datum.")
        resultaat = df_dag.iloc[0:0].copy()
    else:
        if st.session_state.gekozen_tijdsvak not in tijdsvakken:
            st.session_state.gekozen_tijdsvak = tijdsvakken[0]

        gekozen_tijdsvak = st.selectbox(
            "Tijdsvak",
            tijdsvakken,
            index=tijdsvakken.index(st.session_state.gekozen_tijdsvak),
            key="gekozen_tijdsvak",
        )

        resultaat = df_dag[df_dag[SLOT_COL].astype(str).str.strip() == str(gekozen_tijdsvak).strip()].copy()

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
