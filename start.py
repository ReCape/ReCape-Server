import os
import subprocess 
import threading
import optifine_server

DEBUG = os.path.exists(".debug")

def mc_server():
    subprocess.call("java -jar server.jar", shell=True)

def optifine_serve():
    server = optifine_server.Server(DEBUG)
    server.start()

server_thread = threading.Thread(target=mc_server)
optifine_thread = threading.Thread(target=optifine_serve)
server_thread.start()
optifine_thread.start()

if DEBUG:
    import api
    server = api.Server(DEBUG)
    server.start()
else:
    subprocess.run("python3 -m gunicorn --certfile=ssl/domain.cert.pem --keyfile=ssl/private.key.pem --bind 0.0.0.0:443 \"wsgi:create_server()\"", shell=True)

server_thread.join()
optifine_thread.join()