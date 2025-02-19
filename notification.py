import pygame
import time

class Notification:
    """A single notification that disappears after a set duration."""
    def __init__(self, text, duration=3, position=(20, 600), font_size=24):
        self.text = text
        self.duration = duration
        self.start_time = time.time()  # Record when the notification starts
        self.font = pygame.font.SysFont(None, font_size)
        self.image = self.font.render(self.text, True, 'white')
        self.rect = self.image.get_rect(topleft=position)
        self.display_surface = pygame.display.get_surface()

    def update(self):
        """Check if notification should be removed."""
        return (time.time() - self.start_time) > self.duration  # Returns True when expired

    def draw(self):
        """Draw the notification on screen."""
        pygame.draw.rect(self.display_surface, 'black', self.rect.inflate(10, 10), border_radius=10)  # Background
        self.display_surface.blit(self.image, self.rect)  # Text


class NotificationManager:
    """Manages multiple notifications and handles their positioning."""
    def __init__(self):
        self.notifications = []  # List of active notifications
        self.max_notifications = 5  # Limit number of notifications on screen
        self.spacing = 40  # Space between notifications

    def add_notification(self, text, duration=3):
        """Add a new notification and shift others up."""
        base_position = (20, 600)  # Bottom-left starting position
        
        # Shift existing notifications upwards
        for notification in self.notifications:
            notification.rect.y -= self.spacing  # Move up by `self.spacing`

        # Add new notification at the base position
        self.notifications.append(Notification(text, duration, base_position))

        # Remove oldest if exceeding max notifications
        if len(self.notifications) > self.max_notifications:
            self.notifications.pop(0)

    def update(self):
        """Remove expired notifications."""
        self.notifications = [n for n in self.notifications if not n.update()]
        
        """Draw all notifications on the screen."""
        for notification in self.notifications:
            notification.draw()
        
