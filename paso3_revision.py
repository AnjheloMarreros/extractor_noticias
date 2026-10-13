"""
PASO 3 - Revisar y limpiar el corpus.

Elimina duplicados y noticias vacías de corpus_noticias.csv, guarda la versión final
en corpus_final.csv y muestra las cifras para documentar el corpus.

Uso:
    pip install pandas
    python paso3_revision.py
"""

import pandas as pd

df = pd.read_csv("corpus_noticias.csv", encoding="utf-8")
inicial = len(df)

df = df.drop_duplicates(subset="url")
df = df.drop_duplicates(subset="texto")
df = df[df["texto"].notna() & (df["n_palabras"] >= 40)]
df["region"] = df["region"].fillna("")

df.to_csv("corpus_final.csv", index=False, encoding="utf-8")

print("Noticias recolectadas:       ", inicial)
print("Noticias tras la limpieza:   ", len(df))
print("Noticias de La Libertad:     ", (df["region"] == "la-libertad").sum())
print("Periodo cubierto:            ", df["fecha_publicacion"].min(), "a", df["fecha_publicacion"].max())
print("Promedio de palabras:        ", round(df["n_palabras"].mean(), 1))
print("Total de palabras:           ", int(df["n_palabras"].sum()))
print("\nNoticias por región (top 10):")
print(df["region"].replace("", "nacional / sin región").value_counts().head(10).to_string())
print("\nNoticias por año:")
print(df["fecha_publicacion"].str[:4].value_counts().sort_index().to_string())
