
import streamlit as st
import requests
import json
from bs4 import BeautifulSoup
from typing import Dict, Any, List
from pydantic import BaseModel
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
import os
from dotenv import load_dotenv
load_dotenv()

# Define our state schema using Pydantic
class InterviewState(BaseModel):
    input: Dict[str, Any]
    questions: List[Dict[str, str]] = []
    formatted_questions: str = ""
    final_json: str = ""

# Fetch interview questions
def fetch_interview_questions(state: InterviewState) -> InterviewState:
    urls = [
        "https://www.geeksforgeeks.org/top-100-data-structure-and-algorithms-dsa-interview-questions-topic-wise/",
        "https://www.indeed.com/career-advice/interviewing/hr-interview-questions",
        "https://www.interviewbit.com/hr-interview-questions/",
        "https://leetcode.com/discuss/general-discussion/459219/blind-75-leetcode-questions",
        "https://www.javatpoint.com/data-structure-interview-questions",
        "https://www.hackerrank.com/interview/interview-preparation-kit",
        "https://www.careerride.com/Interview-Questions.aspx",
        "https://www.toptal.com/interview-questions",
        "https://www.simplilearn.com/tutorials/data-structure-tutorial/data-structure-interview-questions",
        "https://www.educative.io/blog/crack-system-design-interview"
    ]
    questions = []
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                continue
            soup = BeautifulSoup(response.text, 'html.parser')
            extracted_questions = soup.find_all('h2')
            for question in extracted_questions:
                q_text = question.get_text().strip()
                if q_text:
                    questions.append({
                        'question': q_text,
                        'link': url,
                        'type': 'DSA' if 'dsa' in url.lower() else 'HR'
                    })
        except Exception as e:
            print(f"Exception while fetching {url}: {e}")
    state.questions = questions
    return state

# Format questions for display
def format_questions(state: InterviewState) -> InterviewState:
    formatted_questions = []
    for q in state.questions:
        formatted_questions.append(f"Question: {q['question']}\nLink: {q['link']}\nType: {q['type']}\n")
    state.formatted_questions = "\n".join(formatted_questions)
    return state

# Create final JSON
def create_json(state: InterviewState) -> InterviewState:
    state.final_json = json.dumps(state.questions, indent=4)
    return state

# Build the LangGraph workflow
workflow = StateGraph(InterviewState)
workflow.add_node("fetcher", fetch_interview_questions)
workflow.add_node("formatter", format_questions)
workflow.add_node("json_creator", create_json)

workflow.add_edge("fetcher", "formatter")
workflow.add_edge("formatter", "json_creator")
workflow.add_edge("json_creator", END)

workflow.set_entry_point("fetcher")
app_flow = workflow.compile()

# Streamlit App
st.set_page_config(page_title="Interview Questions Generator", page_icon="💼", layout="wide")
st.title("💼 Interview Questions Generator")
st.markdown("Generate DSA + HR questions for interview prep based on company and job role!")

with st.form("input_form"):
    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("Company Name", placeholder="e.g., Google")
    with col2:
        job_role = st.text_input("Job Role", placeholder="e.g., Software Engineer")
    job_description = st.text_area("Job Description", height=150, placeholder="Paste job description here...")
    submitted = st.form_submit_button("Generate Questions")

if submitted:
    if not company_name or not job_role or not job_description:
        st.error("Please fill in all fields.")
    else:
        with st.spinner("🚀 Fetching and preparing questions..."):
            # Run the workflow
            initial_state = InterviewState(input={
                "company_name": company_name,
                "job_role": job_role,
                "job_description": job_description
            })
            result = app_flow.invoke(initial_state)

            # Display final JSON nicely
            try:
                parsed_json = json.loads(result['final_json'])
                st.success("✅ Questions generated successfully!")
                
                tab1, tab2 = st.tabs(["📚 All Questions", "📝 Raw JSON"])

                with tab1:
                    st.subheader("Formatted Interview Questions")
                    for idx, q in enumerate(parsed_json, 1):
                        with st.expander(f"{idx}. {q['question']}"):
                            st.markdown(f"**Type:** {q['type']}")
                            st.markdown(f"**Link:** [Learn More]({q['link']})")

                with tab2:
                    st.subheader("Final JSON Output")
                    st.json(parsed_json, expanded=False)
            except json.JSONDecodeError:
                st.error("❌ Failed to parse the final output as JSON.")
