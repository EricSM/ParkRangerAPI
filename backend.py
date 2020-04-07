#!flask/bin/python

# Steps to deploy: 
# az login
# az webapp deployment source config-local-git --name parkwatch-backend --resource-group ParkWatch
# OR
# az webapp create -g ParkWatch -p ASP-ParkWatch-9dbf -n parkwatch-backend --runtime "python|3.6" --deployment-local-git

# parkwatch_ranger, (same password as elsewhere)

# Copy url under deployment center > credentials
# git remote add azure <url>
# git push azure <current branch>:master 

# https://docs.microsoft.com/en-us/azure/app-service/containers/how-to-configure-python

import jsonpickle
import logging
import re
import time
import atexit


from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, render_template, make_response, request, render_template, abort, json
from flask_cors import CORS
from controllers.report import Report, ReportHandler
from controllers.weather import Rule, WeatherHandler
from controllers.parking import ParkingLot, ParkingHandler
from controllers.user import UserHandler
from controllers.fire import Fire, WildFireHandler
from controllers.park import Park, ParkHandler
from controllers.email import EmailHandler

documentation_filepath = "parkranger_docs_4-7.html"

app = Flask(__name__, template_folder="templates", static_url_path='/static')
logging.basicConfig(level=logging.DEBUG)
cors = CORS(app)

report_handler = ReportHandler()
weather_handler = WeatherHandler()
parking_handler = ParkingHandler()
user_handler = UserHandler()
fire_handler = WildFireHandler()
park_handler = ParkHandler()
email_handler = EmailHandler()

# Email scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=email_handler.send_all_emails, trigger="interval", hours=12)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

@app.route('/pw/api/docs')
def docs():
    return app.send_static_file(documentation_filepath)

################################################################
#                            Parks                             #
################################################################

#region Parks

@app.route('/pw/api/parks', methods=['GET', 'POST', 'DELETE'])
def get_parks_base():
    log_str = "{}\n{}\n{}".format(str(request.method), str(request.args), str(request.json))
    print(log_str)

    park_id = request.args.get('park')
    token = request.args.get('token')

    if request.method == 'GET':
        if park_id:
            return get_park(int(park_id))
        return get_parks()

    elif request.method == 'POST':
        if token:
            if user_handler.check_user(token, 99): # TODO(IAN) Using park 99 as super user.
                if park_id:
                    return update_park(park_id, request)  
                else:
                    return create_park(request)          
            else:
                abort(401, "Invalid token. Parks can only be created by users from park 99.")
        else:
            abort(400, "Missing url parameters.")

    elif request.method == 'DELETE':
        if token:
            if user_handler.check_user(token, 99):
                if park_id:
                    return delete_park(park_id)
                else:
                    abort(400, "Missing park_id and report_id.")
            else:
                abort(401, "Invalid token.")
        else:
            abort(400, "Missing user token.")
    else:
        abort(400, "We only accept GET/POST/DELETE")

def get_parks():
    parks_list_json = park_handler.get_parks_json()
    return parks_list_json

def get_park(park_id):
    park_json = park_handler.get_park_json(park_id)
    return park_json

def create_park(request):
    """

    """
    check_json_park(request)

    park_json = park_handler.create_park(request.json['park_name'],
                     request.json['park_lat'],
                     request.json['park_lon'],
                     request.json['park_org'],
                     request.json['park_cover_image'],
                     request.json['park_logo'])

    return park_json

def check_json_park(request):
    if not request.json:
        abort(400, "Error in create report request, missing request body")

    if 'park_name' not in request.json:
        abort(400, "Missing park name in request body")

    elif len(request.json['park_name']) <= 0:
        abort(400, "Park name must not be an empty string")

    if 'park_lat' not in request.json:
        abort(400, "Missing park lat in request body")
    
    if 'park_lon' not in request.json:
        abort(400, "Missing park lon in request body")

    if 'park_org' not in request.json:
        abort(400, "Missing park org in request body")
    
    elif len(request.json['park_org']) <= 0:
        abort(400, "Park org must not be an empty string")

    if 'park_cover_image' not in request.json:
        abort(400, "Missing park cover image in request body")
    
    elif len(request.json['park_cover_image']) <= 0:
        abort(400, "Park cover image must not be an empty string")

    if 'park_logo' not in request.json:
        abort(400, "Missing park logo in request body")
    
    elif len(request.json['park_logo']) <= 0:
        abort(400, "Park logo must not be an empty string")

