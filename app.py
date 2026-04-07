from flask import Flask, render_template, request, redirect, url_for, session ,send_from_directory 
import mysql.connector , os 
from datetime import datetime , timedelta

from groq import Groq
from flask import Flask, request, jsonify , send_file
import requests

import pandas as pd
import numpy as np
import math
import json

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import GradientBoostingClassifier
from sklearn.neighbors import KNeighborsClassifier

import pdfplumber
import re
import spacy

import csv
import io

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

import markdown

from sklearn.cluster import KMeans
import random

from werkzeug.utils import secure_filename
import uuid

import mysql.connector
app=Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR,'static','uploads')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# MySQL connection setup
mydb = mysql.connector.connect(
    host="localhost",
    user="root",          
    password="",          
    database="healthplan" 

)
cursor = mydb.cursor(dictionary=True)

@app.route("/record")
def record_page():
    cursor.execute("SELECT * FROM medical_records ORDER BY id DESC """)
    record = cursor.fetchall()
    return render_template("record.html",
                       records=record,
                       selected=None,
                       files=None)
    
@app.route("/save_record", methods=["POST"])
def save_record():

    name = request.form["name"]
    phone = request.form["phone"]
    email = request.form["email"]
    record_date = request.form["record_date"]
    record_time = request.form["record_time"]
    doctor_name = request.form["doctor_name"]
    doctor_contact = request.form["doctor_contact"]
    doctor_location = request.form["doctor_location"]
    
    share_token = str(uuid.uuid4())
    
    query = """
    INSERT INTO medical_records
    (name, phone, email, record_date, record_time,
     doctor_name, doctor_contact, doctor_location,
    share_token)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    cursor.execute(query, (
        name, phone, email, record_date, record_time,
        doctor_name, doctor_contact, doctor_location,
        share_token
    ))
    
    record_id = cursor.lastrowid   

    files = request.files.getlist("files")
    
    for file in files:
        if file and file.filename != "":
            
         unique_name = str(uuid.uuid4()) + "_" + secure_filename(file.filename)

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
        file.save(file_path)

        cursor.execute(
            "INSERT INTO record_files (record_id, file_name) VALUES (%s, %s)",
            (record_id, unique_name)
        )

    mydb.commit()
    
    return redirect(url_for("record"))



# 🟢 View Record
@app.route("/record/<int:id>")
def view_record(id):
    
    cursor.execute("SELECT * FROM medical_records ORDER BY id DESC")
    record = cursor.fetchall()

    cursor.execute("SELECT * FROM record_files WHERE record_id=%s", (id,))
    files = cursor.fetchall()

    cursor.execute("SELECT * FROM medical_records WHERE id=%s", (id,))
    selected = cursor.fetchone()

    return render_template("record.html",
                       records=record,
                       selected=selected,
                       files=files)


@app.route("/edit/<int:id>")
def edit_record(id):

    cursor.execute("SELECT * FROM medical_records ORDER BY id DESC """)
    records = cursor.fetchall()

    cursor.execute("SELECT * FROM medical_records WHERE id=%s", (id,))
    selected = cursor.fetchone()
    
    cursor.execute("SELECT * FROM record_files WHERE record_id=%s", (id,))
    files = cursor.fetchall()

    return render_template("record.html",
                       records=records,
                       selected=selected,
                       edit_record=selected,
                       files=files)


@app.route("/update/<int:id>", methods=["POST"])
def update_record(id):

    name = request.form["name"]
    phone = request.form["phone"]
    email = request.form["email"]
    record_date = request.form["record_date"]
    record_time = request.form["record_time"]
    doctor_name = request.form["doctor_name"]
    doctor_contact = request.form["doctor_contact"]
    doctor_location = request.form["doctor_location"]

    query = """
    UPDATE medical_records SET
    name=%s, phone=%s, email=%s,
    record_date=%s, record_time=%s,
    doctor_name=%s, doctor_contact=%s,
    doctor_location=%s
    WHERE id=%s
    """

    cursor.execute(query, (
        name, phone, email,
        record_date, record_time,
        doctor_name, doctor_contact,
        doctor_location, id
    ))

    mydb.commit()
    
    
    files = request.files.getlist("files")
    
    for file in files:
        if file and file.filename != "":
            
         unique_name = str(uuid.uuid4()) + "_" + secure_filename(file.filename)

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
        file.save(file_path)

        cursor.execute(
            "INSERT INTO record_files (record_id, file_name) VALUES (%s, %s)",
            (id, unique_name)
        )

    mydb.commit()
    
    return redirect(url_for("record",id=id))


@app.route("/delete/<int:id>")
def delete_record(id):

    cursor.execute("DELETE FROM medical_records WHERE id=%s", (id,))
    cursor.execute("DELETE FROM record_files WHERE record_id=%s", (id,))
    
    mydb.commit()

    return redirect(url_for("record"))


@app.route("/share/<int:id>")
def share_record(id):

    cursor.execute("SELECT * FROM medical_records WHERE id=%s", (id,))
    record = cursor.fetchone()

    if not record:
        return "Record not found"

    return render_template("share.html", record=record)



