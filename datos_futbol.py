"""
Módulo de Datos y Noticias de Fútbol Europeo para el Chatbot IA en Shiny.
Contiene datasets completos de Equipos, Jugadores, Partidos y Noticias,
además de un conector RSS en vivo con respaldo local automático.
"""

from pathlib import Path
from datetime import datetime, timedelta
import json
import os
import ssl
import urllib.request
import xml.etree.ElementTree as ET
import math
import unicodedata
import pandas as pd

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except Exception:
    pass

DIRECTORIO_ACTUAL = Path(__file__).parent
RUTA_EQUIPOS_CSV = DIRECTORIO_ACTUAL / "equipos_futbol.csv"
RUTA_JUGADORES_CSV = DIRECTORIO_ACTUAL / "jugadores_futbol.csv"
RUTA_NOTICIAS_CSV = DIRECTORIO_ACTUAL / "noticias_futbol.csv"

# -----------------------------------------------------------------------------
# 1. Base de Datos de Equipos de las 5 Grandes Ligas + Champions League
# -----------------------------------------------------------------------------
DATOS_EQUIPOS_RAW = [
    # LaLiga EA Sports (España)
    {"Equipo": "Real Madrid", "Liga": "LaLiga", "Pais": "España", "Entrenador": "Carlo Ancelotti", "Estadio": "Santiago Bernabéu", "PJ": 28, "G": 20, "E": 5, "P": 3, "GF": 64, "GC": 24, "Pts": 65, "xG_Favor": 61.4, "xG_Contra": 26.8, "Posesion_Pct": 60.5, "Champions_Titulos": 15, "Valor_Plantilla_M": 1360, "Esquema": "4-3-3", "Racha": "G-G-E-G-G"},
    {"Equipo": "FC Barcelona", "Liga": "LaLiga", "Pais": "España", "Entrenador": "Hansi Flick", "Estadio": "Spotify Camp Nou / Montjuïc", "PJ": 28, "G": 21, "E": 3, "P": 4, "GF": 76, "GC": 28, "Pts": 66, "xG_Favor": 71.2, "xG_Contra": 29.1, "Posesion_Pct": 65.2, "Champions_Titulos": 5, "Valor_Plantilla_M": 1020, "Esquema": "4-2-3-1", "Racha": "G-G-G-G-E"},
    {"Equipo": "Atlético de Madrid", "Liga": "LaLiga", "Pais": "España", "Entrenador": "Diego Simeone", "Estadio": "Riyadh Air Metropolitano", "PJ": 28, "G": 17, "E": 7, "P": 4, "GF": 51, "GC": 22, "Pts": 58, "xG_Favor": 47.8, "xG_Contra": 23.5, "Posesion_Pct": 51.4, "Champions_Titulos": 0, "Valor_Plantilla_M": 530, "Esquema": "3-5-2", "Racha": "G-E-G-P-G"},
    {"Equipo": "Athletic Club", "Liga": "LaLiga", "Pais": "España", "Entrenador": "Ernesto Valverde", "Estadio": "San Mamés", "PJ": 28, "G": 14, "E": 9, "P": 5, "GF": 46, "GC": 26, "Pts": 51, "xG_Favor": 43.5, "xG_Contra": 27.0, "Posesion_Pct": 50.8, "Champions_Titulos": 0, "Valor_Plantilla_M": 350, "Esquema": "4-2-3-1", "Racha": "E-G-G-E-G"},
    {"Equipo": "Villarreal CF", "Liga": "LaLiga", "Pais": "España", "Entrenador": "Marcelino García", "Estadio": "Estadio de la Cerámica", "PJ": 28, "G": 13, "E": 8, "P": 7, "GF": 49, "GC": 38, "Pts": 47, "xG_Favor": 46.2, "xG_Contra": 36.4, "Posesion_Pct": 49.5, "Champions_Titulos": 0, "Valor_Plantilla_M": 235, "Esquema": "4-4-2", "Racha": "G-P-G-E-G"},
    {"Equipo": "Real Sociedad", "Liga": "LaLiga", "Pais": "España", "Entrenador": "Imanol Alguacil", "Estadio": "Reale Arena", "PJ": 28, "G": 12, "E": 6, "P": 10, "GF": 34, "GC": 30, "Pts": 42, "xG_Favor": 36.1, "xG_Contra": 29.8, "Posesion_Pct": 56.1, "Champions_Titulos": 0, "Valor_Plantilla_M": 410, "Esquema": "4-3-3", "Racha": "P-G-E-G-P"},

    # Premier League (Inglaterra)
    {"Equipo": "Liverpool", "Liga": "Premier League", "Pais": "Inglaterra", "Entrenador": "Arne Slot", "Estadio": "Anfield", "PJ": 29, "G": 21, "E": 6, "P": 2, "GF": 69, "GC": 26, "Pts": 69, "xG_Favor": 66.8, "xG_Contra": 27.4, "Posesion_Pct": 58.9, "Champions_Titulos": 6, "Valor_Plantilla_M": 970, "Esquema": "4-2-3-1", "Racha": "G-G-E-G-G"},
    {"Equipo": "Arsenal", "Liga": "Premier League", "Pais": "Inglaterra", "Entrenador": "Mikel Arteta", "Estadio": "Emirates Stadium", "PJ": 29, "G": 18, "E": 7, "P": 4, "GF": 58, "GC": 24, "Pts": 61, "xG_Favor": 55.4, "xG_Contra": 22.9, "Posesion_Pct": 59.8, "Champions_Titulos": 0, "Valor_Plantilla_M": 1150, "Esquema": "4-3-3", "Racha": "G-E-G-G-E"},
    {"Equipo": "Manchester City", "Liga": "Premier League", "Pais": "Inglaterra", "Entrenador": "Pep Guardiola", "Estadio": "Etihad Stadium", "PJ": 29, "G": 17, "E": 6, "P": 6, "GF": 61, "GC": 35, "Pts": 57, "xG_Favor": 59.2, "xG_Contra": 33.1, "Posesion_Pct": 66.4, "Champions_Titulos": 1, "Valor_Plantilla_M": 1260, "Esquema": "3-2-4-1", "Racha": "G-P-G-E-G"},
    {"Equipo": "Chelsea", "Liga": "Premier League", "Pais": "Inglaterra", "Entrenador": "Enzo Maresca", "Estadio": "Stamford Bridge", "PJ": 29, "G": 15, "E": 7, "P": 7, "GF": 55, "GC": 36, "Pts": 52, "xG_Favor": 54.0, "xG_Contra": 37.5, "Posesion_Pct": 57.6, "Champions_Titulos": 2, "Valor_Plantilla_M": 1010, "Esquema": "4-2-3-1", "Racha": "G-G-P-E-G"},
    {"Equipo": "Newcastle United", "Liga": "Premier League", "Pais": "Inglaterra", "Entrenador": "Eddie Howe", "Estadio": "St. James' Park", "PJ": 29, "G": 15, "E": 5, "P": 9, "GF": 50, "GC": 37, "Pts": 50, "xG_Favor": 49.1, "xG_Contra": 36.8, "Posesion_Pct": 51.2, "Champions_Titulos": 0, "Valor_Plantilla_M": 660, "Esquema": "4-3-3", "Racha": "G-P-G-G-P"},
    {"Equipo": "Aston Villa", "Liga": "Premier League", "Pais": "Inglaterra", "Entrenador": "Unai Emery", "Estadio": "Villa Park", "PJ": 29, "G": 14, "E": 6, "P": 9, "GF": 45, "GC": 41, "Pts": 48, "xG_Favor": 44.3, "xG_Contra": 39.2, "Posesion_Pct": 50.9, "Champions_Titulos": 1, "Valor_Plantilla_M": 620, "Esquema": "4-2-3-1", "Racha": "E-G-P-G-G"},
    {"Equipo": "Manchester United", "Liga": "Premier League", "Pais": "Inglaterra", "Entrenador": "Rúben Amorim", "Estadio": "Old Trafford", "PJ": 29, "G": 11, "E": 7, "P": 11, "GF": 39, "GC": 40, "Pts": 40, "xG_Favor": 41.5, "xG_Contra": 43.0, "Posesion_Pct": 52.5, "Champions_Titulos": 3, "Valor_Plantilla_M": 790, "Esquema": "3-4-2-1", "Racha": "E-P-G-E-G"},

    # Serie A (Italia)
    {"Equipo": "Inter de Milán", "Liga": "Serie A", "Pais": "Italia", "Entrenador": "Simone Inzaghi", "Estadio": "Giuseppe Meazza (San Siro)", "PJ": 28, "G": 19, "E": 6, "P": 3, "GF": 65, "GC": 25, "Pts": 63, "xG_Favor": 60.8, "xG_Contra": 24.6, "Posesion_Pct": 57.4, "Champions_Titulos": 3, "Valor_Plantilla_M": 680, "Esquema": "3-5-2", "Racha": "G-G-E-G-G"},
    {"Equipo": "Napoli", "Liga": "Serie A", "Pais": "Italia", "Entrenador": "Antonio Conte", "Estadio": "Diego Armando Maradona", "PJ": 28, "G": 18, "E": 6, "P": 4, "GF": 47, "GC": 22, "Pts": 60, "xG_Favor": 45.9, "xG_Contra": 23.8, "Posesion_Pct": 53.8, "Champions_Titulos": 0, "Valor_Plantilla_M": 440, "Esquema": "4-3-3", "Racha": "G-E-E-G-G"},
    {"Equipo": "Atalanta", "Liga": "Serie A", "Pais": "Italia", "Entrenador": "Gian Piero Gasperini", "Estadio": "Gewiss Stadium", "PJ": 28, "G": 17, "E": 6, "P": 5, "GF": 61, "GC": 27, "Pts": 57, "xG_Favor": 56.2, "xG_Contra": 28.4, "Posesion_Pct": 54.1, "Champions_Titulos": 0, "Valor_Plantilla_M": 460, "Esquema": "3-4-1-2", "Racha": "G-G-P-G-E"},
    {"Equipo": "Juventus", "Liga": "Serie A", "Pais": "Italia", "Entrenador": "Thiago Motta", "Estadio": "Allianz Stadium", "PJ": 28, "G": 13, "E": 12, "P": 3, "GF": 44, "GC": 24, "Pts": 51, "xG_Favor": 42.1, "xG_Contra": 23.9, "Posesion_Pct": 58.2, "Champions_Titulos": 2, "Valor_Plantilla_M": 590, "Esquema": "4-2-3-1", "Racha": "G-G-G-P-E"},
    {"Equipo": "AC Milan", "Liga": "Serie A", "Pais": "Italia", "Entrenador": "Sérgio Conceição", "Estadio": "San Siro", "PJ": 28, "G": 13, "E": 8, "P": 7, "GF": 46, "GC": 33, "Pts": 47, "xG_Favor": 47.4, "xG_Contra": 32.5, "Posesion_Pct": 55.0, "Champions_Titulos": 7, "Valor_Plantilla_M": 560, "Esquema": "4-2-3-1", "Racha": "P-G-E-P-G"},

    # Bundesliga (Alemania)
    {"Equipo": "Bayern Múnich", "Liga": "Bundesliga", "Pais": "Alemania", "Entrenador": "Vincent Kompany", "Estadio": "Allianz Arena", "PJ": 26, "G": 20, "E": 4, "P": 2, "GF": 75, "GC": 23, "Pts": 64, "xG_Favor": 68.9, "xG_Contra": 21.5, "Posesion_Pct": 67.8, "Champions_Titulos": 6, "Valor_Plantilla_M": 940, "Esquema": "4-2-3-1", "Racha": "G-G-E-G-G"},
    {"Equipo": "Bayer Leverkusen", "Liga": "Bundesliga", "Pais": "Alemania", "Entrenador": "Xabi Alonso", "Estadio": "BayArena", "PJ": 26, "G": 17, "E": 7, "P": 2, "GF": 59, "GC": 30, "Pts": 58, "xG_Favor": 54.6, "xG_Contra": 28.2, "Posesion_Pct": 61.3, "Champions_Titulos": 0, "Valor_Plantilla_M": 640, "Esquema": "3-4-2-1", "Racha": "G-E-G-G-P"},
    {"Equipo": "Eintracht Frankfurt", "Liga": "Bundesliga", "Pais": "Alemania", "Entrenador": "Dino Toppmöller", "Estadio": "Deutsche Bank Park", "PJ": 26, "G": 13, "E": 6, "P": 7, "GF": 51, "GC": 38, "Pts": 45, "xG_Favor": 47.0, "xG_Contra": 37.9, "Posesion_Pct": 49.4, "Champions_Titulos": 0, "Valor_Plantilla_M": 290, "Esquema": "3-4-2-1", "Racha": "G-P-P-G-E"},
    {"Equipo": "RB Leipzig", "Liga": "Bundesliga", "Pais": "Alemania", "Entrenador": "Marco Rose", "Estadio": "Red Bull Arena", "PJ": 26, "G": 12, "E": 8, "P": 6, "GF": 44, "GC": 33, "Pts": 44, "xG_Favor": 43.2, "xG_Contra": 34.1, "Posesion_Pct": 53.7, "Champions_Titulos": 0, "Valor_Plantilla_M": 510, "Esquema": "4-4-2", "Racha": "E-G-E-P-G"},
    {"Equipo": "Borussia Dortmund", "Liga": "Bundesliga", "Pais": "Alemania", "Entrenador": "Niko Kovač", "Estadio": "Signal Iduna Park", "PJ": 26, "G": 11, "E": 6, "P": 9, "GF": 48, "GC": 41, "Pts": 39, "xG_Favor": 46.8, "xG_Contra": 38.5, "Posesion_Pct": 56.9, "Champions_Titulos": 1, "Valor_Plantilla_M": 470, "Esquema": "4-2-3-1", "Racha": "G-P-G-G-P"},

    # Ligue 1 (Francia)
    {"Equipo": "Paris Saint-Germain", "Liga": "Ligue 1", "Pais": "Francia", "Entrenador": "Luis Enrique", "Estadio": "Parc des Princes", "PJ": 26, "G": 21, "E": 5, "P": 0, "GF": 73, "GC": 24, "Pts": 68, "xG_Favor": 69.5, "xG_Contra": 23.2, "Posesion_Pct": 68.1, "Champions_Titulos": 0, "Valor_Plantilla_M": 890, "Esquema": "4-3-3", "Racha": "G-G-G-G-G"},
    {"Equipo": "Olympique de Marsella", "Liga": "Ligue 1", "Pais": "Francia", "Entrenador": "Roberto De Zerbi", "Estadio": "Stade Vélodrome", "PJ": 26, "G": 15, "E": 4, "P": 7, "GF": 53, "GC": 33, "Pts": 49, "xG_Favor": 49.0, "xG_Contra": 32.8, "Posesion_Pct": 59.4, "Champions_Titulos": 1, "Valor_Plantilla_M": 310, "Esquema": "4-2-3-1", "Racha": "G-P-G-P-G"},
    {"Equipo": "AS Monaco", "Liga": "Ligue 1", "Pais": "Francia", "Entrenador": "Adi Hütter", "Estadio": "Stade Louis-II", "PJ": 26, "G": 14, "E": 5, "P": 7, "GF": 51, "GC": 33, "Pts": 47, "xG_Favor": 50.4, "xG_Contra": 31.9, "Posesion_Pct": 54.6, "Champions_Titulos": 0, "Valor_Plantilla_M": 380, "Esquema": "4-2-3-1", "Racha": "G-E-G-P-G"},
    {"Equipo": "Lille OSC", "Liga": "Ligue 1", "Pais": "Francia", "Entrenador": "Bruno Genesio", "Estadio": "Stade Pierre-Mauroy", "PJ": 26, "G": 13, "E": 8, "P": 5, "GF": 42, "GC": 28, "Pts": 47, "xG_Favor": 41.2, "xG_Contra": 27.6, "Posesion_Pct": 55.2, "Champions_Titulos": 0, "Valor_Plantilla_M": 280, "Esquema": "4-2-3-1", "Racha": "G-P-G-E-G"},
]

