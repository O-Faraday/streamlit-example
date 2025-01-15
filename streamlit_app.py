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

# Function to extract responses and follow-up questions
def extract_response_and_question(text):

    response_match = re.search(r"\*\*RESPONSE:\*\*\s*(.*?)\n\n", text, re.DOTALL)
    response = response_match.group(1).strip() if response_match else "No response found"
        
    # Extract follow-up question
    question_match = re.search(r"\*\*NEW_QUESTION(?:s)?:\*\*\s*(.*?)$", text, re.DOTALL)
    question = question_match.group(1).strip() if question_match else "No follow-up question found"
    
    return response, question
    
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
        if st.button("Simulate Interview") :
            st.session_state.interview_clicked = True

            # Prompt pour générer les questions
            prompt_recruiter = (
                f"""As an expert recruiter, your job is to prepare a interview for the job describe in the following paragraph.\n
                You must prepare a bunch of at max 10 questions to measure the suitability of the candidate. \n\n
                {fiche_de_poste}\n\n
                As in the following sample  : \n
                Based on the job description provided for the Data Engineer position at Scania, here are ten interview questions designed to assess the candidate's suitability for the role:

                1. **Experience with PowerBI and Cloud Technologies:**
                - Could you walk us through your experience with PowerBI, both on the Cloud and on Report Server? How have you used PowerBI to deliver insights and what challenges have you faced?

                2. **Data Analytics Solution Development:**
                - Describe a project where you developed data analytics solutions through semantic model building. What was your approach, and what were the outcomes?"
                """
            )

            response_text = model_answer(client=client, prompt=prompt_recruiter)
            questions = re.findall(r"- (.*?)\n", response_text, re.DOTALL)
            questions_list = [q.strip() for q in questions]

            # Afficher les questions et champs de saisie
            st.subheader("Answer the following questions:")
            # INTERVUEW
            resume_answers = []
            #candidate_answers = []
            for i, question in enumerate(questions_list):
                st.write(f"**Question {i + 1}:** {question}")
                question_prompt = f"""
                    You are an interviewer and recruitment expert analyzing a candidate's resume to answer the following question:
                    {question}

                    Refer to the provided candidate resume: {resume}.

                    1- Extract relevant information from the resume to formulate a complete response to the question.
                    Example:
                    Question: "How long have you been teaching physics? To which level?"
                    Resume Excerpt: "Physics Associate Professor  (09/2003 – 08/2016)"
                    Response: "**RESPONSE:** I have been teaching physics for 13 years."

                    2- If the resume lacks sufficient details to answer fully, identify the missing elements and frame a follow-up question for the candidate.
                    Example:
                    Question: "**NEW_QUESTION:** You have been teaching physics to which level?"

                    Your goal is to extract precise answers and draft additional questions to clarify incomplete information.
                    """

                response, question_bis = extract_response_and_question(model_answer(client=client, prompt=question_prompt))
    
                #candidate_answer = st.text_input(label=question, key=f"key_{i}")
                st.write(question)
                st.write(response)
                resume_answers.append(response)
                #candidate_answers.append(candidate_answer)

        # Bouton "Generate Cover Letter"
        if st.button("Generate Cover Letter") :
            st.session_state.analyse_clicked = True
            transcription = ""
            for q, r_a in zip(questions_list, resume_answers) : #, candidate_answers) :
                transcription += f"""QUESTION: {q}\nRESPONSE: {r_a}\n""" #{c_a}\n\n"""
                        
            # Generation des ongletts
            tab1, tab2, tab3 = st.tabs(["Cover letter", "Evaluate candidate", "Evalute questions"])

            with tab1:
                st.header("Generate cover letter")
                cover_letter_prompt = f"""
                        As a senior candidate, imagine an interview where the recruiter asks the following questions, along with your corresponding answers:  
                        {transcription}  

                        Additionally, you have the following resume:  
                        {resume}  

                        Based on this information, write a compelling and concise cover letter that highlights your suitability for the position.  
                        The cover letter should:  
                        - Clearly demonstrate how your skills and experiences align with the job requirements.  
                        - Be impactful and engaging, avoiding generic or overused phrases.  
                        - Showcase your unique value and enthusiasm for the role.  

                        Focus on creating a document that will capture the recruiter's attention and set you apart as the ideal candidate.
                        """
                st.write(model_answer(client=client, prompt=cover_letter_prompt))
            with tab2:
                st.header("Evaluate candidate")
                candidate_evaluation_prompt = f"""
                        As a senior recruiter, imagine an interview where the recruiter asks the following questions, along with thes corresponding answers:  
                        {transcription}  

                        Additionally, you have the following job description :  
                        {fiche_de_poste}  

                        Based on this information, how would you evaluate the candidate :  
                        - Give a numerical evaluation the candidate.  
                        - Pro and cons of the candidacy. 
                        - Do you think there's a need for a second interview ?

                """
                st.write(model_answer(client=client, prompt=candidate_evaluation_prompt))
            with tab3:
                st.header("Evaluate questions")
                questions_evaluation_prompt = f"""
                    As a senior recruiter, imagine an interview where the recruiter asks the following questions :  
                    {transcription}  

                    Additionally, you have the following job description :  
                    {fiche_de_poste}  

                    Based on this information, how would you evaluate the questions :  
                     - Give a numerical evaluation the set of questions.  
                     - How would you improve it?

                    """
                st.write(model_answer(client=client, prompt=questions_evaluation_prompt))

# Vérifier si la clé API est fournie
if api_key:
    st.success("API key registered!")
    run_generation(api_key)
else:
    st.warning("Please enter your API key in the sidebar.")
