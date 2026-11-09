# ⚽ Fútbol IA Scout: Chatbot, Estadísticas Avanzadas & Noticias en Shiny

Aplicación interactiva desarrollada con **Shiny for Python** que integra un **Chatbot de Inteligencia Artificial con arquitectura RAG (Retrieval-Augmented Generation)** especializado en el **Fútbol Europeo (LaLiga, Premier League, Serie A, Bundesliga, Ligue 1 y UEFA Champions League)**.

---

## 📁 Estructura del Proyecto

```text
Chatbot_Futbol_IA_Shiny/
├── app.py                  # Interfaz Shiny (4 pestañas: Chat IA, Scouting Radar, Simulador y Noticias)
├── datos_futbol.py         # Base de datos de Jugadores, Equipos, Modelo Poisson y Lector RSS en vivo
├── motor_ia_futbol.py      # Motor Híbrido RAG + Conector Google Gemini / Groq API + Analista IA Local
├── equipos_futbol.csv      # Dataset exportado de clubes europeos (xG, posesión, valor, puntos)
├── jugadores_futbol.csv    # Dataset exportado de jugadores top (goles, xG, xA, regates, pases clave)
├── noticias_futbol.csv     # Feed de noticias deportivas sincronizadas
├── requirements.txt        # Dependencias para ejecución local y Posit Connect Cloud
├── manifest.json           # Manifiesto de despliegue para Posit Connect Cloud
└── README.md               # Documentación de uso y configuración de API Keys
```

---

## ✨ Características Principales

1. **🧠 Motor de Inteligencia Artificial Híbrido (Con o Sin API Key)**:
   - **Google Gemini API (`gemini-2.5-flash`)** y **Groq Cloud API (`llama-3.3-70b-versatile`)**: Puedes pegar tu API Key gratuita en el panel lateral (o definir `GEMINI_API_KEY` / `GROQ_API_KEY` en variables de entorno) para potenciar las respuestas con LLMs en la nube alimentados con nuestro contexto RAG verificado.
   - **Analista IA Local RAG + Poisson (Sin API Key)**: Funciona al 100% de inmediato sin requerir claves externas. Detecta jugadores, apodos, clubes, ligas y métricas, construyendo tablas comparativas cara a cara, fichas de scouting, rankings y pronósticos matemáticos.
2. **🌟 Scouting y Comparador Cara a Cara (Gráfico de Radar)**:
   - Compara cualquier par de estrellas europeas mediante un **Spider Chart (Radar)** de 7 dimensiones y gráfica de **Goles Reales vs Esperados ($xG$)**.
3. **🔮 Simulador Matemático de Partidos (Distribución de Poisson + $xG$)**:
   - Calcula probabilidades de victoria local, empate y visitante, $xG$ proyectado, marcadores exactos más probables y mercados de goles (+2.5 y Ambos Anotan).
4. **📰 Centro de Noticias en Vivo (RSS + Base Analítica)**:
   - Se conecta en tiempo real a feeds RSS de prensa deportiva internacional (*Marca*, *BBC Sport*) con respaldo automático local si no hay conexión a internet.

---

## 🚀 Ejecución Local

```bash
cd "Chatbot_Futbol_IA_Shiny"
python app.py
# o con recarga automática:
shiny run --reload --port 8000 app.py
```

Abre en tu navegador: **`http://127.0.0.1:8000`**

