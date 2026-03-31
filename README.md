# 🧮 QuizIA — AI-Powered Math Competency Evaluator

A production-ready **Streamlit** web application that evaluates mathematics competency of computer science students using **AI-generated quizzes**.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔐 **Authentication** | Signup/Login with bcrypt-hashed passwords stored in SQLite |
| 📝 **Quiz Configuration** | Choose topic, difficulty, question count, and type (MCQ / Short Answer) |
| 🤖 **AI Question Generation** | Dynamically generates unique questions via Google Gemini API |
| ✅ **Auto Grading** | MCQs graded by exact match; Short answers evaluated by AI |
| 📊 **Dashboard** | View total quizzes, average score, performance label, recent attempts |
| 📋 **History** | Browse all past quiz attempts with full answer breakdowns |
| 🔄 **Switchable AI** | Modular provider pattern — switch from Gemini to OpenAI by changing one env variable |

---

## 🗂️ Project Structure

```
quizIA/
├── app.py           # Main Streamlit entry point (UI & routing)
├── auth.py          # Signup / Login logic with bcrypt
├── db.py            # SQLite database connection & queries
├── quiz.py          # Quiz generation, grading, persistence
├── api_client.py    # AI provider abstraction (Gemini + OpenAI stub)
├── utils.py         # Shared helper utilities
├── requirements.txt # Python dependencies
├── .env             # API keys (not committed)
├── .env.example     # Template for .env
└── README.md        # You are here
```

---

## 🚀 Quick Start

### 1. Clone & Navigate

```bash
cd quizIA
```

### 2. Create Virtual Environment (recommended)

```bash
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # macOS / Linux
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Key

1. Get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Open `.env` and replace `your_gemini_api_key_here` with your actual key:

```env
GEMINI_API_KEY=AIza...your_real_key...
AI_PROVIDER=gemini
```

### 5. Run the Application

```bash
streamlit run app.py
```

The app will open at **http://localhost:8501**.

---

## ☁️ Deployment

### Streamlit Community Cloud
1. Push your code to a GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io/) and select **New app**.
3. Point it to your GitHub repository and select `app.py` as the main file path.
4. **Important:** Click **Advanced settings** and paste your environment variables into the **Secrets** box using **TOML format**:

```toml
GEMINI_API_KEY = "your_actual_key_here"
AI_PROVIDER = "gemini"
```

---

## 🗄️ Database

SQLite database (`quizia.db`) is auto-created on first run with three tables:

| Table | Purpose |
|---|---|
| `users` | User accounts (id, name, email, hashed password) |
| `quiz_results` | Quiz attempt metadata (topic, difficulty, score, timestamp) |
| `answers` | Per-question answers for review (question, user/correct answer, is_correct) |

---

## 🔄 Switching AI Provider

The `api_client.py` module uses an **abstract base class** pattern.  
To switch from Gemini to OpenAI:

1. Install the OpenAI SDK: `pip install openai`
2. Set your OpenAI key and provider in `.env`:
   ```env
   AI_PROVIDER=openai
   OPENAI_API_KEY=sk-...
   ```
3. That's it — the factory function in `api_client.py` will automatically use the OpenAI provider.

---

## 📌 Topics Available

- Linear Algebra
- Probability & Statistics
- Calculus
- Discrete Mathematics
- Number Theory
- Set Theory
- Graph Theory
- Boolean Algebra
- Combinatorics
- Differential Equations

---

## 🧪 Example Prompt Templates

### MCQ Generation Prompt
```
You are a mathematics professor creating a quiz for computer science students.
Generate exactly {n} multiple-choice questions on "{topic}" at {difficulty} difficulty.
Return ONLY valid JSON with the schema: {"questions": [{"question": "...", "options": [...], "correct_answer": "A"}]}
```

### Short Answer Evaluation Prompt
```
You are evaluating a student's answer.
Question: {question}
Correct answer: {correct_answer}
Student's answer: {user_answer}
Respond with JSON: {"is_correct": true/false, "explanation": "..."}
```

---

## 📄 License

MIT — free to use, modify, and distribute.
