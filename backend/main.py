"""
Prodnosis Backend — FastAPI starter
====================================
Run it:
    pip install -r requirements.txt
    uvicorn main:app --reload

Then open http://localhost:8000/docs to try every endpoint in your browser.

What this gives you:
  - SQLite database (prodnosis.db, created automatically) storing patients + vitals
  - POST /vitals            -> a wearable (or the frontend) pushes a vitals reading
  - GET  /patients          -> list all patients
  - GET  /patients/{id}/vitals/latest -> most recent reading
  - GET  /patients/{id}/risks -> AI risk assessment (same engine as the frontend)

This is the real foundation the simulated frontend will plug into.
"""

import sqlite3
from contextlib import closing
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

DB = "prodnosis.db"

app = FastAPI(title="Prodnosis API", version="0.1.0")

# Allow the frontend (opened as a local file or hosted on Netlify) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------- database
def init_db() -> None:
    with closing(sqlite3.connect(DB)) as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS patients (
                id      TEXT PRIMARY KEY,
                name    TEXT NOT NULL,
                sex     TEXT,
                age     INTEGER,
                history TEXT
            );
            CREATE TABLE IF NOT EXISTS vitals (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL REFERENCES patients(id),
                ts         TEXT NOT NULL,
                steps      INTEGER,
                hr         INTEGER,
                spo2       INTEGER,
                sleep_hrs  REAL,
                bp_sys     INTEGER,
                bp_dia     INTEGER,
                glucose    INTEGER
            );
            """
        )
        # seed demo patients (INSERT OR IGNORE = only added once)
        con.executemany(
            "INSERT OR IGNORE INTO patients VALUES (?,?,?,?,?)",
            [
                ("manya", "Manya Gupta", "F", 18, "Asthma, Frequent Migraines"),
                ("tanmay", "Tanmay Meena", "M", 35, "Type 2 diabetes, Kidney stones removal"),
                ("ramlal", "Ram Lal", "M", 60, "Type 2 diabetes"),
            ],
        )
        con.commit()


init_db()

# ---------------------------------------------------------------- schemas
class VitalsIn(BaseModel):
    patient_id: str
    steps: int = Field(ge=0)
    hr: int = Field(ge=20, le=250, description="Heart rate, bpm")
    spo2: int = Field(ge=50, le=100, description="Blood oxygen, %")
    sleep_hrs: float = Field(ge=0, le=24)
    bp_sys: int = Field(ge=60, le=260)
    bp_dia: int = Field(ge=30, le=160)
    glucose: int = Field(ge=30, le=500, description="mg/dL")


# ---------------------------------------------------------------- risk engine
# Same transparent rules as the frontend prototype. In production this becomes
# a trained ML model; keeping the interface identical means you can swap it
# in later without changing any endpoint.
def clamp(n, lo, hi):
    return max(lo, min(hi, n))


def tier(pct: int) -> str:
    return "high" if pct >= 55 else "med" if pct >= 30 else "low"


def compute_risks(v: dict) -> list[dict]:
    raw = {
        "Insomnia": (7 - v["sleep_hrs"]) * 14,
        "Type 2 Diabetes": (v["glucose"] - 90) * 0.55,
        "Hypertension": ((v["bp_sys"] - 110) + (v["bp_dia"] - 70)) * 0.9,
        "Respiratory Distress": (97 - v["spo2"]) * 12,
        "Fatigue": (8000 - v["steps"]) / 120 + (7 - v["sleep_hrs"]) * 4,
        "Cardiac Irregularity": (v["hr"] - 68) * 2.2,
    }
    risks = [
        {"name": k, "pct": clamp(round(x), 2, 96)} for k, x in raw.items()
    ]
    for r in risks:
        r["tier"] = tier(r["pct"])
    return sorted(risks, key=lambda r: -r["pct"])


def health_score(risks: list[dict]) -> int:
    avg = sum(r["pct"] for r in risks) / len(risks)
    return clamp(round(100 - avg * 0.9), 15, 99)


# ---------------------------------------------------------------- endpoints
@app.get("/")
def root():
    return {"service": "Prodnosis API", "docs": "/docs"}


@app.get("/patients")
def list_patients():
    with closing(sqlite3.connect(DB)) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute("SELECT * FROM patients").fetchall()
    return [dict(r) for r in rows]


@app.post("/vitals", status_code=201)
def push_vitals(v: VitalsIn):
    with closing(sqlite3.connect(DB)) as con:
        exists = con.execute(
            "SELECT 1 FROM patients WHERE id=?", (v.patient_id,)
        ).fetchone()
        if not exists:
            raise HTTPException(404, f"Unknown patient '{v.patient_id}'")
        con.execute(
            """INSERT INTO vitals
               (patient_id, ts, steps, hr, spo2, sleep_hrs, bp_sys, bp_dia, glucose)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                v.patient_id,
                datetime.utcnow().isoformat(timespec="seconds"),
                v.steps, v.hr, v.spo2, v.sleep_hrs, v.bp_sys, v.bp_dia, v.glucose,
            ),
        )
        con.commit()
    return {"status": "stored"}


def _latest_vitals(patient_id: str) -> dict:
    with closing(sqlite3.connect(DB)) as con:
        con.row_factory = sqlite3.Row
        row = con.execute(
            "SELECT * FROM vitals WHERE patient_id=? ORDER BY id DESC LIMIT 1",
            (patient_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(
            404, f"No vitals recorded for '{patient_id}' yet — POST to /vitals first"
        )
    return dict(row)


@app.get("/patients/{patient_id}/vitals/latest")
def latest_vitals(patient_id: str):
    return _latest_vitals(patient_id)


@app.get("/patients/{patient_id}/risks")
def patient_risks(patient_id: str):
    v = _latest_vitals(patient_id)
    risks = compute_risks(v)
    return {
        "patient_id": patient_id,
        "measured_at": v["ts"],
        "health_score": health_score(risks),
        "risks": risks,
    }
