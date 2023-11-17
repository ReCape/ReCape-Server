import os
import subprocess 
import threading
import optifine_server
from contextlib import redirect_stdout, redirect_stderr

DEBUG = os.path.exists(".debug")

def mc_server():
    if not DEBUG:
        with open("log.java.txt", "w+") as log:
            with redirect_stdout(log):
                with redirect_stderr(log):
                    subprocess.call("java -jar server.jar --nogui", shell=True)
    else:
        subprocess.call("java -jar server.jar --nogui", shell=True)

def optifine_serve():
    server = optifine_server.Server(DEBUG)
    if not DEBUG:
        with open("log.optifine.txt", "w+") as log:
            with redirect_stdout(log):
                with redirect_stderr(log):
                    server.start()
    else:
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
    with open("log.api.txt", "w+") as log:
            with redirect_stdout(log):
                with redirect_stderr(log):
                    subprocess.run("python3 -m gunicorn --certfile=ssl/domain.cert.pem --keyfile=ssl/private.key.pem --bind 0.0.0.0:443 \"wsgi:create_server()\"", shell=True)

server_thread.join()
optifine_thread.join()