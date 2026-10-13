"""
PASO 1 - Recolectar los enlaces de las noticias.

Recorre el archivo diario de RPP, sección "Perú" (https://rpp.pe/archivo/peru/AAAA-MM-DD),
y guarda en enlaces.csv la URL de cada noticia, su fecha de archivo y su región.

Uso:
    python paso1_enlaces.py --desde 2021-01-01 --hasta 2026-10-09

Se puede detener y volver a ejecutar: los días ya revisados se saltan.
"""

import argparse
import csv
import os
import re
import time
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup

BASE = "https://rpp.pe"
ARCHIVO = BASE + "/archivo/peru/{fecha}"
SALIDA = "enlaces.csv"
DIAS_HECHOS = "dias_revisados.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (proyecto academico UPAO - extraccion de entidades)",
    "Accept-Language": "es-PE,es;q=0.9",
}
PATRON_NOTICIA = re.compile(r"^https://rpp\.pe/[a-z0-9\-/]+-noticia-(\d+)$")
REGIONES = {
    "amazonas", "ancash", "apurimac", "arequipa", "ayacucho", "cajamarca", "callao",
    "cusco", "huancavelica", "huanuco", "ica", "junin", "la-libertad", "lambayeque",
    "lima", "loreto", "madre-de-dios", "moquegua", "pasco", "piura", "puno",
    "san-martin", "tacna", "tumbes", "ucayali",
}


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


def region_desde_url(url):
    partes = url.replace(BASE + "/", "").split("/")
    if len(partes) > 2 and partes[0] == "peru" and partes[1] in REGIONES:
        return partes[1]
    return ""


def enlaces_del_dia(s, dia):
    html = obtener(s, ARCHIVO.format(fecha=dia.isoformat()))
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    for a in soup.find_all("a", href=True):
        href = a["href"].split("?")[0].split("#")[0]
        if href.startswith("/"):
            href = BASE + href
        if PATRON_NOTICIA.match(href) and href not in urls:
            urls.append(href)
    return urls


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--desde", default="2021-01-01")
    p.add_argument("--hasta", default=(date.today() - timedelta(days=1)).isoformat())
    p.add_argument("--pausa", type=float, default=1.0)
    a = p.parse_args()

    hechos = set()
    if os.path.exists(DIAS_HECHOS):
        hechos = set(open(DIAS_HECHOS, encoding="utf-8").read().split())
    vistas = set()
    if os.path.exists(SALIDA):
        with open(SALIDA, encoding="utf-8", newline="") as f:
            vistas = {fila["url"] for fila in csv.DictReader(f)}

    s = requests.Session()
    s.headers.update(HEADERS)
    nuevo = not os.path.exists(SALIDA)

    with open(SALIDA, "a", encoding="utf-8", newline="") as f, \
         open(DIAS_HECHOS, "a", encoding="utf-8") as reg:
        w = csv.writer(f)
        if nuevo:
            w.writerow(["url", "fecha_archivo", "region"])
        dia, fin = date.fromisoformat(a.hasta), date.fromisoformat(a.desde)
        while dia >= fin:
            if dia.isoformat() not in hechos:
                urls = enlaces_del_dia(s, dia)
                n = 0
                for u in urls:
                    if u not in vistas:
                        w.writerow([u, dia.isoformat(), region_desde_url(u)])
                        vistas.add(u)
                        n += 1
                reg.write(dia.isoformat() + "\n")
                f.flush(); reg.flush()
                print(f"{dia}  enlaces nuevos: {n:3d}  total: {len(vistas)}")
                time.sleep(a.pausa)
            dia -= timedelta(days=1)

    print(f"Listo. {len(vistas)} enlaces en {SALIDA}")


if __name__ == "__main__":
    main()
