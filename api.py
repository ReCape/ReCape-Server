import json
import os
import shutil
import flask
import requests
import werkzeug
import authenticator
import tokens
import uuids
from mojang import API, errors
import urllib.request, urllib.error

class Server:
    app = flask.Flask(__name__)

    CLOAKS_PLUS_URL = "https://server.cloaksplus.com"

    PORT = 443

    def __init__(self, debug):
        self.DEBUG = debug
        self.tokens = tokens.Tokens()
        self.uuids = uuids.UUIDs()
        self.api = API()

        @self.app.route("/authenticate/server_code")
        def authenticate_server_code(): return self.authenticate_server_code()
        @self.app.route("/authenticate/ms_login")
        def authenticate_microsoft(): return self.authenticate_microsoft()
        @self.app.route("/authenticate/check_token")
        def check_token(): return self.check_token()

        @self.app.route('/account/set_cape', methods=['POST'])
        def set_cape(): return self.set_cape()

        @self.app.route('/account/upload_cosmetic', methods=['POST'])
        def upload_cosmetic(): return self.upload_cosmetic()
        @self.app.route('/account/delete_cosmetic')
        def delete_cosmetic(): return self.delete_cosmetic()
        @self.app.route('/account/get_config')
        def get_config(): return self.get_config()
        @self.app.route('/account/set_config', methods=['POST'])
        def set_config(): return self.set_config()
        @self.app.route("/account/get_cosmetic_list")
        def get_cosmetic_list(): return self.get_cosmetic_list()
    
    def create_auth(self, uuid, username, source="Unknown"):
        token = self.tokens.generate_token()
        self.tokens.register_token(token, uuid, source)
        self.uuids.register(uuid, username)
        return token

    def authenticate_server_code(self):

        code = flask.request.headers.get("code")
        username = flask.request.headers.get("username")
        source = flask.request.headers.get("source", "Unknown")

        try:
            uuid = self.api.get_uuid(username)
        except errors.NotFound:
            return {"status": "failure", "error": "The given Minecraft username doesn't exist. Did you type it correctly?"}
        except Exception as e:
            return {"status": "failure", "error": str(e)}

        if authenticator.verify_by_code(code, uuid):
            return {"status": "success", "token": self.create_auth(uuid, username, source), "uuid": uuid}
        else:
            return {"status": "failure", "error": "Could not authenticate. Did you connect to the authentication server with your Minecraft account and type the code in?"}

    def authenticate_microsoft(self):

        email = flask.request.headers.get("email")
        password = flask.request.headers.get("password")
        username = flask.request.headers.get("username")
        source = flask.request.headers.get("source", "Unknown")
        uuid = self.api.get_uuid(username)

        if authenticator.verify_by_ms_account(email, password, username):
            return {"status": "success", "token": self.create_auth(uuid, username, source), "uuid": uuid}
        else:
            return {"status": "failure", "error": "Could not authenticate. Did you type in the correct email and password for your Microsoft account?"}
        
    def check_token(self):
        token = flask.request.headers.get("token")
        uuid = flask.request.headers.get("uuid")
        username = flask.request.headers.get("username", "")

        self.uuids.register(uuid, username)

        if self.tokens.verify(uuid, token):
            return {"status": "success", "result": "valid"}
        return {"status": "success", "result": "invalid"}
    
    def set_cape(self):
        token = flask.request.headers.get("token")
        uuid = flask.request.headers.get("uuid")
        cape_type = flask.request.headers.get("cape_type")

        if not self.tokens.verify(uuid, token):
            return {"status": "failure", "error": "The supplied token and UUID are not valid. Did you log in? Try restarting your client."}
        
        if cape_type == "none":
            try:
                shutil.copy("static/capes/none.png", "static/capes/" + uuid.replace("-", "") + ".png")
            except Exception as e:
                print(e)
            return {"status": "success"}
        
        elif cape_type == "cloaksplus":
            username = self.uuids.get_username(uuid)
            try:
                r = requests.get(self.CLOAKS_PLUS_URL + "/capes/" + username + ".png") 
                with open("static/capes/" + uuid.replace("-", "") + ".png", "wb") as file:
                    file.write(r.content)
                return {"status": "success"}
            except urllib.error.HTTPError as e:
                return {"status": "failure", "error": "You don't have a cape on Cloaks+!"}


        if 'file' not in flask.request.files:
            return {"status": "failure", "error": "No file was detected in the data."}
        file = flask.request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            return {"status": "failure", "error": "The files appears to be empty, or has an empty filename."}
        if file and file.filename.endswith(".png"):
            filename = uuid.replace("-", "") + ".png"
            file.save(os.path.join("static/capes/", filename))
            return {"status": "success"}
    
    def get_config(self):
        token = flask.request.headers.get("token")
        uuid = flask.request.headers.get("uuid")


        if not self.tokens.verify(uuid, token):
            return {"status": "failure", "error": "The supplied token and UUID are not valid. Did you log in? Try restarting your client."}

        try:

            if not os.path.exists("static/models/" + uuid + "/config.json"):
                with open("static/models/" + uuid + "/config.json", "w+") as file:
                    file.write(json.dumps({}))

            with open("static/models/" + uuid + "/config.json", "r+") as file:
                return json.loads(file.read())
            
        except Exception as e:
            return {"status": "failure", "error": str(e)}
    
    def set_config(self):
        token = flask.request.headers.get("token")
        uuid = flask.request.headers.get("uuid")
        data = json.loads(flask.request.headers.get("config"))

        if not self.tokens.verify(uuid, token):
            return {"status": "failure", "error": "The supplied token and UUID are not valid. Did you log in? Try restarting your client."}

        try:
 
            with open("static/models/" + uuid + "/config.json", "w+") as file:
                file.write(json.dumps(data))
            
            return {"status": "success"}
            
        except Exception as e:
            return {"status": "failure", "error": str(e)}

    def get_cosmetic_list(self):
        token = flask.request.headers.get("token")
        uuid = flask.request.headers.get("uuid")


        if not self.tokens.verify(uuid, token):
            return {"status": "failure", "error": "The supplied token and UUID are not valid. Did you log in? Try restarting your client."}

        try:
            if not os.path.exists("static/models/" + uuid):
                os.mkdir("static/models/" + uuid)
                with open("static/models/" + uuid + "/config.json", "w+") as config:
                    config.write("{}")
            models = os.listdir("static/models/" + uuid)
            models.remove("config.json")
            return {"status": "success", "models": models}
            
        except Exception as e:
            return {"status": "failure", "error": str(e)}

    def upload_cosmetic(self):
        token = flask.request.headers.get("token")
        uuid = flask.request.headers.get("uuid")


        if not self.tokens.verify(uuid, token):
            return {"status": "failure", "error": "The supplied token and UUID are not valid. Did you log in? Try restarting your client."}


        if 'model' not in flask.request.files or 'texture' not in flask.request.files:
            return {"status": "failure", "error": "The model and texture files were not detected in the data."}
        
        model = flask.request.files['model']
        texture = flask.request.files['texture']


        if model.filename == '':
            return {"status": "failure", "error": "The files appears to be empty, or has an empty filename."}
        
        model_name = flask.request.headers.get("model_name", default="".join(model.filename.split(".")[:-1]))


        save_dir = "static/models/" + uuid.replace("-", "")

        try: os.mkdir(save_dir)
        except FileExistsError: pass

        save_dir += "/" + model_name

        try: os.mkdir(save_dir)
        except FileExistsError: pass

        if model and model.filename.endswith(".cfg"):
            model.save(os.path.join(save_dir, "model.cfg"))
            texture.save(os.path.join(save_dir, "texture.png"))

            data = {}
            try:    
                with open("static/models/" + uuid + "/config.json", "r") as file:
                    data = json.loads(file.read())
            except FileNotFoundError:
                pass
            with open("static/models/" + uuid + "/config.json", "w+") as file:
                data[model_name] = True
                file.write(json.dumps(data))

        return {"status": "success"}
    
    def start(self):
        # We need to run the API over HTTPS because I don't want to make end-to-end encryption from scratch :)

        if self.DEBUG:
            self.app.run("0.0.0.0", self.PORT, ssl_context=("ssl/domain.cert.pem", "ssl/private.key.pem"))
        else:
            raise Exception("API cannot be run in a non-debug environment. You must run with Gunicorn.")