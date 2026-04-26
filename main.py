from fastapi import FastAPI, UploadFile, File, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json, os, csv
from openai import OpenAI

app = FastAPI()
client = OpenAI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATASET_DIR = "datasets"
INCIDENT_FILE = os.path.join(DATASET_DIR, "incidents.json")

def verify_key(x_shiftlore_key: str = Header(None)):
    if x_shiftlore_key != os.getenv("SHIFTLORE_KEY"):
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/incidents")
def get_incidents(x_shiftlore_key: str = Header(None)):
    verify_key(x_shiftlore_key)
    if not os.path.exists(INCIDENT_FILE):
        return {"incidents": []}
    with open(INCIDENT_FILE, "r") as f:
        return {"incidents": json.load(f)}

@app.post("/upload")
async def upload_file(x_shiftlore_key: str = Header(None), file: UploadFile = File(...)):
    verify_key(x_shiftlore_key)
    os.makedirs(DATASET_DIR, exist_ok=True)
    file_path = os.path.join(DATASET_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"status": "uploaded", "path": file_path}

@app.post("/ingest")
def ingest_incidents(x_shiftlore_key: str = Header(None)):
    verify_key(x_shiftlore_key)
    csv_path = os.path.join(DATASET_DIR, "incidents.csv")
    if not os.path.exists(csv_path):
        return {"error": "incidents.csv not found"}
    incidents = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            incidents.append(row)
    with open(INCIDENT_FILE, "w") as f:
        json.dump(incidents, f, indent=2)
    return {"status": "ingested", "count": len(incidents)}

@app.post("/guidance")
def guidance(payload: dict, x_shiftlore_key: str = Header(None)):
    verify_key(x_shiftlore_key)
    operator_input = payload.get("input", "")
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": "You are ShiftLore AMA Guidance."},
            {"role": "user", "content": operator_input}
        ]
    )
    return {"guidance": response.choices[0].message["content"]}
