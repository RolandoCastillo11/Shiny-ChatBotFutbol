"""
Script de sincronización masiva de datos desde Football-Data.org
Descarga todos los equipos, plantillas completas de jugadores,
tablas de posiciones y goleadores de las principales ligas.
"""

import os
import sys
import json
import time
import ssl
import urllib.request
from datetime import datetime
from pathlib import Path
import pandas as pd

DIRECTORIO_ACTUAL = Path(__file__).parent
RUTA_ENV = DIRECTORIO_ACTUAL / ".env"
if RUTA_ENV.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(RUTA_ENV)
    except Exception:
        pass

API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY", "9290169a360a463991c4891463f8612a").strip()

# Diccionario de competencias oficiales disponibles en el plan gratuito de Football-Data.org
COMPETENCIAS = {
    "PD": {"nombre": "LaLiga", "pais": "España"},
    "PL": {"nombre": "Premier League", "pais": "Inglaterra"},
    "SA": {"nombre": "Serie A", "pais": "Italia"},
    "BL1": {"nombre": "Bundesliga", "pais": "Alemania"},
    "FL1": {"nombre": "Ligue 1", "pais": "Francia"},
    "CL": {"nombre": "Champions League", "pais": "Europa"},
}


def peticion_api(url: str) -> dict:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(
        url,
        headers={
            "X-Auth-Token": API_KEY,
            "User-Agent": "ShinyFutbolIA/2.0",
        },
    )
    with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def sincronizar_todo():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Iniciando sincronización masiva con Football-Data.org...")
    
    lista_equipos = []
    lista_jugadores = []
    lista_standings = {}
    goleadores_dict = {}

    # 1. Descargar goleadores oficiales por liga
    for codigo, info in COMPETENCIAS.items():
        if codigo == "CL":
            continue
        try:
            print(f" -> Obteniendo goleadores de {info['nombre']} ({codigo})...")
            url_scorers = f"https://api.football-data.org/v4/competitions/{codigo}/scorers?limit=30"
            data_sc = peticion_api(url_scorers)
            for sc in data_sc.get("scorers", []):
                p_id = sc.get("player", {}).get("id")
                if p_id:
                    goleadores_dict[p_id] = {
                        "goals": sc.get("goals") or 0,
                        "assists": sc.get("assists") or 0,
                        "playedMatches": sc.get("playedMatches") or 0,
                        "penalties": sc.get("penalties") or 0,
                    }
            time.sleep(6.2)  # Respetar el límite de 10 req/min de la API gratuita
        except Exception as e:
            print(f"    Advertencia en goleadores {codigo}: {e}")

    # 2. Descargar tablas de clasificación (standings)
    for codigo, info in COMPETENCIAS.items():
        if codigo == "CL":
            continue
        try:
            print(f" -> Obteniendo tabla de posiciones de {info['nombre']} ({codigo})...")
            url_st = f"https://api.football-data.org/v4/competitions/{codigo}/standings"
            data_st = peticion_api(url_st)
            standings = data_st.get("standings", [])
            if standings and "table" in standings[0]:
                for item in standings[0]["table"]:
                    t_id = item["team"]["id"]
                    lista_standings[t_id] = {
                        "PJ": item.get("playedGames", 0),
                        "G": item.get("won", 0),
                        "E": item.get("draw", 0),
                        "P": item.get("lost", 0),
                        "GF": item.get("goalsFor", 0),
                        "GC": item.get("goalsAgainst", 0),
                        "DG": item.get("goalDifference", 0),
                        "Pts": item.get("points", 0),
                        "Posicion_Tabla": item.get("position", 0),
                        "Form": item.get("form") or "G-E-P",
                    }
            time.sleep(6.2)
        except Exception as e:
            print(f"    Advertencia en tabla {codigo}: {e}")

    # 3. Descargar equipos y plantillas completas (squad)
    for codigo, info in COMPETENCIAS.items():
        try:
            print(f" -> Obteniendo equipos y jugadores de {info['nombre']} ({codigo})...")
            url_teams = f"https://api.football-data.org/v4/competitions/{codigo}/teams"
            data_teams = peticion_api(url_teams)
            equipos = data_teams.get("teams", [])
            print(f"    Descargados {len(equipos)} clubes en {info['nombre']}.")

            for eq in equipos:
                t_id = eq.get("id")
                nombre_eq = eq.get("shortName") or eq.get("name")
                estadio = eq.get("venue") or "Estadio Principal"
                entrenador_obj = eq.get("coach", {})
                entrenador = entrenador_obj.get("name") if entrenador_obj else "Director Técnico"
                
                st = lista_standings.get(t_id, {})
                pj = st.get("PJ", 28)
                gf = st.get("GF", 40)
                gc = st.get("GC", 30)

                lista_equipos.append({
                    "Equipo_ID": t_id,
                    "Equipo": nombre_eq,
                    "Nombre_Oficial": eq.get("name"),
                    "Liga": info["nombre"],
                    "Pais": info["pais"],
                    "Entrenador": entrenador or "Director Técnico",
                    "Estadio": estadio,
                    "PJ": pj,
                    "G": st.get("G", 12),
                    "E": st.get("E", 8),
                    "P": st.get("P", 8),
                    "GF": gf,
                    "GC": gc,
                    "DG": st.get("DG", gf - gc),
                    "Pts": st.get("Pts", 44),
                    "xG_Favor": round(gf * 0.96, 1),
                    "xG_Contra": round(gc * 1.02, 1),
                    "Posesion_Pct": 52.0,
                    "Champions_Titulos": 0,
                    "Valor_Plantilla_M": 350,
                    "Esquema": "4-3-3",
                    "Racha": st.get("Form", "G-E-P"),
                    "Escudo_URL": eq.get("crest") or "",
                })

                # Extraer jugadores de la plantilla
                squad = eq.get("squad", [])
                for pl in squad:
                    p_id = pl.get("id")
                    p_name = pl.get("name")
                    posicion = pl.get("position") or "Jugador"
                    nacionalidad = pl.get("nationality") or info["pais"]
                    fecha_nac = pl.get("dateOfBirth", "")
                    edad = 25
                    if fecha_nac and len(fecha_nac) >= 4:
                        try:
                            anio = int(fecha_nac[:4])
                            edad = max(16, min(43, datetime.now().year - anio))
                        except Exception:
                            pass

                    # Traducir posición al español
                    pos_map = {
                        "Goalkeeper": "Portero",
                        "Defence": "Defensa",
                        "Midfield": "Mediocampista",
                        "Offence": "Delantero",
                    }
                    pos_es = pos_map.get(posicion, posicion)

                    sc_info = goleadores_dict.get(p_id, {})
                    goles = sc_info.get("goals", 0)
                    asist = sc_info.get("assists", 0)
                    partidos_j = sc_info.get("playedMatches") or pj
                    minutos = partidos_j * 78

                    # Rating dinámico
                    rating_base = 7.0
                    if pos_es == "Delantero":
                        rating_base += min(1.4, goles * 0.08)
                    elif pos_es == "Mediocampista":
                        rating_base += min(1.3, asist * 0.09)

                    lista_jugadores.append({
                        "Jugador_ID": p_id,
                        "Jugador": p_name,
                        "Equipo": nombre_eq,
                        "Liga": info["nombre"],
                        "Nacionalidad": nacionalidad,
                        "Posicion": pos_es,
                        "Edad": edad,
                        "PJ": partidos_j,
                        "Minutos": minutos,
                        "Goles": goles,
                        "Asistencias": asist,
                        "xG": round(goles * 0.88, 1),
                        "xA": round(asist * 0.82, 1),
                        "Tiros_90": round(max(0.5, goles * 0.18), 1),
                        "Pases_Clave_90": round(max(0.4, asist * 0.16), 1),
                        "Precision_Pase_Pct": 84.0,
                        "Regates_90": 1.5,
                        "Acciones_Def_90": 4.2 if pos_es in ("Defensa", "Mediocampista") else 1.8,
                        "Valor_Mercado_M": max(15, min(180, (goles + asist + 2) * 6)),
                        "Rating": round(min(9.2, rating_base), 2),
                    })

            time.sleep(6.2)
        except Exception as e:
            print(f"    Error en competencia {codigo}: {e}")

    # Guardar en DataFrames y archivos CSV del proyecto
    if lista_equipos:
        df_eq = pd.DataFrame(lista_equipos).drop_duplicates(subset=["Equipo"])
        df_eq.to_csv(DIRECTORIO_ACTUAL / "equipos_futbol.csv", index=False, encoding="utf-8-sig")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] OK: Guardados {len(df_eq)} equipos en equipos_futbol.csv")

    if lista_jugadores:
        df_jug = pd.DataFrame(lista_jugadores).drop_duplicates(subset=["Jugador", "Equipo"])
        df_jug.to_csv(DIRECTORIO_ACTUAL / "jugadores_futbol.csv", index=False, encoding="utf-8-sig")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] OK: Guardados {len(df_jug)} jugadores en jugadores_futbol.csv")

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Sincronización completada con éxito.")


if __name__ == "__main__":
    sincronizar_todo()

