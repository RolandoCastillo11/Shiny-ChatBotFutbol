"""
Motor de Inteligencia Artificial Híbrido (RAG + LLM API + Analista Estadístico Local)
para el Chatbot de Fútbol Europeo en Shiny for Python.

Soporta:
1. Google Gemini API (gemini-2.5-flash / gemini-2.0-flash)
2. Groq Cloud API (llama-3.3-70b-versatile)
3. Motor Analítico Local RAG + Modelo Matemático Poisson (sin requerir API Key)
"""

import json
import os
from pathlib import Path
import ssl
import unicodedata
import urllib.request
import urllib.error
import pandas as pd

# Cargar automáticamente las variables de entorno desde el archivo .env si existe
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

from datos_futbol import (
    simular_partido_poisson,
    obtener_partidos_equipo_vivo,
    obtener_partidos_jornada_vivo,
)


def normalizar_texto(texto: str) -> str:
    """Elimina tildes y convierte a minúsculas para búsquedas tolerantes."""
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# Alias comunes de equipos y jugadores para reconocimiento natural en español
ALIAS_EQUIPOS = {
    "madrid": "Real Madrid",
    "real madrid": "Real Madrid",
    "merengues": "Real Madrid",
    "barca": "FC Barcelona",
    "barça": "FC Barcelona",
    "barcelona": "FC Barcelona",
    "culers": "FC Barcelona",
    "blaugrana": "FC Barcelona",
    "atleti": "Atlético de Madrid",
    "atletico": "Atlético de Madrid",
    "colchoneros": "Atlético de Madrid",
    "athletic": "Athletic Club",
    "bilbao": "Athletic Club",
    "villarreal": "Villarreal CF",
    "real sociedad": "Real Sociedad",
    "liverpool": "Liverpool",
    "reds": "Liverpool",
    "arsenal": "Arsenal",
    "gunners": "Arsenal",
    "city": "Manchester City",
    "man city": "Manchester City",
    "manchester city": "Manchester City",
    "citizens": "Manchester City",
    "chelsea": "Chelsea",
    "blues": "Chelsea",
    "newcastle": "Newcastle United",
    "aston villa": "Aston Villa",
    "villa": "Aston Villa",
    "united": "Manchester United",
    "man united": "Manchester United",
    "manchester united": "Manchester United",
    "inter": "Inter de Milán",
    "inter de milan": "Inter de Milán",
    "nerazzurri": "Inter de Milán",
    "napoli": "Napoli",
    "napoles": "Napoli",
    "atalanta": "Atalanta",
    "juve": "Juventus",
    "juventus": "Juventus",
    "milan": "AC Milan",
    "ac milan": "AC Milan",
    "bayern": "Bayern Múnich",
    "bayern munich": "Bayern Múnich",
    "leverkusen": "Bayer Leverkusen",
    "bayer": "Bayer Leverkusen",
    "frankfurt": "Eintracht Frankfurt",
    "leipzig": "RB Leipzig",
    "dortmund": "Borussia Dortmund",
    "bvb": "Borussia Dortmund",
    "psg": "Paris Saint-Germain",
    "paris": "Paris Saint-Germain",
    "marsella": "Olympique de Marsella",
    "monaco": "AS Monaco",
    "lille": "Lille OSC",
}

ALIAS_LIGAS = {
    "laliga": "LaLiga",
    "la liga": "LaLiga",
    "liga espanola": "LaLiga",
    "espana": "LaLiga",
    "premier": "Premier League",
    "premier league": "Premier League",
    "liga inglesa": "Premier League",
    "inglaterra": "Premier League",
    "serie a": "Serie A",
    "liga italiana": "Serie A",
    "italia": "Serie A",
    "bundesliga": "Bundesliga",
    "liga alemana": "Bundesliga",
    "alemania": "Bundesliga",
    "ligue 1": "Ligue 1",
    "liga francesa": "Ligue 1",
    "francia": "Ligue 1",
}


PALABRAS_COMUNES_IGNORAR = {
    "como", "para", "este", "esta", "entre", "quien", "cual", "mejor", "peor",
    "goles", "equipo", "equipos", "liga", "ligas", "tabla", "datos", "todos",
    "tiene", "tienen", "contra", "partido", "jugadores", "jugador", "club",
    "hola", "buenos", "dias", "tardes", "noches", "gracias", "ayuda", "menu",
}


