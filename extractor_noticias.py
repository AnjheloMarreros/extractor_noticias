"""
Extras_Noticias.py - Módulo principal del extractor de noticias.

Este módulo proporciona funciones unificadas para:
1. Analizar texto pegado
2. Cargar noticia desde URL
3. Cargar noticia desde archivo PDF

En todos los casos, devuelve las entidades identificadas.
"""

import re
import spacy
from pathlib import Path
from extractor import DISTRITOS, INSTITUCIONES, SINONIMOS, categoria

# ---------------------------------------------------------------------------
# 2. Expresión regular para fechas
# ---------------------------------------------------------------------------
MESES = "enero|febrero|marzo|abril|mayo|junio|julio|agosto|setiembre|septiembre|octubre|noviembre|diciembre"
DIAS = "lunes|martes|miércoles|jueves|viernes|sábado|domingo"
PATRON_FECHA = re.compile(
    rf"\b(\d{{1,2}} de (?:{MESES})(?: (?:de|del) \d{{4}})?"
    rf"|\d{{1,2}}/\d{{1,2}}/\d{{2,4}}"
    rf"|(?:este|el pasado|el próximo) (?:{DIAS}))\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# 3. Carga del modelo
# ---------------------------------------------------------------------------
def cargar_modelo():
    nlp = spacy.load("es_core_news_md")
    ruler = nlp.add_pipe("entity_ruler", before="ner", config={"overwrite_ents": True})
    patrones = [{"label": "LOC", "pattern": d} for d in DISTRITOS]
    patrones += [{"label": "ORG", "pattern": i} for i in INSTITUCIONES]
    ruler.add_patterns(patrones)
    return nlp

nlp = cargar_modelo()

TIPOS = {"PER": "PERSONA", "ORG": "ORGANIZACION", "LOC": "LUGAR"}


def extraer_entidades(texto):
    doc = nlp(texto)
    resultado = []
    for ent in doc.ents:
        if ent.label_ not in TIPOS:
            continue
        if ent.label_ == "PER" and ent[0].is_stop:
            continue
        nombre = ent.text.strip(" .,;:\"'()")
        if len(nombre) < 2:
            continue
        resultado.append({
            "entidad": SINONIMOS.get(nombre, nombre),
            "tipo": TIPOS[ent.label_],
            "inicio": ent.start_char,
            "fin": ent.end_char,
        })
    for m in PATRON_FECHA.finditer(texto):
        resultado.append({"entidad": m.group(0), "tipo": "FECHA",
                          "inicio": m.start(), "fin": m.end()})
    return sorted(resultado, key=lambda e: e["inicio"])


# ---------------------------------------------------------------------------
# 5. Funciones públicas
# ---------------------------------------------------------------------------

def analizar_texto(texto):
    entidades = extraer_entidades(texto)
    return {
        "texto": texto,
        "entidades": entidades,
        "categoria": categoria(texto),
        "tipo_fuente": "texto_pegado",
    }


def cargar_desde_url(url):
    from carga_noticias import cargar_desde_url as _cargar_url
    noticia = _cargar_url(url)
    if noticia:
        entidades = extraer_entidades(noticia["texto"])
        return {
            "texto": noticia["texto"],
            "entidades": entidades,
            "titulo": noticia["titulo"],
            "url": noticia["url"],
            "categoria": categoria(noticia["texto"]),
            "tipo_fuente": "url",
        }
    return None


def cargar_desde_pdf(ruta_archivo):
    from carga_noticias import cargar_desde_pdf as _cargar_pdf
    noticias = _cargar_pdf(ruta_archivo)
    if noticias:
        noticia = noticias[0]
        entidades = extraer_entidades(noticia["texto"])
        return {
            "texto": noticia["texto"],
            "entidades": entidades,
            "titulo": noticia["titulo"],
            "archivo": noticia["id"],
            "categoria": categoria(noticia["texto"]),
            "tipo_fuente": "pdf",
        }
    return None


def procesar_fuente(origen, tipo=None):
    if tipo == "url" or (tipo is None and re.match(r"^https?://", origen)):
        return cargar_desde_url(origen)
    elif tipo == "pdf" or (tipo is None and Path(origen).suffix.lower() == ".pdf"):
        return cargar_desde_pdf(origen)
    else:
        return analizar_texto(origen)
