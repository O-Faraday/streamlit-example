import streamlit as st
from PyPDF2 import PdfReader
from openai import OpenAI
import re

# Initialisation des états
if "interview_clicked" not in st.session_state:
    st.session_state.interview_clicked = False

if "analyse_clicked" not in st.session_state:
    st.session_state.analyse_clicked = False

if "questions_generated" not in st.session_state:
    st.session_state.questions_generated = False

if "resume_answers" not in st.session_state:
    st.session_state.resume_answers = []

if "candidate_answers" not in st.session_state:
    st.session_state.candidate_answers = []

# Saisie de la clé API dans la barre latérale
st.sidebar.header("Context")
api_key = st.sidebar.text_input(
    "Entrez votre clé API OpenAI :",
    type="password",
    help="Saisissez votre clé API ici pour l'utiliser dans l'application."
)

# Fonction pour extraire du texte d'un PDF
def extract_text_from_pdf(pdf_file):
    loader = PdfReader(pdf_file)
    text = ""
    for page in loader.pages:
        text += page.extract_text()
    return text

# Fonction pour générer une réponse avec OpenAI
def model_answer(client, prompt):
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="gpt-4o",
    )
    return chat_completion.choices[0].message.content

# Interface utilisateur
st.markdown("""
# 📝 Interview Simulator
1. Upload your resume PDF.
2. Load job description.
3. Simulate interview.
4. Generate results.
""")

# Étape 1 : Chargement du CV
uploaded_cv = st.file_uploader("Upload your PDF resume", type="pdf")

# Étape 2 : Lien de la fiche de poste
fiche_de_poste = st.text_input("Job description:")

# Étape 3 : Langue de la lettre de motivation
language = st.radio("Choose cover letter language:", ["Français", "English"])

# Lancement de la génération
def run_generation(api_key):
    client = OpenAI(api_key=api_key)

    if uploaded_cv and fiche_de_poste:
        # Extraction du texte du CV
        resume = extract_text_from_pdf(uploaded_cv)

        # Bouton pour simuler l'interview
        if st.button("Simulate Interview") or st.session_state.interview_clicked:
            st.session_state.interview_clicked = True

            # Prompt pour générer les questions
            prompt_recruiter = f"""
                As an expert recruiter, your job is to prepare an interview for the job described below.
                Prepare 10 questions to assess the candidate's suitability for the role:
                {fiche_de_poste}
            """
            if not st.session_state.questions_generated:
                response_text = model_answer(client=client, prompt=prompt_recruiter)
                questions = re.findall(r"- (.*?)\n", response_text, re.DOTALL)
                st.session_state.questions_generated = True
                st.session_state.questions_list = [q.strip() for q in questions]

            # Afficher les questions et champs de saisie
            st.subheader("Answer the following questions:")
            for i, question in enumerate(st.session_state.questions_list):
                st.write(f"**Question {i + 1}:** {question}")
                candidate_answer = st.text_input(f"Your answer to question {i + 1}:", key=f"candidate_answer_{i}")
                st.session_state.resume_answers.append(f"Response extracted for question {i + 1}")
                st.session_state.candidate_answers.append(candidate_answer)

        # Bouton "Generate Cover Letter"
        if st.session_state.interview_clicked and st.button("Generate Cover Letter") or st.session_state.analyse_clicked:
            st.session_state.analyse_clicked = True
            transcription = "\n".join(
                f"QUESTION: {q}\nRESPONSE: {ra}\nANSWER: {ca}\n"
                for q, ra, ca in zip(
                    st.session_state.questions_list, 
                    st.session_state.resume_answers, 
                    st.session_state.candidate_answers
                )
            )

            # Génération de la lettre de motivation
            cover_letter_prompt = f"""
                Based on the following interview transcription and the candidate's resume, write a compelling cover letter:
                {transcription}
                Resume: {resume}
            """
            st.header("Generated Cover Letter")
            st.write(model_answer(client=client, prompt=cover_letter_prompt))

# Vérifier si la clé API est fournie
if api_key:
    st.success("API key registered!")
    run_generation(api_key)
else:
    st.warning("Please enter your API key in the sidebar.")