def detectar_jugadores(consulta: str, df_jugadores: pd.DataFrame) -> list[pd.Series]:
    """Encuentra jugadores mencionados en la consulta (por nombre completo, apellido o apodo)."""
    q_norm = normalizar_texto(consulta)
    palabras_q = [p.strip(".,¿?¡!()\"'") for p in q_norm.split() if p.strip(".,¿?¡!()\"'")]
    encontrados = []
    nombres_vistos = set()

    apodos = {
        "vini": "Vinicius Junior",
        "vinicius": "Vinicius Junior",
        "mbappe": "Kylian Mbappé",
        "kylian": "Kylian Mbappé",
        "lamine": "Lamine Yamal",
        "yamal": "Lamine Yamal",
        "lewy": "Robert Lewandowski",
        "lewandowski": "Robert Lewandowski",
        "bellingham": "Jude Bellingham",
        "jude": "Jude Bellingham",
        "valverde": "Federico Valverde",
        "fede": "Federico Valverde",
        "haaland": "Erling Haaland",
        "salah": "Mohamed Salah",
        "saka": "Bukayo Saka",
        "palmer": "Cole Palmer",
        "kane": "Harry Kane",
        "musiala": "Jamal Musiala",
        "wirtz": "Florian Wirtz",
        "dembele": "Ousmane Dembélé",
        "lautaro": "Lautaro Martínez",
        "julian": "Julián Álvarez",
        "griezmann": "Antoine Griezmann",
        "pedri": "Pedri",
        "raphinha": "Raphinha",
        "rodri": "Rodri",
        "courtois": "Thibaut Courtois",
        "van dijk": "Virgil van Dijk",
        "isak": "Alexander Isak",
        "leao": "Rafael Leão",
        "pulisic": "Christian Pulisic",
        "lookman": "Ademola Lookman",
        "retegui": "Mateo Retegui",
        "hakimi": "Achraf Hakimi",
        "barcola": "Bradley Barcola",
        "vitinha": "Vitinha",
        "olise": "Michael Olise",
        "guirassy": "Serhou Guirassy",
        "cubarsi": "Pau Cubarsí",
        "nico williams": "Nico Williams",
        "baena": "Álex Baena",
        "saliba": "William Saliba",
        "rice": "Declan Rice",
        "bruno fernandes": "Bruno Fernandes",
        "barella": "Nicolò Barella",
        "thuram": "Marcus Thuram",
    }

    df_ord = df_jugadores.sort_values(["Goles", "Rating"], ascending=False)
    palabras_consumidas = set()

    # 1. Coincidencia exacta de nombre completo en la consulta
    for _, row in df_ord.iterrows():
        nombre = str(row["Jugador"])
        nom_norm = normalizar_texto(nombre)
        if len(nom_norm) >= 4 and nom_norm in q_norm and nombre not in nombres_vistos:
            encontrados.append(row)
            nombres_vistos.add(nombre)
            for p in nom_norm.split():
                palabras_consumidas.add(p)

    # 2. Coincidencia por apodos conocidos
    for apodo, nombre_real in apodos.items():
        if apodo in palabras_q or (len(apodo) >= 5 and apodo in q_norm):
            nom_busq = normalizar_texto(nombre_real)
            for _, row in df_ord.iterrows():
                if nom_busq in normalizar_texto(row["Jugador"]):
                    if row["Jugador"] not in nombres_vistos:
                        encontrados.append(row)
                        nombres_vistos.add(row["Jugador"])
                    for p in apodo.split():
                        palabras_consumidas.add(p)
                    for p in nom_busq.split():
                        palabras_consumidas.add(p)
                    break

    # 3. Coincidencia parcial por apellido/nombre (solo para palabras no consumidas aún)
    palabras_restantes = [p for p in palabras_q if p not in palabras_consumidas]
    if palabras_restantes:
        for _, row in df_ord.iterrows():
            nombre = str(row["Jugador"])
            if nombre in nombres_vistos:
                continue
            nom_norm = normalizar_texto(nombre)
            partes = [p for p in nom_norm.split() if len(p) >= 5 and p not in PALABRAS_COMUNES_IGNORAR]
            if partes and any(p in palabras_restantes for p in partes):
                encontrados.append(row)
                nombres_vistos.add(nombre)
                for p in partes:
                    if p in palabras_restantes:
                        palabras_restantes.remove(p)

    return encontrados[:6]


def detectar_equipos(consulta: str, df_equipos: pd.DataFrame) -> list[pd.Series]:
    """Encuentra cualquiera de los 111 equipos mencionados en la consulta."""
    q_norm = normalizar_texto(consulta)
    palabras = [p.strip(".,¿?¡!()\"'") for p in q_norm.split() if p.strip(".,¿?¡!()\"'")]
    resultados = []
    equipos_vistos = set()

    # 1. Buscar directamente en los nombres de los 111 equipos del CSV
    for _, row in df_equipos.iterrows():
        eq_corto = str(row["Equipo"])
        eq_oficial = str(row.get("Nombre_Oficial", eq_corto))
        n_corto = normalizar_texto(eq_corto)
        n_oficial = normalizar_texto(eq_oficial)

        if (len(n_corto) >= 4 and n_corto in q_norm) or (len(n_oficial) >= 5 and n_oficial in q_norm):
            if eq_corto not in equipos_vistos:
                resultados.append(row)
                equipos_vistos.add(eq_corto)

    # 2. Buscar por alias conocidos (ej. "barcelona", "barca", "madrid", "city", "atleti", "psg")
    for alias, equipo_ref in sorted(ALIAS_EQUIPOS.items(), key=lambda x: len(x[0]), reverse=True):
        coincide = (alias in q_norm) if " " in alias else (alias in palabras)
        if coincide:
            ref_norm = normalizar_texto(equipo_ref)
            for _, row in df_equipos.iterrows():
                eq_corto = str(row["Equipo"])
                if eq_corto in equipos_vistos:
                    continue
                n_corto = normalizar_texto(eq_corto)
                n_oficial = normalizar_texto(str(row.get("Nombre_Oficial", eq_corto)))
                if ref_norm in n_corto or ref_norm in n_oficial or n_corto in ref_norm:
                    resultados.append(row)
                    equipos_vistos.add(eq_corto)
                    break

    return resultados


def detectar_liga(consulta: str) -> str | None:
    """Detecta si el usuario pregunta por una liga específica."""
    q_norm = normalizar_texto(consulta)
    for alias, liga_oficial in sorted(ALIAS_LIGAS.items(), key=lambda x: len(x[0]), reverse=True):
        if alias in q_norm:
            return liga_oficial
    return None


def formatear_partidos_equipo_vivo(equipo_row: pd.Series) -> str:
    """Consulta y formatea en Markdown los partidos recientes, de hoy y próximos de un club en tiempo real."""
    eq_id = equipo_row.get("Equipo_ID")
    if pd.isna(eq_id) or not eq_id:
        return ""
    partidos = obtener_partidos_equipo_vivo(int(eq_id))
    if not partidos:
        return ""

    terminados = [p for p in partidos if p["estado"] == "FINISHED"]
    en_juego = [p for p in partidos if p["estado"] in ("IN_PLAY", "PAUSED", "LIVE")]
    programados = [p for p in partidos if p["estado"] in ("SCHEDULED", "TIMED")]

    lineas = [f"#### 📅 Partidos en Tiempo Real de {equipo_row['Equipo']} (API Football-Data.org):"]
    if en_juego:
        for p in en_juego:
            lineas.append(
                f"- 🔴 **EN JUEGO AHORA ({p['fecha']} - {p['competencia']})**: "
                f"**{p['local']} {p['goles_local']} - {p['goles_visitante']} {p['visitante']}**"
            )
    if terminados:
        ult = terminados[-1]
        ht_txt = f" (Medio tiempo: {ult['ht_local']}-{ult['ht_visitante']})" if ult["ht_local"] is not None else ""
        lineas.append(
            f"- ✅ **ÚLTIMO PARTIDO / RESULTADO MÁS RECIENTE ({ult['fecha']} - {ult['competencia']})**: "
            f"**{ult['local']} {ult['goles_local']} - {ult['goles_visitante']} {ult['visitante']}**{ht_txt}"
        )
        if len(terminados) > 1:
            previos = ", ".join(
                f"{p['fecha']}: {p['local']} {p['goles_local']}-{p['goles_visitante']} {p['visitante']} ({p['competencia']})"
                for p in terminados[-5:-1]
            )
            lineas.append(f"- 📜 **Resultados previos recientes**: {previos}")
    if programados:
        prox = programados[0]
        lineas.append(
            f"- ⏭️ **PRÓXIMO PARTIDO PROGRAMADO ({prox['fecha']} - {prox['competencia']})**: "
            f"**{prox['local']} vs {prox['visitante']}**"
        )
        if len(programados) > 1:
            otros_prox = ", ".join(
                f"{p['fecha']}: {p['local']} vs {p['visitante']} ({p['competencia']})"
                for p in programados[1:4]
            )
            lineas.append(f"- 🗓️ **Calendario siguiente**: {otros_prox}")

    return "\n".join(lineas)


