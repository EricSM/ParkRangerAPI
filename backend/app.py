#!flask/bin/python
from flask import Flask, jsonify, render_template
from controllers.report import Report, ReportHandler

app = Flask(__name__)

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

if __name__ == '__main__':
    app.run(debug=True)