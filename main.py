import logging
from fastapi import FastAPI, HTTPException
import uvicorn

from pydantic import BaseModel
from web_agent import InterviewState, workflow, check_output_and_answer
import json
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Candidate Evaluation API",
    description="API for generating interview questions and evaluating candidate answers",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)



# # Import the router
# from routers.mock_interview_routes import router as candidate_router
# from routers.resume_routers import router as resume_router


class InterviewRequest(BaseModel):
    company_name: str
    job_role: str
    job_description: str
    


class CompanyRequest(BaseModel):
    company_name: str


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create the FastAPI app
app = FastAPI(
    title="Interview Question Search agent",
    description="API for searching for interview and DSA questions online",
    version="1.0.0"
)


@app.get("/", response_description="API Status")
async def root():
    return {"status": "online", "message": "Candidate Evaluation API is running"}

@app.post("/generate_interview_questions")
async def generate_interview_questions(request: InterviewRequest):
    try:
        # Initialize the state with input data
        initial_state = InterviewState(input={
            "company_name": request.company_name,
            "job_role": request.job_role,
            "job_description": request.job_description
        })

        # Execute the workflow
        app = workflow.compile()
        result = app.invoke(initial_state)

        # Parse the JSON result
        parsed_json = json.loads(result['final_json'])

        # Check and validate the output
        validated_json = check_output_and_answer(
            parsed_json,
            job_role=request.job_role,
            company_name=request.company_name,
            job_description=request.job_description
        )

        return validated_json
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_dsa_questions")
async def generate_dsa_questions(request: CompanyRequest) -> dict[str, list[dict]]:
    try:
        with open("dsa.json", "r") as file:
            dsa_data = json.load(file)

        company_name = request.company_name.lower()
        print(f"Looking for company: {company_name}")

        if company_name in dsa_data:
            return {company_name: dsa_data[company_name]}
        else:
            raise HTTPException(status_code=404, detail=f"No DSA questions found for {company_name}")

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    

# Run the application if executed directly
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7070)