CSV_PATH = "HealApp---Health-Monitering-Web-Application/data/hospital.csv"

df_hospitals = pd.read_csv(CSV_PATH)
df_hospitals.columns = df_hospitals.columns.str.strip()
df_hospitals["latitude"]  = pd.to_numeric(df_hospitals["latitude"],  errors="coerce")
df_hospitals["longitude"] = pd.to_numeric(df_hospitals["longitude"], errors="coerce")
df_hospitals.dropna(subset=["latitude", "longitude"], inplace=True)
df_hospitals.reset_index(drop=True, inplace=True)


# ── Vectorized haversine (processes all 1000 rows at once) ─────────
def haversine(lat1, lon1, lat2_arr, lon2_arr):
    R     = 6371
    lat1r = math.radians(lat1)
    lon1r = math.radians(lon1)
    lat2r = np.radians(lat2_arr)
    lon2r = np.radians(lon2_arr)
    dlat  = lat2r - lat1r
    dlon  = lon2r - lon1r
    a = np.sin(dlat/2)**2 + math.cos(lat1r) * np.cos(lat2r) * np.sin(dlon/2)**2
    return np.round(R * 2 * np.arcsin(np.sqrt(a)), 2)


# ── Scalar haversine for single point (used in /route) ────────────
def haversine_scalar(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return round(R * 2 * math.asin(math.sqrt(a)), 2)


# ── Reverse geocode ────────────────────────────────────────────────
def reverse_location(lat, lon):
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json"},
            headers={"User-Agent": "heal-visualizer"},
            timeout=5
        )
        if r.status_code == 200:
            return r.json().get("display_name", "")
    except:
        pass
    return "Unknown location"


# ── VISUALIZER PAGE ────────────────────────────────────────────────
@app.route("/visualizer")
def visualizer():
    return render_template("visualizer.html")


# ── FIND TOP 5 NEAREST HOSPITALS ───────────────────────────────────
@app.route("/visualize", methods=["POST"])
def visualize():
    data     = request.get_json(silent=True, force=True) or {}
    user_lat = float(data["lat"])
    user_lon = float(data["lon"])

    df = df_hospitals.copy()

    # Compute distance for ALL rows at once using numpy — fast for 1000+
    df["distance"] = haversine(
        user_lat, user_lon,
        df["latitude"].values,
        df["longitude"].values
    )

    # Pick top 5 nearest
    top5 = df.nsmallest(5, "distance")

    result = [
        {
            "name":     str(r.get("name",     "—")),
            "city":     str(r.get("city",     "—")),
            "address":  str(r.get("address",  "—")),
            "pincode":  str(r.get("pincode",  "")),
            "contact":  str(r.get("contact",  "—")),
            "website":  str(r.get("website",  "")),
            "lat":      float(r["latitude"]),
            "lon":      float(r["longitude"]),
            "distance": float(r["distance"])
        }
        for _, r in top5.iterrows()
    ]

    return jsonify(result)


