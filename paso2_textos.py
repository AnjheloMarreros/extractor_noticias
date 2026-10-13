"""
PASO 2 - Descargar y extraer el texto de cada noticia.

Lee enlaces.csv (generado en el paso 1), descarga cada noticia y extrae con Trafilatura
el texto limpio del cuerpo, más título, fecha de publicación y sección.
El resultado se guarda en corpus_noticias.csv.

Uso:
    python paso2_textos.py --meta 12000

Se puede detener y volver a ejecutar: las URL ya procesadas se saltan.
"""

import argparse
import csv
import os
import re
import time
from datetime import datetime

import requests
import trafilatura
from bs4 import BeautifulSoup

ENTRADA = "enlaces.csv"
SALIDA = "corpus_noticias.csv"
PROCESADAS = "urls_procesadas.txt"
CAMPOS = ["id", "fecha_publicacion", "titulo", "seccion", "region",
          "url", "texto", "n_palabras", "fecha_recoleccion"]
HEADERS = {
    "User-Agent": "Mozilla/5.0 (proyecto academico UPAO - extraccion de entidades)",
    "Accept-Language": "es-PE,es;q=0.9",
}
MIN_PALABRAS = 40   # descarta videos o galerías sin texto


def obtener(s, url, intentos=3):
    for i in range(intentos):
        try:
            r = s.get(url, timeout=25)
            if r.status_code == 200:
                return r.text
            if r.status_code in (403, 404):
                return None
        except requests.RequestException:
            pass
        time.sleep(3 * (i + 1))
    return None


def meta(soup, *nombres):
    for n in nombres:
        tag = soup.find("meta", attrs={"property": n}) or soup.find("meta", attrs={"name": n})
        if tag and tag.get("content"):
            return tag["content"].strip()
    return ""


def procesar(s, url, region):
    html = obtener(s, url)
    if not html:
        return None
    texto = trafilatura.extract(html, include_comments=False, include_tables=False,
                                favor_precision=True) or ""
    texto = re.sub(r"\s+", " ", texto).strip()
    if len(texto.split()) < MIN_PALABRAS:
        return None
    soup = BeautifulSoup(html, "html.parser")
    titulo = meta(soup, "og:title") or (soup.title.string.strip() if soup.title else "")
    return {
        "id": url.rsplit("-noticia-", 1)[-1],
        "fecha_publicacion": meta(soup, "article:published_time")[:10],
        "titulo": titulo,
        "seccion": meta(soup, "article:section"),
        "region": region,
        "url": url,
        "texto": texto,
        "n_palabras": len(texto.split()),
        "fecha_recoleccion": datetime.now().strftime("%Y-%m-%d"),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--meta", type=int, default=12000)
    p.add_argument("--pausa", type=float, default=1.0)
    a = p.parse_args()

    with open(ENTRADA, encoding="utf-8", newline="") as f:
        enlaces = list(csv.DictReader(f))

    hechas = set()
    if os.path.exists(PROCESADAS):
        hechas = set(open(PROCESADAS, encoding="utf-8").read().split())
    total = 0
    if os.path.exists(SALIDA):
        with open(SALIDA, encoding="utf-8", newline="") as f:
            total = sum(1 for _ in csv.DictReader(f))

    s = requests.Session()
    s.headers.update(HEADERS)
    nuevo = not os.path.exists(SALIDA)

    with open(SALIDA, "a", encoding="utf-8", newline="") as f, \
         open(PROCESADAS, "a", encoding="utf-8") as reg:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        if nuevo:
            w.writeheader()
        for e in enlaces:
            if total >= a.meta:
                break
            if e["url"] in hechas:
                continue
            fila = procesar(s, e["url"], e["region"])
            if fila:
                w.writerow(fila)
                total += 1
            reg.write(e["url"] + "\n")
            hechas.add(e["url"])
            if total % 50 == 0:
                f.flush(); reg.flush()
                print(f"Noticias guardadas: {total}")
            time.sleep(a.pausa)

    print(f"Listo. {total} noticias en {SALIDA}")


if __name__ == "__main__":
    main()