def delete_park(park_id):
    result = park_handler.delete_park(park_id)
    return app.response_class(json.dumps(result), content_type='application/json')

def update_park(park_id, request):
    check_json_park(request)

    park_json = park_handler.update_park(
                        request.json['park_name'],
                        park_id,
                        request.json['park_lat'],
                        request.json['park_lon'],
                        request.json['park_org'],
                        request.json['park_cover_image'],
                        request.json['park_logo'])
                        
    print(park_json, flush=True)
    return park_json

#endregion

################################################################
#                            LOGIN                             #
################################################################

#region Login
@app.route('/pw/api/login', methods=['POST'])
def login_base():
    """
    """
    log_str = "{}\n{}\n{}".format(str(request.method), str(request.args), str(request.json))
    print(log_str)
    if request.method == 'POST':
        login_code = login(request)
        if login_code == -1:
            abort(401, "Invalid username or password")
        else:
            return login_code
    else:
        abort(400, "Login URI only accepts POST requests.")


def login(request):
    if 'email' not in request.json:
        abort(400, "Missing email in request body")
    if 'password' not in request.json:
        abort(400, "Missing password in request body")
    if 'park_id' not in request.json:
        abort(400, "Missing park_id in request body")
    
    login_json = user_handler.login(request.json['email'],
                                    request.json['password'],
                                    request.json['park_id'])

    return login_json

@app.route('/pw/api/login/new', methods=['POST'])
def new_login_base():
    """
    """
    log_str = "{}\n{}\n{}".format(str(request.method), str(request.args), str(request.json))
    print(log_str)

    if request.method == 'POST':
        return create_user(request)
    else:
        abort(400, "Login URI only accepts POST requests.")

def check_user_body(request):
    regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'

    if not re.search(regex, request.json['email']):
        abort(400, "Invalid email")
    if len(request.json['password']) < 8:
        abort(400, "Password must be at least 8 characters")
    if len(request.json['f_name']) == 0:
        abort(400, "First name cannot be empty")
    if len(request.json['l_name']) == 0:
        abort(400, "Last name cannot be empty")
    

def create_user(request):
    if 'email' not in request.json:
        abort(400, "Missing email in request body")
    if 'password' not in request.json:
        abort(400, "Missing password in request body")
    if 'park_id' not in request.json:
        abort(400, "Missing park_id in request body")
    if 'f_name' not in request.json:
        abort(400, "Missing f_name in request body")
    if 'l_name' not in request.json:
        abort(400, "Missing l_name in request body")

    check_user_body(request)
    
    new_user_json = user_handler.create_user(request.json['email'],
                                             request.json['password'],
                                             request.json['f_name'],
                                             request.json['l_name'],
                                             request.json['park_id'])
    # Just making sure that we return the correct error codes.
    if new_user_json == -1:
        abort(401, "A user with this email already exists")
    else:
        return new_user_json
#endregion

#region Update Account
@app.route('/pw/api/password', methods=['POST'])
def change_password_base():
    """
    """
    uID = request.args.get('uID')
    token = request.args.get('token')
    print(request.__dict__)

    if request.method == 'POST':
        if uID and token:
            if user_handler.check_uID(uID, token):
                return change_password(request)
            else:
                abort(401, "Invalid token.")
        else:
            abort(401, "Missing uID or token")
    else:
        abort(400, "Password change URI only accepts POST requests.")

def change_password(request):
    if not request.json or not 'password' in request.json or not 'new_password' in request.json:
        abort(400, "Error in change password request, missing request body")
    
    new_password_json = user_handler.change_password(request.json['uID'],
        request.json['password'],
        request.json['new_password'])
    # Just making sure that we return the correct error codes.
    if new_password_json == -1:
        abort(401, "Invalid uID")
    else:
        print(new_password_json, flush=True)
        return new_password_json

@app.route('/pw/api/profile', methods=['POST'])
def update_user_base():
    """
    """
    uID = request.args.get('uID')
    token = request.args.get('token')
    print(request.__dict__)

    if request.method == 'POST':
        if uID and token:
            if user_handler.check_uID(uID, token):
                return update_user(request)
            else:
                abort(401, "Invalid token")
        else:
            abort(401, "Missing uID or token")
    else:
        abort(400, "Account update URI only accepts POST requests.")