PALABRAS_CAMBIO_TEMA_GENERAL = (
    "tabla", "posiciones", "clasificacion", "lider", "lideres", "mejores equipos",
    "mejores jugadores", "equipos", "liga", "ranking", "top",
    "goleador", "goleadores", "pichichi", "bota de oro", "anotador",
    "asistencia", "asistencias", "asistidor", "asistidores", "pases clave", "creador", "creadores",
    "caro", "caros", "valor", "mercado", "valioso", "valiosos", "millones", "precio",
    "noticia", "noticias", "actualidad", "fichaje", "fichajes", "ultima hora", "titulares", "novedades",
    "partidos de hoy", "resultados de hoy", "quien jugo hoy", "marcadores", "jornada de hoy",
    "hola", "buenos dias", "buenas tardes", "buenas noches", "ayuda", "menu",
)


def recuperar_entidades_con_historial(
    consulta: str,
    df_jugadores: pd.DataFrame,
    df_equipos: pd.DataFrame,
    historial: list[dict] | None = None,
) -> tuple[list[pd.Series], list[pd.Series]]:
    """
    Detecta jugadores y equipos en la consulta actual; si es una pregunta de seguimiento
    (ej. '¿cuál fue el rival de hoy?' o '¿cuándo vuelve a jugar?'), recupera el equipo o jugador
    mencionado en los turnos previos del historial, salvo que sea una consulta general nueva
    (tabla de posiciones, goleadores, noticias, etc.).
    """
    jugadores_det = detectar_jugadores(consulta, df_jugadores)
    equipos_det = detectar_equipos(consulta, df_equipos)
    q_norm = normalizar_texto(consulta)
    es_tema_general = (
        any(p in q_norm for p in PALABRAS_CAMBIO_TEMA_GENERAL)
        or detectar_liga(consulta) is not None
    )
    if not jugadores_det and not equipos_det and historial and not es_tema_general:
        for msg in reversed(historial):
            if msg.get("role") == "user":
                texto_ant = msg.get("content", "")
                equipos_ant = detectar_equipos(texto_ant, df_equipos)
                jugadores_ant = detectar_jugadores(texto_ant, df_jugadores)
                if equipos_ant or jugadores_ant:
                    equipos_det = equipos_ant
                    jugadores_det = jugadores_ant
                    break
    return jugadores_det, equipos_det


