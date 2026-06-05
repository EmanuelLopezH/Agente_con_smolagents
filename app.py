import datetime
import io
import os
import re
import sys
import pytz
import yaml
import PyPDF2
from smolagents import CodeAgent, DuckDuckGoSearchTool, load_tool, tool, OpenAIModel
from tools.final_answer import FinalAnswerTool
from Gradio_UI import GradioUI

@tool
def evaluate_student_code(student_code: str) -> str:
    """
    Executes the Python code provided by the student and returns the stdout or any errors.
    Useful for testing if the student's logic runs correctly.
    
    Args:
        student_code: The Python source code to be executed.
    """
    # Redirect standard output to capture print statements
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    
    local_env = {}
    
    try:
        # Execute the student's code in an isolated local environment dictionary
        exec(student_code, local_env)
        output = redirected_output.getvalue()
        
        if not output:
            return "✅ The code executed successfully without syntax errors, but did not produce any output (no print statements were executed)."
        else:
            return f"✅ Successful execution. Code output:\n{output}"
            
    except Exception as e:
        # Capture syntax errors, indentation errors, runtime exceptions, etc.
        return f"❌ Error executing the code: {type(e).__name__}: {str(e)}"
    finally:
        # Restore standard output
        sys.stdout = old_stdout


@tool
def search_python_theory(concept: str, pdf_path: str = "python_fundamentals.pdf") -> str:
    """
    Searches for academic information about Python fundamentals in the course textbook (PDF).
    Can find specific concepts (e.g., lists, for loops) or provide a general table of contents/summary
    if the concept requested is broad (e.g., 'summary', 'table of contents', 'index', 'python fundamentals').
    
    Args:
        concept: The keyword, concept, or query the student wants to search for (e.g., 'lists', 'summary').
        pdf_path: (Optional) The local path to the PDF file. Defaults to 'python_fundamentals.pdf'.
    """
    try:
        concept_clean = concept.strip().lower()
        
        # --- ESTRATEGIA 1: Petición de Resumen o Tabla de Contenidos ---
        # Si el estudiante (o el agente) busca términos generales, extraemos el inicio del libro.
        summary_keywords = ["summary", "overview", "table of contents", "index", "toc", "introduction", "python fundamentals", "fundamentals", "resumen", "indice", "índice"]
        is_summary_request = any(kw in concept_clean for kw in summary_keywords) or len(concept_clean) < 3
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            if is_summary_request:
                summary_text = []
                # Leemos las primeras 5 páginas (usualmente donde está el índice o la introducción)
                pages_to_read = min(5, num_pages) 
                for page_num in range(pages_to_read):
                    page_text = pdf_reader.pages[page_num].extract_text()
                    if page_text:
                        # Tomamos las primeras 70 líneas de cada página
                        lines = page_text.split('\n')[:70]
                        summary_text.append(f"--- Page {page_num + 1} Index/TOC Section --- \n" + "\n".join(lines))
                
                return (
                    "Here is an overview of the Table of Contents and introductory structure of the textbook:\n\n" + 
                    "\n\n".join(summary_text) + 
                    "\n\nUse this index outline to find specific concepts (e.g., search for 'lists' or 'dictionary' in your next steps)!"
                )
            
            results = []
            
            # --- ESTRATEGIA 2: Búsqueda Estricta (Coincidencia exacta de palabras) ---
            # Busca la palabra o frase exacta respetando los límites de palabras (\b)
            pattern = re.compile(r'\b' + re.escape(concept) + r'\b', re.IGNORECASE)
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if not page_text:
                    continue
                
                if pattern.search(page_text):
                    lines = page_text.split('\n')
                    for i, line in enumerate(lines):
                        if pattern.search(line):
                            start = max(0, i - 2)
                            end = min(len(lines), i + 3)
                            context = " ".join(lines[start:end])
                            results.append(f"Page {page_num + 1}: ...{context}...")
                            break # Solo un resultado por página para no saturar
                if len(results) >= 3:
                    break
            
            # --- ESTRATEGIA 3: Búsqueda Relajada (Substring Match) ---
            # Si no encontró nada exacto, busca ignorando los saltos de línea molestos de los PDFs
            if not results:
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if not page_text:
                        continue
                    
                    if concept_clean in page_text.lower():
                        lines = page_text.split('\n')
                        for i, line in enumerate(lines):
                            if concept_clean in line.lower():
                                start = max(0, i - 2)
                                end = min(len(lines), i + 3)
                                context = " ".join(lines[start:end])
                                results.append(f"Page {page_num + 1} (Fuzzy Match): ...{context}...")
                                break
                    if len(results) >= 3:
                        break
                        
            # --- ESTRATEGIA 4: Búsqueda por Intersección de Palabras Clave ---
            # Si era una frase larga (ej. "funciones recursivas basicas"), la divide y busca las páginas que tengan todas esas palabras
            if not results:
                stopwords = {"a", "an", "the", "in", "of", "to", "for", "with", "on", "at", "by", "about", "and", "or", "is", "are", "el", "la", "los", "las", "un", "una", "de", "en"}
                keywords = [word for word in concept_clean.split() if word not in stopwords and len(word) > 2]
                
                if keywords:
                    for page_num, page in enumerate(pdf_reader.pages):
                        page_text = page.extract_text()
                        if not page_text:
                            continue
                        
                        # Revisa si TODAS las palabras clave están en la página
                        if all(kw in page_text.lower() for kw in keywords):
                            lines = page_text.split('\n')
                            for i, line in enumerate(lines):
                                # Muestra como contexto la línea donde aparece al menos una palabra clave
                                if any(kw in line.lower() for kw in keywords):
                                    start = max(0, i - 2)
                                    end = min(len(lines), i + 3)
                                    context = " ".join(lines[start:end])
                                    results.append(f"Page {page_num + 1} (Keyword Match): ...{context}...")
                                    break
                        if len(results) >= 3:
                            break
                            
            if results:
                return f"Found the following information about '{concept}' in the course materials:\n" + "\n\n".join(results)
            else:
                return f"No specific matches found for '{concept}' in the reference textbook. Please construct an explanation using your general Python 3 knowledge."
                
    except FileNotFoundError:
        return f"Error: The PDF file was not found at '{pdf_path}'. Please ensure it is uploaded and named correctly."
    except Exception as e:
        return f"Error reading the PDF: {str(e)}"

# Define the final answer tool
final_answer = FinalAnswerTool()

# Model configuration using Qwen Coder
# model = HfEngine(
#     max_tokens=2096,
#     temperature=0.5,
#     model_id="Qwen/Qwen2.5-Coder-32B-Instruct",
#     custom_role_conversions=None,
# )
# model = InferenceClientModel(model_id="Qwen/Qwen2.5-7B-Instruct", )
model = OpenAIModel(
    model_id="qwen2.5:7b",
    api_base="http://localhost:11434/v1", # Redirige el tráfico a Ollama en tu PC
    api_key="ollama" # Ollama no pide contraseña real, pero la clase requiere que enviemos algo
)

# Load helper tools (e.g., text-to-image generator from Hub)
image_generation_tool = load_tool("agents-course/text-to-image", trust_remote_code=True)

# Load prompt templates from the local YAML config
with open("prompts.yaml", 'r') as stream:
    prompt_templates = yaml.safe_load(stream)

# Initialize the CodeAgent with the updated English tools
agent = CodeAgent(
    model=model,
    tools=[evaluate_student_code, search_python_theory, final_answer],
    max_steps=6,
    verbosity_level=1,
    prompt_templates=prompt_templates
)
# Launch the interactive Web UI
if __name__ == "__main__":
    GradioUI(agent).launch()