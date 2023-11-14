#type: ignore
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
from flask_cors import CORS
from ratelimit import limits
from ratelimit.exception import RateLimitException
import news
import psutil
import time

start_time = time.time()

class Server: 
    app = flask.Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 8 * 1000 * 1000 # The first number is the maximum upload size in megabyte
    CORS(app)

    CLOAKS_PLUS_URL = "https://server.cloaksplus.com"

    PORT = 443

    MAX_MODELS = 5

    def __init__(self, debug):
        self.DEBUG = debug
        self.tokens = tokens.Tokens()
        self.uuids = uuids.UUIDs()
        self.api = API()

        @self.app.route("/")
        def home(): return flask.render_template("index-https.html", users=self.uuids.get_user_count(), uptime=int( ( time.time()-psutil.boot_time() ) / 60 / 60 ), uptime_program=int( ( time.time()-start_time ) / 60 / 60 ))

        @self.app.route("/authenticate/server_code")
        @limits(calls=5, period=120)
        def authenticate_server_code(): return self.authenticate_server_code()
        @self.app.route("/authenticate/ms_login")
        @limits(calls=5, period=120)
        def authenticate_microsoft(): return self.authenticate_microsoft()

        @self.app.route("/authenticate/check_token")
        @limits(calls=30, period=60)
        def check_token(): return self.check_token()

        @self.app.route('/account/set_cape', methods=['POST'])
        @limits(calls=3, period=60)
        def set_cape(): return self.set_cape()

        @self.app.route('/account/get_cape')
        @limits(calls=15, period=60)
        def get_cape(): return self.get_cape()

        @self.app.route('/account/upload_cosmetic', methods=['POST'])
        @limits(calls=3, period=60)
        def upload_cosmetic(): return self.upload_cosmetic()
        @self.app.route('/account/delete_cosmetic')
        @limits(calls=3, period=60)
        def delete_cosmetic(): return self.delete_cosmetic()
        @self.app.route('/account/get_config')
        @limits(calls=15, period=60)
        def get_config(): return self.get_config()
        @self.app.route('/account/set_config', methods=['POST'])
        @limits(calls=3, period=60)
        def set_config(): return self.set_config()
        @self.app.route("/account/get_cosmetic_list")
        @limits(calls=15, period=60)
        def get_cosmetic_list(): return self.get_cosmetic_list()

        @self.app.route('/account/get_cosmetic_cfg')
        @limits(calls=15, period=60)
        def get_cosmetic_cfg(): return self.get_cosmetic_cfg()

        @self.app.route('/account/get_cosmetic_texture')
        @limits(calls=15, period=60)
        def get_cosmetic_texture(): return self.get_cosmetic_texture()

        @self.app.route("/news/get")
        @limits(calls=15, period=60)
        def get_news(): return self.get_news()

        @self.app.route("/news/get_image")
        @limits(calls=15, period=60)
        def get_news_image(): return self.get_news_image()

        @self.app.errorhandler(RateLimitException)
        def rate_limited(error):
            return {"status": "failure", "error": self.string(["api", "errors", "rate_limit"])}
        
        @self.app.errorhandler(500)
        def server_error(error):
            return {"status": "failure", "error": self.string(["api", "errors", "500"])}
        
        with open("english.json", "r+") as lang:
            self.strings = json.loads(lang.read())
    
    def string(self, path):
        cur = self.strings
        for seg in path:
            cur = cur[seg]
        
        return cur
    
    def create_auth(self, uuid, username, source="Unknown"):
        token = self.tokens.generate_token()
        self.tokens.register_token(token, uuid, source)
        self.uuids.register(uuid, username)
        return token

    def authenticate_server_code(self):

        code = flask.request.headers.get("code")
        username = flask.request.headers.get("username", "")
        source = flask.request.headers.get("source", "Unknown")

        try:
            uuid = self.api.get_uuid(username)
        except errors.NotFound:
            return {"status": "failure", "error": self.string(["api", "errors", "invalid_username"])}
        except Exception as e:
            return {"status": "failure", "error": str(e)}

        if authenticator.verify_by_code(code, uuid):
            return {"status": "success", "token": self.create_auth(uuid, username, source), "uuid": uuid, "username": username}
        else:
            return {"status": "failure", "error": self.string(["api", "errors", "invalid_auth_code"])}

    def authenticate_microsoft(self):

        email = flask.request.headers.get("email")
        password = flask.request.headers.get("password")
        username = flask.request.headers.get("username", "")
        source = flask.request.headers.get("source", "Unknown")

        try:
            uuid = self.api.get_uuid(username)
        except errors.NotFound:
            return {"status": "failure", "error": self.string(["api", "errors", "invalid_username"])}

        if authenticator.verify_by_ms_account(email, password, username):
            return {"status": "success", "token": self.create_auth(uuid, username, source), "uuid": uuid, "username": username}
        else:
            return {"status": "failure", "error": self.string(["api", "errors", "invalid_ms_credentials"])}
    
    def check_token(self):
        token = flask.request.headers.get("token")
        uuid = flask.request.headers.get("uuid")
        username = flask.request.headers.get("username")

        self.uuids.register(uuid, username)

        if self.tokens.verify(uuid, token):
            return {"status": "success", "result": "valid"}
        return {"status": "success", "result": "invalid"}
    
    def set_cape(self):
        capetype = flask.request.headers.get("capetype")
        token = flask.request.headers.get("token", "")
        uuid = flask.request.headers.get("uuid", "")

        if not self.tokens.verify(uuid, token):
            return {"status": "failure", "error": self.string(["api", "errors", "invalid_token"])}
        
        if capetype == "none":
            try:
                shutil.copy("static/capes/none.png", "static/capes/" + uuid.replace("-", "") + ".png")
            except Exception as e:
                return {"status": "failure", "error": e}
            return {"status": "success"}
        
        elif capetype == "cloaksplus":
            username = self.uuids.get_username(uuid)
            if username == False:
                return {"status": "failure", "error": self.string(["api", "errors", "invalid_username"])}
            try:
                r = requests.get(self.CLOAKS_PLUS_URL + "/capes/" + username + ".png") 
                with open("static/capes/" + uuid.replace("-", "") + ".png", "wb") as file:
                    file.write(r.content)
                return {"status": "success"}
            except urllib.error.HTTPError as e:
                return {"status": "failure", "error": self.string(["api", "errors", "invalid_cloaksplus_username"])}


        if 'file' not in flask.request.files:
            return {"status": "failure", "error": self.string(["api", "errors", "no_file"])}
        file = flask.request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '' or file.filename == None:
            return {"status": "failure", "error": self.string(["api", "errors", "empty_file"])}
        if file and file.filename.endswith(".png"):
            filename = uuid.replace("-", "") + ".png"
            file.save(os.path.join("static/capes/", filename))
            return {"status": "success"}
    
    def get_cape(self):
        uuid = flask.request.headers.get("uuid", "")

        file = flask.send_from_directory("static/capes", uuid + ".png")
        if file.status_code == 404:
            username = str(self.api.get_username(uuid))
            file = flask.redirect(self.CLOAKS_PLUS_URL + "/capes/" + username + ".png", code=302)
        return file
    
    def get_cosmetic_cfg(self):
        uuid = flask.request.headers.get("uuid", "")
        model = flask.request.headers.get("model", "")

        file = flask.send_from_directory("static/models/" + uuid + "/" + model, "model.cfg")
        return file
    
    def get_cosmetic_texture(self):
        uuid = flask.request.headers.get("uuid", "")
        model = flask.request.headers.get("model", "")

        file = flask.send_from_directory("static/models/" + uuid + "/" + model, "texture.png")
        return file
    
    def get_news(self):
        count = int(flask.request.headers.get("count", "0"))

        return {"status": "success", "articles": news.get_news_articles(count)}
    
    def get_news_image(self):
        title = flask.request.headers.get("title", "")

        file = flask.send_from_directory("news/" + title, "image.png")
        return file
    
    def get_config(self):
        token = flask.request.headers.get("token", "")
        uuid = flask.request.headers.get("uuid", "")


        if not self.tokens.verify(uuid, token):
            return {"status": "failure", "error": self.string(["api", "errors", "invalid_token"])}

        try:
            if not os.path.exists("static/models/" + uuid):
                os.mkdir("static/models/" + uuid)
            if not os.path.exists("static/models/" + uuid + "/config.json"):
                with open("static/models/" + uuid + "/config.json", "w+") as file:
                    file.write(json.dumps({}))

            with open("static/models/" + uuid + "/config.json", "r+") as file:
                return json.loads(file.read())
            
        except Exception as e:
            return {"status": "failure", "error": str(e)}
    
    def set_config(self):
        token = flask.request.headers.get("token", "")
        uuid = flask.request.headers.get("uuid", "")
        data = json.loads(flask.request.headers.get("config", "{}"))

        if not self.tokens.verify(uuid, token):
            return {"status": "failure", "error": self.string(["api", "errors", "invalid_token"])}

        try:
 
            with open("static/models/" + uuid + "/config.json", "w+") as file:
                file.write(json.dumps(data))
            
            return {"status": "success"}
            
        except Exception as e:
            return {"status": "failure", "error": str(e)}

    def get_cosmetic_list(self):
        token = flask.request.headers.get("token", "")
        uuid = flask.request.headers.get("uuid", "")


        if not self.tokens.verify(uuid, token):
            return {"status": "failure", "error": self.string(["api", "errors", "invalid_token"])}

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
        token = flask.request.headers.get("token", "")
        uuid = flask.request.headers.get("uuid", "")


        if not self.tokens.verify(uuid, token):
            return {"status": "failure", "error": self.string(["api", "errors", "invalid_token"])}

        if 'model' not in flask.request.files or 'texture' not in flask.request.files:
            return {"status": "failure", "error": self.string(["api", "errors", "no_model_files"])}
        
        model = flask.request.files['model']
        texture = flask.request.files['texture']


        if model.filename == '' or model.filename == None:
            return {"status": "failure", "error": self.string(["api", "errors", "empty_model_files"])}
        
        model_name = flask.request.headers.get("model_name", default="".join(model.filename.split(".")[:-1]))


        save_dir = "static/models/" + uuid.replace("-", "")

        try: os.mkdir(save_dir)
        except FileExistsError: pass

        if len(os.listdir(save_dir)) > self.MAX_MODELS:
            return {"status": "failure", "error": self.string(["api", "errors", "max_models"])}

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

    def delete_cosmetic(self):
        token = flask.request.headers.get("token", "")
        uuid = flask.request.headers.get("uuid", "")
        model = flask.request.headers.get("model", "")

        if not self.tokens.verify(uuid, token):
            return {"status": "failure", "error": self.string(["api", "errors", "invalid_token"])}


        if model == "":
            return {"status": "failure", "error": self.string(["api", "errors", "model_not_specified"])}


        save_dir = "static/models/" + uuid.replace("-", "")

        if not os.path.exists(save_dir) or not os.path.exists(save_dir + "/" + model):
            return {"status": "failure", "error": self.string(["api", "errors", "invalid_model"])}

        try:
            shutil.rmtree(save_dir + "/" + model)
            data = {}

            with open("static/models/" + uuid + "/config.json", "r+") as file:
                data = json.loads(file.read())

            if model in data.keys():
                del data[model]
            
            with open("static/models/" + uuid + "/config.json", "w+") as file:
                file.write(json.dumps(data))

        except Exception as e:
            print(e)
            return {"status": "failure", "error": self.string(["api", "errors", "unknown", "deletion"])}

        return {"status": "success"}
    
    def start(self):
        # We need to run the API over HTTPS because I don't want to make end-to-end encryption from scratch :)

        if self.DEBUG:
            self.app.run("0.0.0.0", self.PORT, ssl_context=("ssl/domain.cert.pem", "ssl/private.key.pem"))
        else:
            raise Exception("API cannot be run in a non-debug environment. You must run with Gunicorn.")