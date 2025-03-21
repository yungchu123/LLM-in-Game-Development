from shapely.geometry import Point, Polygon
from pytmx.util_pygame import load_pygame
import json, configparser
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
        topics = self.load_topics()
        location_data = self.load_and_replace_json("locations.json", topics)
        
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
                player.location = location
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
    
    def load_topics(self, filename="config.ini"):
        config = configparser.ConfigParser()
        config.read(filename)
        return dict(config["Topics"]) if "Topics" in config else {}
    
    def load_and_replace_json(self, json_file, topics):
        with open(json_file, "r") as file:
            data = json.load(file)

        # Replace placeholders dynamically
        for location, details in data.items():
            if "topic" in details and details["topic"].lower() in topics:
                data[location]["topic"] = topics[details["topic"].lower()]

        return data