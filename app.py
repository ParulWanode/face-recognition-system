from flask import Flask, render_template, request, redirect, url_for, flash
import face_recognition
import numpy as np
import csv
import os
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Create directories if they don't exist
if not os.path.exists('users'):
    os.makedirs('users')
if not os.path.exists('static/logs'):
    os.makedirs('static/logs')

def save_user_data(name, age, encoding):
    with open(f'users/{name}.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Age", "Encoding"])
        writer.writerow([name, age, json.dumps(encoding.tolist())])  # Use json.dumps to save the encoding

def get_known_encodings():
    known_encodings = []
    known_names = []
    user_files = os.listdir('users')
    for user_file in user_files:
        with open(f'users/{user_file}', mode='r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            user_data = next(reader)
            name = user_data[0]
            encoding = np.array(json.loads(user_data[2]))  # Convert string back to numpy array
            known_names.append(name)
            known_encodings.append(encoding)
    return known_names, known_encodings

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        image = request.files['image']
        
        if image:
            try:
                # Load and encode the image
                image_data = face_recognition.load_image_file(image)
                encodings = face_recognition.face_encodings(image_data)

                if not encodings:
                    flash("No faces found in the image. Please try again with a different image.")
                    return redirect(url_for('register'))
                
                encoding = encodings[0]
                save_user_data(name, age, encoding)
                flash("User registered successfully!")
                return redirect(url_for('index'))
            except Exception as e:
                flash("Error processing image: " + str(e))
                return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        image = request.files['image']
        
        if image:
            try:
                # Load and encode the image
                image_data = face_recognition.load_image_file(image)
                test_encodings = face_recognition.face_encodings(image_data)

                if not test_encodings:
                    flash("No faces found in the image. Please try again with a different image.")
                    return redirect(url_for('index'))
                
                test_encoding = test_encodings[0]
                known_names, known_encodings = get_known_encodings()

                matches = face_recognition.compare_faces(known_encodings, test_encoding)
                face_distances = face_recognition.face_distance(known_encodings, test_encoding)

                if len(face_distances) == 0:
                    flash("No known faces found.")
                    return redirect(url_for('index'))

                if any(matches):
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = known_names[best_match_index]
                        now = datetime.now()
                        current_date_time = now.strftime("%Y-%m-%d %H:%M:%S")
                        flash(f"User {name} logged in at {current_date_time}")

                        # Log the login time and date
                        log_file_path = 'static/logs/login_logs.csv'
                        if not os.path.exists(log_file_path):
                            with open(log_file_path, mode='w', newline='') as file:
                                writer = csv.writer(file)
                                writer.writerow(["Name", "Date and Time"])  # Write header if new file

                        with open(log_file_path, mode='a', newline='') as file:
                            writer = csv.writer(file)
                            writer.writerow([name, current_date_time])
                    else:
                        flash("Login failed: User not recognized.")
                else:
                    flash("Login failed: User not recognized.")
            except Exception as e:
                flash("An error occurred: " + str(e))
            return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/view_logins')
def view_logins():
    logs = []
    log_file_path = 'static/logs/login_logs.csv'
    if os.path.exists(log_file_path):
        with open(log_file_path, mode='r') as file:
            reader = csv.reader(file)
            logs = list(reader)
    return render_template('view_logins.html', logs=logs)

@app.route('/view_users')
def view_users():
    users = []
    user_files = os.listdir('users')
    for user_file in user_files:
        with open(f'users/{user_file}', mode='r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            user_data = next(reader)
            users.append(user_data)
    return render_template('view_users.html', users=users)

if __name__ == "__main__":
    app.run(debug=True)
