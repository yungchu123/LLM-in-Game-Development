from settings import *

class LevelSystem:
    def __init__(self, add_notification, player, location_sprites, level=1, experience=0):
        self.level = level
        self.experience = experience
        self.add_notification = add_notification
        self.player = player
        self.location_sprites = location_sprites

    def get_level(self):
        return self.level
    
    def get_experience(self):
        return self.experience
    
    def gain_experience(self, amount):
        """Add experience and check for level up."""
        self.add_notification(f"experience +{amount}")
        self.experience += amount
        while self.experience >= self.experience_to_next_level():
            self.on_level_up()

    def experience_to_next_level(self):
        """Calculate required XP for next level."""
        return 10 * self.level

    def on_level_up(self):
        """Handle events on leveling up."""
        self.add_notification(f"LEVEL UP! {self.level} -> {self.level + 1}")
        self.experience -= self.experience_to_next_level()
        self.level += 1
        print(f"Congratulations! You've reached level {self.level}")
        # Additional level-up logic can be added here (e.g., increase stats)
        
        if self.level == 2:
            self.unlock_area('Guild House')
            self.add_notification("Unlocked Guild House")
        elif self.level == 3:
            self.unlock_area('Waterworks')
            self.unlock_item('water', 'tool')
            self.add_notification("Unlocked Waterworks and Water")
        elif self.level == 4:
            self.unlock_area('Shop House')
            self.add_notification("Unlocked Shop House")
        elif self.level == 5:
            self.unlock_area('Whispering Woods')
            self.unlock_item('axe', 'tool')
            self.add_notification("Unlocked Whispering Woods and Axe")
    
    def unlock_item(self, item_name, item_type):
        self.player.add_to_inventory(item_name, item_type)
    
    def unlock_area(self, area):
        areas = {
            "Whispering Woods": [(26, 26), (27 , 26)],
            "Guild House": [(26, 36)],
            "Waterworks": [(33, 36)],
            "Shop House": [(40, 36), (41, 36)]
        }
        
        for sprite in self.location_sprites:
            x, y = sprite.rect.topleft
            pos = (x / TILE_SIZE, y / TILE_SIZE)
            if pos in areas[area]:
                sprite.kill()