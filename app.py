import streamlit as st
import pandas as pd

st.set_page_config(page_title="Top 2000 zoekapp", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("top2000.csv", sep=";")
    # alles naar tekst zodat zoeken altijd werkt
    for col in df.columns:
        df[col] = df[col].astype(str)
    return df

df = load_data()

st.title("Top 2000 – zoekapp")

zoekterm = st.text_input("Zoek (alles doorzoekbaar)", "")

if zoekterm.strip():
    term = zoekterm.lower()
    mask = False
    for col in df.columns:
        mask = mask | df[col].str.lower().str.contains(term, na=False)
    resultaat = df[mask]
else:
    resultaat = df

st.write(f"Aantal resultaten: {len(resultaat)}")
# index verbergen
resultaat = resultaat.reset_index(drop=True)

# positie en jaartal zonder decimalen (als ze bestaan)
for kolom in ["positie", "jaartal"]:
    if kolom in resultaat.columns:
        resultaat[kolom] = (
            resultaat[kolom]
            .str.replace(".0", "", regex=False)
        )

st.dataframe(resultaat, use_container_width=True)

