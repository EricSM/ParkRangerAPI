#!flask/bin/python

# Steps to deploy: 
# az login
# az webapp deployment source config-local-git --name parkwatch-backend --resource-group ParkWatch
# OR
# az webapp create -g ParkWatch -p ASP-ParkWatch-9dbf -n parkwatch-backend --runtime "python|3.7" --deployment-local-git

# parkwatch_ranger, (same password as elsewhere)

# Copy url under deployment center > credentials
# git remote add azure <url>
# git push azure master

# https://docs.microsoft.com/en-us/azure/app-service/containers/how-to-configure-python

from flask import Flask, jsonify, render_template
from controllers.report import Report, ReportHandler

app = Flask(__name__, template_folder="templates")

report_handler = ReportHandler()
report_handler.create_report(
    "White Rim",
    100.0,
    100.0,
    "Trail is closed due to flooding at mile 78.",
    5,
    1
)

@app.route('/pw/api/v1.0/reports/<int:report_id>', methods=['GET'])
def get_reports(report_id):
    report_json = report_handler.get_report_json(report_id)
    return report_json

@app.route('/')
def home():
    return "Hello!"

if __name__ == '__main__':
    app.run(debug=True)
    # app.run(host='127.0.0.1', port=8080, debug=True)