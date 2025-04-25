from flask import Flask, render_template, request, redirect, url_for, session ,send_from_directory
import mysql.connector , os
from datetime import datetime
from transformers import AutoModelForCausalLM, AutoTokenizer

app = Flask(__name__)

from flask import jsonify
app = Flask(__name__)
app.secret_key = "healapp_secret"  # Secret key added

import mysql.connector

# MySQL connection setup
mydb = mysql.connector.connect(
    host="localhost",
    user="root",          # Your MySQL username
    password="adhi2004",          # Your MySQL password (if any)
    database="healthplan" # Your database name
)
mycursor = mydb.cursor()

@app.route('/')
def open_page():
    return render_template('open.html')

@app.route('/record')
def record():
    return render_template('record.html')


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

tokenizer = AutoTokenizer.from_pretrained("distilgpt2")
model = AutoModelForCausalLM.from_pretrained("distilgpt2")

def get_local_ai_reply(prompt):
    inputs = tokenizer.encode(prompt, return_tensors="pt")
    outputs = model.generate(inputs, max_length=100, pad_token_id=tokenizer.eos_token_id)
    reply = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return reply.replace(prompt, "").strip()

@app.route("/chatbot")
def chatbot_page():
    return render_template("chatbot.html")

@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():
    if request.method == "POST":
        user_input = request.json["message"].lower()

        if "hi" in user_input or "hello" in user_input:
            reply = "Hello! How can I help you today?"
        elif "bmi" in user_input:
            reply = 'To check your BMI, click here: <a href="/bmi" target="_blank">BMI Calculator</a>'
        elif "calorie" in user_input:
            reply = 'Plan your meals with this: <a href="/calorie" target="_blank">Calorie Calculator</a>'
        elif "water" in user_input:
            reply = 'Know your hydration needs: <a href="/water" target="_blank">Water Intake Calculator</a>'
        elif "ulcer" in user_input:
            reply = "Avoid spicy, oily, and acidic foods. Prefer bananas, coconut water, and rice."
        elif "diabetes" in user_input:
            reply = "Avoid sugary foods. Include more vegetables, oats, and whole grains in your diet."
        elif "cholesterol" in user_input:
            reply = "Limit fried foods. Include oats, nuts, and heart-friendly oils like olive oil."
        elif "obesity" in user_input:
            reply = "Control portions and avoid junk. Choose fruits, veggies, and lean protein."
        elif "acidity" in user_input:
            reply = "Avoid caffeine and spicy foods. Drink cold milk and eat early dinners."
        elif "fever" in user_input:
            reply = "Stay hydrated and rest well. Avoid oily food. Eat khichdi, soup, or curd rice."
        elif "cold" in user_input:
            reply = "Take warm fluids, avoid cold drinks. Ginger tea and turmeric milk can help."
        elif "cough" in user_input:
            reply = "Avoid chilled items. Drink hot water and take honey with ginger."
        elif "constipation" in user_input:
            reply = "Eat high-fiber foods like fruits and drink lots of water."
        elif "gas" in user_input:
            reply = "Avoid carbonated drinks. Jeera water and ginger help relieve gas."
        elif "headache" in user_input:
            reply = "Take rest, stay hydrated, and avoid screen time. Eat something light."
        elif "vomiting" in user_input:
            reply = "Eat light. Drink electrolyte water or ginger tea for relief."
        elif "diarrhea" in user_input:
            reply = "Drink ORS or coconut water. Avoid milk and spicy foods temporarily."
        elif "weakness" in user_input:
            reply = "Eat iron-rich foods like spinach, nuts, and dates. Sleep well."
        elif "health" in user_input:
            reply = "Sure, do you want tips on diet, exercise, or symptoms?"
        else:
            reply = "I'm here to help with your health questions! Please ask about symptoms, diet, or tools like BMI, calories, and water intake."

        return jsonify({"reply": reply})
    return render_template("chatbot.html")


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

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
