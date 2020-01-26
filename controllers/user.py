import pyodbc
import datetime as dt
import jsonpickle
import textwrap
import hashlib
import os

# TODO: add more comments

class User:
    def __init__(self, uid, email):
        self.uid = uid # Int
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
        salt = os.urandom(32) # random 32 character salt
        dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000).hex() # Derived key

        insert_sql_string = "Insert into Users(password_hash, salt, email) Values ({},?,?)".format(dk)

        try:
            return self.create_helper(insert_sql_string, salt, email)
        except Exception as e:
            print('Encountered database error while creating a new user.\nRetrying.\n{}'.format(str(e)))
            cnxn = pyodbc.connect(driver)

            self.cnxn = cnxn
            self.cursor = cnxn.cursor()
            return self.create_helper(insert_sql_string, salt, email)

        return None

    def create_helper(self, query, salt, email):
        self.cursor.execute(query, 
                                salt, 
                                email) # Insert new user into database
        self.cnxn.commit()
        self.cursor.execute("Select @@IDENTITY")

        row = self.cursor.fetchval()

        if row:
            new_id = int(row)
            new_user = User(new_id, email)
            return jsonpickle.encode(new_user)
        else: # user already exists
            new_user = User(None, email)
            return jsonpickle.encode(new_user)

    def login(self, email, password):
        # TODO: keep track of logged user
        print("User signing in.")
        selection_string = "Select uID, password_hash, salt, From Users Where email = ?"

        try:
            return self.login_helper(selection_string, email, password)
        except Exception as e:
            print('Encountered database error while signing in user.\nRetrying.\n{}'.format(str(e)))
            cnxn = pyodbc.connect(driver)

            self.cnxn = cnxn
            self.cursor = cnxn.cursor()
            return self.login_helper(selection_string, email, password)

        return None

    def login_helper(self, query, email, password):
        self.cursor.execute(query, email)
        result = self.cursor.fetchone()
        print(result)

        # hash key derived from user submitted password
        dk = hashlib.pbkdf2_hmac('sha256', password.encode(), str(result.salt).encode(), 100000).hex()

        if result and dk == result.password_hash:
            logged_user = User(result.uid, email)
            return jsonpickle.encode(logged_user)

        elif result and dk != result.password_hash: # wrong password
            existing_user = User(None, email)
            return jsonpickle.encode(existing_user)
        else: # user doesn't exist
            null_user = User(None, None)
            return jsonpickle.encode(null_user)
