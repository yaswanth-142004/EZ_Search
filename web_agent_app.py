import streamlit as st
import requests
from typing import Dict, Any, List

def dict_values_to_list(d):
    """
    Convert a dict with integer or stringified integer keys to a list sorted by key.
    Handles both dicts and lists as input.
    """
    if isinstance(d, dict):
        try:
            # Keys may be int or str; sort as int
            return [d[k] for k in sorted(d, key=lambda x: int(x))]
        except Exception:
            return list(d.values())
    return d

def generate_dsa_questions(company_name: str) -> Dict:
    """
    Call the API to generate DSA questions based on company name.
    Sends company_name in request body.
    """
    try:
        payload = {"company_name": company_name}
        response = requests.post("http://localhost:7070/generate_dsa_questions", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching DSA questions: {str(e)}")
        return {"error": str(e)}

def generate_interview_questions(company_name: str, job_role: str, job_description: str) -> Dict:
    """
    Call the API to generate interview questions based on company, role, and description.
    """
    try:
        payload = {
            "company_name": company_name,
            "job_role": job_role,
            "job_description": job_description
        }
        response = requests.post("http://localhost:7070/generate_interview_questions", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching interview questions: {str(e)}")
        return {"error": str(e)}

def display_dsa_questions(data: Dict):
    """
    Display DSA questions in a formatted way, handling dicts with integer keys.
    """
    if "error" in data:
        st.error(f"Could not retrieve data: {data['error']}")
        return

    # Extract the list/dict of questions
    questions = []
    if isinstance(data, dict):
        # Use the first key (e.g., 'paypal')
        if len(data) == 1:
            questions = dict_values_to_list(list(data.values())[0])
        elif "questions" in data:
            questions = dict_values_to_list(data["questions"])
        else:
            # Fallback: try to use the first value
            questions = dict_values_to_list(next(iter(data.values())))
    elif isinstance(data, list):
        questions = data

    for i, q in enumerate(questions, 1):
        question = q.get("question_name", q.get("question", ""))
        difficulty = q.get("difficulty", "")
        subtopics = q.get("subtopics", [])
        link = q.get("question_link", q.get("link", "")).strip()
        # Badge color
        difficulty_color = "green"
        if difficulty.lower() == "medium":
            difficulty_color = "orange"
        elif difficulty.lower() == "hard":
            difficulty_color = "red"
        with st.expander(f"{i}. {question}"):
            col1, col2 = st.columns(2)
            with col1:
                if subtopics:
                    st.markdown(f"**Topics:** {', '.join(subtopics)}")
            with col2:
                if difficulty:
                    st.markdown(f"**Difficulty:** :{difficulty_color}[{difficulty}]")
            if link:
                st.markdown(f"**Problem Link:** [Open]({link})")

def display_interview_questions(data: Dict):
    """
    Display interview questions in a formatted way, handling dicts with integer keys.
    """
    if "error" in data:
        st.error(f"Could not retrieve data: {data['error']}")
        return

    # Extract the list/dict of questions
    questions = []
    if isinstance(data, dict):
        if "interviewQuestions" in data:
            questions = dict_values_to_list(data["interviewQuestions"])
        elif "questions" in data:
            questions = dict_values_to_list(data["questions"])
        else:
            # Fallback: try to use the first value
            questions = dict_values_to_list(next(iter(data.values())))
    elif isinstance(data, list):
        questions = data

    # Group by type
    questions_by_type = {}
    for q in questions:
        q_type = q.get("type", "General")
        questions_by_type.setdefault(q_type, []).append(q)

    for q_type, qs in questions_by_type.items():
        st.subheader(f"{q_type} Questions")
        for i, q in enumerate(qs, 1):
            with st.expander(f"{i}. {q.get('question', '')}"):
                if "link" in q and q["link"]:
                    st.markdown(f"**Reference:** [Learn more]({q['link']})")

def main():
    st.set_page_config(page_title="Interview Questions Generator", 
                       page_icon="💼", 
                       layout="wide")
    st.title("Interview Questions Generator")
    st.markdown("Generate tailored DSA and interview questions based on company and job details.")

    # Input form
    with st.form("input_form"):
        col1, col2 = st.columns(2)
        with col1:
            company_name = st.text_input("Company Name", placeholder="e.g., Google")
        with col2:
            job_role = st.text_input("Job Role", placeholder="e.g., Software Engineer")
        job_description = st.text_area("Job Description", height=150, placeholder="Paste the job description here...")
        submitted = st.form_submit_button("Generate Questions")

    if submitted:
        if not company_name or not job_role or not job_description:
            st.error("Please fill in all fields before submitting.")
        else:
            with st.spinner("Generating questions..."):
                tab1, tab2 = st.tabs(["DSA Questions", "Interview Questions"])
                with tab1:
                    st.subheader("Data Structures & Algorithms Questions")
                    dsa_questions = generate_dsa_questions(company_name)
                    display_dsa_questions(dsa_questions)
                with tab2:
                    st.subheader("Technical & Behavioral Questions")
                    interview_questions = generate_interview_questions(company_name, job_role, job_description)
                    display_interview_questions(interview_questions)

    st.markdown("---")
    with st.expander("How to use this tool"):
        st.markdown("""
        ### How to use this tool:
        1. Enter the company name, job role, and paste the job description
        2. Click 'Generate Questions' to get tailored interview preparation materials
        3. Review both DSA questions specific to the company and custom interview questions based on the job details

        The questions are organized by type and can be expanded for more details.
        """)

if __name__ == "__main__":
    main()
