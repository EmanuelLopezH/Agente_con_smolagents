import datetime
import io
import os
import re
import sys
import pytz
import yaml
import PyPDF2
from smolagents import CodeAgent, DuckDuckGoSearchTool, HfApiModel, load_tool, tool
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
    Useful when the student asks to explain a theoretical concept (e.g., lists, for loops, dictionaries).
    
    Args:
        concept: The keyword or concept the student wants to learn or review.
        pdf_path: (Optional) The local path to the PDF file. Defaults to 'python_fundamentals.pdf'.
    """
    try:
        results = []
        # Case-insensitive word-boundary regex pattern
        pattern = re.compile(r'\b' + re.escape(concept) + r'\b', re.IGNORECASE)
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Iterate through all pages of the PDF
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                
                if page_text and pattern.search(page_text):
                    # Extract context around the matching keyword
                    lines = page_text.split('\n')
                    for i, line in enumerate(lines):
                        if pattern.search(line):
                            # Take two lines before and after for surrounding context
                            start = max(0, i - 2)
                            end = min(len(lines), i + 3)
                            context = " ".join(lines[start:end])
                            results.append(f"Page {page_num + 1}: ...{context}...")
                            break # Limit to one match per page to save token space
                            
                # Restrict to a maximum of 3 page results to prevent token limit overflows
                if len(results) >= 3:
                    break
                    
        if results:
            return f"Found the following information about '{concept}' in the course materials:\n" + "\n\n".join(results)
        else:
            return f"No specific information about '{concept}' found in the reference PDF. Please explain using your general Python 3 knowledge."
            
    except FileNotFoundError:
        return f"Error: The PDF file was not found at '{pdf_path}'. Please ensure it is uploaded to your Hugging Face Space."
    except Exception as e:
        return f"Error reading the PDF: {str(e)}"


# Define the final answer tool
final_answer = FinalAnswerTool()

# Model configuration using Qwen Coder
model = HfApiModel(
    max_tokens=2096,
    temperature=0.5,
    model_id="Qwen/Qwen2.5-Coder-32B-Instruct",
    custom_role_conversions=None,
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
    grammar=None,
    planning_interval=None,
    name="PythonTutorAgent",
    description="An AI academic tutor to assist students in mastering Python Programming Fundamentals.",
    prompt_templates=prompt_templates
)

# Launch the interactive Web UI
if __name__ == "__main__":
    GradioUI(agent).launch()