# -----------------------------------------------------------------------------
# 2. Base de Datos de Jugadores Top de Europa (Estadísticas Avanzadas)
# -----------------------------------------------------------------------------
DATOS_JUGADORES_RAW = [
    # LaLiga
    {"Jugador": "Kylian Mbappé", "Equipo": "Real Madrid", "Liga": "LaLiga", "Nacionalidad": "Francia", "Posicion": "Delantero", "Edad": 26, "PJ": 38, "Minutos": 3210, "Goles": 31, "Asistencias": 6, "xG": 27.8, "xA": 5.9, "Tiros_90": 4.7, "Pases_Clave_90": 1.9, "Precision_Pase_Pct": 85.4, "Regates_90": 2.8, "Acciones_Def_90": 1.2, "Valor_Mercado_M": 180, "Rating": 8.24},
    {"Jugador": "Vinícius Júnior", "Equipo": "Real Madrid", "Liga": "LaLiga", "Nacionalidad": "Brasil", "Posicion": "Extremo", "Edad": 24, "PJ": 34, "Minutos": 2890, "Goles": 19, "Asistencias": 12, "xG": 16.5, "xA": 10.4, "Tiros_90": 3.4, "Pases_Clave_90": 2.4, "Precision_Pase_Pct": 81.2, "Regates_90": 3.9, "Acciones_Def_90": 1.8, "Valor_Mercado_M": 200, "Rating": 8.15},
    {"Jugador": "Jude Bellingham", "Equipo": "Real Madrid", "Liga": "LaLiga", "Nacionalidad": "Inglaterra", "Posicion": "Mediocampista", "Edad": 21, "PJ": 35, "Minutos": 3040, "Goles": 14, "Asistencias": 11, "xG": 12.1, "xA": 8.7, "Tiros_90": 2.3, "Pases_Clave_90": 2.1, "Precision_Pase_Pct": 88.9, "Regates_90": 2.2, "Acciones_Def_90": 5.4, "Valor_Mercado_M": 180, "Rating": 8.08},
    {"Jugador": "Federico Valverde", "Equipo": "Real Madrid", "Liga": "LaLiga", "Nacionalidad": "Uruguay", "Posicion": "Mediocampista", "Edad": 26, "PJ": 40, "Minutos": 3510, "Goles": 8, "Asistencias": 8, "xG": 5.4, "xA": 6.8, "Tiros_90": 1.8, "Pases_Clave_90": 1.7, "Precision_Pase_Pct": 90.6, "Regates_90": 1.3, "Acciones_Def_90": 6.2, "Valor_Mercado_M": 130, "Rating": 7.89},
    {"Jugador": "Thibaut Courtois", "Equipo": "Real Madrid", "Liga": "LaLiga", "Nacionalidad": "Bélgica", "Posicion": "Portero", "Edad": 32, "PJ": 32, "Minutos": 2880, "Goles": 0, "Asistencias": 0, "xG": 0.0, "xA": 0.1, "Tiros_90": 0.0, "Pases_Clave_90": 0.1, "Precision_Pase_Pct": 78.5, "Regates_90": 0.0, "Acciones_Def_90": 4.8, "Valor_Mercado_M": 28, "Rating": 7.62},
    {"Jugador": "Lamine Yamal", "Equipo": "FC Barcelona", "Liga": "LaLiga", "Nacionalidad": "España", "Posicion": "Extremo", "Edad": 17, "PJ": 37, "Minutos": 3080, "Goles": 14, "Asistencias": 18, "xG": 12.6, "xA": 15.2, "Tiros_90": 3.1, "Pases_Clave_90": 2.9, "Precision_Pase_Pct": 83.7, "Regates_90": 4.6, "Acciones_Def_90": 2.7, "Valor_Mercado_M": 180, "Rating": 8.31},
    {"Jugador": "Robert Lewandowski", "Equipo": "FC Barcelona", "Liga": "LaLiga", "Nacionalidad": "Polonia", "Posicion": "Delantero", "Edad": 36, "PJ": 38, "Minutos": 3120, "Goles": 34, "Asistencias": 4, "xG": 31.2, "xA": 3.8, "Tiros_90": 4.2, "Pases_Clave_90": 1.1, "Precision_Pase_Pct": 79.4, "Regates_90": 0.9, "Acciones_Def_90": 1.4, "Valor_Mercado_M": 15, "Rating": 8.12},
    {"Jugador": "Raphinha", "Equipo": "FC Barcelona", "Liga": "LaLiga", "Nacionalidad": "Brasil", "Posicion": "Extremo", "Edad": 28, "PJ": 39, "Minutos": 3250, "Goles": 27, "Asistencias": 17, "xG": 22.4, "xA": 14.9, "Tiros_90": 3.6, "Pases_Clave_90": 3.2, "Precision_Pase_Pct": 80.5, "Regates_90": 2.1, "Acciones_Def_90": 3.5, "Valor_Mercado_M": 80, "Rating": 8.38},
    {"Jugador": "Pedri", "Equipo": "FC Barcelona", "Liga": "LaLiga", "Nacionalidad": "España", "Posicion": "Mediocampista", "Edad": 22, "PJ": 38, "Minutos": 3090, "Goles": 6, "Asistencias": 9, "xG": 4.9, "xA": 8.8, "Tiros_90": 1.2, "Pases_Clave_90": 2.6, "Precision_Pase_Pct": 91.4, "Regates_90": 2.4, "Acciones_Def_90": 5.8, "Valor_Mercado_M": 100, "Rating": 8.05},
    {"Jugador": "Pau Cubarsí", "Equipo": "FC Barcelona", "Liga": "LaLiga", "Nacionalidad": "España", "Posicion": "Defensa", "Edad": 18, "PJ": 36, "Minutos": 3050, "Goles": 1, "Asistencias": 3, "xG": 1.1, "xA": 2.4, "Tiros_90": 0.4, "Pases_Clave_90": 0.6, "Precision_Pase_Pct": 93.2, "Regates_90": 0.5, "Acciones_Def_90": 7.9, "Valor_Mercado_M": 70, "Rating": 7.58},
    {"Jugador": "Julián Álvarez", "Equipo": "Atlético de Madrid", "Liga": "LaLiga", "Nacionalidad": "Argentina", "Posicion": "Delantero", "Edad": 25, "PJ": 39, "Minutos": 2780, "Goles": 22, "Asistencias": 6, "xG": 18.4, "xA": 5.5, "Tiros_90": 3.0, "Pases_Clave_90": 1.6, "Precision_Pase_Pct": 83.1, "Regates_90": 1.5, "Acciones_Def_90": 3.1, "Valor_Mercado_M": 80, "Rating": 7.84},
    {"Jugador": "Antoine Griezmann", "Equipo": "Atlético de Madrid", "Liga": "LaLiga", "Nacionalidad": "Francia", "Posicion": "Delantero", "Edad": 33, "PJ": 38, "Minutos": 2910, "Goles": 16, "Asistencias": 8, "xG": 13.8, "xA": 8.1, "Tiros_90": 2.5, "Pases_Clave_90": 2.3, "Precision_Pase_Pct": 84.8, "Regates_90": 1.2, "Acciones_Def_90": 3.6, "Valor_Mercado_M": 22, "Rating": 7.76},
    {"Jugador": "Nico Williams", "Equipo": "Athletic Club", "Liga": "LaLiga", "Nacionalidad": "España", "Posicion": "Extremo", "Edad": 22, "PJ": 34, "Minutos": 2760, "Goles": 9, "Asistencias": 11, "xG": 8.2, "xA": 9.6, "Tiros_90": 2.6, "Pases_Clave_90": 2.2, "Precision_Pase_Pct": 79.8, "Regates_90": 3.8, "Acciones_Def_90": 2.4, "Valor_Mercado_M": 70, "Rating": 7.65},
    {"Jugador": "Álex Baena", "Equipo": "Villarreal CF", "Liga": "LaLiga", "Nacionalidad": "España", "Posicion": "Mediocampista", "Edad": 23, "PJ": 31, "Minutos": 2590, "Goles": 7, "Asistencias": 13, "xG": 6.1, "xA": 11.8, "Tiros_90": 2.1, "Pases_Clave_90": 3.4, "Precision_Pase_Pct": 82.6, "Regates_90": 1.7, "Acciones_Def_90": 3.9, "Valor_Mercado_M": 50, "Rating": 7.79},

    # Premier League
    {"Jugador": "Mohamed Salah", "Equipo": "Liverpool", "Liga": "Premier League", "Nacionalidad": "Egipto", "Posicion": "Extremo", "Edad": 32, "PJ": 39, "Minutos": 3340, "Goles": 32, "Asistencias": 22, "xG": 28.1, "xA": 16.4, "Tiros_90": 3.9, "Pases_Clave_90": 2.7, "Precision_Pase_Pct": 81.9, "Regates_90": 2.1, "Acciones_Def_90": 1.9, "Valor_Mercado_M": 55, "Rating": 8.45},
    {"Jugador": "Virgil van Dijk", "Equipo": "Liverpool", "Liga": "Premier League", "Nacionalidad": "Países Bajos", "Posicion": "Defensa", "Edad": 33, "PJ": 38, "Minutos": 3420, "Goles": 4, "Asistencias": 2, "xG": 3.2, "xA": 1.4, "Tiros_90": 0.8, "Pases_Clave_90": 0.5, "Precision_Pase_Pct": 91.8, "Regates_90": 0.3, "Acciones_Def_90": 8.4, "Valor_Mercado_M": 28, "Rating": 7.78},
    {"Jugador": "Ryan Gravenberch", "Equipo": "Liverpool", "Liga": "Premier League", "Nacionalidad": "Países Bajos", "Posicion": "Mediocampista", "Edad": 22, "PJ": 37, "Minutos": 3150, "Goles": 3, "Asistencias": 5, "xG": 2.6, "xA": 4.2, "Tiros_90": 0.9, "Pases_Clave_90": 1.3, "Precision_Pase_Pct": 89.7, "Regates_90": 2.0, "Acciones_Def_90": 6.8, "Valor_Mercado_M": 55, "Rating": 7.64},
    {"Jugador": "Erling Haaland", "Equipo": "Manchester City", "Liga": "Premier League", "Nacionalidad": "Noruega", "Posicion": "Delantero", "Edad": 24, "PJ": 37, "Minutos": 3240, "Goles": 30, "Asistencias": 4, "xG": 29.4, "xA": 3.5, "Tiros_90": 4.5, "Pases_Clave_90": 0.9, "Precision_Pase_Pct": 76.8, "Regates_90": 0.7, "Acciones_Def_90": 1.1, "Valor_Mercado_M": 200, "Rating": 8.09},
    {"Jugador": "Rodri", "Equipo": "Manchester City", "Liga": "Premier League", "Nacionalidad": "España", "Posicion": "Mediocampista", "Edad": 28, "PJ": 25, "Minutos": 2180, "Goles": 4, "Asistencias": 6, "xG": 3.4, "xA": 4.9, "Tiros_90": 1.5, "Pases_Clave_90": 1.8, "Precision_Pase_Pct": 92.8, "Regates_90": 1.4, "Acciones_Def_90": 7.5, "Valor_Mercado_M": 130, "Rating": 8.18},
    {"Jugador": "Bukayo Saka", "Equipo": "Arsenal", "Liga": "Premier League", "Nacionalidad": "Inglaterra", "Posicion": "Extremo", "Edad": 23, "PJ": 31, "Minutos": 2650, "Goles": 13, "Asistencias": 14, "xG": 11.4, "xA": 12.8, "Tiros_90": 3.1, "Pases_Clave_90": 2.9, "Precision_Pase_Pct": 83.4, "Regates_90": 2.6, "Acciones_Def_90": 3.2, "Valor_Mercado_M": 150, "Rating": 8.11},
    {"Jugador": "Declan Rice", "Equipo": "Arsenal", "Liga": "Premier League", "Nacionalidad": "Inglaterra", "Posicion": "Mediocampista", "Edad": 26, "PJ": 37, "Minutos": 3210, "Goles": 5, "Asistencias": 8, "xG": 4.2, "xA": 7.1, "Tiros_90": 1.4, "Pases_Clave_90": 1.9, "Precision_Pase_Pct": 90.3, "Regates_90": 1.2, "Acciones_Def_90": 6.9, "Valor_Mercado_M": 110, "Rating": 7.79},
    {"Jugador": "William Saliba", "Equipo": "Arsenal", "Liga": "Premier League", "Nacionalidad": "Francia", "Posicion": "Defensa", "Edad": 24, "PJ": 37, "Minutos": 3310, "Goles": 2, "Asistencias": 1, "xG": 1.8, "xA": 0.7, "Tiros_90": 0.4, "Pases_Clave_90": 0.3, "Precision_Pase_Pct": 92.5, "Regates_90": 0.4, "Acciones_Def_90": 8.1, "Valor_Mercado_M": 80, "Rating": 7.66},
    {"Jugador": "Cole Palmer", "Equipo": "Chelsea", "Liga": "Premier League", "Nacionalidad": "Inglaterra", "Posicion": "Mediocampista", "Edad": 22, "PJ": 35, "Minutos": 3020, "Goles": 18, "Asistencias": 11, "xG": 15.6, "xA": 10.9, "Tiros_90": 3.3, "Pases_Clave_90": 2.8, "Precision_Pase_Pct": 83.9, "Regates_90": 2.3, "Acciones_Def_90": 2.1, "Valor_Mercado_M": 130, "Rating": 8.07},
    {"Jugador": "Alexander Isak", "Equipo": "Newcastle United", "Liga": "Premier League", "Nacionalidad": "Suecia", "Posicion": "Delantero", "Edad": 25, "PJ": 33, "Minutos": 2810, "Goles": 23, "Asistencias": 6, "xG": 20.1, "xA": 5.2, "Tiros_90": 3.4, "Pases_Clave_90": 1.5, "Precision_Pase_Pct": 80.2, "Regates_90": 2.0, "Acciones_Def_90": 1.6, "Valor_Mercado_M": 100, "Rating": 7.92},
    {"Jugador": "Bruno Fernandes", "Equipo": "Manchester United", "Liga": "Premier League", "Nacionalidad": "Portugal", "Posicion": "Mediocampista", "Edad": 30, "PJ": 38, "Minutos": 3360, "Goles": 14, "Asistencias": 13, "xG": 12.8, "xA": 12.4, "Tiros_90": 2.8, "Pases_Clave_90": 3.3, "Precision_Pase_Pct": 81.5, "Regates_90": 1.1, "Acciones_Def_90": 4.9, "Valor_Mercado_M": 55, "Rating": 7.86},

    # Serie A
    {"Jugador": "Lautaro Martínez", "Equipo": "Inter de Milán", "Liga": "Serie A", "Nacionalidad": "Argentina", "Posicion": "Delantero", "Edad": 27, "PJ": 36, "Minutos": 2980, "Goles": 21, "Asistencias": 6, "xG": 19.5, "xA": 5.1, "Tiros_90": 3.7, "Pases_Clave_90": 1.5, "Precision_Pase_Pct": 81.0, "Regates_90": 1.4, "Acciones_Def_90": 2.5, "Valor_Mercado_M": 100, "Rating": 7.91},
    {"Jugador": "Marcus Thuram", "Equipo": "Inter de Milán", "Liga": "Serie A", "Nacionalidad": "Francia", "Posicion": "Delantero", "Edad": 27, "PJ": 36, "Minutos": 2840, "Goles": 17, "Asistencias": 9, "xG": 15.2, "xA": 7.4, "Tiros_90": 2.6, "Pases_Clave_90": 1.6, "Precision_Pase_Pct": 79.6, "Regates_90": 1.9, "Acciones_Def_90": 2.0, "Valor_Mercado_M": 75, "Rating": 7.78},
    {"Jugador": "Nicolò Barella", "Equipo": "Inter de Milán", "Liga": "Serie A", "Nacionalidad": "Italia", "Posicion": "Mediocampista", "Edad": 28, "PJ": 36, "Minutos": 2990, "Goles": 5, "Asistencias": 8, "xG": 4.1, "xA": 7.6, "Tiros_90": 1.3, "Pases_Clave_90": 2.2, "Precision_Pase_Pct": 88.4, "Regates_90": 1.5, "Acciones_Def_90": 5.9, "Valor_Mercado_M": 80, "Rating": 7.75},
    {"Jugador": "Mateo Retegui", "Equipo": "Atalanta", "Liga": "Serie A", "Nacionalidad": "Italia", "Posicion": "Delantero", "Edad": 25, "PJ": 35, "Minutos": 2540, "Goles": 24, "Asistencias": 5, "xG": 20.6, "xA": 4.1, "Tiros_90": 3.5, "Pases_Clave_90": 1.2, "Precision_Pase_Pct": 77.5, "Regates_90": 0.9, "Acciones_Def_90": 1.8, "Valor_Mercado_M": 45, "Rating": 7.82},
    {"Jugador": "Ademola Lookman", "Equipo": "Atalanta", "Liga": "Serie A", "Nacionalidad": "Nigeria", "Posicion": "Extremo", "Edad": 27, "PJ": 33, "Minutos": 2610, "Goles": 18, "Asistencias": 9, "xG": 15.4, "xA": 8.3, "Tiros_90": 3.2, "Pases_Clave_90": 2.4, "Precision_Pase_Pct": 80.8, "Regates_90": 2.9, "Acciones_Def_90": 2.2, "Valor_Mercado_M": 55, "Rating": 7.88},
    {"Jugador": "Rafael Leão", "Equipo": "AC Milan", "Liga": "Serie A", "Nacionalidad": "Portugal", "Posicion": "Extremo", "Edad": 25, "PJ": 35, "Minutos": 2790, "Goles": 12, "Asistencias": 11, "xG": 11.2, "xA": 9.8, "Tiros_90": 2.7, "Pases_Clave_90": 2.1, "Precision_Pase_Pct": 81.4, "Regates_90": 3.7, "Acciones_Def_90": 1.5, "Valor_Mercado_M": 75, "Rating": 7.63},
    {"Jugador": "Christian Pulisic", "Equipo": "AC Milan", "Liga": "Serie A", "Nacionalidad": "Estados Unidos", "Posicion": "Extremo", "Edad": 26, "PJ": 36, "Minutos": 2880, "Goles": 15, "Asistencias": 10, "xG": 13.1, "xA": 8.9, "Tiros_90": 2.5, "Pases_Clave_90": 2.2, "Precision_Pase_Pct": 84.5, "Regates_90": 2.2, "Acciones_Def_90": 2.6, "Valor_Mercado_M": 50, "Rating": 7.74},

    # Bundesliga
    {"Jugador": "Harry Kane", "Equipo": "Bayern Múnich", "Liga": "Bundesliga", "Nacionalidad": "Inglaterra", "Posicion": "Delantero", "Edad": 31, "PJ": 35, "Minutos": 3010, "Goles": 33, "Asistencias": 11, "xG": 29.8, "xA": 8.4, "Tiros_90": 4.3, "Pases_Clave_90": 1.8, "Precision_Pase_Pct": 82.3, "Regates_90": 1.1, "Acciones_Def_90": 1.7, "Valor_Mercado_M": 90, "Rating": 8.35},
    {"Jugador": "Jamal Musiala", "Equipo": "Bayern Múnich", "Liga": "Bundesliga", "Nacionalidad": "Alemania", "Posicion": "Mediocampista", "Edad": 22, "PJ": 34, "Minutos": 2760, "Goles": 17, "Asistencias": 9, "xG": 14.2, "xA": 8.1, "Tiros_90": 3.0, "Pases_Clave_90": 2.3, "Precision_Pase_Pct": 86.7, "Regates_90": 4.4, "Acciones_Def_90": 3.4, "Valor_Mercado_M": 140, "Rating": 8.16},
    {"Jugador": "Michael Olise", "Equipo": "Bayern Múnich", "Liga": "Bundesliga", "Nacionalidad": "Francia", "Posicion": "Extremo", "Edad": 23, "PJ": 35, "Minutos": 2680, "Goles": 13, "Asistencias": 14, "xG": 11.5, "xA": 12.6, "Tiros_90": 2.8, "Pases_Clave_90": 2.9, "Precision_Pase_Pct": 85.1, "Regates_90": 3.1, "Acciones_Def_90": 2.8, "Valor_Mercado_M": 80, "Rating": 8.02},
    {"Jugador": "Florian Wirtz", "Equipo": "Bayer Leverkusen", "Liga": "Bundesliga", "Nacionalidad": "Alemania", "Posicion": "Mediocampista", "Edad": 21, "PJ": 36, "Minutos": 2950, "Goles": 16, "Asistencias": 15, "xG": 13.9, "xA": 13.4, "Tiros_90": 2.7, "Pases_Clave_90": 3.1, "Precision_Pase_Pct": 86.2, "Regates_90": 3.5, "Acciones_Def_90": 3.8, "Valor_Mercado_M": 140, "Rating": 8.21},
    {"Jugador": "Serhou Guirassy", "Equipo": "Borussia Dortmund", "Liga": "Bundesliga", "Nacionalidad": "Guinea", "Posicion": "Delantero", "Edad": 29, "PJ": 34, "Minutos": 2840, "Goles": 24, "Asistencias": 6, "xG": 21.8, "xA": 5.0, "Tiros_90": 3.6, "Pases_Clave_90": 1.4, "Precision_Pase_Pct": 78.9, "Regates_90": 1.3, "Acciones_Def_90": 1.9, "Valor_Mercado_M": 40, "Rating": 7.85},

    # Ligue 1
    {"Jugador": "Ousmane Dembélé", "Equipo": "Paris Saint-Germain", "Liga": "Ligue 1", "Nacionalidad": "Francia", "Posicion": "Extremo", "Edad": 27, "PJ": 36, "Minutos": 2820, "Goles": 29, "Asistencias": 11, "xG": 23.8, "xA": 11.2, "Tiros_90": 4.1, "Pases_Clave_90": 2.9, "Precision_Pase_Pct": 84.6, "Regates_90": 4.2, "Acciones_Def_90": 2.3, "Valor_Mercado_M": 75, "Rating": 8.29},
    {"Jugador": "Bradley Barcola", "Equipo": "Paris Saint-Germain", "Liga": "Ligue 1", "Nacionalidad": "Francia", "Posicion": "Extremo", "Edad": 22, "PJ": 37, "Minutos": 2790, "Goles": 18, "Asistencias": 12, "xG": 16.1, "xA": 10.5, "Tiros_90": 3.0, "Pases_Clave_90": 2.3, "Precision_Pase_Pct": 85.8, "Regates_90": 3.3, "Acciones_Def_90": 2.6, "Valor_Mercado_M": 65, "Rating": 7.89},
    {"Jugador": "Vitinha", "Equipo": "Paris Saint-Germain", "Liga": "Ligue 1", "Nacionalidad": "Portugal", "Posicion": "Mediocampista", "Edad": 25, "PJ": 36, "Minutos": 3060, "Goles": 6, "Asistencias": 7, "xG": 4.8, "xA": 6.4, "Tiros_90": 1.6, "Pases_Clave_90": 2.1, "Precision_Pase_Pct": 93.4, "Regates_90": 1.8, "Acciones_Def_90": 6.1, "Valor_Mercado_M": 60, "Rating": 7.93},
    {"Jugador": "Achraf Hakimi", "Equipo": "Paris Saint-Germain", "Liga": "Ligue 1", "Nacionalidad": "Marruecos", "Posicion": "Defensa", "Edad": 26, "PJ": 35, "Minutos": 3020, "Goles": 6, "Asistencias": 11, "xG": 5.1, "xA": 9.8, "Tiros_90": 1.7, "Pases_Clave_90": 2.4, "Precision_Pase_Pct": 89.2, "Regates_90": 1.9, "Acciones_Def_90": 6.7, "Valor_Mercado_M": 65, "Rating": 7.96},
    {"Jugador": "Mason Greenwood", "Equipo": "Olympique de Marsella", "Liga": "Ligue 1", "Nacionalidad": "Inglaterra", "Posicion": "Extremo", "Edad": 23, "PJ": 28, "Minutos": 2380, "Goles": 16, "Asistencias": 5, "xG": 13.7, "xA": 4.8, "Tiros_90": 3.4, "Pases_Clave_90": 1.7, "Precision_Pase_Pct": 82.9, "Regates_90": 2.4, "Acciones_Def_90": 1.8, "Valor_Mercado_M": 35, "Rating": 7.62},
    {"Jugador": "Jonathan David", "Equipo": "Lille OSC", "Liga": "Ligue 1", "Nacionalidad": "Canadá", "Posicion": "Delantero", "Edad": 25, "PJ": 36, "Minutos": 3010, "Goles": 23, "Asistencias": 8, "xG": 20.4, "xA": 6.5, "Tiros_90": 3.2, "Pases_Clave_90": 1.6, "Precision_Pase_Pct": 83.5, "Regates_90": 1.4, "Acciones_Def_90": 2.4, "Valor_Mercado_M": 45, "Rating": 7.77},
]