def update_user(request):
    if 'uID' not in request.json:
        abort(400, "Missing uID in request body")
    if 'email' not in request.json:
        abort(400, "Missing email in request body")
    if 'token' not in request.json:
        abort(400, "Missing token in request body")
    if 'park_id' not in request.json:
        abort(400, "Missing park_id in request body")
    if 'f_name' not in request.json:
        abort(400, "Missing f_name in request body")
    if 'l_name' not in request.json:
        abort(400, "Missing l_name in request body")
    
    updated_user_json = user_handler.update_user(request.json['uID'],
                                             request.json['email'],
                                             request.json['f_name'],
                                             request.json['l_name'],
                                             request.json['park_id'],
                                             request.json['token'])
    # Just making sure that we return the correct error codes.
    if updated_user_json == -1:
        abort(401, "Invalid uID")
    else:
        print(updated_user_json, flush=True)
        return updated_user_json
#endregion

#region Reports
@app.route('/pw/api/reports', methods=['GET', 'POST', 'DELETE'])
def get_report_base():
    """
    Base method that handles all requests ending in /reports. 
    If the method is GET and only park id is provided then returns a list of all reports for that park. 
    Otherwise, if park id and report id are provided, returns that specific report.

    If the method is POST then creates a new report object for that park.

    Args:
        None
    Returns:
        GET - A single json report
        GET - A list of json reports
        POST - The new report
    """
    park_id = request.args.get('park')
    report_id = request.args.get('id')
    min_severity = request.args.get('minSeverity')
    max_severity = request.args.get('maxSeverity')
    severity = request.args.get('severity')
    approved_status = request.args.get('approvedStatus')
    closure = request.args.get('closure')
    loc_lon = request.args.get('locLon')
    loc_lat = request.args.get('locLat')
    loc_range = request.args.get('locRange')
    min_date = request.args.get('minDate')
    max_date = request.args.get('maxDate')

    token = request.args.get('token')
    log_str = "{}\n{}\n{}\n".format(str(request.method), str(request.args), '%.500s' % str(request.json))
    print(log_str)


    if request.method == 'GET':
        if park_id and not report_id: # If only the park was provided then get list of all reports
            # return get_reports(int(park_id))
            return get_reports_filter_json(int(park_id), 
                                      min_severity, 
                                      max_severity, 
                                      severity, 
                                      approved_status,
                                      closure,
                                      loc_lon,
                                      loc_lat,
                                      loc_range,
                                      min_date,
                                      max_date
                                    )
        
        elif park_id and report_id: # If park and report id were provided then return specified report
            return get_report(int(park_id), int(report_id))

    elif request.method == 'POST':
        if park_id and not report_id and not token:
            return create_report(request)
        elif token:
            if user_handler.check_user(token, park_id):
                if park_id and report_id:
                    return update_report(park_id, report_id, request)          
            else:
                abort(401, "Invalid token.")
        else:
            abort(400, "Missing url parameters.")

    elif request.method == 'DELETE':
        if token:
            if user_handler.check_user(token, park_id):
                if park_id and report_id:
                    return delete_report(park_id, report_id)
                else:
                    abort(400, "Missing park_id and report_id.")
            else:
                abort(401, "Invalid token.")
        else:
            abort(400, "Missing user token.")
    else:
        abort(400, "We only accept GET/POST/DELETE")

    
def get_reports(park_id):
    """
    Helper function that gets all reports associated with the park

    Args:
        park_id: The id of the park
    Returns:
        A list of json report objects
    """
    reports_list_json = report_handler.get_reports_list_json(park_id)
    return reports_list_json

def get_reports_filter_json(park_id, minSeverity = None, maxSeverity = None, specificSeverity = None, approvedStatus = None, closure = None, locLon = None, locLat = None, locRange = None, minDate = None, maxDate = None):
    reports_list_json = report_handler.get_reports_filter_json(park_id, minSeverity, maxSeverity, specificSeverity, approvedStatus, closure, locLon, locLat, locRange, minDate, maxDate)
    return reports_list_json

