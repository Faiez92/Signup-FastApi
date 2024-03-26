from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta
from email.mime.text import MIMEText
import uuid
import smtplib
from fastapi.responses import RedirectResponse
from pymongo import mongo_client
from config import settings

app = FastAPI()

# Connect to the MongoDB database
client = mongo_client.MongoClient(settings.DATABASE_URL, serverSelectionTimeoutMS=5000)

db = client["mydatabase"]
users_collection = db["users"]


@app.post("/register")
def create_user(email: str, password: str, name: str):
    # Check if the email is already in use
    existing_user = users_collection.find_one({"email": email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already in use")

    # Create a new user
    user = {
        "email": email,
        "password": password,
        "name": name,
        "is_active": False,
        "verification_code": generate_verification_code(),
        "verification_code_created_at": datetime.now(),
    }
    users_collection.insert_one(user)

    # Send an email to the user with the verification code
    send_verification_email(user["email"], user["verification_code"])
    return {"status": "success", "message": "verification code sent succefuly"}


def send_email(to: str, subject: str, body: str):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["To"] = to

    # Replace YOUR_EMAIL_ADDRESS and YOUR_EMAIL_PASSWORD with your own email address and password
    server = smtplib.SMTP(settings.SMTP, settings.SMTP_PORT)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(settings.FROM_ADDR, settings.EMAIL_PWD)
    server.send_message(msg, from_addr=settings.FROM_ADDR, to_addrs=to)
    server.quit()


@app.get("/activate")
def activate_user(email: str, code: str):
    # Find the user with the matching email and code
    user = users_collection.find_one({"email": email, "verification_code": code})

    # Check if the user is already verified
    if user["is_active"]:
        raise HTTPException(status_code=400, detail="already verified")

    # Check if the code and email are valid
    if not user:
        raise HTTPException(status_code=404, detail="Invalid email or code")

    # Check if the code has expired
    if code_has_expired(user["verification_code"]):
        raise HTTPException(status_code=400, detail="Code is expired")

    # Activate the user account
    users_collection.update_one({"_id": user["_id"]}, {"$set": {"is_active": True}})
    return {"status": "success", "message": "verified successfully"}


def generate_verification_code():
    # Generate a random 4-digit code
    return str(uuid.uuid4())[:4]


def send_verification_email(email, code):
    # Load the email template
    user = users_collection.find_one({"email": email, "verification_code": code})

    # Render the email template with the verification code and activation link
    body = (
        f"welcome {user['name']} \n"
        f"Thank you for registering with our service! \n"
        f"you validation code :  {code} \n"
        f" your mail {email} \n"
        f"have a nice day "
    )
    send_email(to=email, subject="Validation code", body=body)


def code_has_expired(code, expiration_minutes=1):
    # Find the user with the matching code
    user = users_collection.find_one({"verification_code": code})
    if not user:
        return True
    # Check if the code was created more than the expiration time ago
    code_created_at = user["verification_code_created_at"]
    expiration_time = code_created_at + timedelta(minutes=expiration_minutes)
    return expiration_time < datetime.now()


@app.get("/")
def redirect_to_docs():
    return RedirectResponse(url="/docs#/")