# -----------------------------------------------------------------------------
# 3. Noticias Curadas de Fútbol Europeo (Respaldo Local + Contexto RAG)
# -----------------------------------------------------------------------------
NOTICIAS_RESPALDO = [
    {
        "Fecha": datetime.now().strftime("%d/%m/%Y"),
        "Competencia": "UEFA Champions League",
        "Titular": "Fase decisiva en Champions League: Barcelona, Real Madrid, Liverpool, Bayern e Inter perfilan sus candidaturas al título",
        "Resumen": "Los modelos de goles esperados (xG) sitúan a Liverpool, FC Barcelona, Bayern Múnich, Real Madrid, Arsenal y PSG como las ofensivas más letales del continente en la presente edición.",
        "Fuente": "Análisis UEFA / Opta",
    },
    {
        "Fecha": datetime.now().strftime("%d/%m/%Y"),
        "Competencia": "LaLiga",
        "Titular": "Pulso cerrado por LaLiga entre FC Barcelona y Real Madrid con Lamine Yamal, Raphinha y Mbappé en estado de gracia",
        "Resumen": "El tridente azulgrana (Lewandowski, Raphinha y Lamine Yamal) lidera la producción ofensiva europea, mientras que Kylian Mbappé y Vinícius Jr. sostienen el ataque blanco en la pelea punto a punto.",
        "Fuente": "Redacción LaLiga",
    },
    {
        "Fecha": datetime.now().strftime("%d/%m/%Y"),
        "Competencia": "Premier League",
        "Titular": "Mohamed Salah firma una temporada histórica en Premier League con más de 50 participaciones de gol para el Liverpool",
        "Resumen": "El extremo egipcio de Arne Slot encabeza tanto la tabla de goleadores como la de asistencias en Inglaterra, superando ampliamente sus métricas de xG y xA.",
        "Fuente": "Premier League Stats",
    },
    {
        "Fecha": datetime.now().strftime("%d/%m/%Y"),
        "Competencia": "Bundesliga",
        "Titular": "Harry Kane, Jamal Musiala y Florian Wirtz dominan los registros de eficiencia creativa en la Bundesliga",
        "Resumen": "El Bayern Múnich de Vincent Kompany comanda la liga alemana con una posesión superior al 67%, seguido de cerca por el Bayer Leverkusen de Xabi Alonso.",
        "Fuente": "Bundesliga Data Hub",
    },
    {
        "Fecha": datetime.now().strftime("%d/%m/%Y"),
        "Competencia": "Serie A",
        "Titular": "Inter de Milán, Napoli y Atalanta protagonizan la carrera por el Scudetto más pareja de la década",
        "Resumen": "Lautaro Martínez y Marcus Thuram lideran la diferencia de goles del Inter (+40), mientras que Mateo Retegui y Ademola Lookman mantienen al Atalanta como el segundo ataque más goleador.",
        "Fuente": "Gazzetta / Serie A",
    },
    {
        "Fecha": datetime.now().strftime("%d/%m/%Y"),
        "Competencia": "Ligue 1",
        "Titular": "Ousmane Dembélé explota como falso '9' en el PSG invicto de Luis Enrique",
        "Resumen": "Con una racha goleadora espectacular en 2025/2026 y más de 4 tiros por partido, Dembélé registra los mejores números de toda su carrera profesional en París.",
        "Fuente": "Ligue 1 Analytics",
    },
]

