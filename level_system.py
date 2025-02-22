class LevelSystem:
    def __init__(self, add_notification, level=1, experience=0):
        self.level = level
        self.experience = experience
        self.add_notification = add_notification

    def get_level(self):
        return self.level
    
    def get_current_experience(self):
        return self.experience
    
    def gain_experience(self, amount):
        """Add experience and check for level up."""
        self.add_notification(f"experience +{amount}")
        self.experience += amount
        while self.experience >= self._experience_to_next_level():
            self.on_level_up()

    def _experience_to_next_level(self):
        """Calculate required XP for next level."""
        return 10 * self.level

    def on_level_up(self):
        """Handle events on leveling up."""
        self.add_notification(f"LEVEL UP! {self.level} -> {self.level + 1}")
        self.experience -= self._experience_to_next_level()
        self.level += 1
        print(f"Congratulations! You've reached level {self.level}")
        # Additional level-up logic can be added here (e.g., increase stats)