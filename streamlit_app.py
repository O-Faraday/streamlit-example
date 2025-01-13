# VerInstallation des bibliothèques
import streamlit as st
from PyPDF2 import PdfReader
from openai import OpenAI

import re

# Saisie de la clé API dans la barre latérale
st.sidebar.header("Context")
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


def model_answer(client, prompt) :
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

# Function to extract responses and follow-up questions
def extract_response_and_question(text):

    response_match = re.search(r"\*\*RESPONSE:\*\*\s*(.*?)\n\n", text, re.DOTALL)
    response = response_match.group(1).strip() if response_match else "No response found"
        
    # Extract follow-up question
    question_match = re.search(r"\*\*NEW_QUESTION(?:s)?:\*\*\s*(.*?)$", text, re.DOTALL)
    question = question_match.group(1).strip() if question_match else "No follow-up question found"
    
    return response, question

# Interface Streamlit
st.markdown("""
# 📝 Interview simulator
1. Upload your resume pdf
2. Load job description
3. Interview simulator
4. Choose langage
Et voila !!
"""
)

# 1- Preliminaires
# Étape 1 : Chargement du CV
uploaded_cv = st.file_uploader("UpLoad your PDF resume", type="pdf")

# Étape 2 : Lien de la fiche de poste
fiche_de_poste = st.text_input("Job description : ")

# Étape 3 : Choix de la langue
language = st.radio("Choose cover letter langage :", ["Français", "English"])


def run_generation(api_key) :

    # Creattion du client
    client = OpenAI(
        api_key=api_key,  # This is the default and can be omitted
    )
        
    # Verification des la presence des cv et job post    
    if uploaded_cv and fiche_de_poste :
        # Prompt recruiter
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

        try:
            #cv_text = extract_text_from_pdf(uploaded_cv)
            resume = extract_text_from_pdf(uploaded_cv)

            # Déclenechement de l interview
            simulate_interview = st.button("Simulate Interview")

            if simulate_interview :
                # Gereration des questions
                response_text = model_answer(client=client, prompt=prompt_recruiter)
                # Extration dans une liste
                # Extract questions using regex
                questions = re.findall(r"- (.*?)\n", response_text, re.DOTALL)

                # Prepare a list of questions
                questions_list = [q.strip() for q in questions]

                # INTERVUEW
                resume_answers = []
                candidate_answers = []
                for question in questions_list :
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

                    response, question = extract_response_and_question(model_answer(client=client, prompt=question_prompt))
    
                    candidate_answer = st.text_input(label=question)
                    resume_answers.append(response)
                    candidate_answers.append(candidate_answer)

                    # Generate results
                    analyse = st.button("Generate cover letter")
                    if analyse :
                        # Transcription de l'entretien
                        transcription = ""
                        for q, r_a, c_a in zip(questions_list, resume_answers, candidate_answers) :
                            transcription += f"""QUESTION: {q}\nRESPONSE: {r_a}\n{c_a}\n\n"""
                        
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

        except Exception as e:
            st.error(f"Une erreur est survenue : {e}")
 

# Affichage conditionnel si la clé API est fournie
if api_key:
    st.success("Open AI API key registered !")
    # Utilisez ici la clé API pour appeler un service, par exemple :
    run_generation(api_key)
    
else:
    st.warning("Please write your API key in the sidebar.")