FEEDS_RSS_DEPORTIVOS = [
    ("Marca - Fútbol Internacional", "https://e00-marca.uecdn.es/rss/futbol/futbol-internacional.xml", "Internacional"),
    ("Marca - Champions League", "https://e00-marca.uecdn.es/rss/futbol/champions-league.xml", "UEFA Champions League"),
    ("BBC Sport - Football", "https://feeds.bbci.co.uk/sport/football/rss.xml", "Europa"),
]


def _norm(txt: str) -> str:
    nfkd = unicodedata.normalize("NFKD", str(txt).lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c)).strip()


def cargar_equipos() -> pd.DataFrame:
    """Devuelve el DataFrame de equipos europeos desde el CSV sincronizado o datos base."""
    if RUTA_EQUIPOS_CSV.exists():
        try:
            df = pd.read_csv(RUTA_EQUIPOS_CSV)
        except Exception:
            df = pd.DataFrame(DATOS_EQUIPOS_RAW)
    else:
        df = pd.DataFrame(DATOS_EQUIPOS_RAW)

    if "Nombre_Oficial" not in df.columns:
        df["Nombre_Oficial"] = df["Equipo"]

    # Enriquecer entrenadores, títulos y valores de plantilla de los clubes principales
    for ref in DATOS_EQUIPOS_RAW:
        ref_n = _norm(ref["Equipo"])
        for idx, row in df.iterrows():
            eq_n = _norm(row["Equipo"])
            of_n = _norm(row.get("Nombre_Oficial", ""))
            if ref_n in eq_n or ref_n in of_n or (eq_n in ref_n and len(eq_n) >= 4):
                df.at[idx, "Entrenador"] = ref["Entrenador"]
                df.at[idx, "Posesion_Pct"] = ref["Posesion_Pct"]
                df.at[idx, "Champions_Titulos"] = ref["Champions_Titulos"]
                df.at[idx, "Valor_Plantilla_M"] = ref["Valor_Plantilla_M"]
                df.at[idx, "Esquema"] = ref["Esquema"]

    if "DG" not in df.columns and "GF" in df.columns and "GC" in df.columns:
        df["DG"] = df["GF"] - df["GC"]
    if "PJ" in df.columns:
        pj_seguro = df["PJ"].replace(0, 1)
        df["Goles_Por_Partido"] = (df["GF"] / pj_seguro).round(2)
        df["Goles_Contra_Partido"] = (df["GC"] / pj_seguro).round(2)
        df["xG_Favor_Partido"] = (df["xG_Favor"] / pj_seguro).round(2)
        df["xG_Contra_Partido"] = (df["xG_Contra"] / pj_seguro).round(2)
    return df


