import sqlite3
import threading

class UUIDs:
    lock = threading.Lock()
    def __init__(self):
        self.con = sqlite3.connect("uuid.db", check_same_thread=False)
        self.cur = self.con.cursor()

        self.cur.execute("CREATE TABLE IF NOT EXISTS uuids (uuid varchar(255), username varchar(255))")

    def register(self, uuid, username):
        try:
            self.lock.acquire(True)
            self.cur.execute("DELETE FROM uuids WHERE uuid = ?", (uuid,))
            self.con.commit()
            self.cur.execute("DELETE FROM uuids WHERE username = ?", (username,))
            self.con.commit()
            
            self.cur.execute("INSERT INTO uuids VALUES (?, ?)", (uuid, username))
            self.con.commit()
        finally:
            self.lock.release()

    def get_username(self, uuid):
        try:
            self.lock.acquire(True)
            self.cur.execute("SELECT * FROM uuids WHERE uuid = ?", (uuid,))
            matching = self.cur.fetchall()
        finally:
            self.lock.release()
        
        if len(matching) > 0:
            return matching[0][1]
        return False
    
    def get_uuid(self, username):
        try:
            self.lock.acquire(True)
            self.cur.execute("SELECT * FROM uuids WHERE username = ?", (username,))
            matching = self.cur.fetchall()
        finally:
            self.lock.release()
        
        if len(matching) > 0:
            return matching[0][0]
        return False
    
    def get_user_count(self):
        try:
            self.lock.acquire(True)
            self.cur.execute("SELECT * FROM uuids")
        finally:
            self.lock.release()
        return len(self.cur.fetchall())
    
    def finish(self):
        self.con.close()