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

from flask import Flask, jsonify, render_template, make_response, request, render_template, abort, json
from flask_cors import CORS
from controllers.report import Report, ReportHandler
from controllers.weather import Rule, WeatherHandler
from controllers.parking import ParkingLot, ParkingHandler
from controllers.user import UserHandler

app = Flask(__name__, template_folder="templates")
logging.basicConfig(level=logging.DEBUG)
cors = CORS(app)

report_handler = ReportHandler()
weather_handler = WeatherHandler()
parking_handler = ParkingHandler()
user_handler = UserHandler()
# weather_handler.add_rule("rain", 0, ">", "Test", "Test Name", 0, "[{\"lat\": 36.86149, \"lng\": 30.63743},{\"lat\": 36.86341, \"lng\": 30.72463}]")

@app.route('/pw/api/login', methods=['POST'])
def login_base():
    """
    """
    if request.method == 'POST':
        login_code = login(request)
        if login_code == -1:
            abort(401, "Invalid username or password")
        elif login_code == -2:
            abort(401, "User not found")
        return login_code
    else:
        abort(400, "Login URI only accepts POST requests.")


def login(request):
    if not request.json:
        abort(400, "Missing request body")
    
    login_json = user_handler.login(request.json['email'],
                                    request.json['password'])

    return login_json

@app.route('/pw/api/login/new', methods=['POST'])
def new_login_base():
    """
    """
    if request.method == 'POST':
        return create_user(request)
    else:
        abort(400, "Login URI only accepts POST requests.")


def create_user(request):
    if not request.json:
        abort(400, "Missing request body")
    
    new_user_json = user_handler.create_user(request.json['email'],
                                             request.json['password'],
                                             request.json['f_name'],
                                             request.json['l_name'],
                                             request.json['park_id'])
    # Just making sure that we return the correct error codes.
    if new_user_json == -1:
        abort(401, "Invalid username or password")
    elif new_user_json == -2:
        abort(401, "User not found")

    return new_user_json


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
    token = request.args.get('token')

    if request.method == 'GET':
        if park_id and not report_id: # If only the park was provided then get list of all reports
            return get_reports(int(park_id))
        
        elif park_id and report_id: # If park and report id were provided then return specified report
            return get_report(int(park_id), int(report_id))

    elif request.method == 'POST':
        if park_id:
            return create_report(request)
        elif token:
            if user_handler.check_user(token, park_id):
                if park_id and report_id:
                    return update_report(park_id, report_id, request)          
            else:
                abort(401, "Invalid token.")
        else:
            abort(400, "Missing user token.")

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

def create_report(request):
    """
    Calls report handler to create a new report object, puts it into the db, and returns it

    Args:
        request: The request object
    Returns:
        The newly created json report object
    """
    if not request.json or not 'loc_name' in request.json:
        abort(400, "Error in create rueport request, missing request body")

    
    park_id = int(request.args.get('park'))

    report_json = report_handler.create_report(request.json['loc_name'],
                     park_id,
                     request.json['loc_lat'],
                     request.json['loc_long'],
                     request.json['description'],
                     request.json['severity'],
                     request.json['closure'],
                     0)

    return report_json

def update_report(park_id, report_id, request):
    """
    Calls report handler to create a new report object, puts it into the db, and returns it

    Args:
        request: The request object
    Returns:
        The newly created json report object
    """
    if not request.json or not 'loc_name' in request.json:
        abort(400, "Error in update report request, missing request body")

    
    report_json = report_handler.update_report(
                     park_id,
                     report_id,
                     request.json['loc_name'],
                     request.json['loc_lat'],
                     request.json['loc_long'],
                     request.json['description'],
                     request.json['severity'],
                     request.json['closure'],
                     0)
    print(report_json, flush=True)
    return report_json

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
    active = request.args.get('active')
    refresh = request.args.get('refresh')
    token = request.args.get('token')

    if request.method == 'GET':
        if park_id and not rule_id and not active and not refresh: # If only the park was provided then get list of all reports
            return get_rules(int(park_id))
        
        elif park_id and not rule_id and active:
            return get_active_rules(int(park_id), active)

        elif park_id and rule_id: # If park and report id were provided then return specified report
            return get_rule(int(park_id), int(rule_id))
        
        elif park_id and refresh: # Refresh all rules for the park
            if active:
                return refresh_rules(int(park_id), int(active))
            else:
                return refresh_rules(int(park_id), None)

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

def create_rule(request):
    if not request.json:
        abort(400, "Error in create rule request, missing request body")

    
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
                     json.dumps(request.json['path'])
                     )

    return report_json

def update_rule(park_id, rule_id, request):
    if not request.json:
        abort(400, "Error in update rule request, missing request body")

   
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
                     json.dumps(request.json['path'])
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

    if request.method == 'GET':
        if park_id and not lot_id: # If only the park was provided then get list of all reports
            return get_parking_lots(int(park_id))
        
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

def get_parking_lots(park_id):
    """
    Helper function that gets all parking lots associated with the park

    Args:
        park_id: The id of the park
    Returns:
        A list of json report objects
    """
    parking_lots_list_json = parking_handler.get_parking_lots_list_json(park_id)
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

def create_parking_lot(request):
    if not request.json:
        abort(400, "Error in parking request, missing request body.")
    
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
    if not request.json:
        abort(400, "Error in update parking request, missing request body")
    
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
    # app.run(host='127.0.0.1', port=8080, debug=True)