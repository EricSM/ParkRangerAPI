import pyodbc
import datetime as dt
import jsonpickle
import textwrap
import requests

app_id = "" # Our unique open weather id
open_weather_request_url = "https://api.openweathermap.org/data/2.5/weather?lat={}&long={}&units={}&appid={}" # The request URL for open weather API

with open("controllers/app_id.txt", 'r') as f:
    app_id = f.readline().strip()


# Python style guide: http://google.github.io/styleguide/pyguide.html

class WeatherHandler:
    """
    Handles updating rules

    Attributes:
        rules: A list of rules associated with this area
    """

    def __init__(self, units="imperial"):
        """
        Initalizes a new area

        Args:
            name: The name of the area
            weather_station_id: The ID of the closest or most central weather station in the area
            units: metric or imperial (default imperial)
        """
        self.units = units
        self.rules = []

        global driver
        # driver = 'Driver={ODBC Driver 17 for SQL Server};Server=tcp:parkwatch-db-server.database.windows.net,1433;Database=parkwatch-database;Uid=ranger;Pwd={ParkWatch123!};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
        driver = 'Driver={ODBC Driver 17 for SQL Server};Server=tcp:parkwatch-db-server.database.windows.net,1433;Database=parkwatch-database;Uid=ranger;Pwd=ParkWatch123!;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=0;'
        pyodbc.pooling = False
        cnxn = pyodbc.connect(driver)

        self.cnxn = cnxn
        self.cursor = cnxn.cursor()

    def add_rule(self, condition_type, condition_interval_value, condition_interval_symbol, description, name, park_id, path):
        """
        Creates a new rule and adds it to the rules list

        Args:
            condition_type: The type of condition associated with the rule, used as the dictionary key for the JSON returned by the weather api.
                Ex: temp, humidity
            condition_interval_value: The value associated with the if(rule is broken) statement
            condition_interval_symbol: Represents the type of inequality
                Ex: leq = less than or equal to
            description: The description returned when this rule is broken
        """
        new_rule = Rule(condition_type, condition_interval_value, condition_interval_symbol, description, name, park_id, path)
        insert_sql_string = textwrap.dedent("""
            Insert Into WeatherRules(park_id, area_name, condition, 
                area_lat, area_long, 
                interval_value, interval_symbol, 
                map_path, rule_desc, activated) 
            Values (?,?,?,?,?,?,?,?,?,?)
        """)
        try:
            return self.get_helper(insert_sql_string, new_rule)
        except Exception as e:
            print('Encountered database error while adding a new rule.\nRetrying.\n{}'.format(str(e)))
            cnxn = pyodbc.connect(driver)

            self.cnxn = cnxn
            self.cursor = cnxn.cursor()
            return self.get_helper(insert_sql_string, new_rule)

    def get_helper(self, query, rule):
        self.cursor.execute(query, 
                            rule.park_id, 
                            rule.name, 
                            rule.condition_type, 
                            str(rule.center_lat), 
                            str(rule.center_long), 
                            rule.condition_interval_value, 
                            rule.condition_interval_symbol,
                            jsonpickle.encode(rule.path),
                            rule.description,
                            rule.active) # Insert it into database

        self.cnxn.commit()
        self.cursor.execute("Select @@IDENTITY")
        new_id = int(self.cursor.fetchone()[0])
        rule.rule_id = new_id

        return jsonpickle.encode(rule)

    def delete_rule(self, park_id, rule_id):
        return

    def get_weather(self, rule):
        """
        Gets the current weather using the OpenWeather API and the weather station associated with the area

        Returns:
            The JSON returned by OpenWeather
        """
        request_url = open_weather_request_url.format(rule.center_lat, rule.center_long, self.units, app_id)
        request = requests.get(request_url)
        return request.json()

    def check_rules(self, park_id):
        """
        Checks all rules against the weather data JSON

        Args:
            weather_json: The JSON object returned by the OpenWeather API
        Returns:
            A list of rules that are triggered by the weather events
        """
        triggered_rules = []
        for rule in self.rules:
            if rule.park_id == park_id: #TODO(Ian) This just runs locally
                weather_json = self.get_weather(rule)
                if rule.check_rule(weather_json):
                    rule.triggered = True
                    triggered_rules.append(rule)
                else:
                    rule.triggered = False

        return triggered_rules

    def get_rules(self, park_id):
        selection_string = textwrap.dedent("""
        Select
            rule_id,
            park_id,
            area_name,
            condition,
            area_lat,
            area_long,
            interval_value,
            interval_symbol,
            map_path,
            rule_desc,
            activated
        From
            WeatherRules
        Where
            park_id = ?
        """)

        self.cursor.execute(selection_string, park_id)
        results = self.cursor.fetchall()
        rules = []

        if results:
            for result in results:
                fetched_rule = Rule(result.condition,
                                    result.interval_value,
                                    result.interval_symbol,
                                    result.rule_desc,
                                    result.area_name,
                                    result.park_id,
                                    result.map_path
                                    )
                fetched_rule.rule_id = result.rule_id   
                rules.append(fetched_rule)
            return rules
        return None

    def get_active_rules(self, park_id, active):
        selection_string = textwrap.dedent("""
        Select
            rule_id,
            park_id,
            area_name,
            condition,
            area_lat,
            area_long,
            interval_value,
            interval_symbol,
            map_path,
            rule_desc,
            activated
        From
            WeatherRules
        Where
            park_id = ?
            AND
            activated = ?
        """)

        self.cursor.execute(selection_string, park_id, active)
        results = self.cursor.fetchall()
        rules = []

        if results:
            for result in results:
                fetched_rule = Rule(result.condition,
                                    result.interval_value,
                                    result.interval_symbol,
                                    result.rule_desc,
                                    result.area_name,
                                    result.park_id,
                                    result.map_path
                                    )
                fetched_rule.rule_id = result.rule_id   
                rules.append(fetched_rule)
            return rules
        return None

    def get_rules_json(self, park_id):
        return jsonpickle.encode(self.get_rules(park_id))

    def get_active_rules_json(self, park_id, active):
        return jsonpickle.encode(self.get_active_rules(park_id, active))

    def get_rule(self, park_id, rule_id):
        selection_string = textwrap.dedent("""
        Select
            rule_id,
            park_id,
            area_name,
            condition,
            area_lat,
            area_long,
            interval_value,
            interval_symbol,
            map_path,
            rule_desc,
            activated
        From
            WeatherRules
        Where
            park_id = ?
            AND
            rule_id = ?
        """)

        self.cursor.execute(selection_string, park_id, rule_id)
        result = self.cursor.fetchone()

        if result:
            fetched_rule = Rule(result.condition,
                                    result.interval_value,
                                    result.interval_symbol,
                                    result.rule_desc,
                                    result.area_name,
                                    result.park_id,
                                    result.map_path
                                    )
            fetched_rule.rule_id = result.rule_id   
            return fetched_rule
        return None

    def get_rule_json(self, park_id, ruke_id):
        return jsonpickle.encode(self.get_rule(park_id, ruke_id))

