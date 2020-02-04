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

    def set_id(self, uID):
        self.uID = uID

    def __eq__(self, other):
        return self.uID == other.uID

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
        if result:
            dk = hashlib.pbkdf2_hmac('sha256', password.encode(), result.salt, 100000)

            if dk == result.password_hash:
                logged_user = User(result.uID,
                                result.email,
                                result.f_name,
                                result.l_name,
                                result.park_id,
                                result.token)

                return jsonpickle.encode(logged_user)

            else: # wrong password
                return -1
                
        else: # user doesn't exist
            return -1

    def change_password(self, uID, password, new_password):
        print("User changing password for this account:")
        new_salt = os.urandom(32) # random 32 character salt
        new_dk = hashlib.pbkdf2_hmac('sha256', new_password.encode(), new_salt, 100000) # Derived key
        new_token = random.randrange(1000000000000000,9999999999999999) # OS Random gives weird characters

        try:
            return self.change_password_helper(uID, password, new_dk, new_salt, new_token)
        except Exception as e:
            print('Encountered database error while signing in user.\nRetrying.\n{}'.format(str(e)))
            cnxn = pyodbc.connect(driver)

            self.cnxn = cnxn
            self.cursor = cnxn.cursor()
            return self.change_password_helper(uID, password, new_dk, new_salt, new_token)

        return None

    def change_password_helper(self, uID, password, new_dk, new_salt, new_token):
        result = self.cursor.execute("SELECT * FROM Users Where uID = ?", uID).fetchone()

        if result:
            print(result)
            # hash key derived from user submitted password
            dk = hashlib.pbkdf2_hmac('sha256', password.encode(), result.salt, 100000)

            if dk == result.password_hash:
                update_query = "update Users set password_hash = ?, salt = ?, token = ? where uID = ?"
                updated = self.cursor.execute(update_query, uID, new_dk, new_salt, new_token).rowcount
                self.cnxn.commit()
                print("Password changed.")

                # return new token
                if updated == 1:
                    logged_user = User(result.uID,
                                    result.email,
                                    result.f_name,
                                    result.l_name,
                                    result.park_id,
                                    new_token)

                    return jsonpickle.encode(logged_user)
                else: return "Update failed."
            else: # wrong password
                print("Wrong email/password.")
                return -1 #"Incorrect email or password."
        else: # user doesn't exist
            print("Account doesn't exist")
            return -1 # "User does not exist."

    def check_user(self, token, park_id):
        token_query = "SELECT 1 FROM Users WHERE token = ? AND park_id = ?"
        self.cursor.execute(token_query, token, park_id)
        result = self.cursor.fetchone()

        if result:
            return True
        return False
