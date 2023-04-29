import sqlite3

class UUIDs:
    def __init__(self):
        self.con = sqlite3.connect("uuid.db", check_same_thread=False)
        self.cur = self.con.cursor()

        self.cur.execute("CREATE TABLE IF NOT EXISTS tokens (uuid varchar(255), username varchar(255))")

    def register(self, uuid, username):
        self.cur.execute("DELETE FROM uuids WHERE uuid = ?", (uuid,))
        self.con.commit()
        self.cur.execute("DELETE FROM uuids WHERE username = ?", (username,))
        self.con.commit()
        
        self.cur.execute("INSERT INTO uuids VALUES (?, ?)", (uuid, username))
        self.con.commit()

    def get_username(self, uuid):
        self.cur.execute("SELECT * FROM uuids WHERE uuid = ?", (uuid,))
        matching = self.cur.fetchall()
        
        if len(matching) > 0:
            return matching[0][1]
        return False
    
    def get_uuid(self, username):
        self.cur.execute("SELECT * FROM uuids WHERE username = ?", (username,))
        matching = self.cur.fetchall()
        
        if len(matching) > 0:
            return matching[0][0]
        return False
    
    def finish(self):
        self.con.close()