class Rule:
    """
    Represents a rule assigned to an area

    Attributes:
        condition_type: The type of data being compared against (temp, humidity, etc). Used as a key in the weather JSON
        condition_interval_value: The value to which the condition is being compared
        condition_interval_symbol: The type of inequality (leq = less than or equal to, eq = ==, etc..)
        description: A short discription of what the rule describes
    """
    def __init__(self, condition_type, condition_interval_value, condition_interval_symbol, description, name, park_id, path):
        """
        Initalizes a new Rule object

        Parameters:
            condition_type: The type of data being compared against (temp, humidity, etc). Used as a key in the weather JSON
            condition_interval_value: The value to which the condition is being compared
            condition_interval_symbol: The type of inequality (leq = less than or equal to, eq = ==, etc..)
            description: A short discription of what the rule describes
        """
        self.condition_type = condition_type #str
        self.condition_interval_value = int(condition_interval_value) #int
        self.condition_interval_symbol = condition_interval_symbol #str
        self.description = description #str
        self.name = name #str
        self.park_id = int(park_id)
        self.path = jsonpickle.decode(path)
        self.center_lat, self.center_long = self.get_center_cords(self.path)
        self.active = 0
        self.rule_id = None

    def get_center_cords(self, path):
        # [{lat: 36.86149, lng: 30.63743},{lat: 36.86341, lng: 30.72463}]
        avg_lat = 0.0
        avg_long = 0.0
        for p in path:
            avg_lat += float(p['lat'])
            avg_long += float(p['lng'])
        
        avg_lat /= len(path)
        avg_long /= len(path)

        return avg_lat, avg_long

    def check_rule(self, weather_json):
        """
        Checks the rule against weather data and returns true if the rule has been broken

        Args:
            weather_json: The most recent weather data
        
        Returns:
            True: if the rule is broken
            False: otherwise
        """
        if (self.condition_interval_symbol == 'leq'): # Less than or equal to
            self.active = True
            return weather_json['main'][self.condition_type] <= self.condition_interval_value
        elif (self.condition_interval_symbol == 'le'): # Less than
            self.active = True
            return weather_json['main'][self.condition_type] < self.condition_interval_value
        elif (self.condition_interval_symbol == 'geq'): # Greater than or equal to
            self.active = True
            return weather_json['main'][self.condition_type] >= self.condition_interval_value
        elif (self.condition_interval_symbol == 'ge'): # Greater than
            self.active = True
            return weather_json['main'][self.condition_type] > self.condition_interval_value
        elif (self.condition_interval_symbol == 'eq'): # Equal to
            self.active = True
            return weather_json['main'][self.condition_type] == self.condition_interval_value
        
        return False # Base case, no rules were broken