def cargar_jugadores() -> pd.DataFrame:
    """Devuelve el DataFrame de jugadores europeos combinando la plantilla masiva de la API con las métricas detalladas."""
    if RUTA_JUGADORES_CSV.exists():
        try:
            df = pd.read_csv(RUTA_JUGADORES_CSV)
        except Exception:
            df = pd.DataFrame(DATOS_JUGADORES_RAW)
    else:
        df = pd.DataFrame(DATOS_JUGADORES_RAW)

    # Enriquecer las métricas de las estrellas principales si tienen 0 goles en la descarga parcial de la API
    mapa_estrellas = {_norm(r["Jugador"]): r for r in DATOS_JUGADORES_RAW}
    for idx, row in df.iterrows():
        clave = _norm(row["Jugador"])
        if clave in mapa_estrellas:
            ref = mapa_estrellas[clave]
            if row["Goles"] < ref["Goles"]:
                for col in ["Goles", "Asistencias", "xG", "xA", "Tiros_90", "Pases_Clave_90", "Precision_Pase_Pct", "Regates_90", "Acciones_Def_90", "Valor_Mercado_M", "Rating"]:
                    if col in df.columns and col in ref:
                        df.at[idx, col] = ref[col]

    df["Goles_Mas_Asistencias"] = df["Goles"] + df["Asistencias"]
    df["xG_Mas_xA"] = (df["xG"] + df["xA"]).round(1)
    df["Diferencial_xG"] = (df["Goles"] - df["xG"]).round(1)
    minutos_seguros = df["Minutos"].replace(0, 90)
    df["G_A_por_90"] = ((df["Goles_Mas_Asistencias"] / minutos_seguros) * 90).round(2)
    return df


