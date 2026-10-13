"""
extractor.py - Modelo de extracción de entidades.

Combina tres piezas:
  1. spaCy (modelo es_core_news_md): reconoce PERSONAS, ORGANIZACIONES y LUGARES.
  2. Reglas propias (EntityRuler): listas de distritos e instituciones de La Libertad
     que el modelo general no siempre reconoce.
  3. Expresiones regulares: reconocen FECHAS ("10 de octubre de 2026", "12/10/2026", "este lunes").

Uso:
    from extractor import extraer_entidades
    extraer_entidades("La PNP intervino en El Porvenir el 10 de octubre.")
"""

import re
import spacy

# ---------------------------------------------------------------------------
# 1. Listas propias de La Libertad (diccionarios o "gazetteers")
# ---------------------------------------------------------------------------
DISTRITOS = [
    # Trujillo
    "Trujillo", "El Porvenir", "Florencia de Mora", "Huanchaco", "La Esperanza", "Laredo",
    "Moche", "Poroto", "Salaverry", "Simbal", "Víctor Larco", "Víctor Larco Herrera", "Alto Trujillo",
    # Ascope
    "Ascope", "Chicama", "Chocope", "Magdalena de Cao", "Paiján", "Rázuri", "Santiago de Cao", "Casa Grande",
    # Bolívar
    "Bolívar", "Bambamarca", "Condormarca", "Longotea", "Uchumarca", "Ucuncha",
    # Chepén
    "Chepén", "Pacanga", "Pueblo Nuevo",
    # Julcán
    "Julcán", "Calamarca", "Carabamba", "Huaso",
    # Otuzco
    "Otuzco", "Agallpampa", "Charat", "Huaranchal", "La Cuesta", "Mache", "Paranday", "Salpo",
    "Sinsicap", "Usquil",
    # Pacasmayo
    "San Pedro de Lloc", "Guadalupe", "Jequetepeque", "Pacasmayo", "San José",
    # Pataz
    "Tayabamba", "Buldibuyo", "Chillia", "Huancaspata", "Huaylillas", "Huayo", "Ongón", "Parcoy",
    "Pataz", "Pías", "Santiago de Challas", "Taurija", "Urpay",
    # Sánchez Carrión
    "Huamachuco", "Chugay", "Cochorco", "Curgos", "Marcabal", "Sanagorán", "Sarín", "Sartimbamba",
    # Santiago de Chuco
    "Santiago de Chuco", "Angasmarca", "Cachicadán", "Mollebamba", "Mollepata", "Quiruvilca",
    "Santa Cruz de Chuca", "Sitabamba",
    # Gran Chimú
    "Cascas", "Lucma", "Marmot", "Sayapullo",
    # Virú
    "Virú", "Chao", "Guadalupito",
]

INSTITUCIONES = [
    "PNP", "Policía Nacional", "Policía Nacional del Perú", "Ministerio Público", "Fiscalía",
    "Poder Judicial", "Corte Superior de Justicia de La Libertad", "Gobierno Regional de La Libertad",
    "Municipalidad Provincial de Trujillo", "Gerencia Regional de Salud", "Geresa", "INPE",
    "Serenazgo", "Defensoría del Pueblo", "Sedalib", "Hidrandina", "Senamhi", "Indeci", "Sunat",
    "EsSalud", "Minsa", "Ministerio de Salud", "Depincri", "Dirincri", "Ejército del Perú",
    "Contraloría", "Contraloría General de la República", "JNE", "ONPE", "Sutran", "Sucamec",
    "Universidad Nacional de Trujillo", "UNT", "UPAO", "Universidad Privada Antenor Orrego",
    "Universidad César Vallejo", "UCV",
]

# Nombres distintos que se refieren a la misma institución -> se unifican
SINONIMOS = {
    "Policía Nacional": "PNP",
    "Policía Nacional del Perú": "PNP",
    "Policía": "PNP",
    "Fiscalía": "Ministerio Público",
    "Ministerio de Salud": "Minsa",
    "Geresa": "Gerencia Regional de Salud",
    "Víctor Larco Herrera": "Víctor Larco",
    "Universidad Privada Antenor Orrego": "UPAO",
    "Universidad Nacional de Trujillo": "UNT",
    "Universidad César Vallejo": "UCV",
    "Contraloría General de la República": "Contraloría",
}

# ---------------------------------------------------------------------------
# 2. Expresión regular para fechas
# ---------------------------------------------------------------------------
MESES = "enero|febrero|marzo|abril|mayo|junio|julio|agosto|setiembre|septiembre|octubre|noviembre|diciembre"
DIAS = "lunes|martes|miércoles|jueves|viernes|sábado|domingo"
PATRON_FECHA = re.compile(
    rf"\b(\d{{1,2}} de (?:{MESES})(?: (?:de|del) \d{{4}})?"   # 10 de octubre (de 2026)
    rf"|\d{{1,2}}/\d{{1,2}}/\d{{2,4}}"                         # 10/10/2026
    rf"|(?:este|el pasado|el próximo) (?:{DIAS}))\b",          # este lunes
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# 3. Carga del modelo (una sola vez)
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
    """Devuelve una lista de diccionarios: {entidad, tipo, inicio, fin}."""
    doc = nlp(texto)
    resultado = []
    for ent in doc.ents:
        if ent.label_ not in TIPOS:          # se descarta MISC
            continue
        if ent.label_ == "PER" and ent[0].is_stop:   # evita errores como "Según la"
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
# 4. Categoría de la noticia (regla simple por palabras clave)
# ---------------------------------------------------------------------------
PALABRAS_POLICIALES = [
    "policía", "pnp", "detenido", "detenida", "capturan", "asesinato", "asesinado", "sicario",
    "extorsión", "extorsionadores", "robo", "delincuentes", "balacera", "disparos", "homicidio",
    "crimen", "fiscalía", "prisión preventiva", "explosivo", "dinamita", "banda criminal",
]


def categoria(texto):
    t = texto.lower()
    coincidencias = sum(1 for p in PALABRAS_POLICIALES if p in t)
    return "Policial" if coincidencias >= 2 else "Otros"
