import sqlite3
from uuid import uuid4
import bcrypt
import time

class Tokens:
    EXPIRES = 30 * 24 * 60 * 60 # 30 days for a token to expire, converted to seconds
    def __init__(self):
        self.con = sqlite3.connect("tokens.db", check_same_thread=False)
        self.cur = self.con.cursor()

        self.cur.execute("CREATE TABLE IF NOT EXISTS tokens (token varchar(255), uuid varchar(255), timestamp INTEGER, source varchar(255))")

    def generate_token(self):
        return uuid4().hex

    def hash(self, text, salt_level=12):
        salt = bcrypt.gensalt(salt_level)
        return bcrypt.hashpw(text.encode("utf-8"), salt)

    def register_token(self, token, uuid, source, autohash=True):
        if autohash:
            token = self.hash(token)
        self.cur.execute("INSERT INTO tokens VALUES (?, ?, ?, ?)", (token, uuid, time.time(), source))
        self.con.commit()

    def verify(self, uuid, token):
        self.cur.execute("DELETE FROM tokens WHERE uuid = ? AND timestamp < ?", (uuid, time.time()-self.EXPIRES))
        self.cur.execute("SELECT * FROM tokens WHERE uuid = ?", (uuid,))
        matching = self.cur.fetchall()
        
        for match in matching:
            try:
                if bcrypt.checkpw(token.encode("utf-8"), match[0]):
                    return True
            except ValueError:
                pass
        
        return False
    
    def finish(self):
        self.con.close()