def get_report(park_id, report_id):
    """
    Helper function that gets a specfic report

    Args:
        park_id: The id of the park
        reprot_id: The id of the report
    Returns:
        A single json report object
    """
    report_json = report_handler.get_report_json(park_id, report_id)
    return report_json

def check_report_request(request):
    if not request.json:
        abort(400, "Missing request body")
    if 'loc_name' not in request.json:
        abort(400, "Missing loc name in request body")
    if 'loc_lat' not in request.json:
        abort(400, "Missing loc lat in request body")
    if 'loc_long' not in request.json:
        abort(400, "Missing loc long in request body")
    if 'description' not in request.json:
        abort(400, "Missing description in request body")
    if 'severity' not in request.json:
        abort(400, "Missing severity in request body")
    if 'closure' not in request.json:
        abort(400, "Missing closure in request body")
    if 'photo' not in request.json:
        abort(400, "Missing photo in request body")

def create_report(request):
    """
    Calls report handler to create a new report object, puts it into the db, and returns it

    Args:
        request: The request object
    Returns:
        The newly created json report object
    """
    check_report_request(request)

    park_id = int(request.args.get('park'))

    report_json = report_handler.create_report(request.json['loc_name'],
                     park_id,
                     request.json['loc_lat'],
                     request.json['loc_long'],
                     request.json['description'],
                     request.json['severity'],
                     request.json['closure'],
                     0,
                     request.json['photo'])

    return report_json

def update_report(park_id, report_id, request):
    """
    Calls report handler to create a new report object, puts it into the db, and returns it

    Args:
        request: The request object
    Returns:
        The newly created json report object
    """
    check_report_request(request)

    if 'approved_status' not in request.json:
        abort(400, "Missing approved status in request body")

    report_json = report_handler.update_report(
                        park_id,
                        report_id,
                        request.json['loc_name'],
                        request.json['loc_lat'],
                        request.json['loc_long'],
                        request.json['description'],
                        request.json['severity'],
                        request.json['closure'],
                        request.json['approved_status'],
                        request.json['photo'])

    # print(report_json, flush=True)
    return report_json
#endregion

################################################################
#                           WEATHER                            #
################################################################

#region Weather
@app.route('/pw/api/weather', methods=['GET', 'POST', 'DELETE'])
def get_rules_base():
    """
    If the method is POST then creates a new report object for that park.

    Args:
        None
    Returns:
        GET - A single json report
        GET - A list of json reports
        POST - The new report
    """
    park_id = request.args.get('park')
    rule_id = request.args.get('id')
    refresh = request.args.get('refresh')
    token = request.args.get('token')

    condition = request.args.get('condition')
    interval_value = request.args.get('interval_value')
    interval_symbol = request.args.get('interval_symbol')
    activated = request.args.get('active')
    area_lat = request.args.get('center_lat')
    area_lon = request.args.get('center_long')
    area_range = request.args.get('area_range')
    
    log_str = "{}\n{}\n{}".format(str(request.method), str(request.args), str(request.json))
    print(log_str)


    if request.method == 'GET':
        if park_id and not rule_id:
            return get_rules_filter(park_id,
                                    condition,
                                    interval_value,
                                    interval_symbol,
                                    activated,
                                    area_lat,
                                    area_lon,
                                    area_range,
                                    refresh)
        elif park_id and rule_id:
            if refresh:
                refreshed = refresh_rules(park_id, None)
            return get_rule(park_id, rule_id)

    elif request.method == 'POST':
        if token:
            if user_handler.check_user(token, park_id):
                if park_id and rule_id:
                    return update_rule(park_id, rule_id, request)
                elif park_id:
                    return create_rule(request)
            else:
                abort(400, "Invalid token.")
        else:
            abort(400, "Missing user token.")

    elif request.method == 'DELETE':
        if token:
            if user_handler.check_user(token, park_id):
                if park_id and rule_id:
                    return delete_rule(park_id, rule_id)
                else:
                    abort(400, "Missing park_id and rule_id")
            else:
                abort(401, "Invalid token.")
        else:
            abort(400, "Missing user token.")
    else:
        abort(400, "We only accept GET/POST/DELETE")


