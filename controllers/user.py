import pyodbc
import datetime as dt
import jsonpickle
import textwrap
import hashlib
import os
import random
from base64 import b64encode

# TODO: add more comments

class User:
    def __init__(self, uID, email, f_name, l_name, park_id, token):
        self.uID = uID # Int
        self.email = email # String
        self.f_name = f_name # String
        self.l_name = l_name # String
        self.park_id = park_id # Int
        self.token = token # Int

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

    def create_user(self, email, password, f_name, l_name, park_id):        
        salt = os.urandom(32) # random 32 character salt
        #salt = b64encode(os.urandom(32)).decode('utf-8')
        dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000) # Derived key
        token = random.randrange(1000000000000000,9999999999999999) # OS Random gives weird characters

        insert_sql_string = textwrap.dedent("""
        INSERT Users
            (password_hash, 
             salt, 
             email,
             f_name,
             l_name,
             park_id,
             token)
        VALUES (?,?,?,?,?,?,?)""")

        try:
            return self.create_helper(insert_sql_string, dk, salt, email, f_name, l_name, int(park_id), token)
        except Exception as e:
            print('Encountered database error while creating a new user.\nRetrying.\n{}'.format(str(e)))
            cnxn = pyodbc.connect(driver)

            self.cnxn = cnxn
            self.cursor = cnxn.cursor()
            return self.create_helper(insert_sql_string, dk, salt, email, f_name, l_name, int(park_id), token)

        return None

    def create_helper(self, query, dk, salt, email, f_name, l_name, park_id, token):
        # Check if this email is already in use
        select_email_str = "SELECT * FROM Users WHERE email = ?"

        self.cursor.execute(select_email_str, email)
        row = self.cursor.fetchone()

        if row:
            new_user = User(row.uID,
                            row.email,
                            row.f_name,
                            row.l_name,
                            row.park_id,
                            row.token)

            return jsonpickle.encode(new_user)

        else:
            self.cursor.execute(query, 
                                    dk,
                                    salt, 
                                    email,
                                    f_name,
                                    l_name,
                                    park_id,
                                    token) # Insert new user into database
            self.cnxn.commit()
            self.cursor.execute("Select @@IDENTITY")
            row = self.cursor.fetchone()
            new_user = User(int(row[0]),
                            email,
                            f_name,
                            l_name,
                            park_id,
                            token)

            return jsonpickle.encode(new_user)

    def login(self, email, password):
        # TODO: keep track of logged user
        print("User signing in.")
        selection_string = "SELECT * FROM Users Where email = ?"

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
        dk = hashlib.pbkdf2_hmac('sha256', password.encode(), result.salt, 100000)

        if result and dk == result.password_hash:
            logged_user = User(result.uID,
                            result.email,
                            result.f_name,
                            result.l_name,
                            result.park_id,
                            result.token)

            return jsonpickle.encode(logged_user)

        elif result and dk != result.password_hash: # wrong password
            return "Incorrect email or password."
        else: # user doesn't exist
            return "User does not exist."
