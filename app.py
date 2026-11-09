import os
import tempfile
from pathlib import Path

# Cargar automáticamente las variables de entorno desde el archivo .env si existe
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

# Configuración de Matplotlib antes de importarlo para evitar advertencias en Windows
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "mpl_cache"))

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from shiny import App, render, ui, reactive

from datos_futbol import (
    cargar_equipos,
    cargar_jugadores,
    obtener_noticias_futbol,
)
from motor_ia_futbol import responder_consulta_futbol_ia

matplotlib.use("Agg")

# -----------------------------------------------------------------------------
# 0. Carga de Datos (111 Equipos, 3,082 Jugadores y Noticias)
# -----------------------------------------------------------------------------
DF_EQUIPOS = cargar_equipos()
DF_JUGADORES = cargar_jugadores()
DF_NOTICIAS_INICIAL, _ = obtener_noticias_futbol(intentar_rss_en_vivo=True)

OPCIONES_LIGAS = {
    "todas": "Todas las Ligas",
    "LaLiga": "LaLiga (España)",
    "Premier League": "Premier League (Inglaterra)",
    "Serie A": "Serie A (Italia)",
    "Bundesliga": "Bundesliga (Alemania)",
    "Ligue 1": "Ligue 1 (Francia)",
    "Champions League": "Champions League",
}

OPCIONES_POSICIONES = {
    "todas": "Todas las Posiciones",
    "Delantero": "Delantero",
    "Mediocampista": "Mediocampista",
    "Defensa": "Defensa",
    "Portero": "Portero",
}

# -----------------------------------------------------------------------------
# Mensaje de bienvenida del Chatbot
# -----------------------------------------------------------------------------
MENSAJE_BIENVENIDA = (
    "¡Hola! 👋 Soy tu **Chatbot de Fútbol con IA en Shiny for Python**.\n\n"
    "Tengo conectada la base de datos con **111 equipos**, **más de 3,000 jugadores**, "
    "**estadísticas** y **noticias de fútbol**.\n\n"
    "Puedes preguntarme sobre:\n"
    "- ⚽ **Goleadores y Estadísticas** (ej. *«¿Quiénes son los máximos goleadores?»*)\n"
    "- 🏃 **Jugadores y Comparaciones** (ej. *«Compara a Lamine Yamal con Mbappé»* o *«Datos de Haaland»*)\n"
    "- 🏆 **Equipos y Tablas** (ej. *«Tabla de posiciones de LaLiga»* o *«¿Cómo va el Real Madrid?»*)\n"
    "- 🔮 **Pronósticos de Partidos** (ej. *«Pronóstico Barcelona vs Bayern»*)\n"
    "- 📰 **Noticias** (ej. *«Últimas noticias de fútbol»*)\n\n"
    "¿Qué te gustaría consultar hoy?"
)