def construir_contexto_rag(
    consulta: str,
    df_jugadores: pd.DataFrame,
    df_equipos: pd.DataFrame,
    df_noticias: pd.DataFrame,
    liga_filtro: str = "todas",
    historial: list[dict] | None = None,
) -> str:
    """
    Construye el bloque de contexto verificado (RAG) que se inyecta al LLM
    con las estadísticas relevantes y resultados en vivo para responder con precisión total.
    """
    jugadores_det, equipos_det = recuperar_entidades_con_historial(consulta, df_jugadores, df_equipos, historial)
    liga_det = detectar_liga(consulta) or (liga_filtro if liga_filtro != "todas" else None)

    bloques = []

    if jugadores_det:
        lineas_j = ["### JUGADORES DETECTADOS EN LA CONSULTA:"]
        for j in jugadores_det[:5]:
            lineas_j.append(
                f"- **{j['Jugador']}** ({j['Equipo']} - {j['Liga']}, {j['Posicion']}, {j['Edad']} años): "
                f"PJ={j['PJ']}, Min={j['Minutos']}, Goles={j['Goles']} (xG={j['xG']}), "
                f"Asistencias={j['Asistencias']} (xA={j['xA']}), G+A={j['Goles_Mas_Asistencias']}, "
                f"Tiros/90={j['Tiros_90']}, Pases Clave/90={j['Pases_Clave_90']}, "
                f"Precisión Pase={j['Precision_Pase_Pct']}%, Regates/90={j['Regates_90']}, "
                f"Acciones Def/90={j['Acciones_Def_90']}, Valor={j['Valor_Mercado_M']}M€, Rating={j['Rating']}"
            )
        bloques.append("\n".join(lineas_j))

    if equipos_det:
        lineas_e = ["### EQUIPOS Y PARTIDOS EN VIVO DETECTADOS EN LA CONSULTA:"]
        for e in equipos_det[:4]:
            lineas_e.append(
                f"- **{e['Equipo']}** ({e['Liga']}, DT: {e['Entrenador']}, Esquema {e['Esquema']}): "
                f"Pts={e['Pts']} en {e['PJ']} PJ ({e['G']}G-{e['E']}E-{e['P']}P), "
                f"GF={e['GF']} (xG={e['xG_Favor']}), GC={e['GC']} (xGA={e['xG_Contra']}), DG={e['DG']:+d}, "
                f"Posesión={e['Posesion_Pct']}%, Valor Plantilla={e['Valor_Plantilla_M']}M€, "
                f"Champions={e['Champions_Titulos']}, Racha={e['Racha']}"
            )
            info_vivo = formatear_partidos_equipo_vivo(e)
            if info_vivo:
                lineas_e.append(info_vivo)
        if len(equipos_det) >= 2:
            sim = simular_partido_poisson(df_equipos, equipos_det[0]["Equipo"], equipos_det[1]["Equipo"])
            if sim:
                lineas_e.append(
                    f"- **SIMULACIÓN POISSON ({sim['equipo_local']} vs {sim['equipo_visitante']})**: "
                    f"Victoria {sim['equipo_local']}={sim['prob_local']}%, Empate={sim['prob_empate']}%, "
                    f"Victoria {sim['equipo_visitante']}={sim['prob_visitante']}%. "
                    f"xG proyectado: {sim['xg_esperado_local']} - {sim['xg_esperado_visitante']}. "
                    f"Marcador más probable: {sim['marcador_mas_probable']}. "
                    f"Prob. +2.5 goles={sim['prob_mas_2_5']}%, Ambos anotan={sim['prob_ambos_anotan']}%."
                )
        bloques.append("\n".join(lineas_e))

    # Si pregunta por partidos de hoy/ayer en general
    q_norm = normalizar_texto(consulta)
    if any(p in q_norm for p in ["hoy", "ayer", "jornada", "resultados", "marcadores", "partidos"]):
        partidos_hoy = obtener_partidos_jornada_vivo()
        if partidos_hoy:
            lineas_hoy = ["### MARCADORES EN VIVO DE LA JORNADA ACTUAL (API Football-Data.org):"]
            for p in partidos_hoy[:15]:
                marc = (
                    f"{p['goles_local']} - {p['goles_visitante']} ({p['estado']})"
                    if p["goles_local"] is not None
                    else f"Programado ({p['estado']})"
                )
                lineas_hoy.append(f"- [{p['fecha']} | {p['competencia']}] **{p['local']}** vs **{p['visitante']}**: **{marc}**")
            bloques.append("\n".join(lineas_hoy))

    # Líderes generales o de la liga consultada
    df_j_sub = df_jugadores[df_jugadores["Liga"] == liga_det] if liga_det else df_jugadores
    df_e_sub = df_equipos[df_equipos["Liga"] == liga_det] if liga_det else df_equipos

    top_gol = df_j_sub.sort_values("Goles", ascending=False).head(5)
    top_asist = df_j_sub.sort_values("Asistencias", ascending=False).head(5)
    top_rating = df_j_sub.sort_values("Rating", ascending=False).head(5)
    top_equipos = df_e_sub.sort_values(["Pts", "DG"], ascending=False).head(6)

    ambito = f"({liga_det})" if liga_det else "(Top 5 Ligas Europeas)"
    bloques.append(
        f"### RESUMEN ESTADÍSTICO {ambito}:\n"
        f"- **Top Goleadores**: "
        + ", ".join(f"{r['Jugador']} ({r['Equipo']}: {r['Goles']} goles, xG {r['xG']})" for _, r in top_gol.iterrows())
        + "\n- **Top Asistidores**: "
        + ", ".join(f"{r['Jugador']} ({r['Equipo']}: {r['Asistencias']} asist., xA {r['xA']})" for _, r in top_asist.iterrows())
        + "\n- **Mejor Rating**: "
        + ", ".join(f"{r['Jugador']} ({r['Rating']})" for _, r in top_rating.iterrows())
        + "\n- **Clubes Líderes**: "
        + ", ".join(f"{r['Equipo']} ({r['Liga']}: {r['Pts']} pts, GF {r['GF']}/GC {r['GC']})" for _, r in top_equipos.iterrows())
    )

    # Titulares recientes de noticias
    if not df_noticias.empty:
        not_txt = "\n".join(
            f"- [{r['Competencia']}] {r['Titular']} ({r['Fuente']}): {r['Resumen']}"
            for _, r in df_noticias.head(5).iterrows()
        )
        bloques.append(f"### NOTICIAS RECIENTES DE FÚTBOL:\n{not_txt}")

    return "\n\n".join(bloques)


# -----------------------------------------------------------------------------
# Llamadas a Proveedores LLM (Google Gemini y Groq API)
# -----------------------------------------------------------------------------
def llamar_gemini_api(
    api_key: str,
    mensaje_usuario: str,
    contexto_rag: str,
    estilo: str,
    historial: list[dict],
) -> tuple[bool, str]:
    """Llama a la API REST de Google Gemini con el contexto futbolero RAG."""
    instruccion_estilo = {
        "tactico": "Responde como un Analista Táctico y Científico de Datos de Fútbol (estilo Opta / FBref / Moneyball), enfatizando métricas de xG, xA, eficiencia, esquemas tácticos y comparativas numéricas.",
        "comentarista": "Responde como un Comentarista Deportivo apasionado y carismático de Champions League, combinando emoción futbolera con estadísticas precisas.",
        "directo": "Responde con un Resumen Ejecutivo directo, conciso y estructurado en viñetas con las cifras clave.",
    }.get(estilo, "Responde como un experto analista de fútbol europeo.")

    system_prompt = (
        "Eres 'Fútbol IA Scout', un asistente experto en fútbol mundial y europeo (LaLiga, Premier League, Champions League, selecciones, Eurocopa, Mundiales e historia de los clubes).\n"
        f"{instruccion_estilo}\n"
        "REGLAS FUNDAMENTALES:\n"
        "1. Para la temporada actual y partidos del día, apóyate en el CONTEXTO RAG adjunto.\n"
        "2. Para preguntas de HISTORIAL, ENFRENTAMIENTOS DIRECTOS (H2H), AÑOS ANTERIORES, TRAYECTORIAS Y ANTECEDENTES HISTÓRICOS "
        "(ej. duelos cara a cara entre jugadores, enfrentamientos entre clubes, finales, Champions League o Eurocopas pasadas), "
        "utiliza TODO tu conocimiento histórico global de fútbol. Sé preciso: menciona fechas exactas, clubes/selecciones donde jugaron, resultados y marcadores reales de cada partido.\n"
        "3. NO te limites únicamente a la temporada 2026/27 cuando el usuario pregunte por enfrentamientos directos, títulos pasados o historia.\n"
        "4. Redacta análisis completos y concluyentes. Nunca dejes oraciones, listas o secciones cortadas a la mitad. Asegúrate de cerrar adecuadamente cada punto tratado.\n\n"
        f"=== CONTEXTO RAG DE DATOS DE LA TEMPORADA Y PARTIDOS EN VIVO ===\n{contexto_rag}\n========================================"
    )

    contenidos = []
    for msg in historial[-6:]:
        rol = "user" if msg.get("role") == "user" else "model"
        contenidos.append({"role": rol, "parts": [{"text": msg.get("content", "")}]})
    contenidos.append({"role": "user", "parts": [{"text": mensaje_usuario}]})

    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": contenidos,
        "generationConfig": {"temperature": 0.45, "maxOutputTokens": 4096},
    }

    modelos_gemini = [
        "gemini-3.5-flash",
        "gemini-3.1-flash-lite",
        "gemini-3.8-flash",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
    ]
    ultimo_error = ""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    for modelo in modelos_gemini:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key.strip()}"
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, context=ctx, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            candidatos = data.get("candidates", [])
            if candidatos:
                cand = candidatos[0]
                partes = cand.get("content", {}).get("parts", [])
                texto = "".join(p.get("text", "") for p in partes).strip()
                if texto:
                    if cand.get("finishReason") == "MAX_TOKENS":
                        texto += "\n\n*(Nota: la respuesta llegó al límite de tokens del modelo; puedes pedirme que continúe con el resto del análisis).* "
                    return True, texto
        except urllib.error.HTTPError as e:
            try:
                detalle = e.read().decode("utf-8")
            except Exception:
                detalle = str(e)
            ultimo_error = f"HTTP {e.code} en {modelo}: {detalle[:180]}"
            if e.code in (400, 401, 403) and "API_KEY" in detalle.upper():
                break
        except Exception as e:
            ultimo_error = str(e)

    return False, ultimo_error


