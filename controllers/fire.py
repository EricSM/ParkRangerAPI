import requests
import jsonpickle


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

    def parse_firedata(self, json_body):
        fires = []
        for feature in json_body['features']:
            if 'geometry' in feature:
                name = feature['attributes']['IncidentName']
                lon, lat = self.find_center(feature['geometry']['rings'])
                new_fire = Fire(name, lon, lat)
                fires.append(new_fire)

        return fires

    def get_and_parse_json(self):
        data = self.get_firedata()
        return jsonpickle.encode(self.parse_firedata(data), unpicklable=False)


# def test_main():
#     wf = WildFire()
#     out = wf.get_firedata()
#     fires = wf.parse_firedata(out)
#     print()


# if __name__ == "__main__":
#     test_main()