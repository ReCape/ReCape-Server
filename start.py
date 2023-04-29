import os
import subprocess 
import threading
import api

def mc_server():
    subprocess.call("java -jar server.jar", shell=True)

server_thread = threading.Thread(target=mc_server)
#server_thread.start()

server = api.Server()
server.start()

server_thread.join()