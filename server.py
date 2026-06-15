from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import sys

# Append the current directory so UVR modules can be found
sys.path.append(os.getcwd())

app = FastAPI(title="Ultimate Vocal Remover API")

# Allow React frontend to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "UVR Backend API is running"}

@app.get("/api/models")
def get_models():
    # In a full implementation, we'd import models from gui_data.constants
    # For now, returning dummy data to demonstrate the connection
    return {
        "mdx_net": ["Kim_Vocal_2", "MDX23C-8KFFT-InstVoc", "UVR-MDX-NET-Voc_FT"],
        "vr_arch": ["1_HP-UVR", "2_HP-UVR", "4_HP-Vocal-UVR"],
        "demucs": ["htdemucs", "htdemucs_ft", "mdx_extra"]
    }

class ProcessRequest(BaseModel):
    file_path: str
    process_method: str
    model_name: str

@app.post("/api/process")
def process_audio(request: ProcessRequest):
    # Here we would initialize the UVR processing logic
    # e.g., using separate.py's SeperateMDXC or similar classes
    return {"status": "processing", "details": f"Started {request.process_method} with {request.model_name}"}

if __name__ == "__main__":
    import uvicorn
    # Run the server on port 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)