def refresh_rules(park_id, active):
    weather_handler.refresh_rules(park_id)

    if active:
        return get_active_rules(park_id, active)
    else:
        return get_rules(park_id)

def get_rule(park_id, rule_id):
    fetched_rule = weather_handler.get_rule_json(park_id, rule_id)

    if not fetched_rule:
        abort(400, f"No rule with park_id={park_id} and rule_id={rule_id} was found.")

    return fetched_rule

def get_rules(park_id):
    """
    Helper function that gets all rules associated with the park

    Args:
        park_id: The id of the park
    Returns:
        A list of json rule objects
    """
    rules_list_json = weather_handler.get_rules_json(park_id)
    return rules_list_json

def get_rules_filter(park_id, condition, interval_value, interval_symbol, activated, areaLat, areaLon, areaRange, refresh):
    rules_list_json = weather_handler.get_rules_filter_json(park_id,
                                                       condition,
                                                       interval_value,
                                                       interval_symbol,
                                                       activated,
                                                       areaLat,
                                                       areaLon,
                                                       areaRange,
                                                       refresh)
    return rules_list_json


def check_weather_request(request):
    if not request.json:
        abort(400, "Missing request body")
    if 'condition_type' not in request.json:
        abort(400, "Missing condition_type in request body")
    if 'condition_interval_value' not in request.json:
        abort(400, "Missing condition_interval_value in request body")
    if 'name' not in request.json:
        abort(400, "Missing name in request body")
    if 'description' not in request.json:
        abort(400, "Missing description in request body")
    if 'path' not in request.json:
        abort(400, "Missing path in request body")

def create_rule(request):
    check_weather_request(request)

    park_id = int(request.args.get('park'))

    print(request)

    # Example post json

    #"{"condition_interval_symbol\":\">\",\"condition_interval_value\":0,
    # \"condition_type\":\"rain\",\"description\":\"Test description\",
    # \"name\":\"Test Name\", \"path\":[{\"lat\":36.86149,\"lng\":30.63743},{\"lat\":36.86341,\"lng\":30.72463}]}"

    report_json = weather_handler.add_rule(request.json['condition_type'],
                     request.json['condition_interval_value'],
                     request.json['condition_interval_symbol'],
                     request.json['description'],
                     request.json['name'],
                     park_id,
                     json.dumps(request.json['path']),
                     request.json['forecast']
                     )

    return report_json

def update_rule(park_id, rule_id, request):
    check_weather_request(request)
   
    # Example post json

    #"{"condition_interval_symbol\":\">\",\"condition_interval_value\":0,
    # \"condition_type\":\"rain\",\"description\":\"Test description\",
    # \"name\":\"Test Name\", \"path\":[{\"lat\":36.86149,\"lng\":30.63743},{\"lat\":36.86341,\"lng\":30.72463}]}"

    report_json = weather_handler.update_rule(
                     rule_id,
                     request.json['condition_type'],
                     request.json['condition_interval_value'],
                     request.json['condition_interval_symbol'],
                     request.json['description'],
                     request.json['name'],
                     park_id,
                     json.dumps(request.json['path']),
                     request.json['forecast']
                     )

    return report_json

def get_active_rules(park_id, active):
    """
    Helper function that gets all active rules associated with the park

    Args:
        park_id: The id of the park
    Returns:
        A list of json rule objects
    """
    report_json = weather_handler.get_active_rules_json(park_id, active)
    return report_json

def delete_rule(park_id, rule_id):
    result = weather_handler.delete_rule(park_id, rule_id)
    return app.response_class(json.dumps(result), content_type='application/json')

def delete_report(park_id, report_id):
    result = report_handler.delete_report(park_id, report_id)
    return app.response_class(json.dumps(result), content_type='application/json')
#endregion

################################################################
#                           PARKING                            #
################################################################

