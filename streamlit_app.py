# Version_1
import streamlit as st
from PyPDF2 import PdfReader
from openai import OpenAI

# Saisie de la clé API dans la barre latérale
st.sidebar.header("Paramètres")
api_key = st.sidebar.text_input(
    "Entrez votre clé API openAI : sk-..",
    type="password",  # Masque la clé
    help="Saisissez votre clé API ici pour l'utiliser dans l'application."
)


# Fonction pour extraire du texte d'un PDF
def extract_text_from_pdf(pdf_file):
    loader = PdfReader(pdf_file)    

    # Collect text from pdf
    text = ""
    for page in loader.pages:
            text += page.extract_text()
    return text

def fetch_cv():
    return st.text_input("cv", "resume")

# Fonction pour récupérer et analyser une fiche de poste
def fetch_job_posting(url):
    response = st.text_input("Fiche de poste", "Fiche de poste")
    return response

# Fonction pour générer une lettre de motivation
def generate_cover_letter(cv_text, job_text, language, client):
    prompt = (
        f"Using the following CV:\n{cv_text}\n\n"
        f"And this job posting:\n{job_text}\n\n"
        f"Write a cover letter in {language}."
    )
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="gpt-4o",
    )

    return chat_completion.choices[0].message.content

# Interface Streamlit
st.markdown("""
# 📝 Générateur de lettre de motivation
1. Chargez votre CV
2. Puis, la fiche de poste
3. Ajouter des informations pertinentes
4. Choisir la langue
Et voila !!
"""
)
# Étape 1 : Chargement du CV
uploaded_cv = st.file_uploader("Chargez votre CV en PDF", type="pdf")

# Étape 2 : Lien de la fiche de poste
job_posting_url = st.text_input("Entrez un descriptif du poste")

# Étape 3 : Choix de la langue
language = st.radio("Choisissez la langue de la lettre", ["français", "anglish"])

def run_generation(api_key) :

    client = OpenAI(
        api_key=api_key,  # This is the default and can be omitted
    )
    generate_button = st.button("Générer la lettre de motivation")

    if generate_button:
        if uploaded_cv and job_posting_url:
            try:
            # Extraction du texte du CV
            #cv_text = extract_text_from_pdf(uploaded_cv)
                cv_text = extract_text_from_pdf(uploaded_cv)

            # Récupération de la fiche de poste
                job_text = fetch_job_posting(job_posting_url)

            # Génération de la lettre
                cover_letter = generate_cover_letter(cv_text, job_text, language, client)

            # Affichage du résultat
                st.subheader("Lettre de Motivation Générée")
                st.text_area("Votre lettre :", cover_letter, height=300)
            except Exception as e:
                st.error(f"Une erreur est survenue : {e}")
        else:
            st.warning("Veuillez charger un CV et fournir un lien valide.")

# Affichage conditionnel si la clé API est fournie
if api_key:
    st.success("Clé API enregistrée avec succès !")
    # Utilisez ici la clé API pour appeler un service, par exemple :
    run_generation(api_key)
    
else:
    st.warning("Veuillez saisir votre clé API dans la barre latérale.")

