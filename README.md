# Prodnosis 🩺

**AI + IoT health monitoring platform** — aggregates wearable data, predicts health risks with AI, and connects patients to doctors for remote monitoring.

Built by **Team Invense** (Keshav Tomar, Manya Gupta, Tanmay Meena) — originally pitched at Technex'25, IIT (BHU) Varanasi.

🔗 **Live demo:** _add your Netlify link here_

## The problem

A 60-year-old diabetic farmer tracks steps on a smartwatch, logs diet in one app, checks blood sugar with a separate monitor — and his doctor sees none of it. Health data today is fragmented, reactive, and inaccessible, especially in rural India.

## What Prodnosis does

- **Unified patient dashboard** — live vitals (heart rate, SpO₂, BP, glucose, sleep, activity) from wearables in one place
- **AI risk prediction** — early flags for insomnia, diabetes, hypertension, respiratory distress, cardiac irregularity
- **Personalized suggestions** — diet & exercise recommendations driven by current risk factors
- **Real-time emergency alerts** — abnormal vitals instantly notify caregivers and the on-call doctor
- **Doctor portal** — panel-wide view of active patients, histories, and AI-flagged high-risk cases

## Project structure

```
├── index.html          # Frontend prototype (patient dashboard + doctor portal)
├── backend/
│   ├── main.py         # FastAPI server: patients, vitals ingestion, risk engine
│   └── requirements.txt
└── README.md
```

## Running it

**Frontend:** just open `index.html` in a browser — no install needed.

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```
Then open http://localhost:8000/docs for the interactive API explorer.

## Current status & roadmap

- [x] Interactive prototype (simulated wearable feed, rule-based risk engine)
- [x] FastAPI backend with SQLite storage and risk-scoring API
- [ ] Connect frontend to backend (replace simulated feed with API calls)
- [ ] Real wearable integration (Google Fit / Fitbit API)
- [ ] Trained ML risk models (PhysioNet ECG, diabetes datasets)
- [ ] User accounts & authentication
- [ ] EHR integration (FHIR/HL7) and compliance (DPDP Act, CDSCO)

## Tech stack

Vanilla JS frontend · Python FastAPI · SQLite · REST APIs

> ⚠ Prodnosis is a student project and prototype — not a certified medical device. Do not use it for medical decisions.
