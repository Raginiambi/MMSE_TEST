# from flask import Flask, request, jsonify, session
# from db import get_connection
# from auth import hash_password, check_password
# from flask_cors import CORS
# import cv2, base64, numpy as np
# from deepface import DeepFace


# import os
# from werkzeug.utils import secure_filename
# import json
# import random
# from datetime import datetime, timedelta
# now = datetime.now()

# from flask import send_from_directory

# Move this to the very top BEFORE any DeepFace or TF import if present
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # reduce TF logging if it gets imported later
from werkzeug.utils import secure_filename
from deepface import DeepFace
import json


from flask import Flask, request, jsonify, session, send_from_directory
from db import get_connection
from auth import hash_password, check_password
from flask_cors import CORS
import cv2, base64, numpy as np

# IMPORTANT: DO NOT import DeepFace here at module level.
# from deepface import DeepFace   <-- REMOVE this top-level import

import json, random
from datetime import datetime, timedelta
now = datetime.now()



app = Flask(__name__)
CORS(app)
app.secret_key = "R@g!n!22"

face_model = None
emotion_model = None

def get_emotion_model():
    """
    Lazy-load DeepFace Emotion model on first use.
    Import DeepFace inside this function to avoid importing TF at module import time.
    """
    global emotion_model
    if emotion_model is None:
        try:
            # Import inside function to avoid TensorFlow being imported during module load
            from deepface import DeepFace
            # Use the model name expected by your DeepFace version
            emotion_model = DeepFace.build_model("Emotion")
            print("✅ Emotion model loaded")
        except Exception as e:
            # Log the error and re-raise so caller can handle it
            import traceback
            traceback.print_exc()
            raise
    return emotion_model




@app.route('/uploads/<path:filename>')
def serve_uploaded_video(filename):
    return send_from_directory(UPLOAD_DIR, filename)

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_VIDEO_MIMES = {"video/webm", "video/mp4", "video/ogg"}

# @app.route('/start_test/<int:user_id>', methods=['POST'])
# def start_test(user_id):
#     conn = get_connection()
#     cursor = conn.cursor()

#     # create new test session
#     cursor.execute("INSERT INTO mmse_test_sessions (user_id) VALUES (%s)", (user_id,))
#     conn.commit()

#     test_session_id = cursor.lastrowid

#     cursor.close()
#     conn.close()

#     return jsonify({"test_session_id": test_session_id})

# @app.route('/start_test/<int:user_id>', methods=['POST'])
# def start_test(user_id):
#     try:
#         print(f"🧠 /start_test called for user_id={user_id}")
#         conn = get_connection()
#         print("✅ DB connection obtained")
#         cursor = conn.cursor()
#         print("✅ cursor created")
#         cursor.execute("INSERT INTO mmse_test_sessions (user_id) VALUES (%s)", (user_id,))
#         conn.commit()
#         test_session_id = cursor.lastrowid
#         cursor.close()
#         conn.close()
#         print("✅ test session inserted:", test_session_id)
#         return jsonify({"test_session_id": test_session_id})
#     except Exception as e:
#         # Print full traceback to console (and optionally to a file)
#         import traceback
#         traceback.print_exc()
#         return jsonify({"error": str(e)}), 500

