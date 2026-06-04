from smolagents import CodeAgent,DuckDuckGoSearchTool, HfApiModel,load_tool,tool
import datetime
import requests
import pytz
import yaml
from tools.final_answer import FinalAnswerTool

from Gradio_UI import GradioUI

@tool
def evaluar_codigo_python(codigo_estudiante: str) -> str:
    """
    Ejecuta el código Python proporcionado por el estudiante y devuelve la salida o los errores.
    Útil para probar si la lógica del estudiante funciona correctamente.
    
    Args:
        codigo_estudiante: El código fuente en Python que se va a ejecutar.
    """
    # Redirigimos la salida estándar para capturar los 'prints' y evitar que se impriman en la consola del servidor
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    
    entorno_local = {}
    
    try:
        # Ejecutamos el código en un entorno aislado (a nivel de variables)
        exec(codigo_estudiante, entorno_local)
        salida = redirected_output.getvalue()
        
        if not salida:
            return "✅ El código se ejecutó sin errores sintácticos, pero no produjo ninguna salida (no hay prints)."
        else:
            return f"✅ Ejecución exitosa. Salida del código:\n{salida}"
            
    except Exception as e:
        # Capturamos errores de sintaxis, indentación, lógica, etc.
        return f"❌ Error al ejecutar el código: {type(e).__name__}: {str(e)}"
    finally:
        # Restauramos la salida estándar
        sys.stdout = old_stdout


@tool
def buscar_teoria_python(concepto: str, ruta_pdf: str = "fundamentos_python.pdf") -> str:
    """
    Busca información teórica sobre fundamentos de Python dentro del libro de texto del curso (PDF).
    Útil cuando el estudiante pide explicar un concepto teórico (ej. qué es una lista, un ciclo for, etc.).
    
    Args:
        concepto: El término clave o concepto que el estudiante quiere aprender o repasar.
        ruta_pdf: (Opcional) La ruta local al archivo PDF. Por defecto es 'fundamentos_python.pdf'.
    """
    try:
        resultados = []
        # Expresión regular para buscar la palabra completa (ignorando mayúsculas/minúsculas)
        patron = re.compile(r'\b' + re.escape(concepto) + r'\b', re.IGNORECASE)
        
        with open(ruta_pdf, 'rb') as archivo:
            lector_pdf = PyPDF2.PdfReader(archivo)
            
            # Recorremos todas las páginas del PDF
            for num_pagina, pagina in enumerate(lector_pdf.pages):
                texto_pagina = pagina.extract_text()
                
                if texto_pagina and patron.search(texto_pagina):
                    # Extraemos un fragmento alrededor de la coincidencia para dar contexto
                    lineas = texto_pagina.split('\n')
                    for i, linea in enumerate(lineas):
                        if patron.search(linea):
                            # Tomamos la línea anterior, la actual y la siguiente como contexto
                            inicio = max(0, i - 2)
                            fin = min(len(lineas), i + 3)
                            contexto = " ".join(lineas[inicio:fin])
                            resultados.append(f"Página {num_pagina + 1}: ...{contexto}...")
                            break # Solo tomamos la primera coincidencia por página para no saturar
                            
                # Limitamos a 3 resultados para no exceder el límite de tokens del LLM
                if len(resultados) >= 3:
                    break
                    
        if resultados:
            return f"He encontrado la siguiente información sobre '{concepto}' en el material:\n" + "\n\n".join(resultados)
        else:
            return f"No encontré información específica sobre '{concepto}' en el PDF base. Explícalo basándote en tus conocimientos generales de Python 3."
            
    except FileNotFoundError:
        return f"Error: No se encontró el archivo PDF en la ruta '{ruta_pdf}'. Verifica que esté subido a tu Space de Hugging Face."
    except Exception as e:
        return f"Error al leer el PDF: {str(e)}"


final_answer = FinalAnswerTool()

# If the agent does not answer, the model is overloaded, please use another model or the following Hugging Face Endpoint that also contains qwen2.5 coder:
# model_id='https://pflgm2locj2t89co.us-east-1.aws.endpoints.huggingface.cloud' 

model = HfApiModel(
max_tokens=2096,
temperature=0.5,
model_id='Meta-Llama-3-8B-Instruct',
custom_role_conversions=None,
)


# Import tool from Hub
image_generation_tool = load_tool("agents-course/text-to-image", trust_remote_code=True)

with open("prompts.yaml", 'r') as stream:
    prompt_templates = yaml.safe_load(stream)
    
agent = CodeAgent(
    model=model,
    tools=[evaluar_codigo_python, buscar_teoria_python, final_answer], ## add your tools here (don't remove final answer)
    max_steps=6,
    verbosity_level=1,
    grammar=None,
    planning_interval=None,
    name=None,
    description=None,
    prompt_templates=prompt_templates
)


GradioUI(agent).launch()