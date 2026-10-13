"""
PASO 4 - Extraer entidades de todo el corpus.

Lee corpus_final.csv, aplica el extractor a cada noticia y genera dos tablas:
  - noticias.csv  : una fila por noticia, con su categoría (Policial / Otros)
  - entidades.csv : una fila por entidad encontrada (id_noticia, entidad, tipo)

Uso:
    python paso4_extraccion.py
"""

import pandas as pd
from extractor import extraer_entidades, categoria

corpus = pd.read_csv("corpus_final.csv", encoding="utf-8")
corpus["categoria"] = corpus["texto"].apply(categoria)

filas = []
for i, noticia in corpus.iterrows():
    texto = f"{noticia['titulo']}. {noticia['texto']}"
    for e in extraer_entidades(texto):
        filas.append({"id_noticia": noticia["id"], "entidad": e["entidad"], "tipo": e["tipo"]})
    if i % 500 == 0:
        print(f"Noticias procesadas: {i}")

entidades = pd.DataFrame(filas).drop_duplicates()   # una mención por noticia
corpus.drop(columns=["texto"]).to_csv("noticias.csv", index=False, encoding="utf-8")
entidades.to_csv("entidades.csv", index=False, encoding="utf-8")

print(f"Listo. {len(corpus)} noticias y {len(entidades)} entidades.")
print(entidades["tipo"].value_counts().to_string())