# ── ROUTE DETAILS ──────────────────────────────────────────────────
@app.route("/route", methods=["POST"])
def route():
    try:
        data = request.get_json()
        slat = float(data["start_lat"])
        slon = float(data["start_lon"])
        elat = float(data["end_lat"])
        elon = float(data["end_lon"])

        return jsonify({
            "status":   "ok",
            "distance": haversine_scalar(slat, slon, elat, elon),
            "from":     reverse_location(slat, slon),
            "to":       reverse_location(elat, elon),
            "coords":   [[slat, slon], [elat, elon]]
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400



@app.route('/')
def open_page():
    return render_template('open.html')

@app.route('/record')
def record():
    return render_template('record.html')

@app.route('/game')
def game():
    return render_template('game.html')




@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == 'admin' and password == '1234':
            return redirect('/index')  # ✅ Go to index, not open page
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/')
def index():
    if "username" in session:
        return render_template("index.html")
    else:
        return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # handle registration logic
        pass
    return render_template("register.html")

# Homepage
@app.route('/index')
def home():
    return render_template('index.html')


GROQ_API_KEY = ""
API_URL = "https://api.groq.com/openai/v1/chat/completions"

@app.route("/chatbot")
def chatbot():
    return render_template("chatbot.html")


@app.route("/chatbot", methods=["POST"])
def chat():
    try:
        mydb.ping(reconnect=True, attempts=3, delay=2)
        data       = request.get_json(silent=True, force=True) or {}
        user_msg   = data.get("message", "").strip()
        session_id = data.get("session_id", "")

        if not user_msg:
            return jsonify({"error": "Empty message"}), 400

        if not session_id:
            session_id = str(uuid.uuid4())
            title = user_msg[:60] + ("…" if len(user_msg) > 60 else "")
            cursor = mydb.cursor()
            cursor.execute(
                "INSERT INTO chat_sessions (session_id, title) VALUES (%s, %s)",
                (session_id, title)
            )
            mydb.commit()

        # Save user message
        cursor = mydb.cursor()
        cursor.execute(
            "INSERT INTO chat_messages (session_id, role, message) VALUES (%s, %s, %s)",
            (session_id, "user", user_msg)
        )
        mydb.commit()

        # Groq API call
        payload = {
            "model": "openai/gpt-oss-20b",
            "messages": [
                {
                    "role": "system",
                    "content": "You are HealMate, a friendly and knowledgeable AI health assistant built into HealApp. Give medically safe, practical guidance. Never diagnose. Encourage users to see a doctor for serious concerns. Keep answers clear and structured."
                },
                {"role": "user", "content": user_msg}
            ],
            "max_tokens": 800,
            "temperature": 0.7
        }

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        data_resp = response.json()
        reply = data_resp["choices"][0]["message"]["content"]

        # Save bot reply
        cursor = mydb.cursor()
        cursor.execute(
            "INSERT INTO chat_messages (session_id, role, message) VALUES (%s, %s, %s)",
            (session_id, "bot", reply)
        )
        mydb.commit()

        return jsonify({"reply": reply, "session_id": session_id})

    except Exception as e:
        print("CHATBOT ERROR:", str(e))
        return jsonify({"reply": "Problem contacting AI service. Please try again.", "session_id": session_id if 'session_id' in locals() else ""})


# ── GET ALL SESSIONS (for history sidebar) ─────────────────────────
@app.route("/chat_sessions")
def get_sessions():
    try:
        mydb.ping(reconnect=True, attempts=3, delay=2)
        cursor = mydb.cursor(dictionary=True)
        cursor.execute("""
            SELECT session_id, title, created_at
            FROM chat_sessions
            ORDER BY created_at DESC
            LIMIT 50
        """)
        rows = cursor.fetchall()
        for r in rows:
            r["created_at"] = r["created_at"].strftime("%d %b %Y, %I:%M %p")
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── GET MESSAGES FOR A SESSION ─────────────────────────────────────
@app.route("/chat_history/<session_id>")
def get_chat_history(session_id):
    try:
        mydb.ping(reconnect=True, attempts=3, delay=2)
        cursor = mydb.cursor(dictionary=True)
        cursor.execute("""
            SELECT role, message, created_at
            FROM chat_messages
            WHERE session_id = %s
            ORDER BY id ASC
        """, (session_id,))
        rows = cursor.fetchall()
        for r in rows:
            r["created_at"] = r["created_at"].strftime("%I:%M %p")
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── DELETE A SESSION ───────────────────────────────────────────────
@app.route("/delete_session/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    try:
        mydb.ping(reconnect=True, attempts=3, delay=2)
        cursor = mydb.cursor()
        cursor.execute("DELETE FROM chat_messages WHERE session_id=%s", (session_id,))
        cursor.execute("DELETE FROM chat_sessions WHERE session_id=%s", (session_id,))
        mydb.commit()
        return jsonify({"success": True})
    except Exception as e:
        mydb.rollback()
        return jsonify({"error": str(e)}), 500



@app.route('/encyclopedia')
def encyclopedia():
    return render_template('encyclopedia.html')

@app.route('/encyclopedia/search')
def encyclopedia_search():

    import urllib.parse
    import requests

    query = request.args.get("q")

    if not query:
        return jsonify({"error": "No query provided"})

    headers = {
        "User-Agent": "HealthPlanApp/1.0 (student project)"
    }

    query = urllib.parse.quote(query.strip())

    # 1️⃣ search title
    search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json"
    search_res = requests.get(search_url, headers=headers).json()

    if not search_res["query"]["search"]:
        return jsonify({"error": "No data found"})

    title = search_res["query"]["search"][0]["title"]
    title_encoded = urllib.parse.quote(title)

    # 2️⃣ get FULL page HTML
    full_url = f"https://en.wikipedia.org/w/api.php?action=parse&page={title_encoded}&prop=text&format=json"

    page_res = requests.get(full_url, headers=headers).json()

    full_html = page_res["parse"]["text"]["*"]

    # 3️⃣ image + summary
    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title_encoded}"
    summary_data = requests.get(summary_url, headers=headers).json()

    return jsonify({
        "title": title,
        "summary": summary_data.get("extract", ""),
        "image": summary_data.get("thumbnail", {}).get("source", ""),
        "content": full_html,   # 🔥 FULL ARTICLE
        "link": f"https://en.wikipedia.org/wiki/{title_encoded}"
    })


@app.route('/healthfacts')
def healthfacts():
    return render_template('healthfacts.html')


@app.route('/calorie')
def calorie():
    return render_template("calorie.html")



food_df = pd.read_csv("HealApp---Health-Monitering-Web-Application/data/Indian_Food_Nutrition_Processed.csv")
food_df.columns = food_df.columns.str.strip()
food_df["Food"] = food_df["Food"].str.lower()
food = food_df["Food"].astype(str).tolist()

@app.route("/calculate_bmi", methods=["POST"])
def calculate_bmi():
    data = request.get_json()

    age = int(data["age"])
    height = float(data["height"])   # in cm
    weight = float(data["weight"])   # in kg

    height_m = height / 100
    bmi = weight / (height_m ** 2)

    # Classification
    if bmi < 18.5:
        category = "Underweight"
        required_calories = 2500
    elif 18.5 <= bmi < 24.9:
        category = "Normal"
        required_calories = 2000
    elif 25 <= bmi < 29.9:
        category = "Overweight"
        required_calories = 1700
    else:
        category = "Obese"
        required_calories = 1500

    return jsonify({
        "bmi": round(bmi, 2),
        "category": category,
        "required_calories": required_calories
    })


@app.route("/get_food_info", methods=["POST"])
def get_food_info():
    data = request.get_json()
    
    food_name = data["food_name"]
    
    result = food_df[food_df["Food"].str.lower() == food_name.lower()]

    if result.empty:
        return jsonify({"error": "Food not found"})

    food = result.iloc[0]

    return jsonify({
        "food_name": food["Food"],
        "calories": float(food["Calories (kcal)"]),
        "protein": float(food["Protein (g)"]),
        "carbs": float(food["Carbohydrates (g)"]),
        "fat": float(food["Fats (g)"])
    })



@app.route("/calculate_total", methods=["POST"])
def calculate_total():
    data = request.get_json()

    foods = data["foods"]   # list of food items
    required_calories = data["required_calories"]

    total_calories = 0
    total_protein = 0
    total_carbs = 0
    total_fat = 0

    for item in foods:
        total_calories += item["calories"]
        total_protein += item["protein"]
        total_carbs += item["carbs"]
        total_fat += item["fat"]

    # Compare with required calories
    if total_calories > required_calories:
        status = "Excess Intake"
    elif total_calories < required_calories:
        status = "Low Intake"
    else:
        status = "Perfect Intake"

    return jsonify({
        "total_calories": round(total_calories, 2),
        "total_protein": round(total_protein, 2),
        "total_carbs": round(total_carbs, 2),
        "total_fat": round(total_fat, 2),
        "status": status
    })

@app.route("/suggest")
def suggest():
    
    query = request.args.get("q","").lower()
    
    results = [food for food in food
               if query in food.lower()]
    
    return{"suggestions": results[0:10]}       




df = pd.read_csv('HealApp---Health-Monitering-Web-Application/data/disease_symptoms-1.csv')

SYMPTOMS  = list(df.columns[1:]) 
DISEASES  = list(df['Disease'])   

X = df[SYMPTOMS].values
y = df['Disease'].values

le = LabelEncoder()
y_encoded = le.fit_transform(y)

# Train 3 models — ensemble for better accuracy
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

rf  = RandomForestClassifier(n_estimators=200, random_state=42, max_depth=None, min_samples_split=2)
knn = KNeighborsClassifier(n_neighbors=3, metric='euclidean')
dt  = DecisionTreeClassifier(random_state=42)

rf.fit(X, y_encoded)
knn.fit(X, y_encoded)
dt.fit(X, y_encoded)

print(f"✅ Models trained — {len(SYMPTOMS)} symptoms, {len(DISEASES)} diseases")
print(f"   RF Accuracy  : {accuracy_score(y_encoded, rf.predict(X))*100:.1f}%")

# Feature importance for symptom ranking
IMPORTANCE = dict(zip(SYMPTOMS, rf.feature_importances_))


# ── HELPER: SYMPTOM MATCHING SCORE ───────────────────────────────
def get_symptom_score(disease_row, input_vec):
    """How many of the user's symptoms match this disease."""
    matched  = sum(1 for i, s in enumerate(input_vec) if s == 1 and disease_row[i] == 1)
    total_sx = sum(input_vec)
    return matched, total_sx


# ── ROUTES ────────────────────────────────────────────────────────

@app.route('/symptom')
def symptom():
    return render_template('symptom.html', symptoms=SYMPTOMS)


@app.route('/predict_disease', methods=['POST'])
def predict_disease():
    try:
        data = request.get_json(silent=True, force=True) or {}
        selected = data.get('symptoms', [])

        if not selected:
            return jsonify({'error': 'Please select at least one symptom'}), 400

        if len(selected) < 2:
            return jsonify({'error': 'Please select at least 2 symptoms for accurate prediction'}), 400

        input_vec = [1 if s in selected else 0 for s in SYMPTOMS]
        input_arr = np.array(input_vec).reshape(1, -1)

        rf_proba  = rf.predict_proba(input_arr)[0]
        knn_proba = knn.predict_proba(input_arr)[0]
        dt_proba  = dt.predict_proba(input_arr)[0]

        ensemble_proba = (rf_proba * 0.6) + (knn_proba * 0.25) + (dt_proba * 0.15)

        top_indices = np.argsort(ensemble_proba)[::-1][:5]

        predictions = []
        for idx in top_indices:
            disease_name = le.inverse_transform([idx])[0]
            confidence   = float(ensemble_proba[idx])
            if confidence < 0.01:
                continue

            disease_row = df[df['Disease'] == disease_name][SYMPTOMS].values[0]
            matched, total = get_symptom_score(disease_row, input_vec)

            missing_sx = [
                SYMPTOMS[i] for i in range(len(SYMPTOMS))
                if disease_row[i] == 1 and input_vec[i] == 0
            ]

            matched_sx = [
                SYMPTOMS[i] for i in range(len(SYMPTOMS))
                if disease_row[i] == 1 and input_vec[i] == 1
            ]

            predictions.append({
                'disease':     disease_name,
                'confidence':  round(confidence * 100, 1),
                'matched_sx':  matched_sx,
                'missing_sx':  missing_sx[:5],  # top 5 missing
                'match_count': matched,
                'total_input': total,
            })

        if not predictions:
            return jsonify({'error': 'Could not predict — try selecting more symptoms'}), 400
        
        important = sorted(
            [(s, IMPORTANCE.get(s, 0)) for s in selected],
            key=lambda x: x[1], reverse=True
        )[:5]

        return jsonify({
            'success':     True,
            'predictions': predictions,
            'important_symptoms': [{'symptom': s, 'importance': round(imp * 100, 2)} for s, imp in important],
            'total_symptoms_selected': len(selected),
            'model_note': 'Ensemble: Random Forest + KNN + Decision Tree',
            'disclaimer': 'This is an AI-based prediction tool for educational purposes only. Always consult a qualified doctor for diagnosis and treatment.'
        })

    except Exception as e:
        print('PREDICT ERROR:', str(e))
        return jsonify({'error': str(e)}), 500


@app.route('/symptom_info', methods=['GET'])
def symptom_info():
    """Return which diseases each symptom is associated with."""
    try:
        symptom = request.args.get('symptom', '')
        if symptom not in SYMPTOMS:
            return jsonify({'error': 'Symptom not found'}), 404

        idx = SYMPTOMS.index(symptom)
        associated = [
            df['Disease'].iloc[i]
            for i in range(len(df))
            if df[SYMPTOMS[idx]].iloc[i] == 1
        ]
        importance = round(IMPORTANCE.get(symptom, 0) * 100, 2)

        return jsonify({
            'symptom':    symptom,
            'importance': importance,
            'associated_diseases': associated,
            'count': len(associated)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/all_symptoms')
def all_symptoms():
    """Return all symptoms with their importance scores."""
    ranked = sorted(
        [{'symptom': s, 'importance': round(IMPORTANCE[s] * 100, 2)} for s in SYMPTOMS],
        key=lambda x: x['importance'], reverse=True
    )
    return jsonify({'symptoms': ranked, 'total': len(SYMPTOMS)})


@app.route('/all_diseases')
def all_diseases():
    """Return all diseases with their symptom lists."""
    result = []
    for _, row in df.iterrows():
        sx = [SYMPTOMS[i] for i in range(len(SYMPTOMS)) if row[SYMPTOMS[i]] == 1]
        result.append({'disease': row['Disease'], 'symptoms': sx, 'symptom_count': len(sx)})
    return jsonify({'diseases': result, 'total': len(result)})



@app.route('/finhealth')
def finhealth():
    return render_template("finhealth.html")


@app.route('/insurance')
def insurance():
    return render_template("insurance.html")

@app.route('/insurance/a_z')
def a_z_terms():
    return render_template("a_z_terms.html")


client = Groq(api_key="")


def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
    return text


def ai_policy_summary(text):

    text = text[:4000]

    prompt = f"""
    You are an insurance expert.

    Read the following insurance policy document and explain it in SIMPLE language.

    Give:
    - Coverage amount
    - Waiting periods
    - Copay
    - Room rent limits
    - Benefits
    - Exclusions
    - Important notes

    Make it easy for normal people to understand.

    Policy text:
    {text}
    """


    chat = client.chat.completions.create(
        model="openai/gpt-oss-20b",   
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    raw_content=chat.choices[0].message.content
    
    return markdown.markdown(raw_content,extensions=['tables','fenced_code'])


@app.route("/policy_explainer", methods=["GET", "POST"])
def policy_explainer():

    summary = None

    if request.method == "POST":
        file = request.files.get("policy")

        if file:
            text = extract_text_from_pdf(file)
            summary = ai_policy_summary(text)

    return render_template("policy_explainer.html", summary=summary)


@app.route('/insurance/claim_guide')
def claim_guide():
    steps = [
        "Fill claim form",
        "Attach documents",
        "Submit to insurance",
        "Track approval",
        "Receive reimbursement"
    ]
    return render_template("claim_guide.html", steps=steps)

@app.route('/insurance/faq')
def faq():
    faqs = [
        {"q": "What is insurance?", "a": "Insurance is a contract to protect you financially."},
        {"q": "When to buy?", "a": "Buy early to cover risks."},
        {"q": "Family vs Individual?", "a": "Choose based on coverage needs."},
    ]
    return render_template("faq.html", faqs=faqs)


@app.route('/finance')
def finance():
    return render_template("finance.html")

@app.route('/finance/sip', methods=['GET', 'POST'])
def sip_calculator():
    result = None
    if request.method == 'POST':
        P = float(request.form['monthly'])
        R = float(request.form['return_rate']) / 100 / 12
        N = int(request.form['years']) * 12
        amount = P * ((pow(1 + R, N) - 1) / R) * (1 + R)
        result = f"Future Value: ₹{amount:.2f}"
    return render_template("sip_calculator.html", result=result)



@app.route("/finance/expense")
def expense():
    return render_template("expense.html")

@app.route("/finance/add_expense", methods=["POST"])
def add_expense():
    data = request.get_json()

    cursor = mydb.cursor()

    cursor.execute("""
        INSERT INTO expenses (date, time, name, category, amount)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        data["date"],
        data["time"],
        data["name"],
        data["category"],
        data["amount"]
    ))

    mydb.commit()

    return jsonify({"message": "Expense added"})

@app.route("/finance/get_expenses")
def get_expenses():
    
    cursor = mydb.cursor(dictionary=True)

    cursor.execute("SELECT * FROM expenses ORDER BY id DESC")
    result = cursor.fetchall()
    
    for row in result:
        if row["time"]:
            row["time"] = str(row["time"])

    return jsonify(result)

@app.route("/finance/delete_expense/<int:id>", methods=["DELETE"])
def delete_expense(id):
    cursor = mydb.cursor()

    cursor.execute("DELETE FROM expenses WHERE id=%s", (id,))
    mydb.commit()

    return jsonify({"message": "Deleted"})

@app.route("/finance/download_csv")
def download_csv():

    cursor = mydb.cursor()

    cursor.execute("SELECT date, time, name, category, amount FROM expenses")
    rows = cursor.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Date", "Time", "Name", "Category", "Amount"])

    for row in rows:
        writer.writerow(row)

    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name="expense_report.csv"
    )


@app.route('/finance/emi', methods=['GET', 'POST'])
def emi_calculator():
    emi = None
    if request.method == 'POST':
        P = float(request.form['loan'])
        R = float(request.form['rate']) / 12 / 100
        N = int(request.form['tenure'])
        emi = (P * R * pow(1 + R, N)) / (pow(1 + R, N) - 1)
    return render_template("emi_calculator.html", emi=emi)

@app.route('/finance/investment', methods=['GET', 'POST'])
def investment_calculator():
    future = None
    if request.method == 'POST':
        P = float(request.form['principal'])
        R = float(request.form['rate']) / 100
        N = int(request.form['years'])
        future = P * pow(1 + R, N)
    return render_template("investment_calculator.html", future=future)

@app.route('/finance/tips')
def finance_tips():
    tips = [
        "Invest regularly in SIPs",
        "Maintain an emergency fund of 6 months expenses",
        "Avoid high-interest debt",
    ]
    return render_template("finance_tips.html", tips=tips)

from datetime import date

@app.route('/foodmed')
def foodmed():

    cursor.execute("SELECT * FROM medicines")
    medicines = cursor.fetchall()

    today = date.today()
    alerts = []

    for m in medicines:
        if m['expiry_date']:
            days_left = (m['expiry_date'] - today).days
            if days_left <= 5:
                alerts.append(f"⚠ {m['name']} expiring in {days_left} days")
        if m['stock'] is not None and m['stock'] <= 5:
            alerts.append(f"⚠ {m['name']} low stock ({m['stock']} left)")

    cursor.execute("SELECT * FROM meals WHERE date = %s", (today,))
    meals = cursor.fetchall()

    return render_template("foodmed.html",
                           medicines=medicines,
                           alerts=alerts,
                           meals=meals)


@app.route('/add_medicine', methods=['POST'])
def add_medicine():
    try:
        data = request.get_json()       
        name     = data.get('name', '').strip()
        dosage   = data.get('dosage', '').strip()
        time     = data.get('time', '')
        relation = data.get('relation', 'After Food')
        expiry   = data.get('expiry') or None  
        stock    = data.get('stock') or 0

        if not name:
            return jsonify({"error": "Medicine name is required"}), 400

        query = """
            INSERT INTO medicines (name, dosage, time, food_relation, expiry_date, stock)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (name, dosage, time, relation, expiry, stock))
        mydb.commit()

        new_id = cursor.lastrowid         

        return jsonify({
            "success": True,
            "id": new_id,
            "message": f"{name} added successfully"
        })

    except Exception as e:
        mydb.rollback()
        return jsonify({"error": str(e)}), 500



@app.route('/taken/<int:id>', methods=['GET', 'POST'])   
def mark_taken(id):
    try:
        today = date.today()

        cursor.execute(
            "SELECT id FROM intake_history WHERE medicine_id = %s AND date = %s",
            (id, today)
        )
        existing = cursor.fetchone()

        if existing:
            return jsonify({"success": True, "message": "Already marked"}), 200

        query = """
            INSERT INTO intake_history (medicine_id, date, status)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (id, today, "Taken"))

        cursor.execute(
            "UPDATE medicines SET stock = stock - 1 WHERE id = %s AND stock > 0",
            (id,)
        )
        mydb.commit()

        return jsonify({"success": True, "message": "Medicine marked as taken"})

    except Exception as e:
        mydb.rollback()
        return jsonify({"error": str(e)}), 500
    

@app.route('/add_meal_item', methods=['POST'])
def add_meal_item():
    try:
        data      = request.get_json(silent=True, force=True) or {}
        meal_type = data.get('meal_type', '').strip()
        food_name = data.get('food_name', '').strip()
        quantity  = data.get('quantity', '').strip()
        note      = data.get('note', '').strip()       # medicine taken with meal

        if not meal_type or not food_name:
            return jsonify({'error': 'meal_type and food_name required'}), 400

        today = date.today()
        cursor.execute("""
            INSERT INTO meals (date, meal_type, food_name, quantity, note, status)
            VALUES (%s, %s, %s, %s, %s, 'Pending')
        """, (today, meal_type, food_name, quantity, note))
        mydb.commit()

        return jsonify({'success': True, 'id': cursor.lastrowid})

    except Exception as e:
        mydb.rollback()
        print('ADD MEAL ITEM ERROR:', str(e))
        return jsonify({'error': str(e)}), 500


@app.route('/mark_meal_done', methods=['POST'])
def mark_meal_done():
    try:
        data      = request.get_json(silent=True, force=True) or {}
        meal_type = data.get('meal_type', '').strip()

        if not meal_type:
            return jsonify({'error': 'meal_type required'}), 400

        today = date.today()
        cursor.execute("""
            UPDATE meals SET status = 'Done'
            WHERE date = %s AND meal_type = %s
        """, (today, meal_type))
        mydb.commit()

        return jsonify({'success': True})

    except Exception as e:
        mydb.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/delete_meal_item/<int:id>', methods=['DELETE'])
def delete_meal_item(id):
    try:
        cursor.execute("DELETE FROM meals WHERE id = %s", (id,))
        mydb.commit()
        return jsonify({'success': True})
    except Exception as e:
        mydb.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/get_meals')
def get_meals():
    try:
        today = date.today()
        cursor.execute("""
            SELECT id, meal_type, food_name, quantity, note, status
            FROM meals
            WHERE date = %s
            ORDER BY id ASC
        """, (today,))
        rows = cursor.fetchall()

        # Group by meal_type
        result = { 'Breakfast': [], 'Lunch': [], 'Dinner': [] }
        done_meals = set()

        for r in rows:
            mt = r['meal_type']
            if mt in result:
                result[mt].append({
                    'id':        r['id'],
                    'food_name': r['food_name'],
                    'quantity':  r['quantity'] or '',
                    'note':      r['note'] or '',
                    'status':    r['status']
                })
                if r['status'] == 'Done':
                    done_meals.add(mt)

        return jsonify({
            'success':    True,
            'meals':      result,
            'done_meals': list(done_meals)
        })

    except Exception as e:
        print('GET MEALS ERROR:', str(e))
        return jsonify({'error': str(e)}), 500


client = Groq(api_key="")

@app.route('/food_ai', methods=['POST'])
def food_ai():
    try:
        data = request.get_json(silent=True, force=True) or {}

        disease  = data.get('disease', '').strip()
        relation = data.get('relation', 'After Food')
        medicine = data.get('medicine', '').strip()

        if not disease:
            return jsonify({'error': 'Disease is required'}), 400

        prompt = f'''
You are a clinical nutritionist.
Disease: {disease}
Medicine timing: {relation}
Medicine: {medicine if medicine else 'Not specified'}
Suggest best foods, foods to avoid, and one tip. Keep it short.
        '''

        response = client.chat.completions.create(
            model='openai/gpt-oss-20b',
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=400
        )

        return jsonify({'success': True, 'suggestion': response.choices[0].message.content})

    except Exception as e:
        print('FOOD AI ERROR:', str(e))
        return jsonify({'error': str(e)}), 500


@app.route('/delete_medicine/<int:id>', methods=['DELETE'])
def delete_medicine(id):
    try:
       
        cursor.execute("DELETE FROM intake_history WHERE medicine_id = %s", (id,))
        cursor.execute("DELETE FROM medicines WHERE id = %s", (id,))
        mydb.commit()
        return jsonify({"success": True, "message": "Medicine deleted"})
    except Exception as e:
        mydb.rollback()
        return jsonify({"error": str(e)}), 500
    
    
    
@app.route('/download_meals_csv')
def download_meals_csv():
    try:
        filter_type = request.args.get("filter", "today")  # today / week / month
        today = date.today()

        cursor = mydb.cursor(dictionary=True)

        # ── FILTER LOGIC ─────────────────────
        if filter_type == "week":
            start = today - timedelta(days=7)
            
            cursor.execute("""
                SELECT date, meal_type, food_name, quantity, note, status, created_at
                FROM meals
                WHERE date BETWEEN %s AND %s
                ORDER BY date DESC, meal_type
            """, (start, today))

        elif filter_type == "month":
            cursor.execute("""
                SELECT date, meal_type, food_name, quantity, note, status, created_at
                FROM meals
                WHERE MONTH(date) = %s AND YEAR(date) = %s
                ORDER BY date DESC, meal_type
            """, (today.month, today.year))

        else:  # default today
            cursor.execute("""
                SELECT date, meal_type, food_name, quantity, note, status, created_at
                FROM meals
                WHERE date = %s
                ORDER BY meal_type
            """, (today,))

        rows = cursor.fetchall()

        # ── CSV ─────────────────────────────
        import io, csv
        out = io.StringIO()
        writer = csv.writer(out)

        writer.writerow(["Date", "Meal Type", "Food", "Qty", "Note", "Status", "Time"])

        for r in rows:
            writer.writerow([
                r["date"],
                r["meal_type"],
                r["food_name"],
                r["quantity"] or "",
                r["note"] or "",
                r["status"],
                r["created_at"]
            ])

        out.seek(0)

        return send_file(
            io.BytesIO(out.getvalue().encode()),
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"meal_log_{filter_type}.csv"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
 
 
@app.route("/calc")
def calc():
    return render_template("calc.html")

 
@app.route("/calc/body")
def body():
    return render_template("body.html")

@app.route("/download_body_pdf", methods=["POST"])
def download_body_pdf():
     try:
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        data = request.get_json()
        text = data.get("data", "")

        file_path = os.path.join(os.getcwd(), "body_report.pdf")

        doc = SimpleDocTemplate(file_path)
        styles = getSampleStyleSheet()

        content = []
        content.append(Paragraph("Body Composition Report", styles['Title']))
        content.append(Spacer(1, 12))

        for line in text.split("\n"):
            content.append(Paragraph(line, styles['Normal']))
            content.append(Spacer(1, 8))

        doc.build(content)
        
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404

        return send_file(file_path, as_attachment=True)
     except Exception as e:
        return jsonify({"error": str(e)}), 500


 
@app.route("/calc/meta")
def meta():
    return render_template("meta.html")

@app.route("/download_metabolism_pdf", methods=["POST"])
def download_metabolism_pdf():
    try:
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        data = request.get_json()
        text = data.get("data", "")

        file_path = os.path.join(os.getcwd(), "metabolism_report.pdf")

        doc = SimpleDocTemplate(file_path)
        styles = getSampleStyleSheet()

        content = []
        content.append(Paragraph("Metabolism & Energy Report", styles['Title']))
        content.append(Spacer(1, 12))

        for line in text.split("\n"):
            content.append(Paragraph(line, styles['Normal']))
            content.append(Spacer(1, 8))

        doc.build(content)
        
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404

        return send_file(file_path, as_attachment=True)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

 
@app.route("/calc/fit")
def fit():
    return render_template("fit.html")

@app.route("/download_fitness_pdf", methods=["POST"])
def download_fitness_pdf():
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    import os

    data = request.get_json()
    text = data.get("data", "")

    file_path = os.path.join(os.getcwd(), "fitness_report.pdf")

    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()

    content = []
    content.append(Paragraph("Fitness & Performance Report", styles['Title']))
    content.append(Spacer(1, 12))

    for line in text.split("\n"):
        if line.strip():
            content.append(Paragraph(line, styles['Normal']))
            content.append(Spacer(1, 8))

    doc.build(content)

    return send_file(file_path, as_attachment=True)

 
@app.route("/calc/risk")
def risk():
    return render_template("risk.html")
 
@app.route("/download_risk_pdf", methods=["POST"])
def download_risk_pdf():
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    import os

    data = request.get_json()
    text = data.get("data", "")

    file_path = os.path.join(os.getcwd(), "risk_report.pdf")

    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()

    content = []
    content.append(Paragraph("Health Risk Report", styles['Title']))
    content.append(Spacer(1, 12))

    for line in text.split("\n"):
        if line.strip():
            content.append(Paragraph(line, styles['Normal']))
            content.append(Spacer(1, 8))

    doc.build(content)

    return send_file(file_path, as_attachment=True)


@app.route("/calc/nutrition")
def nutrition():
    return render_template("nutrition.html")


@app.route("/download_nutrition_pdf", methods=["POST"])
def download_nutrition_pdf():
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    import os

    data = request.get_json()
    text = data.get("data", "")

    file_path = os.path.join(os.getcwd(), "nutrition_report.pdf")

    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()

    content = []
    content.append(Paragraph("Nutrition & Wellness Report", styles['Title']))
    content.append(Spacer(1, 12))

    for line in text.split("\n"):
        if line.strip():
            content.append(Paragraph(line, styles['Normal']))
            content.append(Spacer(1, 8))

    doc.build(content)

    return send_file(file_path, as_attachment=True)


 
client = Groq(api_key="")

@app.route('/Goalsync')
def goalsync():
    return render_template("Goalsync.html")

@app.route('/momentum/ai_plan', methods=['POST'])
def momentum_ai_plan():
    try:
        data        = request.get_json(silent=True, force=True) or {}
        goal        = data.get('goal', '').strip()
        hrs_per_day = float(data.get('hours_per_day', 2))
        skill       = data.get('skill_level', 'intermediate')

        if not goal:
            return jsonify({'error': 'Goal is required'}), 400

        prompt = f"""You are a goal planning expert.
Create a week-by-week plan for this goal: {goal}
Daily available hours: {hrs_per_day}
Skill level: {skill}

Write a clear plan with weeks and tasks. Keep it concise."""

        response = client.chat.completions.create(
            model='openai/gpt-oss-20b',
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=400,
            temperature=0.7
        )

        text = response.choices[0].message.content.strip()
        print("RAW:", text[:200])

        return jsonify({'result': text})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
    
    