def obtener_noticias_futbol(intentar_rss_en_vivo: bool = True, max_items: int = 12) -> tuple[pd.DataFrame, str]:
    """
    Obtiene noticias de fútbol combinando RSS en vivo (si hay conexión)
    con el feed curado de respaldo para garantizar disponibilidad al 100%.
    Retorna (DataFrame, mensaje_estado).
    """
    noticias_vivas = []
    if intentar_rss_en_vivo:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        for nombre_fuente, url_rss, competencia in FEEDS_RSS_DEPORTIVOS:
            try:
                req = urllib.request.Request(
                    url_rss,
                    headers={"User-Agent": "Mozilla/5.0 (ShinyFutbolIA/1.0)"},
                )
                with urllib.request.urlopen(req, context=ctx, timeout=3.5) as resp:
                    xml_bytes = resp.read()
                root = ET.fromstring(xml_bytes)
                items = root.findall(".//item")
                for item in items[:4]:
                    titulo = (item.findtext("title") or "").strip()
                    desc = (item.findtext("description") or "").strip()
                    # Limpiar etiquetas HTML simples si existen en la descripción
                    if "<" in desc and ">" in desc:
                        import re
                        desc = re.sub(r"<[^>]+>", "", desc).strip()
                    if len(desc) > 220:
                        desc = desc[:217] + "..."
                    if titulo:
                        noticias_vivas.append(
                            {
                                "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "Competencia": competencia,
                                "Titular": titulo,
                                "Resumen": desc or "Noticia de última hora en el fútbol europeo.",
                                "Fuente": f"🔴 En Vivo ({nombre_fuente})",
                            }
                        )
            except Exception:
                continue

    if noticias_vivas:
        todas = noticias_vivas[:max_items] + NOTICIAS_RESPALDO[:4]
        df_not = pd.DataFrame(todas)
        estado = f"En vivo RSS ({len(noticias_vivas)} titulares recientes) + Base Analítica"
    else:
        df_not = pd.DataFrame(NOTICIAS_RESPALDO)
        estado = "Base Analítica Local Activa (Modo Offline / Respaldo)"

    if not RUTA_NOTICIAS_CSV.exists():
        try:
            df_not.to_csv(RUTA_NOTICIAS_CSV, index=False, encoding="utf-8-sig")
        except Exception:
            pass
    return df_not, estado


