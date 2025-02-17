from flask import Flask, render_template, request, redirect, url_for, jsonify, session,flash
from models import db, User
import os
import torch
import librosa
import numpy as np
from transformers import AutoModelForAudioClassification, AutoFeatureExtractor
from pydub import AudioSegment
from geopy.geocoders import Nominatim
from flask_cors import CORS
from twilio.rest import Client

app = Flask(__name__)
CORS(app)
# app.config['SECRET_KEY'] = 'a3f9b2c5d8e7a1f4c6d9e0b2a5d7c3f1' 

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
ALLOWED_EXTENSIONS = {"wav", "mp3", "ogg", "m4a"}
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):                                                                                                           
    os.makedirs(UPLOAD_FOLDER)


app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER                                                                                                                     
# Create the database before the first request
with app.app_context():
    db.create_all()
    
# Initialize Geopy geolocator
geolocator = Nominatim(user_agent="women_safety_app")



# Twilio credentials (replace with your own)
TWILIO_PHONE = '+12317512671'  # Your Twilio phone number
# TWILIO_ACCOUNT_SID = 'AC43e2d9954c7ca8333a3715e8f0dac820'  # Your Twilio Account SID
# TWILIO_AUTH_TOKEN = '35696f6f7e6daeb698300c3d009c5e29'   # Your Twilio Auth Token

# Predefined emergency contacts (use valid phone numbers)
EMERGENCY_CONTACTS = ['+919037448078', '+918137042277']  # Example phone numbers

MODEL_ID = "firdhokk/speech-emotion-recognition-with-openai-whisper-large-v3"
MODEL_PATH = "models/my_model"


if not os.path.exists(MODEL_PATH):
    print("Model not found. Downloading and saving...")
    
    # Download and save the model
    model = AutoModelForAudioClassification.from_pretrained(MODEL_ID)
    model.save_pretrained(MODEL_PATH)

    # Download and save the feature extractor
    feature_extractor = AutoFeatureExtractor.from_pretrained(MODEL_ID)
    feature_extractor.save_pretrained(MODEL_PATH)
    
    print("Model saved to:", MODEL_PATH)
else:
    print("Model already exists. Loading from disk...")
    
    # Load from saved files
    model = AutoModelForAudioClassification.from_pretrained(MODEL_PATH)
    feature_extractor = AutoFeatureExtractor.from_pretrained(MODEL_PATH)
id2label = model.config.id2label
print("Model saved to:", MODEL_PATH)

@app.route("/")
def index():
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("username")
        email = request.form.get("mail")
        contact = request.form.get("phno")
        emergency1 = request.form.get("emergency1")
        emergency2 = request.form.get("emergency2")
        emergency3 = request.form.get("emergency3")
        password = request.form.get("password")


        # Check if the user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            error_message = "User already exists! Please log in.", 409
            return render_template("signup.html")

        # Save user data to the database
        new_user = User(
            name=name,
            email=email,
            contact=contact,
            emergency1=emergency1,
            emergency2=emergency2,
            emergency3=emergency3,
            password=password, 
        )
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("index"))
    return render_template("signup.html")
@app.route("/home")
def home():
    user_id = session.get("user_id")  # Get the logged-in user's ID
    if not user_id:
        return redirect(url_for("login"))  # Redirect if not logged in

    user = User.query.get(user_id)  # Fetch user data from the database
    
    if user:
        print("Logged-in User Details:")
        print(f"Name: {user.name}")
        print(f"Email: {user.email}")
        print(f"Contact: {user.contact}")
        print(f"Emergency Contacts: {user.emergency1}, {user.emergency2}, {user.emergency3}")

    return render_template("home.html", user=user)  # Pass user data to the frontend

@app.route("/login", methods=["GET","POST"])
def login():
    error_message= ""
    if request.method == "POST":
        email = request.form.get("username")
        password = request.form.get("password")

        print(email,password)

        user = User.query.filter_by(email=email, password=password).first()
        
        if user:
            session["user_id"] = user.id  # Store user ID in session
            return redirect(url_for("home"))
        else:
            error_message = "Invalid username or password"
        
    return render_template("login.html", error_message=error_message)


@app.route("/logout")
def logout():
    session.pop("user_id", None)  # Remove user ID from session
    print("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/edit_details", methods=["GET", "POST"])
