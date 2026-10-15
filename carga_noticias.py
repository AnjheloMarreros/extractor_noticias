"""
carga_noticias.py - Lectura de noticias desde archivos PDF y URLs.

Funcionalidades:
1. Leer noticias desde archivos PDF locales
2. Leer noticias desde URLs (web)
"""

import re
import os
import requests
import time
from pathlib import Path

import trafilatura
from bs4 import BeautifulSoup


def obtener_html(url, intentos=3):
    """Obtiene contenido HTML de una URL con reintentos."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "es-PE,es;q=0.9",
    }
    for i in range(intentos):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.text
        except requests.RequestException as e:
            print(f"  Intento {i+1} falló: {e}")
        time.sleep(3 * (i + 1))
    return None


def extraer_texto_desde_url(url):
    """Extrae texto limpio de una URL mediante Trafilatura."""
    html = obtener_html(url)
    if not html:
        return None

    texto = trafilatura.extract(
        html, include_comments=False, include_tables=False, favor_precision=True
    )
    if not texto:
        return None

    texto = re.sub(r"\s+", " ", texto).strip()
    if len(texto.split()) < 40:
        return None
    return texto


def obtener_metadatos(soup):
    """Extrae metadatos básicos de la página."""
    metadatos = {"titulo": "", "seccion": "", "fecha_publicacion": ""}

    og_title = soup.find("meta", attrs={"property": "og:title"})
    if og_title and og_title.get("content"):
        metadatos["titulo"] = og_title["content"].strip()

    og_section = soup.find("meta", attrs={"property": "article:section"})
    if og_section and og_section.get("content"):
        metadatos["seccion"] = og_section["content"].strip()

    og_published = soup.find("meta", attrs={"property": "article:published_time"})
    if og_published and og_published.get("content"):
        metadatos["fecha_publicacion"] = og_published["content"][:10]

    if not metadatos["titulo"]:
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            metadatos["titulo"] = title_tag.string.strip()

    return metadatos


def cargar_desde_url(url, longitud_minima=40):
    """
    Carga una noticia desde una URL y devuelve un diccionario con la noticia.

    Args:
        url (str): URL de la noticia.
        longitud_minima (int): Mínimo de palabras para considerar válida.

    Returns:
        dict: Diccionario con la noticia extraída.
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    texto = extraer_texto_desde_url(url)
    if not texto:
        return None

    soup = BeautifulSoup(obtener_html(url), "html.parser")
    metadatos = obtener_metadatos(soup)

    id_noticia = re.sub(
        r"[^a-zA-Z0-9\-]", "", url.replace("https://", "").replace("http://", "")
    )[:50]

    return {
        "id": id_noticia,
        "titulo": metadatos["titulo"],
        "seccion": metadatos["seccion"],
        "fecha_publicacion": metadatos["fecha_publicacion"],
        "url": url,
        "texto": texto,
        "n_palabras": len(texto.split()),
        "tipo_fuente": "url",
    }


# ---------------------------------------------------------------------------
# 3. Carga de noticias desde archivos PDF
# ---------------------------------------------------------------------------

def extraer_texto_pdf(ruta_archivo):
    """
    Extrae el texto de un archivo PDF.

    Args:
        ruta_archivo (str o Path): Ruta al archivo PDF.

    Returns:
        str: Texto extraído del PDF.
    """
    try:
        import pymupdf
    except ImportError:
        raise ImportError(
            "PyMuPDF (pymupdf) no está instalado. "
            "Instálalo con: pip install pymupdf"
        )

    ruta = Path(ruta_archivo)
    if not ruta.exists():
        raise FileNotFoundError(f"El archivo PDF no existe: {ruta}")

    if ruta.suffix.lower() != ".pdf":
        raise ValueError(f"El archivo no es un PDF: {ruta.suffix}")

    doc = pymupdf.open(ruta)
    texto_completo = []

    for pagina in doc:
        texto_pagina = pagina.get_text()
        if texto_pagina:
            texto_completo.append(texto_pagina)

    doc.close()

    texto = " ".join(texto_completo)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def cargar_desde_pdf(ruta_o_directorio):
    """
    Carga todas las noticias de archivos PDF de un directorio.

    Args:
        ruta_o_directorio (str o Path): Ruta a un archivo PDF o a un directorio con PDFs.

    Returns:
        list: Lista de diccionarios con las noticias extraídas.
    """
    ruta = Path(ruta_o_directorio)

    if ruta.exists() and ruta.is_file() and ruta.suffix.lower() == ".pdf":
        archivos_pdf = [ruta]
    elif ruta.exists() and ruta.is_dir():
        archivos_pdf = list(ruta.glob("*.pdf"))
        if not archivos_pdf:
            raise ValueError(f"No se encontraron archivos PDF en el directorio: {ruta}")
    else:
        raise FileNotFoundError(f"No se encontró el archivo o directorio: {ruta}")

    noticias = []
    for pdf in sorted(archivos_pdf):
        try:
            texto = extraer_texto_pdf(pdf)
            if texto:
                noticia = {
                    "id": pdf.stem,
                    "titulo": pdf.stem.replace("_", " ").title(),
                    "url": "",
                    "texto": texto,
                    "n_palabras": len(texto.split()),
                    "tipo_fuente": "pdf",
                }
                noticias.append(noticia)
        except Exception as e:
            print(f"Error al leer {pdf.name}: {e}")

    return noticias


def cargar_noticia(origen, tipo=None):
    """
    Carga una noticia desde un archivo PDF o una URL.

    Args:
        origen (str): Ruta a un archivo PDF o una URL.
        tipo (str, opcional): Tipo explícito de origen: 'pdf' o 'url'.

    Returns:
        dict: Diccionario con la noticia extraída, o None si falló.
    """
    origen = origen.strip()

    if tipo == "url" or (tipo is None and re.match(r"^https?://", origen)):
        return cargar_desde_url(origen)

    elif tipo == "pdf" or (tipo is None and Path(origen).suffix.lower() == ".pdf"):
        return {"noticias": cargar_desde_pdf(origen)}

    else:
        if Path(origen).suffix.lower() == ".pdf":
            return {"noticias": cargar_desde_pdf(origen)}
        else:
            return {"noticias": cargar_desde_url(origen)}