def simular_partido_poisson(df_equipos: pd.DataFrame, equipo_local: str, equipo_visitante: str) -> dict:
    """
    Calcula las probabilidades de un partido entre dos equipos europeos
    utilizando sus promedios de xG a favor/en contra, ventaja de localía y distribución de Poisson.
    """
    fila_loc = df_equipos[df_equipos["Equipo"] == equipo_local]
    fila_vis = df_equipos[df_equipos["Equipo"] == equipo_visitante]
    if fila_loc.empty or fila_vis.empty:
        return {}

    loc = fila_loc.iloc[0]
    vis = fila_vis.iloc[0]

    media_xg_liga = df_equipos["xG_Favor_Partido"].mean()
    fuerza_ataque_loc = loc["xG_Favor_Partido"] / media_xg_liga
    fuerza_def_loc = loc["xG_Contra_Partido"] / media_xg_liga
    fuerza_ataque_vis = vis["xG_Favor_Partido"] / media_xg_liga
    fuerza_def_vis = vis["xG_Contra_Partido"] / media_xg_liga

    # Factor de localía (+10% xG local, -6% xG visitante) + ajuste por valor de plantilla
    factor_plantilla = (loc["Valor_Plantilla_M"] / max(vis["Valor_Plantilla_M"], 150)) ** 0.08
    lambda_loc = max(0.4, min(4.2, media_xg_liga * fuerza_ataque_loc * fuerza_def_vis * 1.10 * factor_plantilla))
    lambda_vis = max(0.3, min(3.9, media_xg_liga * fuerza_ataque_vis * fuerza_def_loc * 0.94 / factor_plantilla))

    def poisson_prob(lmbda: float, k: int) -> float:
        return (math.exp(-lmbda) * (lmbda ** k)) / math.factorial(k)

    prob_local = 0.0
    prob_empate = 0.0
    prob_visitante = 0.0
    mejor_marcador = (1, 1)
    max_p_marcador = -1.0
    prob_ambos_anotan = 0.0
    prob_mas_2_5 = 0.0

    matriz_marcadores = []
    for g_l in range(7):
        for g_v in range(7):
            p = poisson_prob(lambda_loc, g_l) * poisson_prob(lambda_vis, g_v)
            if g_l > g_v:
                prob_local += p
            elif g_l == g_v:
                prob_empate += p
            else:
                prob_visitante += p
            if g_l >= 1 and g_v >= 1:
                prob_ambos_anotan += p
            if (g_l + g_v) >= 3:
                prob_mas_2_5 += p
            matriz_marcadores.append(((g_l, g_v), p))
            if p > max_p_marcador:
                max_p_marcador = p
                mejor_marcador = (g_l, g_v)

    total_p = prob_local + prob_empate + prob_visitante
    prob_local = round((prob_local / total_p) * 100, 1)
    prob_empate = round((prob_empate / total_p) * 100, 1)
    prob_visitante = round(100.0 - prob_local - prob_empate, 1)

    matriz_marcadores.sort(key=lambda x: x[1], reverse=True)
    top_3_marcadores = [f"{m[0]}-{m[1]} ({round(p*100, 1)}%)" for m, p in matriz_marcadores[:3]]

    return {
        "equipo_local": equipo_local,
        "equipo_visitante": equipo_visitante,
        "xg_esperado_local": round(lambda_loc, 2),
        "xg_esperado_visitante": round(lambda_vis, 2),
        "prob_local": prob_local,
        "prob_empate": prob_empate,
        "prob_visitante": prob_visitante,
        "marcador_mas_probable": f"{mejor_marcador[0]} - {mejor_marcador[1]}",
        "top_marcadores": top_3_marcadores,
        "prob_mas_2_5": round(prob_mas_2_5 * 100, 1),
        "prob_ambos_anotan": round(prob_ambos_anotan * 100, 1),
    }


