"""Optional REST API for CSV analysis.
Run separately from Streamlit: uvicorn api:app --reload
"""
import io
# pyright: reportMissingModuleSource=false, reportMissingImports=false
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile

app = FastAPI(title="Smart CSV Analyzer API", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok", "service": "smart-csv-analyzer"}

@app.post("/analyze")
async def analyze_csv(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")

    raw = await file.read()
    if len(raw) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds 20 MB limit")

    try:
        try:
            df = pd.read_csv(io.BytesIO(raw))
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(raw), encoding="latin-1")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid CSV: {exc}")

    missing = df.isna().sum()
    return {
        "file_name": file.filename,
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": [str(c) for c in df.columns],
        "missing_values": {str(k): int(v) for k, v in missing.items()},
        "duplicate_rows": int(df.duplicated().sum()),
    }
