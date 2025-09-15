# CounselPro-AI 🎯

> AI-Powered Counselor Excellence System

CounselPro-AI is a comprehensive AI-driven platform designed to analyze and enhance counselor performance through advanced video and audio processing, real-time feedback, and intelligent assessment tools.

## 🚀 Features

### Core Capabilities
- **🎥 Video Analysis**: Automated video processing for professional standards assessment
- **🎤 Audio Transcription**: Real-time speech-to-text using Deepgram AI
- **📊 Performance Analytics**: Comprehensive counselor session analysis
- **📋 Course Verification**: Automated content validation against training materials
- **📧 Email Notifications**: Automated reporting and alerts
- **☁️ Cloud Storage**: Cloudinary integration for media management

### AI & Machine Learning
- **Computer Vision**: Face detection and professional attire assessment
- **Natural Language Processing**: Conversation analysis and red flag detection
- **LangChain Integration**: Advanced AI workflows for content analysis
- **Pinecone Vector Database**: Semantic search and content matching

## 🏗️ Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Task Queue**: Celery with Redis for background processing
- **AI Services**: LangChain, OpenAI, Google Generative AI
- **Media Processing**: OpenCV, FFmpeg, Ultralytics YOLO

### Frontend (Next.js)
- **Framework**: Next.js 15 with App Router
- **UI Components**: Radix UI with Tailwind CSS
- **State Management**: TanStack Query (React Query)
- **Forms**: React Hook Form with Zod validation
- **Animations**: Framer Motion

## 📁 Project Structure

```
CounselPro-AI/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py            # FastAPI application entry point
│   │   ├── config/            # Configuration and logging
│   │   ├── db/                # Database configuration
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── routes/            # API routes
│   │   ├── service/           # Business logic
│   │   │   ├── audio_processing/
│   │   │   ├── video_processing/
│   │   │   ├── course_verification/
│   │   │   └── celery/        # Background tasks
│   │   └── exceptions/        # Custom exception handlers
│   ├── assets/                # Course catalogs and models
│   ├── requirements.txt       # Python dependencies
│   └── docker-compose.yml     # Container orchestration
│
├── frontend/                  # Next.js frontend
│   ├── src/
│   │   ├── app/              # App Router pages
│   │   ├── components/       # Reusable UI components
│   │   ├── lib/              # Utilities and API layer
│   │   └── contexts/         # React contexts
│   ├── package.json          # Node.js dependencies
│   └── next.config.ts        # Next.js configuration
│
└── README.md                 # This file
```

### Additional Docs

- Frontend & NLP flow: [docs/flow-frontend-nlp.md](docs/flow-frontend-nlp.md)

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose (optional)

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/ravin1100/CounselPro-AI.git
   cd CounselPro-AI/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   
5. **Start Celery Worker**
   
   ```bash
   celery -A app.service.celery.celery_worker.celery_app worker --loglevel=info
   ```

6. **Start Redis Server**
    ```bash
   sudo service redis-server start
   ```
 

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd ../frontend
   ```

2. **Install dependencies**
   ```bash
   pnpm install
   # or npm install
   ```

3. **Start development server**
   ```bash
   pnpm dev
   # or npm run dev
   ```

4. **Open application**
   ```
   http://localhost:3000
   ```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/counselpro
ASYNC_DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/counselpro

# Redis
REDIS_URL=redis://localhost:6379

# AI Services
OPENAI_API_KEY=your_openai_key
GOOGLE_AI_API_KEY=your_google_ai_key
PINECONE_API_KEY=your_pinecone_key

# Deepgram
DEEPGRAM_API_KEY=your_deepgram_key

# Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email
SMTP_PASSWORD=your_password
```

#### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📚 API Documentation

### Core Endpoints

#### Counselors
- `GET /counselors` - List all counselors
- `POST /counselors` - Create new counselor
- `GET /counselors/{uid}` - Get counselor by ID
- `PUT /counselors/{uid}` - Update counselor
- `DELETE /counselors/{uid}` - Delete counselor

#### Sessions
- `GET /sessions` - List all sessions
- `POST /sessions` - Create new session
- `GET /sessions/{uid}` - Get session by ID
- `GET /sessions/{uid}/analysis` - Trigger session analysis

#### Session Analysis
- `GET /session-analysis/by-session/{sessionUid}` - Get analysis by session
- `GET /session-analysis/bulk` - Get bulk analyses for dashboard
- `POST /session-analysis` - Create new analysis