# -----------------------------------------------------------------------------
# 4. Consultas en Vivo de Partidos (Resultados de Hoy, Recientes y Próximos)
# -----------------------------------------------------------------------------
_CACHE_PARTIDOS_EQUIPO: dict[int, tuple[float, list[dict]]] = {}
_CACHE_PARTIDOS_HOY: tuple[float, list[dict]] | None = None


def obtener_partidos_equipo_vivo(equipo_id: int) -> list[dict]:
    """
    Consulta en tiempo real a Football-Data.org los partidos recientes, de hoy
    y próximos de un equipo específico (con caché breve de 3 minutos).
    """
    import time
    ahora_ts = time.time()
    if equipo_id in _CACHE_PARTIDOS_EQUIPO:
        ts_guardado, datos_guardados = _CACHE_PARTIDOS_EQUIPO[equipo_id]
        if ahora_ts - ts_guardado < 180:
            return datos_guardados

    api_key = os.environ.get("FOOTBALL_DATA_API_KEY", "9290169a360a463991c4891463f8612a").strip()
    if not api_key:
        return []

    hoy = datetime.now()
    desde = (hoy - timedelta(days=25)).strftime("%Y-%m-%d")
    hasta = (hoy + timedelta(days=25)).strftime("%Y-%m-%d")
    url = f"https://api.football-data.org/v4/teams/{int(equipo_id)}/matches?dateFrom={desde}&dateTo={hasta}"

    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(
            url,
            headers={"X-Auth-Token": api_key, "User-Agent": "ShinyFutbolIA/2.0"},
        )
        with urllib.request.urlopen(req, context=ctx, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        partidos_limpios = []
        for m in data.get("matches", []):
            fecha_utc = (m.get("utcDate") or "")[:10]
            comp = m.get("competition", {}).get("name", "Competencia")
            local = m.get("homeTeam", {}).get("shortName") or m.get("homeTeam", {}).get("name", "Local")
            visitante = m.get("awayTeam", {}).get("shortName") or m.get("awayTeam", {}).get("name", "Visitante")
            estado = m.get("status", "")
            ft = m.get("score", {}).get("fullTime", {})
            ht = m.get("score", {}).get("halfTime", {})
            g_loc = ft.get("home")
            g_vis = ft.get("away")
            jornada = m.get("matchday")

            partidos_limpios.append({
                "fecha": fecha_utc,
                "competencia": comp,
                "jornada": jornada,
                "local": local,
                "visitante": visitante,
                "goles_local": g_loc,
                "goles_visitante": g_vis,
                "ht_local": ht.get("home"),
                "ht_visitante": ht.get("away"),
                "estado": estado,
            })

        _CACHE_PARTIDOS_EQUIPO[equipo_id] = (ahora_ts, partidos_limpios)
        return partidos_limpios
    except Exception:
        return []


def obtener_partidos_jornada_vivo() -> list[dict]:
    """
    Consulta en tiempo real todos los partidos disputados entre ayer, hoy y mañana
    en todas las competencias de Football-Data.org.
    """
    global _CACHE_PARTIDOS_HOY
    import time
    ahora_ts = time.time()
    if _CACHE_PARTIDOS_HOY and (ahora_ts - _CACHE_PARTIDOS_HOY[0] < 180):
        return _CACHE_PARTIDOS_HOY[1]

    api_key = os.environ.get("FOOTBALL_DATA_API_KEY", "9290169a360a463991c4891463f8612a").strip()
    if not api_key:
        return []

    hoy = datetime.now()
    desde = (hoy - timedelta(days=1)).strftime("%Y-%m-%d")
    hasta = (hoy + timedelta(days=1)).strftime("%Y-%m-%d")
    url = f"https://api.football-data.org/v4/matches?dateFrom={desde}&dateTo={hasta}"

    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(
            url,
            headers={"X-Auth-Token": api_key, "User-Agent": "ShinyFutbolIA/2.0"},
        )
        with urllib.request.urlopen(req, context=ctx, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        partidos = []
        for m in data.get("matches", []):
            fecha_utc = (m.get("utcDate") or "")[:10]
            comp = m.get("competition", {}).get("name", "Competencia")
            local = m.get("homeTeam", {}).get("shortName") or m.get("homeTeam", {}).get("name", "Local")
            visitante = m.get("awayTeam", {}).get("shortName") or m.get("awayTeam", {}).get("name", "Visitante")
            estado = m.get("status", "")
            ft = m.get("score", {}).get("fullTime", {})
            partidos.append({
                "fecha": fecha_utc,
                "competencia": comp,
                "local": local,
                "visitante": visitante,
                "goles_local": ft.get("home"),
                "goles_visitante": ft.get("away"),
                "estado": estado,
            })

        _CACHE_PARTIDOS_HOY = (ahora_ts, partidos)
        return partidos
    except Exception:
        return []


