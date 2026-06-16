# 🤖 Hexaware AI Chatbot Assistant using RAG

An intelligent internal chatbot for Hexaware employees that instantly answers HR, IT, Finance, and Company questions — and automatically raises support tickets.

---

## 🚀 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React.js |
| Backend | FastAPI (Python) |
| AI Model | LLaMA 3.3-70B via Groq |
| Embeddings | all-MiniLM-L6-v2 |
| Vector DB | ChromaDB |
| Database | SQLite |
| Auth | JWT |
| Fuzzy Match | RapidFuzz |

---

## ✨ Key Features

- 💬 Answers HR, IT, Finance, Company & Facilities questions instantly
- 🎫 Auto-detects problems and raises support tickets
- 🔤 Typo tolerant — understands `leeve` as `leave`, `wff` as `wfh`
- 💡 Suggests related questions after every answer
- 🔐 JWT-secured Admin Panel for ticket and knowledge base management

---

## ⚙️ Setup

**1. Install dependencies**
```bash
pip install fastapi uvicorn chromadb sentence-transformers langchain langchain-groq python-jose python-dotenv rapidfuzz
```

**2. Create `.env` file**
```env
GROQ_API_KEY=your_groq_api_key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_password
JWT_SECRET=your_secret_key
TOKEN_EXPIRE_HOURS=8
```

**3. Index knowledge base**
```bash
python load_data.py
```

**4. Start backend**
```bash
uvicorn Backend_server:app --reload
```

**5. Start frontend**
```bash
cd frontend
npm install
npm run dev
```

- Backend → `http://localhost:8000`
- Frontend → `http://localhost:5173`

---

## 📂 Knowledge Base Domains

| Domain | Topics |
|--------|--------|
| HR | Leave, WFH, Notice Period, Resignation, Appraisal |
| IT | VPN, Password Reset, Laptop Issues, WiFi, Software |
| Finance | Salary, Payslip, Expense Claims, Form 16, Travel |
| Company | CEO, History, Services, Mission, Careers |
| General | Cafeteria, Transport, Meeting Rooms, Gym, ID Card |

---

## 🔄 How It Works

```
Employee Question
      ↓
Domain Detection (HR / IT / Finance / Company / General)
      ↓
ChromaDB Similarity Search → Top 3 Relevant Chunks
      ↓
LLaMA 3.3-70B → Answers from Context Only
      ↓
Response + Related Suggestions
```

---

## 👤 Author

Built by **Vinotha** as part of Hexaware Technologies internship.

---

<div align="center">
  <em>Powered by RAG • FastAPI • React • ChromaDB • Groq LLaMA 3.3-70B</em>
</div>
