from flask import Flask, render_template, request, redirect, url_for, session ,send_from_directory 
import mysql.connector , os 
from datetime import datetime 

from groq import Groq
from flask import Flask, request, jsonify , send_file
import requests

import pandas as pd
import math

import pdfplumber
import re
import spacy

import csv
import io

import markdown

from sklearn.cluster import KMeans
import random

import mysql.connector

# MySQL connection setup
mydb = mysql.connector.connect(
    host="localhost",
    user="root",          # Your MySQL username
    password="adhi2004",          # Your MySQL password (if any)
    database="healthplan" # Your database name
)
mycursor = mydb.cursor()

app = Flask(__name__)



CSV_PATH = "HealApp---Health-Monitering-Web-Application/data/hospital.csv"

# ---------------- Distance ----------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return round(R * 2 * math.asin(math.sqrt(a)), 2)

# ---------------- Reverse Geocode ----------------
def reverse_location(lat, lon):
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json"
        }
        headers = {"User-Agent": "heal-visualizer"}
        r = requests.get(url, params=params, headers=headers, timeout=5)
        if r.status_code == 200:
            return r.json().get("display_name", "")
    except:
        pass
    return "Unknown location"

# ---------------- Routes ----------------
@app.route("/visualizer")
def visualizer():
    return render_template("visualizer.html")

@app.route("/visualize", methods=["POST"])
def visualize():
    
    user_lat = float(request.json["lat"])
    user_lon = float(request.json["lon"])

    df = pd.read_csv(CSV_PATH)

    hospitals = []
    
    for _, row in df.iterrows():
        
        lat = row.get("latitude")
        lon = row.get("longitude")
        
        if pd.isna(lat) or pd.isna(lon): 
            continue
        
        dist = haversine(
            user_lat, user_lon, 
            float(lat),float(lon))
        
        hospitals.append({
        
           "name": row.get("name", ""),
           "city": row.get("city", ""),
           "address": row.get("address", ""),
           "pincode": row.get("pincode", ""),
           "distance": dist,
           "lat": float(lat),
           "lon": float(lon),
           "website": row.get("website", ""),
           "contact": row.get("contact", "")
           })


    hospitals = sorted(hospitals,key=lambda x: x["distance"])
    
    return jsonify(hospitals)