#### Raw Transcripts
- `GET /raw-transcript/by-session/{sessionUid}` - Get transcript by session
- `POST /raw-transcript` - Create new transcript

### Interactive API Docs
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔄 Workflow

1. **Session Creation**: Counselor creates a new counseling session with video recording
2. **Background Processing**: Celery workers process video and audio asynchronously
3. **AI Analysis**: 
   - Video analysis for professional standards (attire, background)
   - Audio transcription using Deepgram
   - Course content verification against training materials
   - Red flag detection in conversation
4. **Results Storage**: Analysis results stored in PostgreSQL
5. **Email Notifications**: Automated reports sent to stakeholders
6. **Dashboard Visualization**: Results displayed in intuitive frontend interface

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
pnpm test
# or npm test
```

## 🚀 Deployment

### Docker Deployment
```bash
# Backend
cd backend
docker-compose up -d

# Frontend
cd frontend
docker build -t counselpro-frontend .
docker run -p 3000:3000 counselpro-frontend

```


#    Cost Report — Video Processing Pipeline

This report covers **per-video costs** for CouncelPro AI:  
- **Transcription**: Deepgram  
- **Embeddings**: OpenAI `text-embedding-3-large`  
- **Chat completions**: GPT-4.1  
- **Frame analysis**: Gemini 1.5 Flash (5-frame analysis, constant per video)  
- *(Note: Pinecone will also incur ingestion + retrieval charges — see below)*

---

## ⚙️ Assumptions
- **Transcription (Deepgram)**: $0.00433 per minute  
- **Embedding (text-embedding-3-large)**: $0.13 per 1M tokens  
  - 312 tokens for 4.8 min → ~65 tokens/min  
  - Cost ≈ $0.00000845 per min  
- **Chat (GPT-4.1)**:  
  - 1 min → $0.00096  
  - 5 min → $0.0048  
  - 1 hr → $0.057  
- **Gemini 1.5 Flash (5-frame analysis)**: flat **$0.00193 per video**

---

## 💰 Per-Video Cost Breakdown

### 1 minute video
- Transcription: $0.00433  
- Embedding: $0.00000845  
- Chat (GPT-4.1): $0.00096  
- Gemini 1.5 Flash: $0.00193  
**➡️ Total = $0.00723 (~0.72 cents)**  

---

### 5 minute video
- Transcription: $0.02165  
- Embedding: $0.00004225  
- Chat (GPT-4.1): $0.00480  
- Gemini 1.5 Flash: $0.00193  
**➡️ Total = $0.02842 (~2.84 cents)**  

---

### 1 hour video
- Transcription: $0.25980  
- Embedding: $0.000507  
- Chat (GPT-4.1): $0.05700  
- Gemini 1.5 Flash: $0.00193  
**➡️ Total = $0.31924 (~31.9 cents)**  

---

## 📑 Summary Table

| Duration | Transcription | Embedding | Chat (GPT-4.1) | Gemini 5-frame | **Total** |
|----------|--------------:|----------:|---------------:|---------------:|----------:|
| **1 min** | $0.00433 | $0.00000845 | $0.00096 | $0.00193 | **$0.00723** |
| **5 min** | $0.02165 | $0.00004225 | $0.00480 | $0.00193 | **$0.02842** |
| **1 hr**  | $0.25980 | $0.00050700 | $0.05700 | $0.00193 | **$0.31924** |

---

## 📌 Notes
- **Transcription dominates costs** (≈75–82% of totals). Optimizing this yields the largest savings.  
- **Embedding costs are negligible** (<0.2% of totals).  
- **Gemini’s flat $0.00193/video** is significant for very short clips but negligible for long videos.  
- **Chat completions** are ~15–18% of costs, especially noticeable on longer inputs.  
- **Pinecone**: There will be **additional costs** for **document ingestion and retrieval** (pricing depends on index size, vector dimension, and query frequency). These are **not included** in the above numbers.  

---

## 📅 Example Monthly Projections
- 100 videos of 1 min → **$0.723**  
- 200 videos of 5 min → **$5.68**  
- 10 videos of 1 hr → **$3.19**


## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support, email support@counselpro-ai.com or join our Slack channel.

## 🔗 Links

- **Frontend Live Demo**: https://counselpro-ai.vercel.app
- **API Documentation**: http://localhost:8000/docs
- **Project Repository**: https://github.com/ravin1100/CounselPro-AI

---

Built with ❤️ by the CounselPro-AI Team
