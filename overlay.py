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
        self.font = pygame.font.SysFont(None, 24)
        
        # imports 
        overlay_path = './graphics/overlay'
        self.items_surf = [
            pygame.transform.scale(
                pygame.image.load(f"{overlay_path}/{item['type']}/{item['name']}.png").convert_alpha(),
                (SLOT_SIZE - 15, SLOT_SIZE - 15)  # Resize image 
            ) 
            for item in player.inventory
        ]
        
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
                    text_surface = self.font.render(str(item["quantity"]), True, BLACK)
                    text_rect = text_surface.get_rect()
                    
                    # Position the text in the bottom-right corner of the slot
                    text_x = x + SLOT_SIZE - text_rect.width
                    text_y = INVENTORY_Y + SLOT_SIZE - text_rect.height  
                    
                    self.display_surface.blit(text_surface, (text_x, text_y))
            
            # Highlight selected slot
            if i == self.player.inventory_index:
                pygame.draw.rect(self.display_surface, HIGHLIGHT_COLOR, (x, INVENTORY_Y, SLOT_SIZE, SLOT_SIZE), 3)