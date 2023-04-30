import json
import os
import shutil
import flask
import werkzeug
import authenticator
import tokens
import uuids
from mojang import API, errors
import urllib.request, urllib.error

class Server:
    app = flask.Flask(__name__)

    CLOAKS_PLUS_URL = "https://server.cloaksplus.com"

    PORT = 80

    def __init__(self):
        self.tokens = tokens.Tokens()
        self.uuids = uuids.UUIDs()
        self.api = API()

        @self.app.route("/capes/<username>")
        def serve_cape(username): return self.serve_cape(username)

        @self.app.route("/users/<username>.cfg")
        def serve_user_config(username): return self.serve_user_config(username)

        @self.app.route("/items/<uuid>/<model>/model.cfg")
        def serve_item_model(uuid, model): return self.serve_item_model(uuid, model)
        @self.app.route("/items/<uuid>/<model>/texture.png")
        def serve_item_texture(uuid, model): return self.serve_item_texture(uuid, model, None)
        @self.app.route("/items/<uuid>/<model>/users/<user>")
        def serve_item_texture_with_user(uuid, model, user): return self.serve_item_texture(uuid, model, user)

    
    def serve_cape(self, username):
        username = username.replace(".png", "")
        try:
            uuid = self.uuids.get_uuid(username).replace("-", "")
        except:
            return ""
        print(uuid)
        file = flask.send_from_directory("static/capes", uuid + ".png")
        if file.status_code == 404:
            file = flask.redirect(self.CLOAKS_PLUS_URL + "/capes/" + username + ".png", code=200)
        return file

    def serve_user_config(self, config):
        print(config)
        uuid = self.uuids.get_uuid(config)
        if not uuid:
            return ""
        uuid = uuid.replace("-", "")
        with open("static/models/" + uuid + "/config.json", "r+") as file:
            config = json.loads(file.read())
        if config == "":
            config = {}
        
        optifine_formatted_cfg = {"items": []}

        for item in config.keys():
            optifine_formatted_cfg["items"].append({
                "type": item,
                "model": "items/" + uuid + "/" + item + "/model.cfg",
                "texture": "items/" + uuid + "/" + item + "/texture.png",
                "active": config[item]
            })

        return optifine_formatted_cfg
    
    def serve_item_model(self, uuid, model):
        return flask.send_from_directory("static/models/" + uuid + "/" + model, "model.cfg")
    def serve_item_texture(self, uuid, model, user):
        return flask.send_from_directory("static/models/" + uuid + "/" + model, "texture.png")
    
    def start(self):
        self.app.run("0.0.0.0", self.PORT) # We need to run the OF server over HTTP since we can't use OptiFine's SSL certificates (duh) and OptiFine can use HTTP anyway