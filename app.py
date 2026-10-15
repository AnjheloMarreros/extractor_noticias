"""
app.py - Aplicación web del extractor (Streamlit).

Ejecutar:
    streamlit run app.py

La aplicación unificada acepta:
1. Texto pegado
2. URL de noticia
3. Archivo PDF

En todos los casos, reporta las entidades identificadas.
"""

import os
import pandas as pd
import streamlit as st
from pathlib import Path

from extractor_noticias import analizar_texto, cargar_desde_url, cargar_desde_pdf

st.set_page_config(page_title="Extractor de noticias regionales", layout="wide")
st.title("Extractor de información de noticias regionales")
st.caption("Personas, organizaciones, lugares y fechas en noticias de La Libertad")

COLORES = {"PERSONA": "#f4c7c3", "ORGANIZACION": "#c6dafc", "LUGAR": "#c8e6c9", "FECHA": "#ffe0b2"}


def mostrar_entidades_con_resaltado(texto, entidades):
    """Muestra el texto con las entidades resaltadas."""
    html, ultimo = "", 0
    for e in entidades:
        if e["inicio"] < ultimo:
            continue
        html += texto[ultimo:e["inicio"]]
        html += (
            "<mark style='background:" + COLORES[e["tipo"]] + ";padding:2px 4px;"
            "border-radius:4px'>" + texto[e["inicio"]:e["fin"]] + " "
            "<b style='font-size:0.7em'>" + e["tipo"] + "</b></mark>"
        )
        ultimo = e["fin"]
    html += texto[ultimo:]
    st.markdown(html, unsafe_allow_html=True)


def mostrar_tabla_entidades(entidades):
    """Muestra la tabla de entidades."""
    tabla = pd.DataFrame(entidades)[["entidad", "tipo"]].drop_duplicates()
    st.dataframe(tabla, use_container_width=True, hide_index=True)


def mostrar_resultado_procesamiento(resultado):
    """Muestra el resultado de procesar una fuente."""
    if not resultado:
        st.error("No se pudo procesar la fuente.")
        return

    st.success(f"Fuente procesada correctamente")
    st.markdown(f"**Título:** {resultado.get('titulo', 'N/A')}")
    st.markdown(f"**Categoría:** {resultado.get('categoria', 'N/A')}")
    st.markdown(f"**Fuente:** {resultado.get('tipo_fuente', 'N/A')}")

    texto = resultado["texto"]
    entidades = resultado["entidades"]

    st.subheader("Entidades identificadas")
    mostrar_entidades_con_resaltado(texto, entidades)
    mostrar_tabla_entidades(entidades)

# ============================================================================
# SECCIÓN PRINCIPAL: Carga de fuente
# ============================================================================

st.subheader("1. Selecciona la fuente de la noticia")

opcion = st.radio(
    "¿Cómo deseas ingresar la noticia?",
    ["Texto pegado", "URL de noticia", "Archivo PDF"],
)

if opcion == "Texto pegado":
    st.subheader("Ingresa el texto de la noticia")
    texto = st.text_area("Pega aquí el texto de una noticia:", height=300)

    if st.button("Extraer entidades") and texto.strip():
        resultado = analizar_texto(texto)
        mostrar_resultado_procesamiento(resultado)

elif opcion == "URL de noticia":
    st.subheader("Ingresa la URL de la noticia")
    url = st.text_input("Ingresa la URL de la noticia:", placeholder="https://rpp.pe/noticia-123")

    if st.button("Cargar desde URL") and url:
        with st.spinner("Cargando y analizando noticia..."):
            resultado = cargar_desde_url(url)
            mostrar_resultado_procesamiento(resultado)

elif opcion == "Archivo PDF":
    st.subheader("Sube un archivo PDF")
    archivo_pdf = st.file_uploader("Sube un archivo PDF", type=["pdf"])

    if archivo_pdf is not None:
        with st.spinner("Extrayendo texto del PDF y analizando..."):
            pdf_bytes = archivo_pdf.read()
            temp_path = "temp_carga.pdf"
            with open(temp_path, "wb") as f:
                f.write(pdf_bytes)

            try:
                resultado = cargar_desde_pdf(temp_path)
                mostrar_resultado_procesamiento(resultado)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