@app.route('/start_test/<int:user_id>', methods=['POST'])
def start_test(user_id):
    print(f"🧠 /start_test called for user_id={user_id}")

    try:
        from db import get_connection
        print("📦 DB module imported successfully")

        conn = get_connection()
        print("✅ Got DB connection")

        cursor = conn.cursor()
        print("🧾 Running INSERT query...")
        cursor.execute("INSERT INTO mmse_test_sessions (user_id) VALUES (%s)", (user_id,))
        conn.commit()

        test_session_id = cursor.lastrowid
        print(f"✅ Test session created with ID: {test_session_id}")

        cursor.close()
        conn.close()
        print("🔒 Connection closed safely")

        # Return dummy questions for now to test frontend
        dummy_questions = [
            {"id": 1, "question": "What is your name?"},
            {"id": 2, "question": "What is today's date?"}
        ]

        return jsonify({
            "test_session_id": test_session_id,
            "questions": dummy_questions
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        print("❌ Error occurred:", e)
        return jsonify({"error": str(e)}), 500





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
    cursor = conn.cursor()
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
    cursor = conn.cursor()
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
    cursor = conn.cursor()
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
    test_session_id = data.get('test_session_id')

    conn = get_connection()
    cursor = conn.cursor()

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
                "winter" if month in [10, 11, 12,1] else
                "summer" if month in [2,3,4,5] else
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
            correct_date = now.date().strftime("%d %B %Y").lower().strip()
            if user_answer == correct_date:
                score = max_score
            else:
                score = 0

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
        elif "from the given pictures choose the option" in qtext:
            correct_ans = "apple,chair,pencil"
            user_ans = user_answer.lower().replace(".avif","").replace(".jpeg","").replace(".jpg","")
            user_ans = " ".join(user_ans.replace(",", " ").split())
            correct_ans_norm = " ".join(correct_ans.replace(",", " ").split())
    
            if user_ans == correct_ans_norm:
                score = max_score
           


        # ✅ 3-object registration / recall
        elif "3 objects" in qtext and "recall" in qtext:
            correct_Ans = "apple,chair,pencil"
            if user_answer.lower().strip() == correct_Ans:
                score = max_score
            else:
                score = 0
        

        # ✅ Phrase repeat
        elif "no ifs, ands" in qtext:
            if user_answer == "no ifs, ands, or buts":
                score = max_score

        elif "write all three" in qtext:
            if user_answer == "apple, chair, pencil" or user_answer == "apple chair pencil " or user_answer == "apple,chair,pencil":
                score = max_score
        # ✅ Name the object (image click like "pencil.png")
        elif "name the object" in qtext:
            if any(x in user_answer for x in ["pencil"]):
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
    (user_id, question_id, answer, time_taken_seconds, score_awarded,test_session_id)
    VALUES (%s, %s, %s, %s, %s,%s)
    """,
    (data['user_id'], data['question_id'], data['answer'], data['time_taken'], score, test_session_id))
    


    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Answer submitted", "score_awarded": score})




@app.route('/score_history/<int:user_id>', methods=['GET'])
def score_history(user_id):
    conn = get_connection()
    cursor = conn.cursor()
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
    cursor = conn.cursor()

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
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, created_at FROM users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(users)


    
@app.route('/admin/user_tests/<int:user_id>', methods=['GET'])
def get_user_tests(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
      SELECT
            ts.id AS session_id,
            ts.started_at,
            ts.ended_at,
            SUM(r.score_awarded) AS total_score,
            SUM(r.time_taken_seconds) AS total_time,
            COUNT(r.id) AS questions_answered
        FROM mmse_test_sessions ts
        LEFT JOIN mmse_responses r ON ts.id = r.test_session_id
        WHERE ts.user_id = %s
        GROUP BY ts.id, ts.started_at, ts.ended_at
        ORDER BY ts.started_at ASC
    """, (user_id,))
    sessions = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(sessions)

# @app.route('/admin/test_details/<int:session_id>', methods=['GET'])
# def get_test_details(session_id):
#     conn = get_connection()
#     cursor = conn.cursor(dictionary=True)
    
#     # Fetch test responses
#     cursor.execute("""
#         SELECT
#             q.question_text,
#             r.answer,
#             r.time_taken_seconds,
#             r.score_awarded,
#             r.submitted_at
#         FROM mmse_responses r
#         JOIN mmse_questions q ON r.question_id = q.id
#         WHERE r.test_session_id = %s
#         ORDER BY r.submitted_at ASC
#     """, (session_id,))
    
#     responses = cursor.fetchall()

#     # Fetch video filename if exists
#     video_path = f"uploads/recordings/session_{session_id}.webm"
    
#     if not os.path.exists(video_path):
#         video_url = None
#     else:
#         # Flask static URL for frontend
#         video_url = f"http://127.0.0.1:5000/{video_path}"

#     cursor.close()
#     conn.close()
    
#     return jsonify({
#         "responses": responses,
#         "video_url": video_url
#     })



@app.route('/admin/test_details/<int:session_id>', methods=['GET'])
def get_test_details(session_id):
    conn = get_connection()
    cursor = conn.cursor()
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

# Upload recorded video for a session
# @app.route('/upload_session_video', methods=['POST'])
# def upload_session_video():
#     # multipart/form-data expected: 'video' file and 'test_session_id'
#     if 'video' not in request.files:
#         return jsonify({"error": "No video file sent"}), 400

#     video_file = request.files['video']
#     test_session_id = request.form.get('test_session_id') or request.form.get('testSessionId')
#     if not test_session_id:
#         return jsonify({"error": "Missing test_session_id"}), 400

#     filename = secure_filename(video_file.filename or f"session_{test_session_id}.webm")
#     save_name = f"session_{test_session_id}_{filename}"
#     save_path = os.path.join(UPLOAD_DIR, save_name)

#     # Save file
#     video_file.save(save_path)  

#     # Validate mime (optional)
#     mime = video_file.mimetype or "application/octet-stream"
#     size = os.path.getsize(save_path)

#     # Insert record into mmse_session_videos and update mmse_test_sessions.video_path
#     conn = get_connection()
#     cursor = conn.cursor()
#     cursor.execute("""
#         INSERT INTO mmse_session_videos (test_session_id, file_path, mime_type, size_bytes)
#         VALUES (%s, %s, %s, %s)
#     """, (test_session_id, save_path, mime, size))
#     video_id = cursor.lastrowid

#     # Also update test session's video_path and ended_at (mark end of test)
#     try:
#         cursor.execute("UPDATE mmse_test_sessions SET video_path = %s, ended_at = NOW() WHERE id = %s",
#                        (save_path, test_session_id))
#     except Exception:
#         # If underlying schema lacks columns, ignore gracefully
#         pass

#     conn.commit()
#     cursor.close()
#     conn.close()

#     return jsonify({"message": "video saved", "video_id": video_id, "path": save_path})

import cv2
from deepface import DeepFace
import json
from db import get_connection

@app.route('/upload_session_video', methods=['POST'])
def upload_session_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video file sent"}), 400

    video_file = request.files['video']
    test_session_id = request.form.get('test_session_id') or request.form.get('testSessionId')
    if not test_session_id:
        return jsonify({"error": "Missing test_session_id"}), 400

    filename = secure_filename(video_file.filename or f"session_{test_session_id}.webm")
    save_name = f"session_{test_session_id}_{filename}"
    save_path = os.path.join(UPLOAD_DIR, save_name)
    video_file.save(save_path)

    # Save to DB
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO mmse_session_videos (test_session_id, file_path)
        VALUES (%s, %s)
    """, (test_session_id, save_path))
    video_id = cursor.lastrowid
    conn.commit()

    # --- AUTOMATED DEEPFACE ANALYSIS ---
    cap = cv2.VideoCapture(save_path)
    frame_rate = cap.get(cv2.CAP_PROP_FPS) or 25
    frame_idx = 0
    metrics_cursor = conn.cursor()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Analyze every 10th frame to reduce load
        if frame_idx % 10 == 0:
            try:
                result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
                dominant_emotion = result[0]['dominant_emotion']
                timestamp_ms = int((frame_idx / frame_rate) * 1000)
                metrics_cursor.execute("""
                    INSERT INTO mmse_facial_metrics (session_video_id, timestamp_ms, emotion_json)
                    VALUES (%s, %s, %s)
                """, (video_id, timestamp_ms, json.dumps({"dominant_emotion": dominant_emotion})))
            except Exception as e:
                print(f"⚠️ Error analyzing frame {frame_idx}: {e}")

        frame_idx += 1

    conn.commit()
    metrics_cursor.close()
    cursor.close()
    conn.close()
    cap.release()

    return jsonify({"message": "video saved and analyzed", "video_id": video_id})



# Optional: accept per-frame metrics (emotion probs / landmarks) from client
@app.route('/upload_frame_metrics', methods=['POST'])
def upload_frame_metrics():
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "Invalid JSON"}), 400

    test_session_id = payload.get('test_session_id')
    metrics = payload.get('metrics', [])
    if not test_session_id or not metrics:
        return jsonify({"error": "Missing test_session_id or metrics"}), 400

    # Find latest video id for this session (if any)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM mmse_session_videos WHERE test_session_id = %s ORDER BY uploaded_at DESC LIMIT 1", (test_session_id,))
    row = cursor.fetchone()
    session_video_id = row['id'] if row else None

    # Insert metrics
    insert_count = 0
    if session_video_id:
        insert_cursor = conn.cursor()
        for m in metrics:
            ts = m.get('timestamp_ms', None)
            emotion = json.dumps(m.get('emotion')) if m.get('emotion') is not None else None
            landmarks = json.dumps(m.get('landmarks')) if m.get('landmarks') is not None else None
            aus = json.dumps(m.get('aus')) if m.get('aus') is not None else None
            insert_cursor.execute("""
                INSERT INTO mmse_facial_metrics (session_video_id, timestamp_ms, emotion_json, landmarks_json, au_json)
                VALUES (%s, %s, %s, %s, %s)
            """, (session_video_id, ts, emotion, landmarks, aus))
            insert_count += 1
        conn.commit()
        insert_cursor.close()

    cursor.close()
    conn.close()
    return jsonify({"inserted": insert_count})


@app.route('/admin')
def admin_dashboard():
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT u.id AS user_id, u.name AS user_name,
               s.id AS session_id, s.started_at, s.ended_at,
               s.video_path, s.consent
        FROM mmse_test_sessions s
        JOIN users u ON s.user_id = u.id
        ORDER BY s.started_at DESC
    """
    cursor.execute(query)
    sessions = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin_dashboard.html', sessions=sessions)

    # Lazy-load emotion model safely inside request handling
    try:
        model = get_emotion_model()
    except Exception as e:
        print("❌ get_emotion_model failed:", e)
        return jsonify({"error": "Emotion model load failed"}), 500

    try:
        from deepface import DeepFace
        result = DeepFace.analyze(
            frame,
            actions=['emotion'],
            enforce_detection=False,
            models={"emotion": model}
        )
        emotion = result[0]['dominant_emotion']
    except Exception as e:
        import traceback
        traceback.print_exc()
        emotion = "unknown"

def mmse_score_percentage(user_id, test_session_id):
    """
    Calculate MMSE test contribution to Alzheimer's risk.
    Lower MMSE score → higher risk.
    Returns a percentage (0-100).
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get latest scores for the session
    cursor.execute("""
        SELECT SUM(score_awarded) AS total_score,
               SUM(q.max_score) AS max_score
        FROM mmse_responses r
        JOIN mmse_questions q ON r.question_id = q.id
        WHERE r.user_id = %s AND r.test_session_id = %s
    """, (user_id, test_session_id))
    
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not result or not result['max_score'] or result['max_score'] == 0:
        return 50  # default medium risk if no data
    
    score_percent = (result['total_score'] / result['max_score']) * 100
    mmse_risk = 100 - score_percent  # lower score = higher risk
    return mmse_risk


def emotion_risk_percentage(session_id):
    """
    Calculate risk from facial emotion metrics.
    More negative emotions (sad, fear, angry) → higher risk.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT emotion_json
        FROM mmse_facial_metrics m
        JOIN mmse_session_videos v ON m.session_video_id = v.id
        WHERE v.test_session_id = %s
    """, (session_id,))
    
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if not rows:
        return 50  # default medium risk if no data
    
    negative_emotions = ['sad', 'angry', 'fear', 'disgust']
    negative_count = 0
    total_count = 0
    
    for row in rows:
        import json
        emotions = json.loads(row['emotion_json'])
        dominant = emotions.get('dominant_emotion', None)
        if dominant:
            total_count += 1
            if dominant.lower() in negative_emotions:
                negative_count += 1
                
    if total_count == 0:
        return 50
    
    emotion_risk = (negative_count / total_count) * 100
    return emotion_risk

@app.route('/alzheimer_risk/<int:user_id>/<int:session_id>', methods=['GET'])
def get_alzheimer_risk(user_id, session_id):
    try:
        mmse_risk = mmse_score_percentage(user_id, session_id)
        emotion_risk = emotion_risk_percentage(session_id)
        
        # Combine both (weight can be adjusted)
        # Example: 70% MMSE + 30% emotion
        combined_risk = 0.7 * mmse_risk + 0.3 * emotion_risk
        combined_risk = round(combined_risk, 2)
        
        return jsonify({
            "user_id": user_id,
            "session_id": session_id,
            "alzheimer_risk_percent": combined_risk
        })
       
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500






if __name__ == '__main__':
    print("🚀 Starting Flask server (no reloader, single-threaded)...")
    # Already set TF_CPP_MIN_LOG_LEVEL earlier
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=True, threaded=False)

