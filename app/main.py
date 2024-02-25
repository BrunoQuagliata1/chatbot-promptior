from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from app.vector_db import query_vector_db, vectorize_text
from openai import OpenAI

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')

client = OpenAI(api_key=openai_api_key)
app = FastAPI()

class Question(BaseModel):
    question: str

def generate_response(question, documents):
    messages = [
        {"role": "system", "content": "You are a knowledgeable assistant."},
        {"role": "user", "content": question}
    ]
    
    if documents:
        messages.append({"role": "assistant", "content": f"Relevant Information: {documents}"})
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    
    if response and response.choices:
        answer_text = response.choices[0].message.content.strip()
        return answer_text
    else:
        return "Sorry, I couldn't generate a response."
    
@app.get("/")
async def healthcheck():
    return {"status": "ok"}


@app.post("/ask")
async def ask_question(question: Question):
    vector_question = vectorize_text(question.question)
    documents = query_vector_db(vector_question)
    response = generate_response(question.question, documents)
    
    return {"response": response}
