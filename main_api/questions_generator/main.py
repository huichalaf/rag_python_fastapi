from pylatex import Document, Section, Command, Enumerate
import re
import openai
import os
from dotenv import load_dotenv
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def generar_pdf_examen(titulo, instrucciones, preguntas_respuestas, archivo_salida):
    doc = Document(archivo_salida)

    with doc.create(Section(titulo)):
        for instruccion in instrucciones:
            doc.append(instruccion)

        doc.append(Command('vspace', '1em'))

        with doc.create(Section('Preguntas:')):
            with doc.create(Enumerate()) as enum:
                for pregunta in preguntas_respuestas:
                    enum.add_item(pregunta)
                    
    doc.append(Command('vspace', '1em'))
    doc.append("¡Buena suerte en tu examen!")

    doc.generate_pdf(clean_tex=False)

def get_question(prompt):
    model = "gpt-4"
    messages = [{'role': 'user', 'content': prompt}]
    system_message = {'role': 'system', 'content': 'I need you to act as a professor and generate exam questions for my students. I will provide you with the subject, difficulty level, and whether or not to include hints. It is important that all questions are only in the language of the student. Your task is to create only one challenging and relevant question based on these inputs'}
    messages.append(system_message)
    response = openai.ChatCompletion.create(
        model=model,
        messages = messages,
        max_tokens=500,
        temperature=0.9,
    )
    return response.choices[0].message.content

def main(subject, questions, difficulty, hints, user):
    preguntas_separadas = []
    prompt = f"subject: {subject}\ndifficulty: {difficulty}/100\nHints: {hints}"
    for i in range(questions):
        preguntas_separadas.append(get_question(prompt))
    generar_pdf_examen(
        titulo=subject,
        instrucciones=["Answer the following questions in the space provided."],
        preguntas_respuestas=preguntas_separadas,
        archivo_salida=f"tex/{user}_{subject}.pdf"
    )
    #eliminamos los archvivos adicionales al pdf
    os.remove(f"tex/{user}_{subject}.log")
    os.remove(f"tex/{user}_{subject}.aux")
    os.remove(f"tex/{user}_{subject}.tex")
    os.remove(f"tex/{user}_{subject}.out")
    return True

if __name__ == "__main__":
    subject = "Linear Transformations"
    questions = 2
    difficulty = 50
    hints = 'True'
    user = "test"
    main(subject, questions, difficulty, hints, user)