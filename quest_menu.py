import pygame
from settings import *

class QuestMenu:
    """Displays the player's active quests when 'E' is pressed."""
    
    def __init__(self, player):
        self.player = player  # Reference to player's quests
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.SysFont(None, 32)
        self.title_font = pygame.font.SysFont(None, 40, bold=True)

        self.is_open = False  # Menu starts closed
        self.max_displayed_quests = 3  # Limit quests shown

        # Menu Box Properties
        self.quest_width = 1000
        self.quest_height = 200
        self.quest_x = (SCREEN_WIDTH - self.quest_width) // 2

    def toggle_menu(self):
        """Opens or closes the quest menu when 'E' is pressed."""
        self.is_open = not self.is_open  # Toggle menu state

    def draw_quest(self, quest, offset_y):
        # Draw Quest Box (background)
        pygame.draw.rect(self.display_surface, (50, 50, 50), 
                         (self.quest_x, offset_y, self.quest_width, self.quest_height), border_radius=15)
        pygame.draw.rect(self.display_surface, (255, 255, 255), 
                         (self.quest_x, offset_y, self.quest_width, self.quest_height), 3, border_radius=15)
        
        # Render Quest Name
        name_surface = self.font.render(quest.name, True, (255, 200, 0))
        name_rect = name_surface.get_rect(topleft=(self.quest_x + 20, offset_y + 20))
        self.display_surface.blit(name_surface, name_rect)
        
        # Render Quest Description
        wrapped_text = self.wrap_text(quest.description, self.quest_width - 40)
        offset_y_for_description = offset_y + 60  # Start position for text inside box
        for line in wrapped_text:
            npc_surface = self.font.render(line, True, WHITE)
            self.display_surface.blit(npc_surface, (self.quest_x + 20, offset_y_for_description))
            offset_y_for_description += self.font.get_height() + 5  # Space between lines
        
        self.draw_progress_bar(quest, offset_y)

    def wrap_text(self, text, max_width):
        """Splits text into multiple lines based on available width."""
        words = text.split()  # Split text into individual words
        lines = []
        current_line = ""

        for word in words:
            # Check if adding this word exceeds the width
            test_line = f"{current_line} {word}".strip()
            if self.font.size(test_line)[0] < max_width:
                current_line = test_line
            else:
                lines.append(current_line)  # Store current line and start a new one
                current_line = word  # Start with the new word

        # Append last line
        if current_line:
            lines.append(current_line)

        return lines  

    def draw_progress_bar(self, quest, offset_y):
        # Draw progress bar
        progress_box_margin = 10
        progress_box_height = 40
        progress_box_width = self.quest_width - 2 * progress_box_margin
        progress_box_x = self.quest_x + progress_box_margin
        progress_box_y = offset_y + self.quest_height - progress_box_height - progress_box_margin
        
        progress_box_rect = pygame.Rect(progress_box_x, progress_box_y, progress_box_width, progress_box_height)
        pygame.draw.rect(self.display_surface, (100, 100, 100), progress_box_rect, border_radius=12)
        pygame.draw.rect(self.display_surface, BLACK, progress_box_rect, width=3, border_radius=12)
        
        # Draw progress filled bar
        progress = quest.progress
        target = quest.target_quantity
        filled_width = (progress / target) * progress_box_width if target > 0 else 0
        if progress > 0:
            pygame.draw.rect(self.display_surface, GREEN, (progress_box_x, progress_box_y, filled_width, progress_box_height), border_radius=12)
        
        # Render progress text
        progress_text = self.font.render(f"{quest.target_item}: {progress} / {target}", True, BLACK)
        text_x = self.quest_x + self.quest_width // 2 - progress_text.get_width() // 2
        text_y = progress_box_y + progress_box_height // 2 - progress_text.get_height() // 2
        self.display_surface.blit(progress_text, (text_x, text_y))
        
    def draw(self):
        """Draws the quest menu on the screen."""
        if not self.is_open:
            return  # Don't draw if the menu is closed

        # Draw Title
        title_y = 50
        title_surface = self.title_font.render("Quest Menu", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, title_y))
        self.display_surface.blit(title_surface, title_rect)

        # Get Player's Active Quests
        quests = self.player.quests[:self.max_displayed_quests]  

        offset_y = title_y + 30  # First quest starts here
        spacing = 30  # Space between quests

        for quest in quests:
            self.draw_quest(quest, offset_y)
            offset_y += self.quest_height + spacing

    def handle_event(self, event):
        """Handles key press events to toggle the menu."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            self.toggle_menu()
