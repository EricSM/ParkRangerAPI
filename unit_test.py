import unittest
import json
from backend import *

from controllers.report import Report, ReportHandler
from controllers.weather import Rule, WeatherHandler
from controllers.parking import ParkingLot, ParkingHandler
from controllers.user import UserHandler

class Request:
    def __init__(self):
        self.json = None
        self.args = None

class TestBaseMethods(unittest.TestCase):
    cache_report_id = 0
    cache_report_json = None

    ################################################################
    #                            LOGIN                             #
    ################################################################

    #region Login
    def test_login_invalid(self):
        request = Request()
        request.json = {}
        request.json['email'] = 'albus@hogwarts.edu'
        request.json['password'] = 'wrong_password'

        response = login(request)

        self.assertEqual(response, -1)
    
    def test_login_no_user(self):
        request = Request()
        request.json = {}
        request.json['email'] = 'no_exist@email.com'
        request.json['password'] = 'password'

        response = login(request)

        self.assertEqual(response, -1)

    def test_login(self):
        request = Request()
        request.json = {}
        request.json['email'] = 'albus@hogwarts.edu'
        request.json['password'] = 'password'

        response = json.load(login(request))

        self.assertEqual(response['email'], request.json['email'])
    #endregion

    ################################################################
    #                           REPORTS                            #
    ################################################################

    #region Reports
    def test_create_report(self):
        request = Request()
        request.json = {}
        request.json['loc_name'] = "Test Report Name"
        request.json['loc_lat'] = 100.0
        request.json['loc_long'] = 100.0
        request.json['description'] = "Test Report Description"
        request.json['severity'] = 0
        request.json['closure'] = 0

        request.args['park_id'] = 99

        response = json.load(create_report(request))

        self.cache_report_id = response['park_id'] # Save this to delete the report later

        self.assertEqual(response['loc_name'], request.json['loc_name'])

    def test_update_report(self):
        request = Request()
        self.cache_report_json['loc_name'] = "Test Update Report"
        request.json = self.cache_report_json

        response = json.load(update_report(99, self.cache_report_id, self.update_report_json))

        self.assertEqual(response['loc_name'], self.cache_report_json['loc_name'])

    def test_get_report(self):
        response = json.load(get_report(99, self.cache_report_id))
        self.assertEqual(resposne['loc_name'], "Test Update Report")

    def test_get_reports(self):
        response = json.load(get_reports(99))
        self.assertEqual(response, 1) # This will fail.

    def test_delete_report(self):
        response = delete_report(99, self.cache_report_id)
        self.assertTrue(response)
    #endregion

    ################################################################
    #                           WEATHER                            #
    ################################################################

    #region Weather
    def test_create_rule(self):
        request = Request()
        request.json = {}
        request.args['park'] = 99

        request.json['condition_type'] = 'temp'
        request.json['condition_interval_value'] = -100
        request.json['condition_interval_symbol'] = 'geq'
        request.json['description'] = 'Test rule, should always trigger'
        request.json['name'] = 'Test Rule'
        request.json['path'] = "path\":[{\"lat\":36.86149,\"lng\":30.63743},{\"lat\":36.86341,\"lng\":30.72463}]"

        response = json.load(create_rule(request))
        self.assertEqual(response['name'], request.json['name'])
    #endregion


    ################################################################
    #                           PARKING                            #
    ################################################################

    #region Parking
    #endregion

if __name__ == '__main__':
    unittest.main()