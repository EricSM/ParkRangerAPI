import pyodbc
import datetime as dt
import jsonpickle

class Report:
    def __init__(self, loc_name, loc_lat, loc_long, description, severity, closure):
        self.id = 0 # Int
        self.loc_name = loc_name # String
        self.loc_lat = loc_lat # Float
        self.loc_long = loc_long # Float
        self.report_description = description # String
        self.severity = severity # Int
        self.closure = closure # Bit
        self.report_datetime = dt.datetime.now().strftime("%m/%d/%Y, %H:%M:%S") # String

    def set_id(self, id):
        self.id = id

    def insert_string(self):
        return "{}, {}, {}, {}, {}, {}, {}".format(self.loc_name, str(self.loc_lat), str(self.loc_long), self.report_description, str(self.severity), str(self.closure), self.report_datetime)

class ReportHandler:
    def __init__(self):
        # server = 'parkwatch-db-server.database.windows.net'
        # database = 'parkwatch-database'
        # username = 'ranger'
        # password = 'ParkWatch123!'
        # driver = '{ODBC Driver 13 for SQL Server};Server=tcp:parkwatch-db-server.database.windows.net,1433;Database=parkwatch-database;Uid=ranger;Pwd=ParkWatch123!;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30'
        # cnxn = pyodbc.connect(driver)

        # self.cnxn = cnxn
        # self.cursor = cnxn.cursor()

        self.report_dictionary = {}

    def create_report(self, loc_name, loc_lat, loc_long, description, severity, closure):
        print("Create report")

        new_report = Report(loc_name, loc_lat, loc_long, description, severity, closure) # Create a new report

        # Commented out temporarily

        # self.cursor.execute("insert into reports(loc_name, loc_lat, loc_long, report_description, severity, closure, report_datetime) values ({})".format(new_report.insert_string())) # Insert it into databse
        # self.cnxn.commit()
        # self.cursor("select SCOPE_IDENTITY()")
        # self.cnxn.commit()

        # new_id = int(self.cursor.fetchone())
        # new_report.set_id(new_id)

        # # Commit report with new id
        # self.cursor.execute("insert into reports(id) values ({})".format(str(new_report.id))) # Insert it into databse
        # self.cnxn.commit()

        new_id = 0
        self.report_dictionary[new_id] = new_report

    def get_report(self, id):
        return self.report_dictionary[id]
    
    def get_report_json(self, id):
        return jsonpickle.encode(self.report_dictionary[id])

