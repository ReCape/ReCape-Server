import api

def create_server():
    server = api.Server(False)
    return server.app