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

app = Flask(__name__, template_folder="templates")
logging.basicConfig(level=logging.DEBUG)
cors = CORS(app)

report_handler = ReportHandler()
weather_handler = WeatherHandler()
# weather_handler.add_rule("rain", 0, ">", "Test", "Test Name", 0, "[{\"lat\": 36.86149, \"lng\": 30.63743},{\"lat\": 36.86341, \"lng\": 30.72463}]")

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

    if request.method == 'GET':
        if park_id and not report_id: # If only the park was provided then get list of all reports
            return get_reports(int(park_id))
        
        elif park_id and report_id: # If park and report id were provided then return specified report
            return get_report(int(park_id), int(report_id))

    elif request.method == 'POST':
        return create_report(request)

    elif request.method == 'DELETE':
        if park_id and report_id:
            return delete_report(park_id, report_id)
    else:
        abort(404)

    
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
        abort(400)
    
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

    if request.method == 'GET':
        if park_id and not rule_id and not active and not refresh: # If only the park was provided then get list of all reports
            return get_rules(int(park_id))
        
        elif park_id and not rule_id and active:
            return get_active_rules(int(park_id), active)

        elif park_id and rule_id: # If park and report id were provided then return specified report
            return get_rule(int(park_id), int(rule_id))
        
        elif park_id and refresh: # Refresh all rules for the park
            return refresh_rules(int(park_id), int(active))

    elif request.method == 'POST':
        return create_rule(request)
    else:
        abort(404)

def refresh_rules(park_id, active):
    weather_handler.refresh_rules(park_id)

    if active:
        return get_active_rules(park_id, active)
    else:
        return get_rules(park_id)

def get_rule(park_id, rule_id):
    fetched_rule = weather_handler.get_rule_json(park_id, rule_id)

    if not fetched_rule:
        abort(404)

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
    if not request.json or not 'name' in request.json:
        abort(400)
    
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

def delete_report(park_id, report_id):
    result = report_handler.delete_report(park_id, report_id)
    return app.response_class(json.dumps(result), content_type='application/json')

@app.route('/')
def home():
    return render_template('home.html', title='Home')

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    app.run(debug=True)
    # app.run(host='127.0.0.1', port=8080, debug=True)