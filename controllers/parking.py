import pyodbc
import datetime as dt
import jsonpickle
import textwrap

class ParkingLot:
    def __init__(self, lot_name, park_id, lot_lat, lot_long, description, severity):
        self.id = 0 #int
        self.lot_name = lot_name # varchar
        self.park_id = park_id # int
        self.lot_lat = lot_lat # float
        self.lot_long = lot_long #float
        self.description = description # varchar
        self.severity = severity # int

    def set_id(self, id):
        self.id = id

class ParkingHandler:
    def __init__(self):
        global driver
        # driver = 'Driver={ODBC Driver 17 for SQL Server};Server=tcp:parkwatch-db-server.database.windows.net,1433;Database=parkwatch-database;Uid=ranger;Pwd={ParkWatch123!};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
        driver = 'Driver={ODBC Driver 17 for SQL Server};Server=tcp:parkwatch-db-server.database.windows.net,1433;Database=parkwatch-database;Uid=ranger;Pwd=ParkWatch123!;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=0;'
        pyodbc.pooling = False
        cnxn = pyodbc.connect(driver)

        self.cnxn = cnxn
        self.cursor = cnxn.cursor()

    def create_parking_lot(self, lot_name, park_id, lot_lat, lot_long, description, severity):
        print("Create new parking lot.")
        new_parking_lot = ParkingLot(lot_name, park_id, lot_lat, lot_long, description, severity)
        insert_sql_string = textwrap.dedent("""
            Insert Into ParkingLots(park_id,
             loc_lat, 
             loc_long, 
             severity, 
             closure, 
             loc_name, 
             lot_description) 
             Values(?,?,?,?,?,?,?)
        """)

        try:
            return self.create_helper(insert_sql_string, new_parking_lot)
        except Exception as e:
            print('Encountered database error while creating a report.\nRetrying.\n{}'.format(str(e)))
            cnxn = pyodbc.connect(driver)

            self.cnxn = cnxn
            self.cursor = cnxn.cursor()
            return self.create_helper(insert_sql_string, new_parking_lot)

        return None

    def create_helper(self, query, new_parking_lot):
        self.cursor.execute(query, 
                            new_parking_lot.park_id,
                            new_parking_lot.lot_lat,
                            new_parking_lot.lot_long,
                            new_parking_lot.severity,
                            0,
                            new_parking_lot.lot_name,
                            new_parking_lot.description) # Insert it into database
        self.cursor.execute("Select @@IDENTITY")
        new_id = int(self.cursor.fetchone()[0])
        new_parking_lot.set_id(new_id)
        self.cnxn.commit()
        
        return jsonpickle.encode(new_parking_lot)

    def update_parking_lot(self, lot_id, lot_name, park_id, lot_lat, lot_long, description, severity):
        print("Update parking lot.")

        new_parking_lot = ParkingLot(lot_name, park_id, lot_lat, lot_long, description, severity)
        new_parking_lot.id = lot_id

        insert_sql_string = textwrap.dedent("""
            Update ParkingLots
            Set park_id = ?,
                loc_lat = ?, 
                loc_long = ?, 
                severity = ?, 
                closure = ?, 
                loc_name = ?, 
                lot_description = ? 
             Where lot_id = ?
        """)

        try:
            return self.update_helper(insert_sql_string, lot_id, new_parking_lot)
        except Exception as e:
            print('Encountered database error while creating a report.\nRetrying.\n{}'.format(str(e)))
            cnxn = pyodbc.connect(driver)

            self.cnxn = cnxn
            self.cursor = cnxn.cursor()
            return self.update_helper(insert_sql_string, lot_id, new_parking_lot)

        return None

    def update_helper(self, query, lot_id, new_parking_lot):
        self.cursor.execute(query, 
                            new_parking_lot.park_id,
                            new_parking_lot.lot_lat,
                            new_parking_lot.lot_long,
                            new_parking_lot.severity,
                            0,
                            new_parking_lot.lot_name,
                            new_parking_lot.description,
                            lot_id) # Insert it into database
        self.cnxn.commit()
        # self.cursor.execute("Select @@IDENTITY")
        # new_id = int(self.cursor.fetchone()[0])
        # new_parking_lot.id = new_id

        return jsonpickle.encode(new_parking_lot)

    def get_parking_lots(self, park_id):
        """
        Returns the parking_lots associated with the given park id

        Args:
            park_id: The id of the park
        Returns:
            Array of Report objects
        """
        print("Get parking lots.")

        selection_string = textwrap.dedent(""" 
            Select lot_id, park_id, loc_lat, loc_long, severity, loc_name, lot_description 
            From ParkingLots 
            Where park_id = ?""")
        
        try:
            return self.get_list_helper(selection_string, park_id)
        except Exception as e:
            print('Encountered database error while retrieving a list of reports.\nRetrying.\n{}'.format(str(e)))
            cnxn = pyodbc.connect(driver)

            self.cnxn = cnxn
            self.cursor = cnxn.cursor()

            return self.get_list_helper(selection_string, park_id)
        return None
    
    def get_list_helper(self, query, park_id):
        self.cursor.execute(query, park_id)
        results = self.cursor.fetchall()
        lots = []
        if results:
            for result in results:
                fetched_lot = ParkingLot(result.loc_name,
                                        result.park_id,
                                        result.loc_lat,
                                        result.loc_long,
                                        result.lot_description,
                                        result.severity)
                fetched_lot.id = result.lot_id
                lots.append(fetched_lot)
            return lots
    
    def get_parking_lots_list_json(self, park_id):
        return jsonpickle.encode(self.get_parking_lots(park_id))

    def get_parking_lot(self, park_id, lot_id):
        """
        Returns the lot associated with the given id

        Args:
            id: The id of the lot
        Returns:
            ParkingLot object
        """
        print("Get a parking lot.")

        selection_string = textwrap.dedent("""
            Select lot_id, park_id, loc_lat, loc_long, severity, loc_name, lot_description
            From ParkingLots
            Where park_id = ? AND lot_id = ?""")

        try:
            return self.get_helper(selection_string, park_id, lot_id)
        except Exception as e:
            print('Encountered database error while retrieving a report.\nRetrying.\n{}'.format(str(e)))
            cnxn = pyodbc.connect(driver)

            self.cnxn = cnxn
            self.cursor = cnxn.cursor()
            return self.get_helper(selection_string, park_id, lot_id)

        return None

    def get_helper(self, query, park_id, lot_id):
        self.cursor.execute(query, park_id, lot_id)
        result = self.cursor.fetchone()
        if result:
            fetched_lot = ParkingLot(result.loc_name,
                                        result.park_id,
                                        result.loc_lat,
                                        result.loc_long,
                                        result.lot_description,
                                        result.severity)
            fetched_lot.id = result.lot_id
            
            return fetched_lot
        return None

    def get_parking_lot_json(self, park_id, lot_id):
        return jsonpickle.encode(self.get_parking_lot(park_id, lot_id))

    def delete_parking_lot(self, park_id, lot_id):
        print("Delete a parking lot.")

        delete_string = "Delete from ParkingLots where park_id = ? AND lot_id = ?"

        try:
            return self.delete_helper(delete_string, park_id, lot_id)
        except Exception as e:
            print('Encountered database error while deletig a report.\nRetrying.\n{}'.format(str(e)))
            cnxn = pyodbc.connect(driver)

            self.cnxn = cnxn
            self.cursor = cnxn.cursor()
            return self.delete_helper(delete_string, park_id, lot_id)

        return False

    def delete_helper(self, query, park_id, lot_id):
        self.cursor.execute(query, park_id, lot_id)
        self.cursor.commit()
        return True