def edit_details():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    if request.method == "POST":
        name = request.form.get("username", "").strip()
        email = request.form.get("mail", "").strip()
        emergency1 = request.form.get("emergency_contact1", "").strip()
        emergency2 = request.form.get("emergency_contact2", "").strip()
        emergency3 = request.form.get("emergency_contact3", "").strip()


        # Update fields only if they are not empty and different
        if name and name != user.name:
            user.name = name
        if email and email != user.email:
            user.email = email
        if emergency1 and emergency1 != user.emergency1:
            user.emergency1 = emergency1
        if emergency2 and emergency2 != user.emergency2:
            user.emergency2 = emergency2
        if emergency3 and emergency3 != user.emergency3:
            user.emergency3 = emergency3
        
        

        
        db.session.commit()  # Save changes to database

        flash("Your details have been updated!", "success")
        return redirect(url_for("login"))
    
    return render_template("edit_details.html", user=user)

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def convert_to_wav(file_path):
    """Convert audio file to WAV format (PCM 16-bit, 16kHz, Mono)."""
    output_path = os.path.join(UPLOAD_FOLDER, "converted.wav")
       
    if os.path.exists(output_path):
        os.remove(output_path)  
    audio = AudioSegment.from_file(file_path)
    audio = audio.set_frame_rate(16000).set_channels(1)
    audio.export(output_path, format="wav", codec="pcm_s16le")
    return output_path
def preprocess_audio(audio_path,max_duration=30):
    # Load audio
    audio, sr = librosa.load(audio_path, sr=16000)

    # Truncate or pad the audio to the maximum duration
    if len(audio) > max_duration * sr:
        audio = audio[: max_duration * sr]
    else:
        padding = max_duration * sr - len(audio)
        audio = np.pad(audio, (0, padding), 'constant')

    # Extract features
    inputs = feature_extractor(audio, sampling_rate=sr, return_tensors="pt")
    return inputs

@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle file upload, conversion, and emotion detection."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        #print("FILE EXISTS AND IS ALLOWED")
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)  # Save original file

        # Convert to WAV format
        converted_path = convert_to_wav(file_path)
        print(converted_path)
        # Preprocess audio
        inputs = preprocess_audio(converted_path)
        print("processing audio for model")

        # Run model inference
        with torch.no_grad():
            logits = model(**inputs).logits

        # Get the predicted emotion
        predicted_id = torch.argmax(logits, dim=-1).item()
        predicted_emotion = id2label[predicted_id]
        print(predicted_emotion)
        return jsonify({"message": predicted_emotion})
    print("FILE HAS SOME ISSUE")
    return jsonify({"error": "Invalid file format"}), 400
@app.route('/send-location', methods=['POST'])
def send_location():
    try:
        user_id = session.get("user_id")
        if not user_id:
             return jsonify({"error": "User not logged in"}), 401 
        # Fetch user details from the database
        user = User.query.get(session["user_id"])
        if not user:
            return jsonify({"error": "User not found"}), 404

            # Store emergency contacts in an array
        emergency_contacts = [user.emergency1, user.emergency2, user.emergency3]
        emergency_contacts = [contact for contact in emergency_contacts if contact]  # Remove empty contacts
        print("eeeeee",emergency_contacts)
        if not emergency_contacts:
            return jsonify({"error": "No emergency contacts set"}), 400
        # Get latitude and longitude from frontend
        data = request.get_json()
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        # Reverse geocode to get the address
        location = geolocator.reverse((latitude, longitude))
        address = location.address if location else "Address not found"

        # Create tracking link (you can use a real mapping API or just a placeholder)
        tracking_link = f"http://maps.google.com/?q={latitude},{longitude}"
        print(address, latitude, longitude, tracking_link,emergency_contacts)

        # Send the SMS with location and tracking link
        # send_sms(address, latitude, longitude, tracking_link)

        return jsonify({
            "message": "Location sent to emergency contacts",
            "address": address,
            "location": {"latitude": latitude, "longitude": longitude},
            "tracking_link": tracking_link
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def send_sms(address, latitude, longitude, tracking_link,emergency_contacts):
    try:
        # Create a Twilio client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        # Message content with location and tracking link
        message_body = f"Emergency! Current location: {address}, Latitude: {latitude}, Longitude: {longitude}. Track the location: {tracking_link}"

        # Send the message to each emergency contact
        for contact in emergency_contacts:
            print(f"Sending message to: {contact}")
            message = client.messages.create(
                body=message_body,      # The content of the SMS
                from_=TWILIO_PHONE,      # Your Twilio phone number
                to=contact              # The contact to receive the SMS
            )
            print(f"SMS sent to {contact}: {message.sid}")
    except Exception as e:
        print(f"Error sending SMS: {str(e)}")
@app.route("/view_data")
def view_data():
    # Query all users from the database
    users = User.query.all()

    # Pass the data to the template
    return render_template("view_data.html", users=users)

if __name__ == "__main__":
    app.run(debug=True)
