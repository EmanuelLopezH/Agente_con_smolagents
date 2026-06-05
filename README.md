# 🐍 Tutor de IA Pedagógico para Python (Local-First)

Este proyecto implementa un **Agente Inteligente Pedagógico** diseñado para ayudar a estudiantes a aprender Python. A diferencia de los calificadores automáticos tradicionales o asistentes comerciales (que entregan la respuesta directa), este agente utiliza la técnica de **Andamiaje Educativo (Scaffolding)**. 

Está construido sobre el framework `smolagents` de Hugging Face y utiliza una arquitectura **ReAct (Reasoning & Acting)** conectada a un modelo LLM local (`Qwen2.5:7b` vía Ollama), garantizando total privacidad de los datos y ejecución sin costo de APIs.

---

## 📂 Estructura del Proyecto

El repositorio está organizado de la siguiente manera:

```text
📦 raiz_del_proyecto/
 ┣ 📂 __pycache__/            # Archivos compilados de Python
 ┣ 📂 tools/                  # Herramientas adicionales o dependencias modulares
 ┣ 📜 app.py                  # Lógica central del agente y definición de herramientas
 ┣ 📜 prompts.yaml            # Configuración del "System Prompt" y reglas del agente
 ┣ 📜 Gradio_UI.py            # Interfaz gráfica de usuario basada en Gradio
 ┣ 📜 python_fundamentals.pdf # Libro de texto/diapositivas para el sistema RAG
 ┣ 📜 requirements.txt        # Dependencias de Python (smolagents, PyPDF2, gradio, etc.)
 ┗ 📜 agent.json              # Configuración persistente o metadatos del agente
```

### Descripción de Archivos Clave

* **`app.py`**: Es el "motor" del proyecto. Aquí se inicializa el framework `smolagents`, se configura la conexión al modelo local de Ollama y se programan las funciones que actúan como herramientas del agente (como `evaluate_student_code` para el entorno seguro de ejecución y `search_python_theory` para el RAG progresivo).
* **`prompts.yaml`**: Es el "cerebro pedagógico". Contiene el *System Prompt* con reglas críticas que obligan al modelo a no dar la respuesta directa, aislar el entorno de memoria durante la evaluación de código y mantener un formato de salida estricto para evitar errores de sintaxis (*parsing errors*).
* **`python_fundamentals.pdf`**: Base de conocimientos estática. El agente la lee localmente para extraer la teoría oficial del curso antes de responder dudas conceptuales.

---

## 🚀 Requisitos Previos

Para garantizar la privacidad y ejecución local, este proyecto requiere **Ollama**.

1. Descarga e instala [Ollama](https://ollama.com/).
2. Abre tu terminal y descarga el modelo utilizado por el agente:
   ```bash
   ollama run qwen2.5:7b
   ```

---

## 🛠️ Instalación y Ejecución

**Paso 1: Clonar el repositorio y preparar el entorno**
Abre la terminal en la carpeta del proyecto e instala las dependencias necesarias:
```bash
pip install -r requirements.txt
```

**Paso 2: Ejecutar el Agente**

Puedes interactuar con el agente de dos maneras:

* **Opción A: Interfaz Gráfica (Recomendada)**
  Ejecuta el archivo de la interfaz web. Esto levantará un servidor local de Gradio amigable para el estudiante.
  ```bash
  python Gradio_UI.py
  ```

* **Opción B: Línea de Comandos (Modo Debug/Desarrollo)**
  Si deseas ver los logs internos del ciclo de razonamiento (Thought -> Code -> Observation), ejecuta el archivo principal:
  ```bash
  python app.py
  ```

---

## ✨ Características Principales

* **Ejecución Segura (Sandbox):** El agente evalúa el código de los alumnos en un entorno aislado sin comprometer la máquina anfitriona.
* **Búsqueda RAG en 4 Niveles:** Busca en el material del curso utilizando coincidencia de índice, estricta, relajada o intersección de palabras clave para superar las limitaciones clásicas de lectura de PDFs.
* **Prevención de Plagio Asistido:** Restricciones sistémicas para guiar, sugerir y explicar, evitando escribir el código solucionado por el alumno.