@app.route("/route", methods=["POST"])
def route():
    try:
        data = request.get_json()

        slat = float(data["start_lat"])
        slon = float(data["start_lon"])
        elat = float(data["end_lat"])
        elon = float(data["end_lon"])

        return jsonify({
            "status": "ok",
            "distance": haversine(slat, slon, elat, elon),
            "from": reverse_location(slat, slon),
            "to": reverse_location(elat, elon)
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

@app.route('/student', methods=['GET', 'POST'])
def student():
    if request.method == 'POST':
        id = request.form.get('id')
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        bmi = request.form['bmi']
        water = request.form['water']
        calories = request.form['calories']

        if id:
            mycursor.execute("""
                UPDATE students SET name=%s, age=%s, gender=%s, bmi=%s, water=%s, calories=%s WHERE id=%s
            """, (name, age, gender, bmi, water, calories, id))
        else:
            mycursor.execute("""
                INSERT INTO students (name, age, gender, bmi, water, calories) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, age, gender, bmi, water, calories))

        mydb.commit()
        return redirect('/student')

    mycursor.execute("SELECT * FROM students ORDER BY used_on DESC")
    records = mycursor.fetchall()
    return render_template('record.html', records=records, student=None)

@app.route('/edit/<int:id>')
def edit(id):
    mycursor.execute("SELECT * FROM students WHERE id=%s", (id,))
    data = mycursor.fetchone()
    student = {
        'id': data[0],
        'name': data[1],
        'age': data[2],
        'gender': data[3],
        'bmi': data[4],
        'water': data[5],
        'calories': data[6]
    }
    mycursor.execute("SELECT * FROM students ORDER BY used_on DESC")
    records = mycursor.fetchall()
    return render_template('record.html', records=records, student=student)

@app.route('/delete/<int:id>')
def delete(id):
    mycursor.execute("DELETE FROM students WHERE id=%s", (id,))
    mydb.commit()
    return redirect('/student')


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

@app.route('/bmi', methods=['GET', 'POST'])
def bmi():
    result = ''
    tips = ''
    if request.method == 'POST':
        try:
            weight = float(request.form['weight'])
            height = float(request.form['height'])
            height_in_meters = height / 100
            bmi_value = round(weight / (height_in_meters ** 2), 2)

            if bmi_value < 18.5:
                tips = "You are underweight. Include more calories and proteins."
            elif 18.5 <= bmi_value < 24.9:
                tips = "You are healthy. Maintain a balanced diet."
            elif 25 <= bmi_value < 29.9:
                tips = "You are overweight. Cut down on sugar and do regular exercise."
            else:
                tips = "You are obese. Consult a dietician and increase physical activity."

            result = bmi_value
        except:
            result = "Invalid input"
    return render_template('bmi.html', result=result, tips=tips)


@app.route('/calorie', methods=['GET', 'POST'])
def calorie():
    result = None
    tips = ""
    if request.method == 'POST':
        try:
            age = int(request.form['age'])
            gender = request.form['gender']
            activity = request.form['activity']
            weight = float(request.form['weight'])
            height = float(request.form['height']) / 100  # cm to meters

            bmr = 0
            if gender == 'male':
                bmr = 10 * weight + 6.25 * (height * 100) - 5 * age + 5
            else:
                bmr = 10 * weight + 6.25 * (height * 100) - 5 * age - 161

            multiplier = {
                'low': 1.2,
                'moderate': 1.55,
                'high': 1.725
            }
            calorie_needs = round(bmr * multiplier[activity], 2)
            result = calorie_needs

            tips = (
                "🍚 Eat balanced meals including rice, legumes, and vegetables. "
                "🥥 Use healthy fats like coconut oil. "
                "💧 Drink enough water and avoid sugary snacks. "
                "🏃 Stay active to maintain a healthy metabolism."
            )

        except Exception as e:
            result = "Error in calculation: " + str(e)

    return render_template('calorie.html', result=result, tips=tips)


@app.route('/water', methods=['GET', 'POST'])
def water():
    result = None
    tips = ""
    if request.method == 'POST':
        try:
            age = int(request.form['age'])

            if age <= 8:
                result = "5–7 glasses (1.2–1.6 liters) per day"
            elif age <= 18:
                result = "8–10 glasses (1.6–2 liters) per day"
            elif age <= 55:
                result = "10–12 glasses (2–2.5 liters) per day"
            else:
                result = "8–10 glasses (1.6–2 liters) per day"

            tips = (
                "💧 Drink small amounts frequently throughout the day. "
                "🥗 Eat water-rich fruits like watermelon and cucumber. "
                "🚫 Avoid excess coffee and soda. "
                "🌞 Drink more in hot weather or after physical activity."
            )
        except Exception as e:
            result = "Error: " + str(e)

    return render_template('water.html', result=result, tips=tips)


GROQ_API_KEY = ""
API_URL = "https://api.groq.com/openai/v1/chat/completions"

@app.route("/chatbot")
def chat():
    return render_template("chatbot.html")

@app.route("/chatbot", methods=["POST"])
def chatbot():
    user_msg = request.json.get("message")

    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "system", "content": "You are HealMate, a friendly health assistant. Give medically safe guidance, not diagnosis."},
            {"role": "user", "content": user_msg}
        ]
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        data = response.json()
        reply = data["choices"][0]["message"]["content"]
    except:
        reply = "Problem contacting AI service. Try later."

    return jsonify({"reply": reply})



@app.route('/predict', methods=['GET', 'POST'])
def predict():
    symptoms = ""
    disease_info = {
        "cough": "Dry throat, chest discomfort, fatigue, wheezing",
        "fever": "High body temperature, chills, sweating, headache",
        "cold": "Runny nose, sneezing, sore throat, congestion",
        "diabetes": "Frequent urination, excessive thirst, fatigue, blurry vision",
        "hypertension": "Headache, chest pain, vision problems, irregular heartbeat",
        "asthma": "Shortness of breath, wheezing, coughing, chest tightness",
        "covid": "Fever, cough, loss of taste/smell, fatigue, body pain",
        "malaria": "Fever, chills, nausea, vomiting, sweating",
        "typhoid": "Prolonged fever, weakness, abdominal pain, headache",
        "dengue": "High fever, rash, joint pain, bleeding gums",
        "ulcer": "Stomach pain, bloating, heartburn, nausea",
        "migraine": "Severe headache, nausea, sensitivity to light/sound",
        "tuberculosis": "Cough with blood, chest pain, weight loss, night sweats",
        "jaundice": "Yellow skin, dark urine, fatigue, abdominal pain",
        "anemia": "Fatigue, weakness, pale skin, shortness of breath",
        "arthritis": "Joint pain, swelling, stiffness, fatigue",
        "cholera": "Diarrhea, dehydration, leg cramps, vomiting",
        "measles": "Rash, fever, cough, runny nose, red eyes",
        "flu": "Fever, chills, sore throat, muscle aches",
        "appendicitis": "Severe abdominal pain (lower right), fever, nausea",
        "eczema": "Itchy skin, redness, rashes, dryness",
        "bronchitis": "Cough with mucus, fatigue, chest tightness",
        "chickenpox": "Itchy rash, fever, tiredness, blisters",
        "pneumonia": "Cough, fever, difficulty breathing, chest pain"
    }

    if request.method == 'POST':
        disease = request.form['disease'].strip().lower()
        symptoms = disease_info.get(disease, "Disease not found. Please check the spelling or try another common disease.")

    return render_template('predict.html', symptoms=symptoms)


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


df = pd.read_csv("HealApp---Health-Monitering-Web-Application/data/Indian_Food_Nutrition_Processed.csv")

features = ['Calories (kcal)', 'Carbohydrates (g)', 'Protein (g)', 'Fats (g)', 'Fibre (g)']
X = df[features]

kmeans = KMeans(n_clusters=3, random_state=42)
df['cluster'] = kmeans.fit_predict(X)



def calculate_bmi(weight, height):
    h = height / 100
    return round(weight / (h * h), 2)


@app.route("/recommend_food_ml", methods=["POST"])
def recommend_food_ml():

    data = request.get_json()

    age = int(data["age"])
    height = float(data["height"]) / 100
    weight = float(data["weight"])

    bmi = round(weight / (height * height), 2)

    # decide cluster using BMI
    cluster = get_cluster_by_bmi(bmi)

    foods_df = df[df['cluster'] == cluster]

    sample = foods_df.sample(9)

    foods = []

    for _, row in sample.iterrows():
        foods.append({
            "food": row["Food"],
            "cal": row["Calories (kcal)"],
            "protein": row["Protein (g)"],
            "carbs": row["Carbohydrates (g)"]
        })

    breakfast = foods[0:3]
    lunch = foods[3:6]
    dinner = foods[6:9]

    return jsonify({
        "bmi": bmi,
        "breakfast": breakfast,
        "lunch": lunch,
        "dinner": dinner
    })


def get_cluster_by_bmi(bmi):
    if bmi < 18.5:
        return 2   # high calories
    elif bmi < 25:
        return 1   # medium
    else:
        return 0   # low



@app.route("/foodtips", methods=["GET", "POST"])
def foodtips():

    if request.method == "POST":

        age = int(request.form['age'])
        height = float(request.form['height'])
        weight = float(request.form['weight'])

        bmi = calculate_bmi(weight, height)
        cluster = get_cluster_by_bmi(bmi)

        foods = df[df['cluster'] == cluster]['Food'].tolist()
        random.shuffle(foods)

        breakfast = foods[:3]
        lunch = foods[3:6]
        dinner = foods[6:9]

        fun_fact = random.choice([
            "🍎 Balanced diet improves brain focus by 30%",
            "🥗 Fiber helps digestion & weight control",
            "💧 Drinking water boosts metabolism",
            "🍚 Carbs give quick energy for the body",
            "🥜 Protein builds muscle strength"
        ])

        return render_template("foodtips.html",
                               bmi=bmi,
                               breakfast=breakfast,
                               lunch=lunch,
                               dinner=dinner,
                               fact=fun_fact)

    return render_template("foodtips.html")




@app.route('/finhealth')
def finhealth():
    return render_template("finhealth.html")

# Insurance hub
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
        model="openai/gpt-oss-20b",   # fast + free + good
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




@app.route('/insurance/compare')
def compare_plans():
    # Sample comparison
    plans = [
        {"name": "Plan A", "premium": "₹9k", "cover": "5L", "waiting": "2y", "copay": "10%"},
        {"name": "Plan B", "premium": "₹11k", "cover": "10L", "waiting": "1y", "copay": "0"},
        {"name": "Plan C", "premium": "₹8k", "cover": "5L", "waiting": "3y", "copay": "20%"},
    ]
    return render_template("compare_plans.html", plans=plans)

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

# Finance hub
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

@app.route("/finance/download_csv", methods=["POST"])
def download_csv():

    data = request.get_json()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Date", "Time", "Name", "Category", "Amount"])

    for item in data:
        writer.writerow([
            item["date"],
            item["time"],
            item["name"],
            item["category"],
            item["amount"]
        ])

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


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route("/healometer")
def healometer():
    return render_template("healometer.html")

# Run the app
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
    
    
