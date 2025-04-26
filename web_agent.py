import requests
from bs4 import BeautifulSoup
import json
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
from typing import Dict, Any, List, TypedDict
import os
from dotenv import load_dotenv
load_dotenv()
from langchain_groq import ChatGroq

# Define our state schema using Pydantic BaseModel
class InterviewState(BaseModel):
    input: Dict[str, Any]  # Contains: company name, job role, job description
    questions: List[Dict[str, str]] = []  # Fetched questions as a list of dictionaries
    formatted_questions: str = ""  # Readable formatted questions
    final_json: str = ""  # Final structured JSON output

# Define the node functions (not tools) that operate on the state
def fetch_interview_questions(state: InterviewState) -> InterviewState:
    """Fetch interview questions from external URLs."""
    print("Fetcher Agent: Starting to fetch interview questions...")
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
        print(f"Fetcher Agent: Fetching URL: {url}")
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                print(f"Fetcher Agent: Failed to fetch {url} (Status Code: {response.status_code})")
                continue
            soup = BeautifulSoup(response.text, 'html.parser')
            # Example extraction: find all <h2> tags (adjust as needed)
            extracted_questions = soup.find_all('h2')
            print(f"Fetcher Agent: Found {len(extracted_questions)} potential questions.")
            for question in extracted_questions:
                q_text = question.get_text().strip()
                if q_text:
                    questions.append({
                        'question': q_text,
                        'link': url,
                        'type': 'DSA' if 'dsa' in url.lower() else 'HR'
                    })
        except Exception as e:
            print(f"Fetcher Agent: Exception occurred while fetching {url}: {e}")
    state.questions = questions
    print("Fetcher Agent: Finished fetching questions.")
    return state
def filter_requests_on_user_query(dsa_question: dict , wed_question:dict,user_query : str):
    
    # Initialize the Groq chat model
    chat = ChatGroq(temperature=0.1, model="llama-3.3-70b-versatile")
    
    # Create a prompt template
    prompt = ChatPromptTemplate.from_template("""
    Given the following sets of interview questions and a user query, filter and modify the questions to best match the user's request. Return the result as a JSON object.

    DSA Questions: {dsa_questions}
    Web Questions: {web_questions}
    User Query: {user_query}

    Instructions:
    1. Select relevant questions from both sets based on the user query.
    2. Modify questions if necessary to better fit the user's needs.
    3. Ensure the output is a valid JSON object with 'dsa_questions' and 'web_questions' as keys.
    4. Limit the total number of questions to 10 (5 for each category if possible).

    Return only the JSON object with the filtered and modified questions.
    """)

    # Create the parser
    parser = JsonOutputParser()

    # Create the chain
    chain = prompt | chat | parser

    # Invoke the chain
    result = chain.invoke({
        "dsa_questions": json.dumps(dsa_questions),
        "web_questions": json.dumps(web_questions),
        "user_query": user_query
    })
    
    return json.dumps(result,indent=2)
    
    
def format_questions(state: InterviewState) -> InterviewState:
    """Format interview questions from JSON to a readable text format."""
    print("Formatter Agent: Formatting questions...")
    formatted_questions = []
    for q in state.questions:
        formatted_questions.append(f"Question: {q['question']}\nLink: {q['link']}\nType: {q['type']}\n")
    state.formatted_questions = "\n".join(formatted_questions)
    print("Formatter Agent: Formatting complete.")
    return state

def create_json(state: InterviewState) -> InterviewState:
    """Create structured JSON output from the formatted questions."""
    print("JSON Creator Agent: Creating structured JSON...")
    state.final_json = json.dumps(state.questions, indent=4)
    print("JSON Creator Agent: JSON creation complete.")
    return state

