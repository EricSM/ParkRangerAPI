import requests
import jsonpickle
import math


class Fire:
    def __init__(self, name, lon, lat):
        self.incident_name = name
        self.center_lon = lon
        self.center_lat = lat

class WildFireHandler:
    def __init__(self):
        self.request_url = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Public_Wildfire_Perimeters_View/FeatureServer/0/query?where=1%3D1&outFields=OBJECTID,IncidentName,CreateDate,DateCurrent,ComplexName,ComplexID,GACC,IMTName,UnitID,LocalIncidentID,IRWINID,GeometryID,GlobalID,Shape__Area,Label&outSR=4326&f=json"

    def get_firedata(self):
        request = requests.get(self.request_url)
        return request.json()

    def find_center(self, rings):
        lon = 0
        lat = 0

        for r in rings[0]:
            lon += r[0]
            lat += r[1]

        return lon/len(rings[0]), lat/len(rings[0])

    def check_range(self, centerLon, centerLat, locLon, locLat, locRange):
        dist = math.sqrt((locLon - centerLon)**2 + (locLat - centerLat)**2)
        if dist <= locRange:
            return True
        else:
            return False

    def parse_firedata(self, json_body, locLon, locLat, locRange):
        fires = []
        for feature in json_body['features']:
            if 'geometry' in feature:
                name = feature['attributes']['IncidentName']
                lon, lat = self.find_center(feature['geometry']['rings'])
                if locLon and locLat and locRange:
                    if self.check_range(lon, lat, locLon, locLat, locRange):
                        new_fire = Fire(name, lon, lat)
                        fires.append(new_fire)
                else:
                    new_fire = Fire(name, lon, lat)
                    fires.append(new_fire)

        return fires

    def get_and_parse_json_filter(self, locLon = None, locLat = None, locRange = None):
        data = self.get_firedata()
        parsed_data = self.parse_firedata(data, locLon, locLat, locRange)
        return jsonpickle.encode(parsed_data, unpicklable=False)
