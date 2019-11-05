import requests

app_id = "" # Our unique open weather id
open_weather_request_url = "https://api.openweathermap.org/data/2.5/weather?id={}&units={}&appid={}" # The request URL for open weather API

with open("app_id.txt", 'r') as f:
    app_id = f.readline().strip()


# Python style guide: http://google.github.io/styleguide/pyguide.html

class Area:
    """
    Represents an area such as a national park

    Attributes:
        rules: A list of rules associated with this area
        name: The name of the area
        weather_station_id: The id of the nearest weather station
        units: metric or imperial
    """
    rules = []
    name = ""
    weather_station_id = ""
    units = ""

    def __init__(self, name, weather_station_id, units="imperial"):
        """
        Initalizes a new area

        Args:
            name: The name of the area
            weather_station_id: The ID of the closest or most central weather station in the area
            units: metric or imperial (default imperial)
        """
        self.name = name
        self.weather_station_id = weather_station_id
        self.units = units

    def add_rule(self, condition_type, condition_interval_value, condition_interval_symbol, description):
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
        new_rule = Rule(condition_type, condition_interval_value, condition_interval_symbol, description)
        self.rules.append(new_rule)

    def get_weather(self):
        """
        Gets the current weather using the OpenWeather API and the weather station associated with the area

        Returns:
            The JSON returned by OpenWeather
        """
        request_url = open_weather_request_url.format(self.weather_station_id, self.units, app_id)
        request = requests.get(request_url)
        return request.json()

    def check_rules(self, weather_json):
        """
        Checks all rules against the weather data JSON

        Args:
            weather_json: The JSON object returned by the OpenWeather API
        Returns:
            A list of rules that are triggered by the weather events
        """
        triggered_rules = []
        for rule in self.rules:
            if rule.check_rule(weather_json):
                triggered_rules.append(rule)

        return triggered_rules

class Rule:
    """
    Represents a rule assigned to an area

    Attributes:
        condition_type: The type of data being compared against (temp, humidity, etc). Used as a key in the weather JSON
        condition_interval_value: The value to which the condition is being compared
        condition_interval_symbol: The type of inequality (leq = less than or equal to, eq = ==, etc..)
        description: A short discription of what the rule describes
    """
    condition_type = ""
    condition_interval_value = 0
    condition_interval_symbol = ""
    description = ""

    def __init__(self, condition_type, condition_interval_value, condition_interval_symbol, description):
        """
        Initalizes a new Rule object

        Parameters:
            condition_type: The type of data being compared against (temp, humidity, etc). Used as a key in the weather JSON
            condition_interval_value: The value to which the condition is being compared
            condition_interval_symbol: The type of inequality (leq = less than or equal to, eq = ==, etc..)
            description: A short discription of what the rule describes
        """
        self.condition_type = condition_type
        self.condition_interval_value = condition_interval_value
        self.condition_interval_symbol = condition_interval_symbol
        self.description = description

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
            return weather_json['main'][self.condition_type] <= self.condition_interval_value
        elif (self.condition_interval_symbol == 'le'): # Less than
            return weather_json['main'][self.condition_type] < self.condition_interval_value
        elif (self.condition_interval_symbol == 'geq'): # Greater than or equal to
            return weather_json['main'][self.condition_type] >= self.condition_interval_value
        elif (self.condition_interval_symbol == 'ge'): # Greater than
            return weather_json['main'][self.condition_type] > self.condition_interval_value
        elif (self.condition_interval_symbol == 'eq'): # Equal to
            return weather_json['main'][self.condition_type] == self.condition_interval_value
        
        return False # Base case, no rules were broken
