# Product Flow: Frontend and NLP (Voice)

This document maps the end-to-end flows for the UI and the voice/NLP processing pipeline based on the current codebase.

## 1) Frontend flows (Next.js 15 + React Query)

Key modules:
- API client: `frontend/src/lib/api.ts` (Axios + toasts)
- Sessions: `frontend/src/lib/services/sessions.ts`
- Analysis: `frontend/src/lib/services/analysis.ts`
- Dashboard utils: `frontend/src/lib/analysis-utils.ts`

### Frontend folder structure

```
frontend/
├── API_LAYER.md
├── COUNSELORS_FEATURES.md
├── next.config.ts
├── package.json
├── public/
│   ├── file.svg
│   ├── globe.svg
│   ├── next.svg
│   ├── vercel.svg
│   └── window.svg
└── src/
  ├── app/
  │   ├── (dashboard)/
  │   ├── favicon.ico
  │   ├── globals.css
  │   └── layout.tsx
  ├── components/
  │   ├── analysis/
  │   │   ├── OneOnOneCard.tsx
  │   │   ├── PaymentVerificationCard.tsx
  │   │   ├── PressureAnalysisCard.tsx
  │   │   ├── analysis-action-button.tsx
  │   │   ├── analysis-dashboard.tsx
  │   │   ├── analysis-empty-state.tsx
  │   │   ├── course-accuracy-card.tsx
  │   │   ├── environment-card.tsx
  │   │   ├── participants-grid.tsx
  │   │   ├── session-metadata.tsx
  │   │   ├── session-timeline.tsx
  │   │   └── technical-info.tsx
  │   ├── counselors/
  │   ├── dashboard/
  │   │   ├── KpiRow.tsx
  │   │   ├── QualityGlance.tsx
  │   │   └── RecentAnalyses.tsx
  │   ├── transcript/
  │   ├── ui/
  │   ├── app-header.tsx
  │   ├── app-sidebar.tsx
  │   ├── page-transition.tsx
  │   ├── providers.tsx
  │   ├── theme-provider.tsx
  │   └── theme-toggle.tsx
  ├── contexts/
  │   └── analysis-context.tsx
  ├── lib/
  │   ├── analysis-utils.ts
  │   ├── api.ts
  │   ├── queryClient.ts
  │   ├── utils.ts
  │   ├── types.ts
  │   ├── types.analysis.ts
  │   └── services/
  │       ├── analysis.ts
  │       ├── catalog.ts
  │       ├── counselor-service.ts
  │       ├── counselors.ts
  │       ├── index.ts
  │       └── sessions.ts
  ├── hooks/
  └── ...
```

### A. Create a session
1. UI collects: `counselor_uid`, `description`, `session_date`, `recording_link`
2. `createSession(body)` → POST `/sessions`
3. Returns `SessionResponse { uid, status: "PENDING", ... }`

### B. List sessions (paginated)
- `listSessions({ skip, limit })` → GET `/sessions/all`
- Returns `{ items, total, skip, limit }`

### C. View session details
- `getSession(uid)` → GET `/sessions/{uid}`

### D. Trigger analysis
- Preferred (Celery): `analyzeSession(uid)` → GET `/sessions/{uid}/analysis_by_celery` → `{ task_id, status: "STARTED" }`
- Alternative (direct): `triggerSessionAnalysis(uid)` → GET `/sessions/{uid}/analysis?session_id={uid}`

### E. Poll analysis status/results
- Single: `getSessionAnalysisBySession(uid)` → GET `/session-analysis/by-session/{uid}`
  - React Query hooks: `useSessionAnalysis`, `useSessionAnalysisWithPolling`
- Bulk: `getBulkSessionAnalyses(uids[])` → GET `/session-analysis/bulk?session_ids=...`

### F. Fetch raw transcript (gated)
- `getRawTranscript(uid)` → GET `/raw-transcripts/by-session/{uid}`
- Returns full transcript only when status is `COMPLETED`; otherwise, status without data

Notes:
- Base URL: `NEXT_PUBLIC_API_BASE_URL` (default: `http://localhost:8000`)
- Axios interceptors handle offline/422/401/429/5xx with toasts

## 2) NLP/Voice processing pipeline (Celery + FastAPI)

Key modules:
- Route: `backend/app/routes/session_route.py`
- Celery: `backend/app/service/celery/celery_worker.py`
- Pipeline: `backend/app/service/celery/video_processing_for_celery.py`
- Video analysis: `backend/app/service/video_processing/video_processing.py`
- Transcript routes: `backend/app/routes/raw_transcript_route.py`
- Analysis routes: `backend/app/routes/session_analysis_route.py`

### Trigger
- Frontend → `GET /sessions/{session_uid}/analysis_by_celery`
- Enqueues `process_video.delay(session_uid, video_path)`

### Celery task: `process_video(session_uid, video_path)`
1) Ensure/mark `SessionAnalysis` status = `STARTED`
2) Run `process_video_background(session_uid, video_path)` (no DB writes):
   - Extract frames/audio: `VideoExtractor.get_video_frames_and_audio_paths`
   - Video analysis: `VideoProcessor.analyze_video_for_celery`
   - Transcription (STT): `DeepgramTranscriber.transcribe_chunk`
   - Course verification: `CourseVerifier.verify_full_transcript`
   - Returns: `video_analysis_data`, `audio_analysis_data`, `transcript_data`
3) Persist upserts:
   - Transcript: `create_or_update_raw_transcript`
   - Analysis: `create_or_update_session_analysis`
   - Set status = `COMPLETED`
   - Send email: `send_simple_email_template`
4) On error: set status = `FAILED`

### Non-Celery (direct) path
- `GET /sessions/{session_uid}/analysis?session_id={uid}` → async pipeline with same steps, DB writes via async services

## 3) API contracts (high level)

- Sessions
  - `POST /sessions` → `SessionResponse { uid, description, session_date, recording_link, status, counselor }`
  - `GET /sessions/all` → paginated list
  - `GET /sessions/{uid}`

- Analysis
  - `GET /session-analysis/by-session/{uid}` → detailed status + data
  - `GET /session-analysis/bulk?session_ids=...` → summaries for dashboard

- Transcripts
  - `GET /raw-transcripts/by-session/{uid}` → full transcript only if `COMPLETED`

## 4) Status + polling
- Lifecycle: `PENDING` → `STARTED` → `COMPLETED | FAILED`
- Poll `/session-analysis/by-session/{uid}` until terminal state
- Show transcript only on `COMPLETED`

## 5) Edge cases
- Missing/invalid recording_link → task not started / error returned
- Transcription/verification failures don’t abort video analysis; partial data is saved
- CORS in `app/main.py` allows `http://localhost:3000` and the Vercel app URL

## 6) Quick references
- Frontend: `src/lib/api.ts`, `src/lib/services/sessions.ts`, `src/lib/services/analysis.ts`
- Backend: `app/routes/session_route.py`, `app/service/celery/celery_worker.py`, `app/service/celery/video_processing_for_celery.py`, `app/service/video_processing/video_processing.py`
