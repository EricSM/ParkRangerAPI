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
        self.report_datetime = dt.datetime.now()# .strftime("%m/%d/%Y, %H:%M:%S") # String

    def set_id(self, id):
        self.id = id

    def insert_string(self):
        return "{}, {}, {}, {}, {}, {}, {}".format(self.loc_name, str(self.loc_lat), str(self.loc_long), self.report_description, str(self.severity), str(self.closure), self.report_datetime)

class ReportHandler:
    def __init__(self):
        server = 'parkwatch-db-server.database.windows.net'
        database = 'parkwatch-database'
        username = 'ranger'
        password = 'ParkWatch123!'
        driver = 'Driver={ODBC Driver 17 for SQL Server};Server=tcp:parkwatch-db-server.database.windows.net,1433;Database=parkwatch-database;Uid=ranger;Pwd={ParkWatch123!};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
        cnxn = pyodbc.connect(driver)

        self.cnxn = cnxn
        self.cursor = cnxn.cursor()

        self.temp_fake_db = []
        self.report_dictionary = {}

    def create_report(self, loc_name, loc_lat, loc_long, description, severity, closure):
        """
        Creates a new report object, adds it to the database, then updates and returns the new report's ID

        Args:
            loc_name: The name of the location (str)
            loc_lat: The latitude of the location (float)
            loc_long: The longitude of the location (float)
            description: A short description of the issue (str)
            severity: The severity of the issue from 1-10 (int)
            closure: 0 for not closed, 1 for closed (bit)
        Returns:
            Returns the id of the newly created report
        """

        new_report = Report(loc_name, loc_lat, loc_long, description, severity, closure) # Create a new report

        insert_sql_string = "Insert Into Reports(loc_name, loc_lat, loc_long, report_description, severity, closure, report_datetime) Values (?,?,?,?,?,?,?)"
        self.cursor.execute(insert_sql_string, 
                            new_report.loc_name, 
                            str(new_report.loc_lat), 
                            str(new_report.loc_long), 
                            new_report.report_description, 
                            str(new_report.closure), 
                            str(new_report.severity), 
                            new_report.report_datetime) # Insert it into database
        self.cnxn.commit()
        self.cursor.execute("Select @@IDENTITY")
        new_id = int(self.cursor.fetchone()[0])
        new_report.set_id(new_id)
        self.cnxn.commit()

        new_id = 0
        print(new_id)

        # Commit report with new id
        # update_report_id_string = "Update Reports Set id = " + str(new_id) +" Where id = " + str(new_id)
        # self.cursor.execute(update_report_id_string)
        # self.cnxn.commit()

        self.temp_fake_db.append(new_report)
        self.report_dictionary[new_id] = new_report

        return new_id

    def get_report(self, id):
        """
        Returns the report associated with the given id

        Args:
            id: The id of the report
        Returns:
            Report object
        """
        return self.report_dictionary[id]
    
    def get_report_json(self, id):
        """
        Returns the report associated with the given id as a JSON

        Args:
            id: The id of the report
        Returns:
            Returns json of report object
        """
        return jsonpickle.encode(self.report_dictionary[id])

    def get_reports_list_json(self):
        """
        TODO(Ian): This should return all cached reports
        """
        reports = []

        for r in self.temp_fake_db:
            reports.append(jsonpickle.encode(r))
    
        return jsonpickle.encode({'reports': reports})



