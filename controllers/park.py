import pyodbc
import textwrap
import jsonpickle

class Park:
    def __init__(self, park_name, park_id, park_lat, park_lon, park_org, park_cover_image, park_logo):
        self.park_name = park_name # varchar
        self.park_id = park_id # int
        self.park_lat = park_lat # float
        self.park_lon = park_lon #float
        self.park_org = park_org
        self.park_cover_image = park_cover_image
        self.park_logo = park_logo
        

    def set_id(self, id):
        self.id = id

class ParkHandler():
    def __init__(self):
        global driver
        # driver = 'Driver={ODBC Driver 17 for SQL Server};Server=tcp:parkwatch-db-server.database.windows.net,1433;Database=parkwatch-database;Uid=ranger;Pwd={ParkWatch123!};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
        driver = 'Driver={ODBC Driver 17 for SQL Server};Server=tcp:parkwatch-db-server.database.windows.net,1433;Database=parkwatch-database;Uid=ranger;Pwd=ParkWatch123!;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=0;'
        pyodbc.pooling = False
        cnxn = pyodbc.connect(driver)

        self.cnxn = cnxn
        self.cursor = cnxn.cursor()

    def get_parks(self):
        print("Get parks")

        selection_string = textwrap.dedent(""" 
            Select * From Parks""")
        
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
        parks = []
        if results:
            for result in results:
                fetched_park = Park(result.Name,
                                    result.ID,
                                    result.park_lat,
                                    result.park_lon,
                                    None,
                                    None,
                                    None
                )

                parks.append(fetched_park)

                parks_sorted = sorted(parks, key=lambda x: x.park_name)
            return parks_sorted

    def get_parks_json(self):
        return jsonpickle.encode(self.get_parks(), unpicklable=False)

    def get_park(self, park_id):
        print("Get specific park")

        selection_string = textwrap.dedent(""" 
            Select * From Parks Where ID = ?""")
        
        try:
            return self.get_park_helper(selection_string, park_id)
        except Exception as e:
            print('Encountered database error while retrieving a list of reports.\nRetrying.\n{}'.format(str(e)))
            cnxn = pyodbc.connect(driver)

            self.cnxn = cnxn
            self.cursor = cnxn.cursor()

            return self.get_park_helper(selection_string, park_id)
        return None
    
    def get_park_helper(self, query, park_id):
        self.cursor.execute(query, park_id)
        results = self.cursor.fetchall()
        if results:
            for result in results:
                # TODO: test image retrieval
                cover_binary = None
                logo_binary = None

                # Retrieve images on server
                try:
                    print('Accessing park cover image')

                    # Image file name of given park
                    filename = 'parkcovers/coverimage' + str(result.park_id) + '.jpeg'

                    cover = open(filename, 'rb') # Open binary file
                    cover_binary = cover.read()
                    cover.close()
                    print('Park cover retrieved')
                except:
                    print('No park cover image')

                try:
                    print('Accessing park logo image')
                    filename = 'parklogos/logoimage' + str(result.park_id) + '.jpeg'
                    logo = open(filename, 'rb')
                    logo_binary = logo.read()
                    logo.close()
                    print('Park logo retrieved')
                except:
                    print('No park logo image')

                fetched_park = Park(result.Name,
                                    result.ID,
                                    result.park_lat,
                                    result.park_lon,
                                    None,
                                    cover_binary,
                                    logo_binary
                )
                return fetched_park
        return None

    def get_park_json(self, park_id):
        return jsonpickle.encode(self.get_park(park_id), unpicklable=False)

    def create_park(self, park_name, park_lat, park_lon, park_org, park_cover_image, park_logo):
        print("Creating a new park.")

        new_park = Park(park_name, -1, park_lat, park_lon, park_org, park_cover_image, park_logo)

        insert_sql_string = "Insert Into Parks(Name, park_lat, park_lon) Values (?,?,?)" # TODO(Ian) Update this with image params
        
        
        try:
            return self.create_helper(insert_sql_string, new_park)
        except Exception as e:
            print('Encountered database error while creating a park.\nRetrying.\n{}'.format(str(e)))
            cnxn = pyodbc.connect(driver)

            self.cnxn = cnxn
            self.cursor = cnxn.cursor()
            return self.create_helper(insert_sql_string, new_park)

        return None

    def create_helper(self, query, new_park):
        self.cursor.execute(query, 
                                new_park.park_name, 
                                str(new_park.park_lat), 
                                str(new_park.park_lon)) # Insert it into database
        self.cursor.execute("Select @@IDENTITY")
        new_id = int(self.cursor.fetchone()[0])
        new_park.park_id = new_id
        self.cnxn.commit()
        
        # TODO: test image storage
        # # Save images on server
        # if new_park.park_cover_image:
        #     print('Storing park cover image')
        #     # Generate image file name
        #     filename = 'parkcovers/coverimage' + str(new_park.park_id) + '.jpeg'

        #     cover = open(filename, 'wb') # Create binary file
        #     cover.write(new_park.park_cover_image) # Write image to file
        #     cover.close()

        #     print('Park cover saved')

        # if new_park.park_logo:
        #     print('Storing park logo image')
        #     filename = 'parklogos/logoimage' + str(new_park.park_id) + '.jpeg'
        #     logo = open(filename, 'wb')
        #     logo.write(new_park.park_logo)
        #     logo.close()
        #     print('Park logo saved')

        return jsonpickle.encode(new_park, unpicklable=False)

    def delete_park(self, park_id):
        print("Delete a park.")

        delete_string = "Delete from Parks where ID = ?"

        try:
            return self.delete_helper(delete_string, park_id)
        except Exception:
            return False

    def delete_helper(self, query, park_id):
        self.cursor.execute(query, park_id)
        self.cursor.commit()
        return True

    def update_park(self, park_name, park_id, park_lat, park_lon, park_org, park_cover_image, park_logo):
        print("Update a park.")
        
        new_park = Park(park_name, park_id, park_lat, park_lon, park_org, park_cover_image, park_logo)

        # TODO(Ian) Update this to match DB
        update_string = textwrap.dedent("""
            update Parks 
            set Name = ?, 
                park_lat = ?, 
                park_lon = ?
            where ID = ?
        """)
        
        try:
            return self.update_helper(update_string, park_id, new_park)
        except Exception as e:
            print('Encountered database error while updating a report.\nRetrying.\n{}'.format(str(e)))
            cnxn = pyodbc.connect(driver)

            self.cnxn = cnxn
            self.cursor = cnxn.cursor()

            return self.update_helper(update_string, park_id, new_park)
        return None


    def update_helper(self, query, park_id, new_park):
        self.cursor.execute(query, 
                                new_park.park_name, 
                                str(new_park.park_lat), 
                                str(new_park.park_lon),
                                park_id)
        self.cursor.commit()

        # TODO: test image updating
        # # Update images
        # if new_park.park_cover_image:
        #     print('Updating park cover image')
        #     # Generate image file name
        #     filename = 'parkcovers/coverimage' + str(new_park.park_id) + '.jpeg'

        #     cover = open(filename, 'wb') # Create binary file
        #     cover.write(new_park.park_cover_image) # Write image to file
        #     cover.close()

        #     print('Park cover updated')

        # if new_park.park_logo:
        #     print('Updating park logo image')
        #     filename = 'parklogos/logoimage' + str(new_park.park_id) + '.jpeg'
        #     logo = open(filename, 'wb')
        #     logo.write(new_park.park_logo)
        #     logo.close()
        #     print('Park logo updated')

        print('report {} updated'.format(id), flush=True)
        return jsonpickle.encode(new_park, unpicklable=False)
