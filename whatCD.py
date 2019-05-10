# this will load libdiscid
# Make sure the correct version of discid.dll for the machines architechure is installed
import discid
import ctypes
import sqlite3
import sys

conn = sqlite3.connect("glastonbury_cds.db")

c = conn.cursor()

try:
    c.execute("""CREATE TABLE discs (
            shelfmark text NOT NULL UNIQUE,
            cddb_id text NOT NULL PRIMARY KEY,
            tracks integer NOT NULL,
            length integer NOT NULL)""")
except sqlite3.OperationalError:
    print("Database already exists continuing...")


def insert_disc(disc):
    with conn:
        try:
            c.execute("""INSERT into discs VALUES (
            :shelfmark, 
            :cddb_id, 
            :tracks, 
            :length)""", {'shelfmark':disc.shelfmark, 'cddb_id':disc.freedb_id.upper(), 'tracks':len(disc.tracks), 'length':disc.seconds})
        except sqlite3.IntegrityError:
            exc_obj = sys.exc_info()[1]
            if "discs.cddb_id" in str(exc_obj):
                print("This disc is already in the database")
                c.execute("SELECT * FROM discs WHERE cddb_id=:cddb_id", {'cddb_id':disc.freedb_id.upper()})
                print(c.fetchone())
                read_disc_info()
            elif "discs.shelfmark" in str(exc_obj):
                print("This shelfmark is already in the database")
                c.execute("SELECT * FROM discs WHERE shelfmark=:shelfmark", {'shelfmark':disc.shelfmark})
                print(c.fetchone())
                enter_shelfmark(disc)
                insert_disc(disc)
        


def open_cd_door():
    ctypes.windll.winmm.mciSendStringW('set cdaudio door open', None, 0, None)


def close_cd_door():
    ctypes.windll.winmm.mciSendStringW('set cdaudio door closed', None, 0, None)

def enter_shelfmark(disc):
    while True:
            disc.shelfmark = input("Please enter the sub-shelfmark of the current disc C1238/")
            if disc.shelfmark != "":
                disc.shelfmark = "C1238/" + disc.shelfmark.replace(" ", "")  
                break
            print("Sub-shelfmark cannot be blank!\n")

def read_disc_info():
    while True:
        open_cd_door()
        input("Press enter to close the cd door\n\n")
        close_cd_door()
        
        print(f"Reading device: {discid.get_default_device()}\n")
        # reads from default device
        try:
            disc = discid.read()
        except discid.disc.DiscError as e:
            print(e)
            print("\n")
            read_disc_info()        
        
        print(f"Disc cddb_id: {disc.freedb_id.upper()}")
        print(f"The number of tracks is {len(disc.tracks)}")
        print(f"The total duration in seconds is: {disc.seconds}")
        
        enter_shelfmark(disc)
        
        # https://www.tutorialspoint.com/How-to-get-Python-exception-text
        
        insert_disc(disc)   
    
        if input("Press enter for the next disc or q to quit: ") == "q":
            break


read_disc_info()


c.execute("SELECT * FROM discs")

print(c.fetchall())


conn.commit()
conn.close()