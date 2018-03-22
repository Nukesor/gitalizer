#!/usr/bin/env python

from geopy.geocoders import Nominatim
from pprint import pprint

geolocator = Nominatim()
location = geolocator.geocode("America, New York")
location = geolocator.reverse([location.raw['lat'], location.raw['lon']])

pprint(location.raw)
