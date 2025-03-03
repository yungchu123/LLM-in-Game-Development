import pygame
from settings import *
from timer import Timer

class Announcer:
    def __init__(self):
        # general setup
        self.display_surface = pygame.display.get_surface()
        
        # Fonts
        self.title_font = pygame.font.SysFont(None, 48)  # Larger font for title
        self.desc_font = pygame.font.SysFont(None, 24)   # Smaller font for description
        
        # Event data
        self.event_active = False
        self.event_timer = Timer(10000, self.hide_event)
    
    def start_event(self, event_name, event_description, npc_name):
        self.event_name = event_name
        self.event_description = event_description
        self.event_helper = f"(Go to {npc_name} now to start the quest!!)"
        
        self.event_active = True
        self.event_timer.activate()
    
    def hide_event(self):
        self.event_active = False
    
    def draw_event(self):
        background_image = pygame.image.load('./graphics/objects/banner.png').convert()
        
        # Background box dimensions
        box_width = 800
        box_x = (SCREEN_WIDTH - box_width) // 2
        box_height = 250
        box_y = 10
        
        # Draw background
        # pygame.draw.rect(self.display_surface, 'grey', (box_x, box_y, box_width, box_height), border_radius = 20)
        background_image = pygame.transform.scale(background_image, (box_width, box_height))
        self.display_surface.blit(background_image, (box_x, box_y))
        
        # Event title
        title_surf = self.title_font.render(self.event_name, True, 'white')         # Render text
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, box_y + 40))    # Get text rects
        self.display_surface.blit(title_surf, title_rect)                           # Draw text
        
        # Helper text
        helper_surf = self.desc_font.render(self.event_helper, True, 'yellow')
        helper_rect = helper_surf.get_rect(center=(SCREEN_WIDTH // 2, box_y + box_height - 40))
        self.display_surface.blit(helper_surf, helper_rect)
        
        # Event description (Need wrapping)
        wrapped_text = self.wrap_text(self.event_description, box_width - 100)
        y_offset = box_y + 80  # Start position for text inside box
        for line in wrapped_text:
            npc_surface = self.desc_font.render(line, True, WHITE)
            self.display_surface.blit(npc_surface, (box_x + 60, y_offset))
            y_offset += self.desc_font.get_height() + 5  # Space between lines
    
    def wrap_text(self, text, max_width):
        """Splits text into multiple lines based on available width."""
        words = text.split()  # Split text into individual words
        lines = []
        current_line = ""

        for word in words:
            # Check if adding this word exceeds the width
            test_line = f"{current_line} {word}".strip()
            if self.desc_font.size(test_line)[0] < max_width:
                current_line = test_line
            else:
                lines.append(current_line)  # Store current line and start a new one
                current_line = word  # Start with the new word

        if current_line:
            lines.append(current_line)

        return lines  
    
    def update(self):
        self.event_timer.update()
        
        if self.event_active:
            self.draw_event()