def check_output_and_answer(parsed_json,job_role="Software Engineer",company_name="Google",job_description="Responsible for developing scalable software solutions."):
    """
    Validates and enhances JSON output from Groq Llama model.
    
    Args:
        parsed_json: The JSON object to validate
        
    Returns:
        Modified and validated JSON object
    """
    from groq import Groq
    import json
    
    # Initialize Groq client
    client = Groq()
    model = "llama-3.3-70b-versatile" 
    
    # Prepare the validation prompt
    validation_prompt = f"""
As an AI assistant specializing in interview question validation, your task is to analyze and improve the following JSON output containing interview questions:

{json.dumps(parsed_json, indent=2)}

Please perform the following actions:

1. Validate the JSON structure and fix any syntax issues.
2. For each question, evaluate and ensure:
   a. It is appropriate and relevant for the job role of {job_role}.
   b. It is relevant to the company {company_name}.
   c. It has clear meaning and purpose in an interview context.
   d. It is not redundant with other questions in the set.

3. Modify, improve, or remove questions based on the following criteria:
   a. If a question is irrelevant to the job role or company, either remove it or modify it to be relevant.
   b. If a question lacks clear meaning, rephrase it to be more specific and purposeful.
   c. If a question is too generic, tailor it to the specific job role or company.
   d. Ensure a mix of technical and soft skill questions appropriate for {job_role} at {company_name}.

4. Add any crucial questions that might be missing, considering the job description: "{job_description}"

5. Maintain the original structure of the JSON, including the 'question', 'link', and 'type' fields for each entry.

6. Limit the total number of questions to a maximum of 15, prioritizing the most relevant and insightful ones.

Return only a valid JSON object with the improved and curated list of interview questions. Each question should be meaningful, relevant, and appropriate for the specified job role and company.
"""

    
    # Set up response format to ensure JSON output
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a JSON validation assistant. Only respond with valid JSON."},
                {"role": "user", "content": validation_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        
        # Parse the validated JSON
        validated_json = json.loads(response.choices[0].message.content)
        return validated_json
    
    except Exception as e:
        # If validation fails, attempt to fix the structure
        try:
            # Try to fix common JSON issues
            if isinstance(parsed_json, str):
                parsed_json = json.loads(parsed_json)
            
            # Remove any invalid fields (example implementation)
            if isinstance(parsed_json, dict):
                # Filter out any fields with None values or empty strings
                cleaned_json = {k: v for k, v in parsed_json.items() if v is not None and v != ""}
                return cleaned_json
            else:
                return parsed_json
        except:
            # If all else fails, return an error message as JSON
            return {"error": "Invalid JSON structure", "original": str(parsed_json)}

    

# Build the workflow using LangGraph with our InterviewState schema
workflow = StateGraph(InterviewState)
workflow.add_node("fetcher", fetch_interview_questions)
workflow.add_node("formatter", format_questions)
workflow.add_node("json_creator", create_json)

workflow.add_edge("fetcher", "formatter")
workflow.add_edge("formatter", "json_creator")
workflow.add_edge("json_creator", END)

workflow.set_entry_point("fetcher")


# if __name__ == "__main__":
#     company_name = "Google"
#     job_role = "Software Engineer"
#     job_description = "Responsible for developing scalable software solutions."

#     print("Starting the multi-agent execution workflow...")

#     # Initialize the state with input data
#     initial_state = InterviewState(input={
#         "company_name": company_name,
#         "job_role": job_role,
#         "job_description": job_description
#     })

#     # Execute the workflow
#     app = workflow.compile()
#     result = app.invoke(initial_state)

#     # Access the final_json directly from the result dictionary
#     #print("\nFinal Output JSON:\n", result['final_json'])
    
#     # Optionally, you can also pretty-print the JSON for better readability
#     try:
#         parsed_json = json.loads(result['final_json'])
#         #print("\nPretty Printed JSON:")
#         #print(json.dumps(parsed_json, indent=2))
#     except json.JSONDecodeError:
#         print("Could not parse the final_json as valid JSON")
#     print(check_output_and_answer(parsed_json))