#region Parking
@app.route('/pw/api/parking', methods=['GET', 'POST', 'DELETE'])
def get_parking_base():
    """
    Base method that handles all requests ending in /parking. 

    Args:
        None
    Returns:
        GET - A single json report
        GET - A list of json reports
        POST - The new report
    """
    park_id = request.args.get('park')
    lot_id = request.args.get('id')
    token = request.args.get('token')
    status = request.args.get('severity')
    log_str = "{}\n{}\n{}".format(str(request.method), str(request.args), str(request.json))
    print(log_str)


    if request.method == 'GET':
        if park_id and not lot_id: # If only the park was provided then get list of all reports
            return get_parking_lots(int(park_id), status)
        
        elif park_id and lot_id: # If park and report id were provided then return specified report
            return get_parking_lot(int(park_id), int(lot_id))

    elif request.method == 'POST':
        if token:
            if user_handler.check_user(token, park_id):
                if park_id and lot_id:
                    return update_parking_lot(park_id, lot_id, request)
                elif park_id:
                    return create_parking_lot(request)
            else:
                abort(401, "Invalid token.")
        else:
            abort(400, "Missing user token.")

    elif request.method == 'DELETE':
        if token:
            if user_handler.check_user(token, park_id):
                if park_id and lot_id:
                    return delete_parking_lot(park_id, lot_id)
                else:
                    abort(400, "Missing park_id and lot_id")
            else:
                abort(401, "Invalid token.")
        else:
            abort(400, "Missing user token.")
    else:
        abort(400)

def get_parking_lots(park_id, status):
    """
    Helper function that gets all parking lots associated with the park

    Args:
        park_id: The id of the park
    Returns:
        A list of json report objects
    """
    parking_lots_list_json = parking_handler.get_parking_lots_list_json(park_id, status)
    return parking_lots_list_json

def get_parking_lot(park_id, lot_id):
    """
    Helper function that gets a specfic parking lot

    Args:
        park_id: The id of the park
        reprot_id: The id of the report
    Returns:
        A single json report object
    """
    parking_lot_json = parking_handler.get_parking_lot_json(park_id, lot_id)
    return parking_lot_json

def check_parking_request(request):
    if not request.json:
        abort(400, "Missing request body")
    if 'lot_lat' not in request.json:
        abort(400, "Missing lot_lat in request body")
    if 'lot_long' not in request.json:
        abort(400, "Missing lot_long in request body")
    if 'lot_name' not in request.json:
        abort(400, "Missing lot_name in request body")
    if 'description' not in request.json:
        abort(400, "Missing description in request body")
    if 'severity' not in request.json:
        abort(400, "Missing severity in request body")

def create_parking_lot(request):
    check_parking_request(request)
    
    park_id = int(request.args.get('park'))

    lot_json = parking_handler.create_parking_lot(request.json['lot_name'],
                     park_id,
                     request.json['lot_lat'],
                     request.json['lot_long'],
                     request.json['description'],
                     request.json['severity']
                     )

    return lot_json

def update_parking_lot(park_id, lot_id, request):
    check_parking_request(request)

    
    lot_json = parking_handler.update_parking_lot(lot_id,
                     request.json['lot_name'],
                     park_id,
                     request.json['lot_lat'],
                     request.json['lot_long'],
                     request.json['description'],
                     request.json['severity']
                     )

    return lot_json


def delete_parking_lot(park_id, lot_id):
    result = parking_handler.delete_parking_lot(park_id, lot_id)
    return app.response_class(json.dumps(result), content_type='application/json')

#endregion

################################################################
#                           FIRE                               #
################################################################

#region fire
@app.route('/pw/api/wildfire', methods=['GET'])
def get_fire_base():
    """
    Gets wildfires in the US

    Args:
        None
    Returns:
        GET - A wildfire
    """
    loc_lon = request.args.get('locLon')
    loc_lat = request.args.get('locLat')
    loc_range = request.args.get('locRange')

    log_str = "{}\n{}\n{}".format(str(request.method), str(request.args), str(request.json))
    print(log_str)


    if request.method == 'GET':
        if loc_lat and loc_lon and loc_range:
            return fire_handler.get_and_parse_json_filter(float(loc_lon), float(loc_lat), float(loc_range))
        else:
            return fire_handler.get_and_parse_json_filter()
    else:
        abort(400, "We only accept GET")
#endregion

@app.route('/')
def home():
    return render_template('home.html', title='Home')

@app.errorhandler(404)
def not_found(e):
    return jsonify(error=str(e)), 404

@app.errorhandler(400)
def bad_request(e):
    return jsonify(error=str(e)), 400

@app.errorhandler(401)
def invalid_login(e):
    return jsonify(error=str(e)), 401

if __name__ == '__main__':
    app.run(debug=True)