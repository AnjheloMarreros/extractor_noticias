"""
app.py - Aplicación web del extractor (Streamlit).

Ejecutar:
    streamlit run app.py

Tiene dos pestañas:
  1. Analizar texto  : se pega una noticia y se muestran sus entidades.
  2. Consultar corpus: responde preguntas como "¿qué instituciones aparecen más
     en noticias policiales?" o "¿qué distritos se mencionan más?".
"""

import os
import pandas as pd
import streamlit as st
from extractor import extraer_entidades, DISTRITOS, SINONIMOS

st.set_page_config(page_title="Extractor de noticias regionales", layout="wide")
st.title("Extractor de información de noticias regionales")
st.caption("Personas, organizaciones, lugares y fechas en noticias de La Libertad")

COLORES = {"PERSONA": "#f4c7c3", "ORGANIZACION": "#c6dafc", "LUGAR": "#c8e6c9", "FECHA": "#ffe0b2"}

pestana1, pestana2 = st.tabs(["Analizar texto", "Consultar corpus"])

# ---------------------------------------------------------------------------
# Pestaña 1: analizar una noticia
# ---------------------------------------------------------------------------
with pestana1:
    texto = st.text_area("Pega aquí el texto de una noticia:", height=200)

    if st.button("Extraer entidades") and texto.strip():
        entidades = extraer_entidades(texto)

        # Texto con las entidades resaltadas
        html, ultimo = "", 0
        for e in entidades:
            if e["inicio"] < ultimo:          # se salta entidades superpuestas
                continue
            html += texto[ultimo:e["inicio"]]
            html += (f"<mark style='background:{COLORES[e['tipo']]};padding:2px 4px;"
                     f"border-radius:4px'>{texto[e['inicio']:e['fin']]} "
                     f"<b style='font-size:0.7em'>{e['tipo']}</b></mark>")
            ultimo = e["fin"]
        html += texto[ultimo:]
        st.markdown(html, unsafe_allow_html=True)

        # Tabla estructurada
        st.subheader("Tabla de entidades")
        tabla = pd.DataFrame(entidades)[["entidad", "tipo"]].drop_duplicates()
        st.dataframe(tabla, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Pestaña 2: consultar el corpus completo
# ---------------------------------------------------------------------------
with pestana2:
    if not (os.path.exists("noticias.csv") and os.path.exists("entidades.csv")):
        st.warning("Primero ejecuta paso4_extraccion.py para generar noticias.csv y entidades.csv.")
        st.stop()

    noticias = pd.read_csv("noticias.csv")
    entidades = pd.read_csv("entidades.csv")
    datos = entidades.merge(noticias, left_on="id_noticia", right_on="id")

    c1, c2, c3 = st.columns(3)
    c1.metric("Noticias", f"{len(noticias):,}")
    c2.metric("Entidades extraídas", f"{len(entidades):,}")
    c3.metric("Noticias de La Libertad", f"{(noticias['region'] == 'la-libertad').sum():,}")

    pregunta = st.selectbox("Elige una pregunta:", [
        "¿Qué instituciones aparecen más en noticias policiales?",
        "¿Qué distritos de La Libertad se mencionan más?",
        "¿Qué personas aparecen más?",
        "Consulta libre",
    ])

    if pregunta.startswith("¿Qué instituciones"):
        filtro = datos[(datos["tipo"] == "ORGANIZACION") & (datos["categoria"] == "Policial")]
    elif pregunta.startswith("¿Qué distritos"):
        distritos = {SINONIMOS.get(d, d) for d in DISTRITOS}
        filtro = datos[(datos["tipo"] == "LUGAR") & (datos["entidad"].isin(distritos))]
    elif pregunta.startswith("¿Qué personas"):
        filtro = datos[datos["tipo"] == "PERSONA"]
    else:
        tipo = st.selectbox("Tipo de entidad:", ["PERSONA", "ORGANIZACION", "LUGAR", "FECHA"])
        cat = st.selectbox("Categoría:", ["Todas", "Policial", "Otros"])
        solo_ll = st.checkbox("Solo noticias de La Libertad")
        filtro = datos[datos["tipo"] == tipo]
        if cat != "Todas":
            filtro = filtro[filtro["categoria"] == cat]
        if solo_ll:
            filtro = filtro[filtro["region"] == "la-libertad"]

    cantidad = st.slider("Cantidad a mostrar:", 5, 30, 10)
    ranking = (filtro.groupby("entidad")["id_noticia"].nunique()
               .sort_values(ascending=False).head(cantidad)
               .rename("noticias").reset_index())

    st.subheader(pregunta)
    st.bar_chart(ranking, x="entidad", y="noticias", horizontal=True)
    st.dataframe(ranking, use_container_width=True, hide_index=True)

    # Ver las noticias donde aparece una entidad
    if not ranking.empty:
        elegida = st.selectbox("Ver noticias donde aparece:", ranking["entidad"])
        ids = filtro[filtro["entidad"] == elegida]["id_noticia"].unique()
        st.dataframe(noticias[noticias["id"].isin(ids)][["fecha_publicacion", "titulo", "url"]],
                     use_container_width=True, hide_index=True)
