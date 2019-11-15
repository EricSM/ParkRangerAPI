import pyodbc
import datetime as dt
import jsonpickle
import textwrap

class Report:
    def __init__(self, loc_name, park_id, loc_lat, loc_long, description, severity, closure, approved_status):
        self.id = 0 # Int
        self.park_id = park_id
        self.loc_name = loc_name # String
        self.loc_lat = loc_lat # Float
        self.loc_long = loc_long # Float
        self.report_description = description # String
        self.severity = severity # Int
        self.closure = closure # Bit
        self.report_datetime = dt.datetime.now()# .strftime("%m/%d/%Y, %H:%M:%S") # String
        self.approved_status = approved_status # Bit

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
        # driver = 'Driver={ODBC Driver 17 for SQL Server};Server=tcp:parkwatch-db-server.database.windows.net,1433;Database=parkwatch-database;Uid=ranger;Pwd={ParkWatch123!};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
        driver = 'Driver={ODBC Driver 17 for SQL Server};Server=tcp:parkwatch-db-server.database.windows.net,1433;Database=parkwatch-database;Uid=ranger;Pwd=ParkWatch123!;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
        cnxn = pyodbc.connect(driver)

        self.cnxn = cnxn
        self.cursor = cnxn.cursor()

        self.temp_fake_db = []
        self.report_dictionary = {}

    def create_report(self, loc_name, park_id, loc_lat, loc_long, description, severity, closure, approved_status):
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

        new_report = Report(loc_name, park_id, loc_lat, loc_long, description, severity, closure, approved_status) # Create a new report

        insert_sql_string = "Insert Into Reports(loc_name, loc_lat, loc_long, report_description, severity, closure, report_datetime, park_id, approved_status) Values (?,?,?,?,?,?,?,?,?)"
        self.cursor.execute(insert_sql_string, 
                            new_report.loc_name, 
                            str(new_report.loc_lat), 
                            str(new_report.loc_long), 
                            new_report.report_description, 
                            str(new_report.closure), 
                            str(new_report.severity), 
                            new_report.report_datetime,
                            new_report.park_id,
                            approved_status) # Insert it into database
        self.cnxn.commit()
        self.cursor.execute("Select @@IDENTITY")
        new_id = int(self.cursor.fetchone()[0])
        new_report.set_id(new_id)
        self.cnxn.commit()

        # Commit report with new id
        # update_report_id_string = "Update Reports Set id = " + str(new_id) +" Where id = " + str(new_id)
        # self.cursor.execute(update_report_id_string)
        # self.cnxn.commit()

        self.temp_fake_db.append(new_report)
        self.report_dictionary[new_id] = new_report

        return jsonpickle.encode(new_report)

    def get_report(self, park_id, id):
        """
        Returns the report associated with the given id

        Args:
            id: The id of the report
        Returns:
            Report object
        """

        selection_string = "Select * Where park_id = {} AND id = {}".format(park_id, id)
        self.cursor.execute(selection_string)
        rows = self.cursor.fetchall()

        if rows:
            fetched_report = Report(rows.loc_name,
                                    rows.park_id,
                                    rows.loc_lat,
                                    rows.loc_long,
                                    rows.report_description,
                                    rows.severity,
                                    rows.closure,
                                    rows.approved_status)
            
            return fetched_report

        return None
    
    def update_report(self, id, loc_name, loc_lat, loc_long, description, severity, closure, approved_status):
        """
        Updates the report associated with the given ID with the given arguments.

        Args:
            id: The ID of the report
            loc_name: The name of the location (str)
            loc_lat: The latitude of the location (float)
            loc_long: The longitude of the location (float)
            description: A short description of the issue (str)
            severity: The severity of the issue from 1-10 (int)
            closure: 0 for not closed, 1 for closed (bit)
            approved_status: 0 for not approved, 1 for approved (bit)
        Returns:
            None
        """

        update_string = textwrap.dedent("""
            update Reports 
            set loc_name = ?, 
                loc_lat = ?, 
                loc_long = ?, 
                report_description = ?, 
                severity = ?, 
                closure = ?, 
                approved_status = ?
            where ID = ?"
        """)
        self.cursor.execute(update_string, 
                            loc_name, 
                            str(loc_lat), 
                            str(loc_long), 
                            description, 
                            str(severity), 
                            str(closure), 
                            approved_status)
        self.cursor.commit()
        
        print('report {} updated'.format(id))

    def delete_report(self, park_id, id):
        """
        Deletes the report associated with the given ID.

        Args:
            id: The ID of the report
        Returns:
            None
        """

        delete_string = "Delete from Reports where park_id = ? AND ID = ?"
        self.cursor.execute(delete_string, park_id, id)
        self.cursor.commit()
        
        print('report {0} deleted from park {1}'.format(id, park_id))

    def get_report_json(self, park_id, id):
        """
        Returns the report associated with the given id as a JSON

        Args:
            id: The id of the report
        Returns:
            Returns json of report object
        """
        return jsonpickle.encode(self.get_report(park_id, id))

    def get_reports_list_json(self, park_id):
        """
        TODO(Ian): This should return all cached reports
        """
        reports = []

        for r in self.temp_fake_db:
            reports.append(jsonpickle.encode(r))
    
        return jsonpickle.encode(reports)