# -----------------------------------------------------------------------------
# 1. Interfaz de Usuario (UI) Limpia y Ordenada
# -----------------------------------------------------------------------------
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.h4("⚽ Panel del Chatbot", class_="fw-bold text-primary mb-2"),
        ui.p(
            "Chatbot de fútbol con IA, estadísticas de jugadores, equipos y noticias.",
            class_="text-muted small",
        ),
        ui.input_select(
            "liga_filtro",
            "Seleccionar Liga:",
            OPCIONES_LIGAS,
            selected="todas",
        ),
        ui.input_select(
            "modo_respuesta",
            "Estilo de Respuesta:",
            {
                "comentarista": "😊 Amigable y Dinámico",
                "tactico": "📊 Analítico (Con Estadísticas)",
                "directo": "⚡ Breve (Resumen Rápido)",
            },
            selected="tactico",
        ),
        ui.hr(),
        ui.h6("💡 Preguntas Rápidas:", class_="fw-bold mb-2"),
        ui.input_action_button(
            "btn_q_goleadores",
            "¿Quiénes son los goleadores?",
            class_="btn-outline-primary btn-sm w-100 mb-2",
        ),
        ui.input_action_button(
            "btn_q_comparar",
            "Lamine Yamal vs Mbappé",
            class_="btn-outline-primary btn-sm w-100 mb-2",
        ),
        ui.input_action_button(
            "btn_q_tabla",
            "Tabla de posiciones",
            class_="btn-outline-primary btn-sm w-100 mb-2",
        ),
        ui.input_action_button(
            "btn_q_noticias",
            "Últimas noticias de fútbol",
            class_="btn-outline-secondary btn-sm w-100 mb-3",
        ),
        ui.hr(),
        ui.input_action_button(
            "btn_limpiar",
            "🗑️ Reiniciar Conversación",
            class_="btn-danger btn-sm w-100",
        ),
        width=300,
    ),
    # Encabezado y KPIs superiores
    ui.h3("⚽ Chatbot de Fútbol con IA y Estadísticas", class_="fw-bold mb-2"),
    ui.layout_columns(
        ui.value_box(
            "Equipos Registrados",
            ui.output_text("kpi_equipos"),
            theme="primary",
        ),
        ui.value_box(
            "Jugadores en Base de Datos",
            ui.output_text("kpi_jugadores"),
            theme="success",
        ),
        ui.value_box(
            "Mensajes del Usuario",
            ui.output_text("kpi_turnos"),
            theme="info",
        ),
        col_widths=[4, 4, 4],
        fill=False,
    ),
    # Pestañas ordenadas para Chat, Jugadores, Equipos y Noticias
    ui.navset_card_tab(
        # Pestaña 1: Chat
        ui.nav_panel(
            "💬 Chatbot IA",
            ui.chat_ui(
                id="chat_principal",
                placeholder="Escribe tu pregunta de fútbol aquí (ej. '¿Cuántos goles lleva Raphinha?', 'Tabla de Premier League')...",
                greeting=MENSAJE_BIENVENIDA,
                width="100%",
                height="480px",
                fill=True,
            ),
        ),
        # Pestaña 2: Jugadores
        ui.nav_panel(
            "🏃 Jugadores",
            ui.layout_columns(
                ui.input_select(
                    "posicion_filtro",
                    "Filtrar por Posición:",
                    OPCIONES_POSICIONES,
                    selected="todas",
                ),
                ui.input_text(
                    "buscar_jugador",
                    "Buscar Jugador o Equipo:",
                    placeholder="Ej. Mbappé, Haaland, Real Madrid...",
                ),
                col_widths=[6, 6],
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Top 10 Goleadores (Filtro Actual)", class_="fw-bold"),
                    ui.output_plot("grafico_goleadores", height="360px"),
                ),
                ui.card(
                    ui.card_header("Tabla de Jugadores y Estadísticas", class_="fw-bold"),
                    ui.output_data_frame("tabla_jugadores"),
                ),
                col_widths=[5, 7],
            ),
        ),
        # Pestaña 3: Equipos
        ui.nav_panel(
            "🏆 Equipos",
            ui.layout_columns(
                ui.card(
                    ui.card_header("Top 10 Equipos por Puntos", class_="fw-bold"),
                    ui.output_plot("grafico_equipos", height="360px"),
                ),
                ui.card(
                    ui.card_header("Tabla de Equipos y Posiciones", class_="fw-bold"),
                    ui.output_data_frame("tabla_equipos"),
                ),
                col_widths=[5, 7],
            ),
        ),
        # Pestaña 4: Noticias
        ui.nav_panel(
            "📰 Noticias",
            ui.div(
                ui.input_action_button(
                    "btn_actualizar_noticias",
                    "🔄 Actualizar Noticias",
                    class_="btn-outline-primary btn-sm mb-2",
                ),
            ),
            ui.card(
                ui.card_header("Noticias Recientes de Fútbol", class_="fw-bold"),
                ui.output_data_frame("tabla_noticias"),
            ),
        ),
        id="pestanas",
    ),
    title="Chatbot de Fútbol IA - Shiny",
    fillable=False,
)


