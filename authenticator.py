from mojang import Client, errors
import bcrypt
import os

def verify_by_code(code, uuid):
    try:
        with open("auth_codes/" + uuid + ".auth", "r") as file:
            hash = file.read()
    except:
        print("Doesn't exist *shrug*")
        return False

    result = bcrypt.checkpw(code, hash)
    
    if result:
        os.remove("auth_codes/" + uuid + ".auth")

    return result

def verify_by_ms_account(email, password, username):
    try:
        client = Client(email, password)
    except errors.LoginFailure:
        return False

    profile = client.get_profile()

    return profile.name == username