def llamar_groq_api(
    api_key: str,
    mensaje_usuario: str,
    contexto_rag: str,
    estilo: str,
    historial: list[dict],
) -> tuple[bool, str]:
    """Llama a la API REST de Groq (Llama 3.3 70B) con el contexto futbolero RAG."""
    instruccion_estilo = {
        "tactico": "Analista Táctico y Científico de Datos de Fútbol (estilo Opta/FBref), enfocándote en xG, xA, regates, pases clave y táctica.",
        "comentarista": "Comentarista de Fútbol apasionado y dinámico de noches de Champions League, respaldado por estadísticas exactas.",
        "directo": "Analista Ejecutivo conciso y al grano, presentando tablas breves y viñetas directas.",
    }.get(estilo, "Experto en fútbol europeo.")

    system_prompt = (
        f"Eres 'Fútbol IA Scout', asistente experto en fútbol europeo en Shiny. Tu rol es: {instruccion_estilo}\n"
        "Usa prioritariamente las cifras del CONTEXTO RAG adjunto y responde en español usando Markdown.\n\n"
        f"{contexto_rag}"
    )

    mensajes = [{"role": "system", "content": system_prompt}]
    for msg in historial[-6:]:
        mensajes.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    mensajes.append({"role": "user", "content": mensaje_usuario})

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    for modelo in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
        payload = {
            "model": modelo,
            "messages": mensajes,
            "temperature": 0.45,
            "max_tokens": 4096,
        }
        try:
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key.strip()}",
                    "User-Agent": "ShinyFutbolIA/1.0",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, context=ctx, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            choices = data.get("choices", [])
            if choices:
                texto = choices[0].get("message", {}).get("content", "").strip()
                if texto:
                    return True, texto
        except Exception as e:
            ultimo_error = str(e)
            continue

    return False, ultimo_error