# -----------------------------------------------------------------------------
# 2. Lógica del Servidor (Server)
# -----------------------------------------------------------------------------
def server(input, output, session):
    contador_mensajes = reactive.value(0)
    historial_chat = reactive.value([])
    noticias_actuales = reactive.value(DF_NOTICIAS_INICIAL)

    chat = ui.Chat(id="chat_principal")

    # Datos filtrados reactivos
    @reactive.calc
    def equipos_filtrados():
        df = DF_EQUIPOS.copy()
        if input.liga_filtro() != "todas":
            df = df[df["Liga"] == input.liga_filtro()]
        return df.sort_values(["Pts", "DG"], ascending=False)

    @reactive.calc
    def jugadores_filtrados():
        df = DF_JUGADORES.copy()
        if input.liga_filtro() != "todas":
            df = df[df["Liga"] == input.liga_filtro()]
        if input.posicion_filtro() != "todas":
            df = df[df["Posicion"] == input.posicion_filtro()]
        texto_busq = input.buscar_jugador().strip().lower()
        if texto_busq:
            mask = (
                df["Jugador"].astype(str).str.lower().str.contains(texto_busq, na=False)
                | df["Equipo"].astype(str).str.lower().str.contains(texto_busq, na=False)
            )
            df = df[mask]
        return df.sort_values(["Goles", "Rating"], ascending=False)

    # Función para procesar preguntas del usuario en el Chat
    async def responder_consulta(pregunta: str, mostrar_pregunta_usuario: bool = False):
        if mostrar_pregunta_usuario:
            await chat.append_message({"content": pregunta, "role": "user"})

        contador_mensajes.set(contador_mensajes.get() + 1)
        hist = list(historial_chat.get())

        respuesta, _ = responder_consulta_futbol_ia(
            consulta=pregunta,
            df_jugadores=DF_JUGADORES,
            df_equipos=DF_EQUIPOS,
            df_noticias=noticias_actuales.get(),
            proveedor="auto",
            estilo=input.modo_respuesta(),
            liga_filtro=input.liga_filtro(),
            historial=hist,
        )

        hist.append({"role": "user", "content": pregunta})
        hist.append({"role": "assistant", "content": respuesta})
        historial_chat.set(hist[-10:])

        await chat.append_message({"content": respuesta, "role": "assistant"})

    @chat.on_user_submit
    async def _(mensaje_usuario: str):
        await responder_consulta(mensaje_usuario, mostrar_pregunta_usuario=False)

    # Botones de preguntas rápidas
    @reactive.effect
    @reactive.event(input.btn_q_goleadores)
    async def _():
        ui.update_navs("pestanas", selected="💬 Chatbot IA")
        await responder_consulta("¿Quiénes son los máximos goleadores?", mostrar_pregunta_usuario=True)

    @reactive.effect
    @reactive.event(input.btn_q_comparar)
    async def _():
        ui.update_navs("pestanas", selected="💬 Chatbot IA")
        await responder_consulta("Compara a Lamine Yamal con Kylian Mbappé", mostrar_pregunta_usuario=True)

    @reactive.effect
    @reactive.event(input.btn_q_tabla)
    async def _():
        ui.update_navs("pestanas", selected="💬 Chatbot IA")
        liga = input.liga_filtro()
        pregunta = f"Tabla de posiciones de {liga}" if liga != "todas" else "Tabla de posiciones de los mejores equipos"
        await responder_consulta(pregunta, mostrar_pregunta_usuario=True)

    @reactive.effect
    @reactive.event(input.btn_q_noticias)
    async def _():
        ui.update_navs("pestanas", selected="💬 Chatbot IA")
        await responder_consulta("¿Cuáles son las últimas noticias de fútbol?", mostrar_pregunta_usuario=True)

    @reactive.effect
    @reactive.event(input.btn_limpiar)
    async def _():
        await chat.clear_messages()
        contador_mensajes.set(0)
        historial_chat.set([])
        await chat.append_message({"content": MENSAJE_BIENVENIDA, "role": "assistant"})

    @reactive.effect
    @reactive.event(input.btn_actualizar_noticias)
    def _():
        df_nuevas, _ = obtener_noticias_futbol(intentar_rss_en_vivo=True)
        noticias_actuales.set(df_nuevas)

    # KPIs superiores
    @render.text
    def kpi_equipos():
        return f"{len(equipos_filtrados())} equipos"

    @render.text
    def kpi_jugadores():
        return f"{len(jugadores_filtrados())} jugadores"

    @render.text
    def kpi_turnos():
        n = contador_mensajes.get()
        return f"{n} mensaje" if n == 1 else f"{n} mensajes"

    # Gráficos sencillos y limpios
    @render.plot
    def grafico_goleadores():
        df = jugadores_filtrados().head(10).iloc[::-1]
        fig, ax = plt.subplots(figsize=(6, 4))
        if df.empty:
            ax.text(0.5, 0.5, "Sin datos para este filtro", ha="center", va="center")
            return fig

        ax.barh(df["Jugador"], df["Goles"], color="#2563EB", edgecolor="black", alpha=0.8)
        ax.set_title("Top 10 Goleadores", fontsize=11, fontweight="bold")
        ax.set_xlabel("Goles")
        ax.grid(axis="x", linestyle="--", alpha=0.6)
        plt.tight_layout()
        return fig

    @render.plot
    def grafico_equipos():
        df = equipos_filtrados().head(10).iloc[::-1]
        fig, ax = plt.subplots(figsize=(6, 4))
        if df.empty:
            ax.text(0.5, 0.5, "Sin datos para este filtro", ha="center", va="center")
            return fig

        ax.barh(df["Equipo"], df["Pts"], color="#059669", edgecolor="black", alpha=0.8)
        ax.set_title("Puntos por Equipo (Top 10)", fontsize=11, fontweight="bold")
        ax.set_xlabel("Puntos")
        ax.grid(axis="x", linestyle="--", alpha=0.6)
        plt.tight_layout()
        return fig

    # Tablas limpias
    @render.data_frame
    def tabla_jugadores():
        columnas = ["Jugador", "Equipo", "Liga", "Posicion", "Edad", "PJ", "Goles", "Asistencias", "Rating"]
        return render.DataGrid(jugadores_filtrados()[columnas], width="100%", height="360px")

    @render.data_frame
    def tabla_equipos():
        columnas = ["Equipo", "Liga", "Entrenador", "Estadio", "PJ", "G", "E", "P", "GF", "GC", "DG", "Pts"]
        return render.DataGrid(equipos_filtrados()[columnas], width="100%", height="360px")

    @render.data_frame
    def tabla_noticias():
        return render.DataGrid(noticias_actuales.get(), width="100%", height="380px")


# -----------------------------------------------------------------------------
# 3. Inicialización de la Aplicación
# -----------------------------------------------------------------------------
app = App(app_ui, server)

if __name__ == "__main__":
    app.run(port=8000)
