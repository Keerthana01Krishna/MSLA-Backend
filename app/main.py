from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine, text

app = FastAPI()

# Database Connection
DATABASE_URL = "mysql+pymysql://root:Keerthi%406362@localhost:3306/msla"
engine = create_engine(DATABASE_URL)


# ==========================
# Models
# ==========================

class StudentRegister(BaseModel):
    name: str
    email: str
    password: str
    semester: int


class StudentLogin(BaseModel):
    email: str
    password: str

class AnswerItem(BaseModel):
    question_id: int
    selected_answer: str


class QuizSubmission(BaseModel):
    student_id: int
    subject: str
    difficulty: str
    answers: list[AnswerItem]

class AIRequest(BaseModel):
    question: str


# ==========================
# Home API
# ==========================

@app.get("/")
def home():
    return {
        "message": "MSLA Backend Running"
    }


# ==========================
# Get All Questions
# ==========================

@app.get("/questions")
def get_questions():
    try:
        with engine.connect() as connection:

            result = connection.execute(
                text("SELECT * FROM quiz_questions")
            )

            questions = []

            for row in result:
                questions.append({
                    "question_id": row.question_id,
                    "subject": row.subject,
                    "difficulty": row.difficulty,
                    "question": row.question
                })

            return questions

    except Exception as e:
        return {"error": str(e)}


# ==========================
# Get Questions By Subject
# ==========================

# ==========================
# Get Questions By Subject & Difficulty
# ==========================

@app.get("/quiz/{subject}/{difficulty}")
def get_quiz(subject: str, difficulty: str):
    try:
        with engine.connect() as connection:

            query = text("""
                SELECT *
                FROM quiz_questions
                WHERE subject = :subject
                AND difficulty = :difficulty
                LIMIT 10
            """)

            result = connection.execute(
                query,
                {
                    "subject": subject,
                    "difficulty": difficulty
                }
            )

            questions = []

            for row in result:
                questions.append({
                    "question_id": row.question_id,
                    "subject": row.subject,
                    "difficulty": row.difficulty,
                    "question": row.question,
                    "option_a": row.option_a,
                    "option_b": row.option_b,
                    "option_c": row.option_c,
                    "option_d": row.option_d
                })

            return questions

    except Exception as e:
        return {
            "error": str(e)
        }
# ==========================
# Student Registration
# ==========================

@app.post("/register")
def register_student(student: StudentRegister):
    try:
        with engine.connect() as connection:

            query = text("""
                INSERT INTO students
                (name, email, password, semester)
                VALUES
                (:name, :email, :password, :semester)
            """)

            connection.execute(
                query,
                {
                    "name": student.name,
                    "email": student.email,
                    "password": student.password,
                    "semester": student.semester
                }
            )

            connection.commit()

            return {
                "message": "Student registered successfully"
            }

    except Exception as e:
        return {"error": str(e)}


# ==========================
# Student Login
# ==========================

@app.post("/login")
def login_student(student: StudentLogin):
    try:
        with engine.connect() as connection:

            query = text("""
                SELECT *
                FROM students
                WHERE email = :email
                AND password = :password
            """)

            result = connection.execute(
                query,
                {
                    "email": student.email,
                    "password": student.password
                }
            )

            user = result.fetchone()

            if user:
                return {
                    "message": "Login successful",
                    "student_id": user.student_id,
                    "name": user.name,
                    "semester": user.semester
                }

            return {
                "message": "Invalid email or password"
            }

    except Exception as e:
        return {"error": str(e)}

# ==========================
# Submit Quiz
# ==========================

@app.post("/submit-quiz")
def submit_quiz(submission: QuizSubmission):

    try:

        score = 0
        total_questions = len(submission.answers)

        with engine.connect() as connection:

            for answer in submission.answers:

                query = text("""
                    SELECT correct_answer
                    FROM quiz_questions
                    WHERE question_id = :question_id
                """)

                result = connection.execute(
                    query,
                    {
                        "question_id": answer.question_id
                    }
                )

                row = result.fetchone()

                if row:

                    correct_answer = row.correct_answer.upper()
                    selected_answer = answer.selected_answer.upper()

                    if correct_answer == selected_answer:
                        score += 1

            percentage = 0

            if total_questions > 0:
                percentage = (score / total_questions) * 100

            save_query = text("""
                INSERT INTO quiz_results
                (
                    student_id,
                    subject,
                    difficulty,
                    score,
                    total_questions,
                    percentage
                )
                VALUES
                (
                    :student_id,
                    :subject,
                    :difficulty,
                    :score,
                    :total_questions,
                    :percentage
                )
            """)

            connection.execute(
                save_query,
                {
                    "student_id": submission.student_id,
                    "subject": submission.subject,
                    "difficulty": submission.difficulty,
                    "score": score,
                    "total_questions": total_questions,
                    "percentage": percentage
                }
            )

            connection.commit()

            return {
                "message": "Quiz submitted successfully",
                "score": score,
                "total_questions": total_questions,
                "percentage": percentage
            }

    except Exception as e:
        return {
            "error": str(e)
        }

# ==========================
# Get Student Results
# ==========================

@app.get("/results/{student_id}")
def get_results(student_id: int):

    try:

        with engine.connect() as connection:

            query = text("""
                SELECT
                    result_id,
                    subject,
                    difficulty,
                    score,
                    total_questions,
                    percentage,
                    quiz_date
                FROM quiz_results
                WHERE student_id = :student_id
                ORDER BY quiz_date DESC
            """)

            result = connection.execute(
                query,
                {
                    "student_id": student_id
                }
            )

            results = []

            for row in result:

                results.append({
                    "result_id": row.result_id,
                    "subject": row.subject,
                    "difficulty": row.difficulty,
                    "score": row.score,
                    "total_questions": row.total_questions,
                    "percentage": float(row.percentage),
                    "quiz_date": str(row.quiz_date)
                })

            return results

    except Exception as e:
        return {
            "error": str(e)
        }
import requests


@app.post("/ask-ai")
def ask_ai(data: AIRequest):

    print("QUESTION RECEIVED:", data.question)

    try:

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "phi3",
                "prompt": f"""
Answer briefly in 3-5 lines.

Question:
{data.question}
""",
                "stream": False,
                "options": {
            "num_predict": 150
        }
                
            }
        )

        print("OLLAMA RESPONSE RECEIVED")

        result = response.json()

        return {
            "answer": result["response"]
        }

    except Exception as e:

        print("ERROR:", str(e))

        return {
            "answer": str(e)
        }

@app.get("/test")
def test():
    return {"message": "Backend OK"}