# -----------------------------------------------------------------------------
# Motor Analítico Local Inteligente (RAG Estadístico sin API Key)
# -----------------------------------------------------------------------------
def generar_respuesta_analitica_local(
    consulta: str,
    df_jugadores: pd.DataFrame,
    df_equipos: pd.DataFrame,
    df_noticias: pd.DataFrame,
    estilo: str = "tactico",
    liga_filtro: str = "todas",
    historial: list[dict] | None = None,
) -> str:
    """
    Genera una respuesta analítica rica basada en reconocimiento de entidades,
    resultados en vivo de Football-Data.org, modelo de Poisson y rankings estadísticos.
    """
    q_norm = normalizar_texto(consulta)
    jugadores_det, equipos_det = recuperar_entidades_con_historial(consulta, df_jugadores, df_equipos, historial)
    liga_det = detectar_liga(consulta) or (liga_filtro if liga_filtro != "todas" else None)

    prefijo = {
        "tactico": "📊 **Informe de Scouting & Big Data:**\n\n",
        "comentarista": "🎙️ **¡Hola, crack del fútbol! Aquí tienes el análisis desde la cabina:**\n\n",
        "directo": "⚡ **Resumen Estadístico Directo:**\n\n",
    }.get(estilo, "")

    # 1. Comparación de 2 o más jugadores
    if len(jugadores_det) >= 2:
        j1, j2 = jugadores_det[0], jugadores_det[1]
        mejor_gol = j1["Jugador"] if j1["Goles"] >= j2["Goles"] else j2["Jugador"]
        mejor_creacion = j1["Jugador"] if j1["Pases_Clave_90"] >= j2["Pases_Clave_90"] else j2["Jugador"]
        mejor_rating = j1["Jugador"] if j1["Rating"] >= j2["Rating"] else j2["Jugador"]

        tabla_comp = (
            f"### ⚔️ Comparativa Cara a Cara: **{j1['Jugador']}** vs **{j2['Jugador']}**\n\n"
            f"| Métrica | 🔵 {j1['Jugador']} ({j1['Equipo']}) | 🟢 {j2['Jugador']} ({j2['Equipo']}) |\n"
            f"| :--- | :---: | :---: |\n"
            f"| **Posición / Edad** | {j1['Posicion']} ({j1['Edad']} años) | {j2['Posicion']} ({j2['Edad']} años) |\n"
            f"| **Partidos (Minutos)** | {j1['PJ']} ({j1['Minutos']}') | {j2['PJ']} ({j2['Minutos']}') |\n"
            f"| **Goles (xG Esperados)** | **{j1['Goles']}** ({j1['xG']} xG) | **{j2['Goles']}** ({j2['xG']} xG) |\n"
            f"| **Asistencias (xA)** | **{j1['Asistencias']}** ({j1['xA']} xA) | **{j2['Asistencias']}** ({j2['xA']} xA) |\n"
            f"| **Goles + Asistencias (G+A/90)** | **{j1['Goles_Mas_Asistencias']}** ({j1['G_A_por_90']}/90') | **{j2['Goles_Mas_Asistencias']}** ({j2['G_A_por_90']}/90') |\n"
            f"| **Tiros / 90 min** | {j1['Tiros_90']} | {j2['Tiros_90']} |\n"
            f"| **Pases Clave / 90 min** | {j1['Pases_Clave_90']} | {j2['Pases_Clave_90']} |\n"
            f"| **Regates Exitosos / 90** | {j1['Regates_90']} | {j2['Regates_90']} |\n"
            f"| **Precisión de Pase** | {j1['Precision_Pase_Pct']}% | {j2['Precision_Pase_Pct']}% |\n"
            f"| **Valor de Mercado** | €{j1['Valor_Mercado_M']}M | €{j2['Valor_Mercado_M']}M |\n"
            f"| **Rating Global** | ⭐ **{j1['Rating']}** | ⭐ **{j2['Rating']}** |\n\n"
            f"**🔍 Conclusión del Analista IA:**\n"
            f"- En **impacto goleador**, destaca **{mejor_gol}** con una conversión superior frente a su xG.\n"
            f"- En **generación de peligro y volumen creativo**, lidera **{mejor_creacion}** en pases clave por 90 minutos.\n"
            f"- El rendimiento global más alto según nuestro índice algorítmico lo registra **{mejor_rating}**.\n"
            f"*(💡 Puedes ver su gráfico de radar superpuesto en la pestaña **Explorador y Comparador de Jugadores**)*."
        )
        return prefijo + tabla_comp

    # 2. Ficha analítica de 1 jugador específico
    if len(jugadores_det) == 1:
        j = jugadores_det[0]
        sobregoles = round(j["Goles"] - j["xG"], 1)
        eficiencia_txt = (
            f"superando su expectativa de gol en **+{sobregoles} goles** (definidor de élite)"
            if sobregoles >= 0
            else f"con un diferencial de **{sobregoles}** respecto a su xG"
        )
        ficha = (
            f"### 🌟 Ficha de Scouting IA: **{j['Jugador']}** ({j['Equipo']})\n\n"
            f"- **Liga / Nacionalidad**: {j['Liga']} | {j['Nacionalidad']} ({j['Edad']} años)\n"
            f"- **Posición**: {j['Posicion']} | **Valor de Mercado**: **€{j['Valor_Mercado_M']} Millones**\n"
            f"- **Producción Ofensiva**: **{j['Goles']} goles** ({j['xG']} $xG$) y **{j['Asistencias']} asistencias** ({j['xA']} $xA$) en {j['PJ']} partidos ({j['Minutos']} min).\n"
            f"- **Contribución Total**: **{j['Goles_Mas_Asistencias']} G+A** (**{j['G_A_por_90']}** participaciones de gol cada 90 min), {eficiencia_txt}.\n"
            f"- **Métricas Avanzadas por 90 min**:\n"
            f"  - 🎯 **Tiros**: {j['Tiros_90']} | 🔑 **Pases Clave**: {j['Pases_Clave_90']}\n"
            f"  - ⚡ **Regates Exitosos**: {j['Regates_90']} | 🛡️ **Acciones Defensivas**: {j['Acciones_Def_90']}\n"
            f"  - 📐 **Precisión de Pase**: {j['Precision_Pase_Pct']}% | ⭐ **Rating**: **{j['Rating']}/10**\n\n"
            f"¿Te gustaría compararlo con otro jugador? Escribe por ejemplo: *«Compara a {j['Jugador']} con Kylian Mbappé»*."
        )
        return prefijo + ficha

    # 3. Enfrentamiento / Simulación entre 2 equipos
    if len(equipos_det) >= 2:
        e1, e2 = equipos_det[0], equipos_det[1]
        sim = simular_partido_poisson(df_equipos, e1["Equipo"], e2["Equipo"])
        estrellas_e1 = df_jugadores[df_jugadores["Equipo"] == e1["Equipo"]].sort_values("Rating", ascending=False).head(2)
        estrellas_e2 = df_jugadores[df_jugadores["Equipo"] == e2["Equipo"]].sort_values("Rating", ascending=False).head(2)
        cracks_1 = ", ".join(f"{r['Jugador']} ({r['Goles']}G/{r['Asistencias']}A)" for _, r in estrellas_e1.iterrows()) or "Plantilla titular"
        cracks_2 = ", ".join(f"{r['Jugador']} ({r['Goles']}G/{r['Asistencias']}A)" for _, r in estrellas_e2.iterrows()) or "Plantilla titular"

        return (
            prefijo
            + f"### 🔮 Simulación Táctica y Modelo Poisson: **{e1['Equipo']}** vs **{e2['Equipo']}**\n\n"
            f"| Indicador del Club | 🏠 {e1['Equipo']} | ✈️ {e2['Equipo']} |\n"
            f"| :--- | :---: | :---: |\n"
            f"| **Liga / Entrenador** | {e1['Liga']} ({e1['Entrenador']}) | {e2['Liga']} ({e2['Entrenador']}) |\n"
            f"| **Sistema Táctico** | `{e1['Esquema']}` | `{e2['Esquema']}` |\n"
            f"| **Puntos (Récord)** | **{e1['Pts']} pts** ({e1['G']}G-{e1['E']}E-{e1['P']}P) | **{e2['Pts']} pts** ({e2['G']}G-{e2['E']}E-{e2['P']}P) |\n"
            f"| **Goles a Favor / Contra** | {e1['GF']} GF / {e1['GC']} GC ({e1['DG']:+d}) | {e2['GF']} GF / {e2['GC']} GC ({e2['DG']:+d}) |\n"
            f"| **xG a Favor / Partido** | {e1['xG_Favor_Partido']} xG | {e2['xG_Favor_Partido']} xG |\n"
            f"| **Posesión Media** | {e1['Posesion_Pct']}% | {e2['Posesion_Pct']}% |\n"
            f"| **Valor de Plantilla** | €{e1['Valor_Plantilla_M']}M | €{e2['Valor_Plantilla_M']}M |\n"
            f"| **Figuras Clave** | {cracks_1} | {cracks_2} |\n\n"
            f"#### 📈 Pronóstico Matemático (Distribución de Poisson + $xG$):\n"
            f"- 🏆 **Probabilidad de Victoria {e1['Equipo']}**: **{sim['prob_local']}%** ($xG$ esperado: `{sim['xg_esperado_local']}`)\n"
            f"- 🤝 **Probabilidad de Empate**: **{sim['prob_empate']}%**\n"
            f"- 🚀 **Probabilidad de Victoria {e2['Equipo']}**: **{sim['prob_visitante']}%** ($xG$ esperado: `{sim['xg_esperado_visitante']}`)\n"
            f"- 🎯 **Marcadores Exactos Más Probables**: {', '.join(sim['top_marcadores'])}\n"
            f"- 🔥 **Ambos Equipos Anotan**: **{sim['prob_ambos_anotan']}%** | **Más de 2.5 Goles**: **{sim['prob_mas_2_5']}%**"
        )

    # 4. Análisis de 1 equipo específico (incluyendo resultados en vivo y próximos partidos)
    if len(equipos_det) == 1:
        e = equipos_det[0]
        info_vivo = formatear_partidos_equipo_vivo(e)
        bloque_vivo = f"\n{info_vivo}\n\n" if info_vivo else "\n"
        jugs = df_jugadores[df_jugadores["Equipo"] == e["Equipo"]].sort_values("Rating", ascending=False).head(6)
        lista_jugs = "\n".join(
            f"  - **{r['Jugador']}** ({r['Posicion']}): {r['Goles']} goles, {r['Asistencias']} asistencias, Rating **{r['Rating']}**"
            for _, r in jugs.iterrows()
        )
        return (
            prefijo
            + f"### 🛡️ Informe y Resultados en Vivo: **{e['Equipo']}** ({e['Liga']})\n"
            f"{bloque_vivo}"
            f"- **Director Técnico**: {e['Entrenador']} | **Esquema Base**: `{e['Esquema']}` | **Estadio**: {e['Estadio']}\n"
            f"- **Rendimiento en Liga**: **{e['Pts']} puntos** en {e['PJ']} PJ (**{e['G']}G - {e['E']}E - {e['P']}P**) | **Racha**: `{e['Racha']}`\n"
            f"- **Balance Goleador**: **{e['GF']} goles a favor** ({e['xG_Favor']} $xG$) y **{e['GC']} en contra** ({e['xG_Contra']} $xGA$) → Diferencia: **{e['DG']:+d}**\n\n"
            f"**🌟 Jugadores Referentes del Club:**\n{lista_jugs or '  - Plantilla general en seguimiento.'}"
        )

    # 4b. Consultas sobre partidos de hoy / resultados de la jornada
    if any(p in q_norm for p in ["partidos de hoy", "resultados de hoy", "quien jugo hoy", "marcadores", "jornada de hoy"]):
        partidos_hoy = obtener_partidos_jornada_vivo()
        if partidos_hoy:
            lineas_p = ["### ⚽ Marcadores en Vivo de la Jornada (Football-Data.org)\n"]
            for p in partidos_hoy[:12]:
                marc = (
                    f"**{p['goles_local']} - {p['goles_visitante']}** ({p['estado']})"
                    if p["goles_local"] is not None
                    else f"*Programado* ({p['estado']})"
                )
                lineas_p.append(f"- **[{p['fecha']} | {p['competencia']}]** {p['local']} vs {p['visitante']}: {marc}")
            return prefijo + "\n".join(lineas_p)

    # 5. Consultas sobre Noticias / Fichajes / Última hora
    if any(p in q_norm for p in ["noticia", "noticias", "actualidad", "fichaje", "fichajes", "ultima hora", "titulares", "hoy", "novedades"]):
        lineas = ["### 📰 Boletín de Noticias y Actualidad del Fútbol Europeo\n"]
        for _, r in df_noticias.head(6).iterrows():
            lineas.append(
                f"- **[{r['Competencia']}] {r['Titular']}**\n"
                f"  *{r['Resumen']}* — `{r['Fuente']} ({r['Fecha']})`"
            )
        return prefijo + "\n".join(lineas)

    # 6. Consultas de Rankings: Goleadores, Asistidores, Valor de Mercado, Porteros, Defensas, Mediocampistas
    df_j_sub = df_jugadores[df_jugadores["Liga"] == liga_det] if liga_det else df_jugadores
    titulo_ambito = f"en {liga_det}" if liga_det else "en las 5 Grandes Ligas Europeas"

    if any(p in q_norm for p in ["goleador", "goleadores", "goles", "pichichi", "bota de oro", "anotador"]):
        top = df_j_sub.sort_values(["Goles", "Asistencias"], ascending=False).head(8)
        filas = "\n".join(
            f"| {i+1} | **{r['Jugador']}** | {r['Equipo']} ({r['Liga']}) | **{r['Goles']}** | {r['xG']} | {r['Asistencias']} | {r['Rating']} |"
            for i, (_, r) in enumerate(top.iterrows())
        )
        return (
            prefijo
            + f"### ⚽ Ranking de Máximos Goleadores {titulo_ambito}\n\n"
            f"| # | Jugador | Club (Liga) | Goles | xG | Asist. | Rating |\n"
            f"| :-: | :--- | :--- | :-: | :-: | :-: | :-: |\n{filas}"
        )

    if any(p in q_norm for p in ["asistencia", "asistencias", "asistidor", "asistidores", "pases clave", "creador", "creadores"]):
        top = df_j_sub.sort_values(["Asistencias", "Pases_Clave_90"], ascending=False).head(8)
        filas = "\n".join(
            f"| {i+1} | **{r['Jugador']}** | {r['Equipo']} ({r['Liga']}) | **{r['Asistencias']}** | {r['xA']} | {r['Pases_Clave_90']} | {r['Rating']} |"
            for i, (_, r) in enumerate(top.iterrows())
        )
        return (
            prefijo
            + f"### 🎯 Líderes en Asistencias y Creación de Juego {titulo_ambito}\n\n"
            f"| # | Jugador | Club (Liga) | Asistencias | xA | Pases Clave/90 | Rating |\n"
            f"| :-: | :--- | :--- | :-: | :-: | :-: | :-: |\n{filas}"
        )

    if any(p in q_norm for p in ["caro", "caros", "valor", "mercado", "valioso", "valiosos", "millones", "precio"]):
        top = df_j_sub.sort_values(["Valor_Mercado_M", "Rating"], ascending=False).head(8)
        filas = "\n".join(
            f"| {i+1} | **{r['Jugador']}** | {r['Equipo']} | {r['Edad']} años | **€{r['Valor_Mercado_M']}M** | {r['Goles']}G / {r['Asistencias']}A | {r['Rating']} |"
            for i, (_, r) in enumerate(top.iterrows())
        )
        return (
            prefijo
            + f"### 💰 Jugadores Más Valiosos del Mercado {titulo_ambito}\n\n"
            f"| # | Jugador | Club | Edad | Valor de Mercado | Producción | Rating |\n"
            f"| :-: | :--- | :--- | :-: | :-: | :-: | :-: |\n{filas}"
        )

    if any(p in q_norm for p in ["tabla", "posiciones", "clasificacion", "lider", "lideres", "equipos", "liga"]) or liga_det:
        df_e_sub = df_equipos[df_equipos["Liga"] == liga_det] if liga_det else df_equipos
        top_e = df_e_sub.sort_values(["Pts", "DG"], ascending=False).head(10)
        filas = "\n".join(
            f"| {i+1} | **{r['Equipo']}** | {r['Liga']} | {r['PJ']} | {r['G']}-{r['E']}-{r['P']} | {r['GF']}:{r['GC']} ({r['DG']:+d}) | **{r['Pts']}** | {r['xG_Favor']} |"
            for i, (_, r) in enumerate(top_e.iterrows())
        )
        return (
            prefijo
            + f"### 🏆 Clasificación y Rendimiento de Equipos {titulo_ambito}\n\n"
            f"| # | Equipo | Liga | PJ | G-E-P | GF:GC (DG) | Pts | xG Favor |\n"
            f"| :-: | :--- | :--- | :-: | :-: | :-: | :-: | :-: |\n{filas}"
        )

    # 7. Saludos / Ayuda / Respuesta general inteligente
    top_3_cracks = df_jugadores.sort_values("Rating", ascending=False).head(4)
    resumen_cracks = ", ".join(f"**{r['Jugador']}** ({r['Equipo']}, Rating {r['Rating']})" for _, r in top_3_cracks.iterrows())
    return (
        prefijo
        + "Soy **Fútbol IA Scout**, tu analista inteligente de fútbol europeo conectado a nuestra base de **Jugadores, Equipos, Partidos en Vivo y Noticias**.\n\n"
        f"- 🌟 **Jugadores con mejor índice actual**: {resumen_cracks}.\n"
        "- 💡 **Ejemplos de consultas que puedes hacerme ahora mismo**:\n"
        "  1. **Partidos en vivo / Resultados**: *«¿Cuánto quedó el Madrid hoy?»* o *«¿Contra quién juega su próximo partido el Barcelona?»*\n"
        "  2. **Comparar estrellas**: *«Compara a Lamine Yamal con Vinícius»* o *«Mbappé vs Haaland»*\n"
        "  3. **Simular partidos con IA**: *«Pronóstico Real Madrid vs Liverpool»*\n"
        "  4. **Rankings y Tablas**: *«¿Quiénes son los máximos goleadores?»* o *«Tabla de posiciones de la Premier League»*\n"
        "  5. **Actualidad**: *«¿Cuáles son las últimas noticias de fútbol?»*"
    )


