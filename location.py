from shapely.geometry import Point, Polygon
from pytmx.util_pygame import load_pygame
import json
from settings import *

""""
Two main requirements
1. Check if player is inside a location
2. Return a list of location coordinates
"""

class Location:
    def __init__(self, name, tile_positions, description, topic):
        self.name = name
        self.tile_positions = tile_positions
        self.polygon = Polygon(self.tile_positions)
        self.description = description
        self.topic = topic
        
    def add_tile_positions(self, tile_positions):
        self.tile_positions += tile_positions
        self.polygon = Polygon(self.tile_positions)
    
    def check_pos(self, pos):
        return self.polygon.contains(Point(pos))
        
        
class Location_Manager:
    def __init__(self):
        self.locations = {}
        self.set_up()
        for _, (_, location) in enumerate(self.locations.items()):
            print(location.name, location.polygon, location.description, location.topic)
    
    def set_up(self):
        with open("locations.json", "r") as file:
            location_data = json.load(file)
        
        tmx_data = load_pygame('./data/map.tmx')
        
        for obj in tmx_data.get_layer_by_name('Location'):
            if obj.name not in self.locations:
                data = location_data.get(obj.name, {})  # safe access
                description = data.get("description", "")
                topic = data.get("topic", "")
                self.locations[obj.name] = Location(obj.name, [(p.x, p.y) for p in obj.as_points], description, topic)
            else:
                self.locations[obj.name].add_tile_positions([(p.x, p.y) for p in obj.as_points])  
    
    def check_player_location(self, player):
        player_pos = (int(player.rect.centerx), int(player.rect.centery))
        for location in self.locations.values():
            if location.check_pos(player_pos):
                # Update player current location
                player.location = location.name
                return
    
    def get_location(self, pos):
        for location in self.locations.values():
            if location.check_pos(pos):
                return location
        return None
    
    def get_locations(self):
        res = []
        for location in self.locations.values():
            res.append([location.name, location.polygon])
        return res
        