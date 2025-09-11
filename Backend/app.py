from flask import Flask, request, jsonify, session
from db import get_connection
from auth import hash_password, check_password
from flask_cors import CORS

import json
import random
from datetime import datetime, timedelta
now = datetime.now()

app = Flask(__name__)
CORS(app)
app.secret_key = "R@g!n!22"

@app.route('/register', methods=['POST'])
def register():
    print("🔔 Register route triggered")
    try:
        data = request.json
        print("📥 Received data:", data)

        conn = get_connection()
        print("✅ DB connected")

        cursor = conn.cursor()
        print("🧠 Running INSERT query")

        cursor.execute(
            "INSERT INTO users (name, email, password_hash, age, gender) VALUES (%s, %s, %s, %s, %s)",
            (data['name'], data['email'], hash_password(data['password']), data['age'], data['gender'])
        )

        conn.commit()
        cursor.close()
        conn.close()
        print("✅ User registered")

        return jsonify({"message": "Registered successfully"})

    except Exception as e:
        print("❌ Exception:", e)
        return jsonify({"error": str(e)}), 500



@app.route('/login', methods=['POST'])
def login():
    data = request.json
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (data['email'],))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user and check_password(user['password_hash'], data['password']):
        session['user_id'] = user['id']
        return jsonify({"message": "Login successful", "user": user})
    else:
        return jsonify({"error": "Invalid credentials"}), 401

@app.route('/questions', methods=['GET'])
def get_questions():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM mmse_questions")
    questions = cursor.fetchall()
    cursor.close()
    conn.close()
    import json
    for q in questions:
        if q.get("options_json"):
            try:
                q["options"] = json.loads(q["options_json"])
            except:
                q["options"] = []
        elif q.get("answer_type") == "multiple_choice":  # Case 2: dynamic
            qtext = q["question_text"].lower()

            if "year" in qtext:
                year = now.year
                q["options"] = [
                    str(year - 2), str(year - 1),
                    str(year), str(year + 1), str(year + 2)
                ]
                random.shuffle(q["options"])

            elif "date" in qtext:
                dates = [
                    (now + timedelta(days=i)).strftime("%d %B %Y")
                    for i in range(-2, 3)
                ]
                random.shuffle(dates)
                q["options"] = dates

            else:
                q["options"] = []
        else:
            q["options"] = []

    return jsonify(questions)
    

from datetime import datetime

from datetime import datetime

