import pygame
from settings import *

# Colors
BG_COLOR = (0, 0, 0)
UI_BG_COLOR = (100, 80, 50)
SLOT_COLOR = (200, 180, 120)
HIGHLIGHT_COLOR = (255, 255, 0)

# Inventory settings
NUM_SLOTS = 10
SLOT_SIZE = 50
SLOT_MARGIN = 5
INVENTORY_Y = SCREEN_HEIGHT - SLOT_SIZE - 10

class Overlay:
    def __init__(self,player):

        # general setup
        self.display_surface = pygame.display.get_surface()
        self.player = player
        self.small_font = pygame.font.SysFont(None, 24)
        self.medium_font = pygame.font.SysFont(None, 30)
        self.large_font = pygame.font.SysFont(None, 40)
        
        # imports for inventory image
        overlay_path = './graphics/overlay'
        self.items_surf = [
            pygame.transform.scale(
                pygame.image.load(f"{overlay_path}/{item['type']}/{item['name']}.png").convert_alpha(),
                (SLOT_SIZE - 15, SLOT_SIZE - 15)  # Resize image 
            ) 
            for item in player.inventory
        ]
        
    def draw_level(self):
        # Define a rectangle for the background. Adjust the position and size as needed.
        background_rect = pygame.Rect(10, 10, 170, 115)
        pygame.draw.rect(self.display_surface, BEIGE, background_rect, border_radius=20)

        # Player name
        name_surf = self.large_font.render(self.player.name, True, BLACK)
        name_rect = name_surf.get_rect(topleft=(30, 20))
        self.display_surface.blit(name_surf, name_rect)
        
        # Player level
        level_surf = self.medium_font.render(f"Level {self.player.level_system.get_level()}", True, BLACK)
        level_rect = level_surf.get_rect(topleft=(30, 60))
        self.display_surface.blit(level_surf, level_rect)
        
        # Player experience
        experience_surf = self.medium_font.render(
            f"Exp    {self.player.level_system.get_experience()} / {self.player.level_system.experience_to_next_level()}",
            True, BLACK)
        experience_rect = experience_surf.get_rect(topleft=(30, 95))
        self.display_surface.blit(experience_surf, experience_rect)
        
    def draw_money(self):
        text_surf = self.medium_font.render(f"Money: {self.player.money}", True, BLACK)
        text_rect = text_surf.get_rect(topleft=(40, SCREEN_HEIGHT-40))
        self.display_surface.blit(text_surf, text_rect)
    
    def draw_player_location(self):
        # Background box dimensions
        margin = 20
        box_width = 300
        box_height = 100
        box_x = SCREEN_WIDTH - box_width - margin
        box_y = SCREEN_HEIGHT - box_height - margin
        
        location_name = getattr(self.player.location, "name", None)
        location_topic = getattr(self.player.location, "topic", None)
        
        background_image = pygame.image.load('./graphics/objects/banner.png').convert_alpha()
        background_image = pygame.transform.scale(background_image, (box_width, box_height))
        background_rect = background_image.get_rect(topleft=(box_x, box_y))
        self.display_surface.blit(background_image, background_rect)
        
        if location_topic:
            name_surf = self.medium_font.render(location_name, True, WHITE)
            topic_surf = self.small_font.render(f"({location_topic})", True, WHITE)
            
            name_rect = name_surf.get_rect(midtop=(background_rect.centerx, background_rect.top + 20))
            topic_rect = topic_surf.get_rect(midtop=(background_rect.centerx, name_rect.bottom + 20))
            
            self.display_surface.blit(topic_surf, topic_rect)
            
            # Draw line in between name and topic
            line_y = name_rect.bottom + 10  
            line_start = (background_rect.left + 20, line_y)
            line_end = (background_rect.right - 20, line_y)
            pygame.draw.line(self.display_surface, WHITE, line_start, line_end, width=2)
        else:
            name_surf = self.medium_font.render(location_name, True, WHITE)
            name_rect = name_surf.get_rect(center=background_rect.center)
        
        self.display_surface.blit(name_surf, name_rect)
        
        
        

    
    def draw_inventory(self):
        inventory_width = (SLOT_SIZE + SLOT_MARGIN) * NUM_SLOTS - SLOT_MARGIN
        inventory_x = (SCREEN_WIDTH - inventory_width) // 2
        
        # Draw inventory background
        pygame.draw.rect(self.display_surface, UI_BG_COLOR, (inventory_x - 10, INVENTORY_Y - 10, inventory_width + 20, SLOT_SIZE + 20))
        
        # Draw slots
        for i in range(NUM_SLOTS):
            x = inventory_x + i * (SLOT_SIZE + SLOT_MARGIN)
            pygame.draw.rect(self.display_surface, SLOT_COLOR, (x, INVENTORY_Y, SLOT_SIZE, SLOT_SIZE))
            
            # Draw item image if exists
            if i < len(self.player.inventory):
                item_surf = self.items_surf[i]
                if item_surf:
                    img_rect = item_surf.get_rect(center=(x + SLOT_SIZE // 2, INVENTORY_Y + SLOT_SIZE // 2))
                    self.display_surface.blit(item_surf, img_rect)
                    
                # Display quantity if applicable
                item = self.player.inventory[i]
                if "quantity" in item:
                    text_surface = self.small_font.render(str(item["quantity"]), True, BLACK)
                    text_rect = text_surface.get_rect()
                    
                    # Position the text in the bottom-right corner of the slot
                    text_x = x + SLOT_SIZE - text_rect.width
                    text_y = INVENTORY_Y + SLOT_SIZE - text_rect.height  
                    
                    self.display_surface.blit(text_surface, (text_x, text_y))
            
            # Highlight selected slot
            if i == self.player.inventory_index:
                pygame.draw.rect(self.display_surface, HIGHLIGHT_COLOR, (x, INVENTORY_Y, SLOT_SIZE, SLOT_SIZE), 3)
    
    def draw_guide(self):
        background_image = pygame.image.load('./graphics/objects/old_paper.png').convert_alpha()
        
        # Background box dimensions
        box_width = 1400
        box_x = (SCREEN_WIDTH - box_width) // 2
        box_height = 700
        box_y = 10
        
        # Draw background
        background_image = pygame.transform.scale(background_image, (box_width, box_height))
        self.display_surface.blit(background_image, (box_x, box_y))
        
        # Can move to settings for dynamic key binding
        key_bindings = {
            "Arrow Keys": "Move Character",
            "Q": "Shift Selected Item Left",
            "W": "Shift Selected Item Right",
            "Space": "Use Item",
            "N": "Interact",
            "M": "Start Question"
        }
        
        y_offset = box_y + 220
        x_offset = box_x + 440
        
        self.create_text("Welcome to Math Harvest, where wisdom is your", x_offset, y_offset)
        y_offset += 35
        self.create_text("greatest tool, and numbers guide your journey!", x_offset, y_offset)
        y_offset += 60

        for key, action in key_bindings.items():
            self.create_text(f"{key}: {action}", x_offset, y_offset, size="small")
            y_offset += 25  # Space between lines
    
    def create_text(self, text, x , y, size="medium"):
        if size == "small":
            text_surface = self.small_font.render(text, True, BLACK)
        elif size == "medium":
            text_surface = self.medium_font.render(text, True, BLACK)
        else:
            text_surface = self.large_font.render(text, True, BLACK)
        self.display_surface.blit(text_surface, (x, y))
    
    def update(self):
        self.draw_inventory()
        self.draw_level()
        self.draw_money()
        self.draw_player_location()