import streamlit as st
import pandas as pd

st.set_page_config(page_title="Top 2000 - Zoeken", layout="wide")
st.title("Top 2000 (2025) - Zoeken")

df = pd.read_csv("TOP2000-2025.csv", encoding="utf-8")
df.columns = df.columns.str.replace("\ufeff", "", regex=False).str.strip()
df.columns = df.columns.str.replace("ï»¿", "", regex=False).str.strip()


zoekterm = st.text_input("Zoek op titel of artiest")

if zoekterm:
    resultaat = df[
        df["Titel"].astype(str).str.contains(zoekterm, case=False, na=False)
        | df["Artiest"].astype(str).str.contains(zoekterm, case=False, na=False)
    ]
else:
    resultaat = df

st.write(f"Aantal resultaten: {len(resultaat)}")

kolommen = list(resultaat.columns)
sorteer_kolom = None
for k in ["Notering", "notering", "Positie", "positie", "Rank", "rank", "Nr", "nr"]:
    if k in kolommen:
        sorteer_kolom = k
        break

if sorteer_kolom:
    st.dataframe(resultaat.sort_values(sorteer_kolom), use_container_width=True)
else:
    st.dataframe(resultaat, use_container_width=True)
    st.info("Geen kolom 'Notering/Positie/Rank' gevonden, daarom niet gesorteerd.")
