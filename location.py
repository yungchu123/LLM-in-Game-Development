from shapely.geometry import Point, Polygon
from pytmx.util_pygame import load_pygame
from settings import *

""""
Two main requirements
1. Check if player is inside a location
2. Return a list of location coordinates
"""

class Location:
    def __init__(self, name, tile_positions):
        self.name = name
        self.tile_positions = tile_positions
        self.polygon = Polygon(self.tile_positions)
        
    def add_tile_positions(self, tile_positions):
        self.tile_positions += tile_positions
        self.polygon = Polygon(self.tile_positions)
    
    def check_player_entered(self, player):
        player_pos = (int(player.rect.centerx), int(player.rect.centery))
        return self.polygon.contains(Point(player_pos))
        
        
class Location_Manager:
    def __init__(self):
        self.locations = {}
        self.set_up()
        for _, (_, location) in enumerate(self.locations.items()):
            print(location.name, location.polygon)
    
    def set_up(self):
        tmx_data = load_pygame('./data/map.tmx')
        
        for obj in tmx_data.get_layer_by_name('Location'):
            if obj.name not in self.locations:
                self.locations[obj.name] = Location(obj.name, [(p.x, p.y) for p in obj.as_points])
            else:
                self.locations[obj.name].add_tile_positions([(p.x, p.y) for p in obj.as_points])
    
    def check_player_location(self, player):
        for location in self.locations.values():
            if location.check_player_entered(player):
                # Update player current location
                player.location = location.name
                return
    
    def get_locations(self):
        res = []
        for location in self.locations.values():
            res.append([location.name, location.polygon])
        return res
        