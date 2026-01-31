from flask import Flask, render_template, request, redirect, url_for, session ,send_from_directory 
import mysql.connector , os 
from datetime import datetime 
app = Flask(__name__)

from groq import Groq
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

import mysql.connector

# MySQL connection setup
mydb = mysql.connector.connect(
    host="localhost",
    user="root",          # Your MySQL username
    password="adhi2004",          # Your MySQL password (if any)
    database="healthplan" # Your database name
)
mycursor = mydb.cursor()


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


GROQ_API_KEY = "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"
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

# 🔹 Food Tips Dictionary (Eat / Avoid list for each disease)
food_tips = {
    "ulcer": {
        "eat": ["Bananas", "Coconut water", "Boiled rice", "Oats", "Vegetable soups", "Pumpkin", "Sweet potatoes"],
        "avoid": ["Spicy foods", "Chili powder", "Fried food", "Tomato", "Caffeine", "Citrus fruits", "Carbonated drinks"]
    },
    "diabetes": {
        "eat": ["Leafy greens", "Nuts", "Whole grains", "Beans", "Berries", "Low-fat yogurt"],
        "avoid": ["Sugar", "White rice", "Soft drinks", "White bread", "Pastries", "Sweetened cereal"]
    },
    "cough": {
        "eat": ["Warm water", "Honey", "Tulsi leaves", "Ginger tea", "Black pepper with honey"],
        "avoid": ["Cold drinks", "Ice cream", "Fried items", "Citrus fruits (if throat sensitive)"]
    },
    "acidity": {
        "eat": ["Cold milk", "Banana", "Oats", "Coconut water", "Cucumber"],
        "avoid": ["Tea", "Coffee", "Spicy food", "Pickles", "Soda", "Tomato"]
    },
    "high cholesterol": {
        "eat": ["Oats", "Beans", "Fruits like apples", "Nuts", "Olive oil"],
        "avoid": ["Red meat", "Full-fat dairy", "Butter", "Fried foods", "Processed meat"]
    },
    "obesity": {
        "eat": ["Fruits", "Vegetables", "Whole grains", "Legumes", "Nuts (in moderation)"],
        "avoid": ["Sugary snacks", "Processed foods", "Soft drinks", "Fried items", "White bread"]
    }
}

# 🔹 Route for Food Tips
@app.route("/foodtips", methods=["GET", "POST"])
def foodtips():
    food_data = None
    error = None
    disease_name = ""

    if request.method == "POST":
        disease = request.form["disease"].strip().lower()
        disease_name = disease
        food_data = food_tips.get(disease)

        if not food_data:
            error = "Disease not found in food tips."

    return render_template("foodtips.html", food_data=food_data, error=error, disease_name=disease_name)

@app.route('/healthfacts')
def healthfacts():
    return render_template('healthfacts.html')

@app.route("/visualizer")
def visualizer():
    return render_template("visualizer.html")

@app.route('/nutrition')
def nutrition():
    return render_template('nutrition.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route("/healometer")
def healometer():
    return render_template("healometer.html")

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


