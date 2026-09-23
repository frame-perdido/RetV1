from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
from collections import Counter

app = FastAPI(title="RetroTVE API", version="1.0")

# CORS — permite peticiones desde tu web (y cualquier origen)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).parent / "data"

SERIES, PELICULAS = {}, {}
for f in (DATA_DIR / "series").glob("*.json"):
    d = json.load(open(f))
    if d.get("titulo"):
        SERIES[d["url"].rstrip("/").split("/")[-1]] = d
for f in (DATA_DIR / "peliculas").glob("*.json"):
    d = json.load(open(f))
    if d.get("titulo"):
        PELICULAS[d["url"].rstrip("/").split("/")[-1]] = d

def _s(s): return {k: s.get(k) for k in ["titulo","titulo_original","generos","imagen_hd","primera_emision","ultima_emision","total_temporadas","total_episodios","url"]}
def _p(p): return {k: p.get(k) for k in ["titulo","titulo_original","generos","imagen_hd","fecha_lanzamiento","url","urls_directas"]}

@app.get("/")
def root(): return {"name":"RetroTVE API","series":len(SERIES),"peliculas":len(PELICULAS)}

@app.get("/series")
def listar_series(genero: str = None, anio: int = None, limit: int = 50, offset: int = 0):
    items = list(SERIES.values())
    if genero: items = [s for s in items if any(genero.lower() in g.lower() for g in s.get("generos",[]))]
    if anio: items = [s for s in items if str(anio) in str(s.get("primera_emision",""))]
    items.sort(key=lambda x: x.get("titulo") or "")
    return {"total":len(items),"resultados":[_s(s) for s in items[offset:offset+limit]]}

@app.get("/series/{slug}")
def detalle_serie(slug: str):
    if slug not in SERIES: raise HTTPException(404,"Serie no encontrada")
    return SERIES[slug]

@app.get("/series/{slug}/temporadas")
def temporadas_serie(slug: str):
    if slug not in SERIES: raise HTTPException(404,"Serie no encontrada")
    return {"titulo":SERIES[slug]["titulo"],"temporadas":SERIES[slug].get("temporadas",[])}

@app.get("/series/{slug}/temporadas/{nt}/episodios")
def eps(slug: str, nt: int):
    if slug not in SERIES: raise HTTPException(404,"Serie no encontrada")
    for t in SERIES[slug].get("temporadas",[]):
        if t["numero"]==nt: return {"temporada":nt,"episodios":t["episodios"]}
    raise HTTPException(404,"Temporada no encontrada")

@app.get("/series/{slug}/temporadas/{nt}/episodios/{ne}")
def ep(slug: str, nt: int, ne: int):
    if slug not in SERIES: raise HTTPException(404,"Serie no encontrada")
    for t in SERIES[slug].get("temporadas",[]):
        if t["numero"]==nt:
            for e in t["episodios"]:
                if e["episodio"]==ne: return e
    raise HTTPException(404,"Episodio no encontrado")

@app.get("/peliculas")
def listar_peliculas(genero: str = None, limit: int = 50, offset: int = 0):
    items = list(PELICULAS.values())
    if genero: items = [p for p in items if any(genero.lower() in g.lower() for g in p.get("generos",[]))]
    items.sort(key=lambda x: x.get("titulo") or "")
    return {"total":len(items),"resultados":[_p(p) for p in items[offset:offset+limit]]}

@app.get("/peliculas/{slug}")
def detalle_pelicula(slug: str):
    if slug not in PELICULAS: raise HTTPException(404,"Película no encontrada")
    return PELICULAS[slug]

@app.get("/buscar")
def buscar(q: str = Query(..., min_length=2)):
    ql = q.lower()
    rs = [_s(s) for s in SERIES.values() if ql in (s.get("titulo") or "").lower()]
    rp = [_p(p) for p in PELICULAS.values() if ql in (p.get("titulo") or "").lower()]
    return {"query":q,"series":rs,"peliculas":rp}

@app.get("/generos")
def generos():
    c = Counter()
    for x in list(SERIES.values()) + list(PELICULAS.values()):
        for g in x.get("generos",[]): c[g] += 1
    return {"generos":[{"nombre":g,"cantidad":n} for g,n in c.most_common()]}

@app.get("/stats")
def stats():
    return {"total_series":len(SERIES),"total_peliculas":len(PELICULAS),"total_episodios":sum(s.get("total_episodios",0) for s in SERIES.values())}
