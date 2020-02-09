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
        self.description = description # String
        self.severity = severity # Int
        self.closure = closure # Bit
        self.date = dt.datetime.now()# .strftime("%m/%d/%Y, %H:%M:%S") # String
        self.approved_status = approved_status # Bit

    def set_id(self, id):
        self.id = id

    def insert_string(self):
        return "{}, {}, {}, {}, {}, {}, {}".format(self.loc_name, str(self.loc_lat), str(self.loc_long), self.description, str(self.severity), str(self.closure), self.date)

    def __eq__(self, other):
        return self.id == other.id

class ReportHandler:
    def __init__(self):
        global driver
        # driver = 'Driver={ODBC Driver 17 for SQL Server};Server=tcp:parkwatch-db-server.database.windows.net,1433;Database=parkwatch-database;Uid=ranger;Pwd={ParkWatch123!};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
        driver = 'Driver={ODBC Driver 17 for SQL Server};Server=tcp:parkwatch-db-server.database.windows.net,1433;Database=parkwatch-database;Uid=ranger;Pwd=ParkWatch123!;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=0;'
        pyodbc.pooling = False
        cnxn = pyodbc.connect(driver)

        self.cnxn = cnxn
        self.cursor = cnxn.cursor()

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
        print("Creating a new report.")

        new_report = Report(loc_name, park_id, loc_lat, loc_long, description, severity, closure, approved_status) # Create a new report

        insert_sql_string = "Insert Into Reports(loc_name, loc_lat, loc_long, description, severity, closure, date, park_id, approved_status) Values (?,?,?,?,?,?,?,?,?)"
        
        
        try:
            return self.create_helper(insert_sql_string, new_report)
        except Exception as e:
            print('Encountered database error while creating a report.\nRetrying.\n{}'.format(str(e)))
            cnxn = pyodbc.connect(driver)

            self.cnxn = cnxn
            self.cursor = cnxn.cursor()
            return self.create_helper(insert_sql_string, new_report)

        return None

    def create_helper(self, query, new_report):
        self.cursor.execute(query, 
                                new_report.loc_name, 
                                str(new_report.loc_lat), 
                                str(new_report.loc_long), 
                                new_report.report_description, 
                                new_report.severity,
                                str(new_report.closure), 
                                new_report.date,
                                new_report.park_id,
                                str(new_report.approved_status)) # Insert it into database
        self.cnxn.commit()
        self.cursor.execute("Select @@IDENTITY")
        new_id = int(self.cursor.fetchone()[0])
        new_report.set_id(new_id)

        return jsonpickle.encode(new_report)

    def get_report(self, park_id, id):
        """
        Returns the report associated with the given id

        Args:
            id: The id of the report
        Returns:
            Report object
        """
        print("Getting Report.")
        selection_string = "Select loc_name, loc_lat, loc_long, report_description, severity, closure, date, park_id, approved_status From Reports Where park_id = {} AND ID = {}".format(park_id, id)
        print(selection_string)

        try:
            return self.get_helper(selection_string)
        except Exception as e:
            print('Encountered database error while retrieving a report.\nRetrying.\n{}'.format(str(e)))
            cnxn = pyodbc.connect(driver)

            self.cnxn = cnxn
            self.cursor = cnxn.cursor()
            return self.get_helper(selection_string)

        return None

    def get_helper(self, query):
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        print(result)
        if result:
            fetched_report = Report(result.loc_name,
                                    result.park_id,
                                    result.loc_lat,
                                    result.loc_long,
                                    result.report_description,
                                    result.severity,
                                    result.closure,
                                    result.approved_status)
            
            return fetched_report

    def get_reports(self, park_id):
        """
        Returns the reports associated with the given park id

        Args:
            park_id: The id of the park
        Returns:
            Array of Report objects
        """
        print("Getting reports.")

        selection_string = "Select id, loc_name, loc_lat, loc_long, report_description, severity, closure, date, park_id, approved_status From Reports Where park_id = {}".format(park_id)
        
        try:
            return self.get_list_helper(selection_string)
        except Exception as e:
            print('Encountered database error while retrieving a list of reports.\nRetrying.\n{}'.format(str(e)))
            cnxn = pyodbc.connect(driver)

            self.cnxn = cnxn
            self.cursor = cnxn.cursor()

            return self.get_list_helper(selection_string)
        return None
    
    def get_list_helper(self, query):
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        reports = []
        if results:
            for result in results:
                fetched_report = Report(result.loc_name,
                                        result.park_id,
                                        result.loc_lat,
                                        result.loc_long,
                                        result.report_description,
                                        result.severity,
                                        result.closure,
                                        result.approved_status)
                fetched_report.set_id(result.id)
                reports.append(fetched_report)
            return reports

    def update_report(self, park_id, rule_id, loc_name, loc_lat, loc_long, description, severity, closure, approved_status):
        """
        Updates the report associated with the given ID with the given arguments, then returns the report.

        Args:
            id: The ID of the report
            park_id: The id of the park
            loc_name: The name of the location (str)
            loc_lat: The latitude of the location (float)
            loc_long: The longitude of the location (float)
            description: A short description of the issue (str)
            severity: The severity of the issue from 1-10 (int)
            closure: 0 for not closed, 1 for closed (bit)
            approved_status: 0 for not approved, 1 for approved (bit)
        Returns:
            The updated report
        """
        print("Update a report.")
        
        updated_report = Report(loc_name, park_id, loc_lat, loc_long, description, severity, closure, approved_status) # Update the old report

        update_string = textwrap.dedent("""
            update Reports 
            set loc_name = ?, 
                loc_lat = ?, 
                loc_long = ?, 
                report_description = ?, 
                severity = ?, 
                closure = ?, 
                approved_status = ?
            where ID = ?
        """)
        
        try:
            return self.update_helper(update_string, rule_id, updated_report)
        except Exception as e:
            print('Encountered database error while updating a report.\nRetrying.\n{}'.format(str(e)))
            cnxn = pyodbc.connect(driver)

            self.cnxn = cnxn
            self.cursor = cnxn.cursor()

            return self.update_helper(update_string, rule_id, updated_report)
        return None


    def update_helper(self, query, report_id, report):
        self.cursor.execute(query, 
                            report.loc_name, 
                            str(report.loc_lat), 
                            str(report.loc_long), 
                            str(report.description), 
                            str(report.severity), 
                            str(report.closure), 
                            str(report.approved_status),
                            report_id)
        self.cursor.commit()

        print('report {} updated'.format(id), flush=True)
        return jsonpickle.encode(report)

    def delete_report(self, park_id, id):
        """
        Deletes the report associated with the given ID.

        Args:
            id: The ID of the report
        Returns:
            True or False
        """
        print("Delete a report.")

        delete_string = "Delete from Reports where park_id = ? AND ID = ?"

        try:
            return self.delete_helper(delete_string, park_id, id)
        except Exception as e:
            print('Encountered database error while deletig a report.\nRetrying.\n{}'.format(str(e)))
            cnxn = pyodbc.connect(driver)

            self.cnxn = cnxn
            self.cursor = cnxn.cursor()
            return self.delete_helper(delete_string, park_id, id)

        return False

    def delete_helper(self, query, park_id, id):
        self.cursor.execute(query, park_id, id)
        self.cursor.commit()
        print('report {0} deleted from park {1}'.format(id, park_id))
        return True

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
        return jsonpickle.encode(self.get_reports(park_id))



