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

from flask import Flask, jsonify, render_template, make_response, request
from flask_cors import CORS
from controllers.report import Report, ReportHandler

app = Flask(__name__, template_folder="templates")
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

report_handler = ReportHandler()
report_id = report_handler.create_report(
    'White Rim',
    100.0,
    100.0,
    'Trail is closed due to flooding at mile 78.',
    5,
    1
)

@app.route('/pw/api/reports/<int:report_id>', methods=['GET'])
def get_report(report_id):
    report_json = report_handler.get_report_json(report_id)
    return report_json

@app.route('/pw/api/reports/', methods=['GET'])
def get_reports():
    reports_list_json = report_handler.get_reports_list_json()
    return reports_list_json

@app.route('/pw/api/reports/', methods=['POST'])
def create_task():
    if not request.json or not 'loc_name' in request.json:
        abort(400)
    
    report_id = report_handler.create_report(request.json['loc_name'],
                     request.json['loc_lat'],
                     request.json['loc_long'],
                     request.json['description'],
                     request.json['severity'],
                     request.json['closure'])

    report_json = report_handler.get_report_json(report_id)
    return report_json

@app.route('/')
def home():
    return """API:\n\n
            GET Report: /pw/api/reports/<int:report_id>"""

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    app.run(debug=True)
    # app.run(host='127.0.0.1', port=8080, debug=True)