import pyodbc
import datetime as dt
import jsonpickle
import textwrap
import hashlib
import os

class User:
    def __init__(self, email):
        self.uid = 0 # Int
        self.email = email # String

    def set_id(self, uid):
        self.uid = uid

    def __eq__(self, other):
        return self.uid == other.uid

class UserHandler:
    def __init__(self):
        global driver
        # driver = 'Driver={ODBC Driver 17 for SQL Server};Server=tcp:parkwatch-db-server.database.windows.net,1433;Database=parkwatch-database;Uid=ranger;Pwd={ParkWatch123!};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
        driver = 'Driver={ODBC Driver 17 for SQL Server};Server=tcp:parkwatch-db-server.database.windows.net,1433;Database=parkwatch-database;Uid=ranger;Pwd=ParkWatch123!;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=0;'
        pyodbc.pooling = False
        cnxn = pyodbc.connect(driver)

        self.cnxn = cnxn
        self.cursor = cnxn.cursor()

    def create_user(self, email, password):
        # TODO: return some kind of message if user already exists
        
        salt = os.urandom(32) # random 32 character salt
        dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000).hex() # Derived key

        new_user = User(email)
        insert_sql_string = "Insert into Users(password_hash, salt, email) Values (?,?,?)"

        try:
            return self.create_helper(insert_sql_string, dk, salt, new_user)
        except Exception as e:
            print('Encountered database error while creating a new user.\nRetrying.\n{}'.format(str(e)))
            cnxn = pyodbc.connect(driver)

            self.cnxn = cnxn
            self.cursor = cnxn.cursor()
            return self.create_helper(insert_sql_string, dk, salt, new_user)

        return None

    def create_helper(self, query, dk, salt, new_user):
        self.cursor.execute(query, 
                                dk,
                                salt,
                                new_user.email) # Insert new user into database
        self.cnxn.commit()
        self.cursor.execute("Select @@IDENTITY")
        new_id = int(self.cursor.fetchone()[0])
        new_user.set_id(new_id)

        return jsonpickle.encode(new_user)

def get_user(self, email, password):
    # TODO: handle if user does not exist
    # TODO: keep track of logged user
    print("User signing in.")
    selection_string = "Select uID, password_hash, salt, From Users Where email = ?"

    try:
        return self.get_helper(selection_string, email, password)
    except Exception as e:
        print('Encountered database error while signing in user.\nRetrying.\n{}'.format(str(e)))
        cnxn = pyodbc.connect(driver)

        self.cnxn = cnxn
        self.cursor = cnxn.cursor()
        return self.get_helper(selection_string, email, password)

    return None

def get_helper(self, query, email, password):
    self.cursor.execute(query, email)
    result = self.cursor.fetchone()
    print(result)

    # hash key derived from user submitted password
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), result.salt, 100000).hex()

    if result and dk == result.password_hash:
        logged_user = User(result.email)
        logged_user.set_id(result.uid)
        
        return logged_user
