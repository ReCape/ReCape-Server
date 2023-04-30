import os
import subprocess 
import threading
import api
import optifine_server

DEBUG = os.path.exists(".debug")

def mc_server():
    subprocess.call("java -jar server.jar", shell=True)

def optifine_serve():
    server = optifine_server.Server()
    server.start()

server_thread = threading.Thread(target=mc_server)
optifine_thread = threading.Thread(target=optifine_serve)
server_thread.start()
optifine_thread.start()

server = api.Server()
server.start()

server_thread.join()
optifine_thread.join()