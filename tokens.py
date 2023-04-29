import sqlite3
from uuid import uuid4
import bcrypt

class Tokens:
    def __init__(self):
        self.con = sqlite3.connect("tokens.db", check_same_thread=False)
        self.cur = self.con.cursor()

    def generate_token(self):
        return uuid4().hex

    def hash(self, text, salt_level=12):
        salt = bcrypt.gensalt(salt_level)
        return bcrypt.hashpw(text, salt)

    def register_token(self, token, uuid, source, autohash=True):
        if autohash:
            token = self.hash(token)
        self.cur.execute("INSERT INTO tokens VALUES (?, ?, ?)", (token, uuid, source))
        self.con.commit()

    def verify(self, uuid, token):
        self.cur.execute("SELECT * FROM tokens WHERE uuid = ?", (uuid,))
        matching = self.cur.fetchall()
        
        for match in matching:
            try:
                if bcrypt.checkpw(token, match[0]):
                    return True
            except ValueError:
                pass
        
        return False
    
    def finish(self):
        self.con.close()