@app.route('/get_question/<int:question_id>', methods=['GET'])
def get_question(question_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, question_text, answer_type, options_json
        FROM mmse_questions
        WHERE id = %s
    """, (question_id,))
    question = cursor.fetchone()
    cursor.close()
    conn.close()
    
    # # Convert options_json to Python list
    # if question and question['options_json']:
    #     import json
    #     question['options'] = json.loads(question['options_json'])
    # else:
    #     question['options'] = []

    # return jsonify(question)
    if question:
        import json
        # Case 1: If options are already stored in DB as JSON, use them
        if question.get('options_json'):
            question['options'] = json.loads(question['options_json'])

        # Case 2: If it's a multiple choice but no predefined options in DB,
        # generate them dynamically
        elif question.get('answer_type') == "multiple_choice":
            qtext = question['question_text'].lower()
            from datetime import datetime
            import random
            now = datetime.now()

            # Example: Year question
            if "year" in qtext:
                year = now.year
                question['options'] = [
                    str(year - 2), str(year - 1),
                    str(year), str(year + 1), str(year + 2)
                ]
                random.shuffle(question['options'])
            elif "date" in qtext:
                    today = now.date()
                    date_options = [
                        today + timedelta(days=i)
                        for i in range (-2,3)
                    ]
                    question['options'] = [d.strftime("%d %B %Y") for d in date_options]
                    random.shuffle(question['options'])

           
        else:
            question['options'] = []

    return jsonify(question)




from datetime import datetime
import os

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    data = request.json
    user_answer_raw = data['answer']
    user_answer = os.path.splitext(user_answer_raw.strip().lower())[0]  # remove ".png" if present
    score = 0

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT question_text, correct_answer, max_score FROM mmse_questions WHERE id = %s",
        (data['question_id'],)
    )
    question = cursor.fetchone()

    if question:
        qtext = question['question_text'].lower()
        correct = (question['correct_answer'] or "").strip().lower()
        max_score = question['max_score']
        now = datetime.now()

        # ✅ Time/Date-based logic
        if "year" in qtext and user_answer == str(now.year):
            score = max_score
        elif "season" in qtext:
            month = now.month
            season = (
                "winter" if month in [12, 1, 2,3] else
                "summer" if month in [4,5,6,7] else
                "monsoon" 
            )
            if season in user_answer:
                score = max_score
        elif "day of the week" in qtext:
             correct_day = now.strftime("%A").lower()  # e.g. "thursday"
             user_day = user_answer.lower().replace(".png", "").replace(".jpg", "").replace(".jpeg", "")
             if correct_day == user_day:
                score = max_score
        elif "date today" in qtext:
            if user_answer in now.strftime("%d %B %Y").lower() or \
               user_answer in now.strftime("%Y-%m-%d").lower():
                score = max_score

        # ✅ Location-related
        elif "place" in qtext or "city" in qtext in qtext:
            if any(loc in user_answer for loc in ["india", "home", "sangli", "maharashtra"]):
                score = max_score
        elif "state" in qtext :
            correct_state = "maharashtra"
            user_state = user_answer.lower().replace(".png","").replace(".jpg", "").replace(".jpeg", "")
            if correct_state == user_state:
                score = max_score

        # ✅ Subtract 7
        elif "subtract 7" in qtext:
            expected = "65"
            if user_answer.strip() == expected:
                score = max_score
            else:   
                score = 0

        # ✅ 3-object registration / recall
        elif "3 objects" in qtext and "recall" in qtext:
            if all(x in user_answer for x in ["pencil", "apple", "chair"]):
                score = max_score
        elif "3 objects" in qtext and "repeat" in qtext:
            if all(x in user_answer for x in ["pencil", "apple", "chair"]):
                score = max_score

        # ✅ Phrase repeat
        elif "no ifs, ands" in qtext:
            if user_answer == "no ifs, ands, or buts":
                score = max_score

        elif "write all three" in qtext:
            if user_answer == "apple, chair, pencil" or user_answer == "apple chair pencil " or user_answer == "apple,chair,pencil":
                score = max_score
        # ✅ Name the object (image click like "pencil.png")
        elif "name the object" in qtext:
            if any(x in user_answer for x in ["pencil", "apple", "chair"]):
                score = max_score
        elif "sentence of your choosing" in qtext:
            if user_answer.strip():
                score = max_score
            else:
                score = 0

        # ✅ Default fallback: match correct answer
        elif correct and user_answer == correct:
            score = max_score

    # ✅ Store the response
    cursor = conn.cursor()
    cursor.execute(
    """
    INSERT INTO mmse_responses 
    (user_id, question_id, answer, time_taken_seconds, score_awarded)
    VALUES (%s, %s, %s, %s, %s)
    """,
    (data['user_id'], data['question_id'], data['answer'], data['time_taken'], score)
    )


    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Answer submitted", "score_awarded": score})




@app.route('/score_history/<int:user_id>', methods=['GET'])
def score_history(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT q.question_text, r.answer, r.score_awarded, r.time_taken_seconds, r.submitted_at
        FROM mmse_responses r
        JOIN mmse_questions q ON r.question_id = q.id
        WHERE r.user_id = %s
        ORDER BY r.submitted_at DESC
    """, (user_id,))
    history = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(history)

@app.route('/total_score/<int:user_id>', methods=['GET'])
def total_score(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Latest response per question only
    cursor.execute("""
        SELECT SUM(r.score_awarded) AS user_score,
               SUM(q.max_score) AS total_score
        FROM (
            SELECT MAX(id) AS latest_response_id
            FROM mmse_responses
            WHERE user_id = %s
            GROUP BY question_id
        ) latest
        JOIN mmse_responses r ON r.id = latest.latest_response_id
        JOIN mmse_questions q ON r.question_id = q.id
    """, (user_id,))

    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify(result)

@app.route('/admin/users', methods=['GET'])
def get_all_users():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email, created_at FROM users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(users)
    
@app.route('/admin/user_tests/<int:user_id>', methods=['GET'])
def get_user_tests(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
       SELECT
        DATE(submitted_at) AS test_date,
        MIN(submitted_at) AS started_at,
        MAX(submitted_at) AS ended_at,
        COUNT(*) AS questions_answered,
        SUM(score_awarded) AS total_score,
        SUM(time_taken_seconds) AS total_time
    FROM mmse_responses
    WHERE user_id = %s
    GROUP BY DATE(submitted_at)
    ORDER BY started_at DESC
    """, (user_id,))
    sessions = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(sessions)


@app.route('/admin/test_details/<int:session_id>', methods=['GET'])
def get_test_details(session_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            q.question_text,
            r.answer,
            r.time_taken_seconds,
            r.score_awarded,
            r.submitted_at
        FROM mmse_responses r
        JOIN mmse_questions q ON r.question_id = q.id
        WHERE r.test_session_id = %s 
        ORDER BY r.submitted_at ASC
    """, (session_id,))
    details = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(details)




if __name__ == '__main__':
    app.run(debug=True)