def responder_consulta_futbol_ia(
    consulta: str,
    df_jugadores: pd.DataFrame,
    df_equipos: pd.DataFrame,
    df_noticias: pd.DataFrame,
    proveedor: str = "auto",
    api_key_usuario: str = "",
    estilo: str = "tactico",
    liga_filtro: str = "todas",
    historial: list[dict] | None = None,
) -> tuple[str, str]:
    """
    Orquesta la respuesta del Chatbot de Fútbol IA:
    - Construye el contexto RAG con datos verificados y resultados en vivo de Football-Data.org.
    - Si hay API Key válida (Google Gemini o Groq), consulta el LLM en la nube con RAG.
    - Si no hay API Key o el usuario eligió el motor local, ejecuta el Analista Estadístico Local.
    Retorna: (respuesta_markdown, etiqueta_motor_usado)
    """
    historial = historial or []
    contexto_rag = construir_contexto_rag(consulta, df_jugadores, df_equipos, df_noticias, liga_filtro, historial)

    # Resolver API key desde el input de la UI o variables de entorno
    key_limpia = (api_key_usuario or "").strip()
    gemini_key = key_limpia if proveedor == "gemini" and key_limpia else os.environ.get("GEMINI_API_KEY", "")
    groq_key = key_limpia if proveedor == "groq" and key_limpia else os.environ.get("GROQ_API_KEY", "")

    if proveedor == "auto" and key_limpia:
        if key_limpia.startswith("gsk_"):
            groq_key = key_limpia
        else:
            gemini_key = key_limpia

    # 1. Intentar Google Gemini si corresponde
    if proveedor in ("gemini", "auto") and gemini_key:
        ok, resp = llamar_gemini_api(gemini_key, consulta, contexto_rag, estilo, historial)
        if ok:
            return resp, "Google Gemini IA + RAG 🟢"

    # 2. Intentar Groq API si corresponde
    if proveedor in ("groq", "auto") and groq_key:
        ok, resp = llamar_groq_api(groq_key, consulta, contexto_rag, estilo, historial)
        if ok:
            return resp, "Groq Llama 3.3 70B + RAG 🟢"

    # 3. Respaldo / Motor Analítico Local RAG
    respuesta_local = generar_respuesta_analitica_local(
        consulta=consulta,
        df_jugadores=df_jugadores,
        df_equipos=df_equipos,
        df_noticias=df_noticias,
        estilo=estilo,
        liga_filtro=liga_filtro,
        historial=historial,
    )
    return respuesta_local, "Motor IA Local RAG + Vivo 🔵"

