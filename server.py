"""
LangServe server for Mental Wellness Agent.
Exposes the multi-agent workflow as a REST API.
"""
import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langserve import add_routes
from pydantic import BaseModel, Field
from graph import app as wellness_graph


class WellnessInput(BaseModel):
    user_input: str = Field(description="What you'd like to talk about")


app = FastAPI(
    title="Mental Wellness Agent",
    version="1.0",
    description="A multi-agent mental wellness support API powered by LangGraph",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.get("/")
def root():
    return {
        "status": "ok",
        "docs": "/docs",
        "playground": "/wellness/playground/",
    }

add_routes(
    app,
    wellness_graph.with_types(input_type=WellnessInput),
    path="/wellness",
)

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
