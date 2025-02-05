import pygame
import pyperclip
from settings import *

class Dialogue_Menu:
    def __init__(self):
        
        # general setup
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font('./font/LycheeSoda.ttf', 30)

        self.active = False
        self.message = ""
        self.input_text = ""    # Get player input
        
        self.cursor_visible = True
        self.cursor_timer = 0
        self.selection_start = 0  # Start of selected text
        self.selection_end = 0  # End of selected text
        
    def draw_chatbox(self):
        """Draw the NPC chatbox and the conversation."""
        # NPC Chatbox
        chatbox_rect = pygame.Rect(
            CHATBOX_MARGIN,
            SCREEN_HEIGHT - CHATBOX_HEIGHT - CHATBOX_MARGIN - INPUT_BOX_HEIGHT - 10,
            SCREEN_WIDTH - 2 * CHATBOX_MARGIN,
            CHATBOX_HEIGHT,
        )
        pygame.draw.rect(self.display_surface, GREY, chatbox_rect, border_radius=10)
        pygame.draw.rect(self.display_surface, WHITE, chatbox_rect, width=3, border_radius=10)
    
        # Render and display NPC dialogue
        npc_surface = self.font.render(f"NPC: {self.message}", True, WHITE)
        self.display_surface.blit(npc_surface, (chatbox_rect.x + 20, chatbox_rect.y + 20))

    def draw_input_box(self):
        """Draw the player input box."""
        color = WHITE 
        input_box_rect = pygame.Rect(
            CHATBOX_MARGIN,
            SCREEN_HEIGHT - INPUT_BOX_HEIGHT - CHATBOX_MARGIN,
            SCREEN_WIDTH - 2 * CHATBOX_MARGIN,
            INPUT_BOX_HEIGHT,
        )
        pygame.draw.rect(self.display_surface, color, input_box_rect, border_radius=10)
        pygame.draw.rect(self.display_surface, BLACK, input_box_rect, width=3, border_radius=10)

        # Render and display the player's input text
        input_surface = self.font.render(self.input_text, True, BLACK)
        self.display_surface.blit(input_surface, (input_box_rect.x + 10, input_box_rect.y + 10))

        # Cursor blinking
        self.cursor_timer += 1
        if self.cursor_timer % 60 == 0:  # Toggle cursor every second
            self.cursor_visible = not self.cursor_visible
            
        # Draw cursor
        if self.cursor_visible:
            cursor_x = input_box_rect.x + 10 + self.font.size(self.input_text[:self.selection_start])[0]
            cursor_y_top = input_box_rect.y + 8  # Align with text
            cursor_y_bottom = input_box_rect.y + input_box_rect.height - 8  # Align with text
            pygame.draw.line(self.display_surface, BLACK, (cursor_x, cursor_y_top), (cursor_x, cursor_y_bottom), 2)

    def input(self, events, get_response):
        for event in events:
            if event.type == pygame.KEYDOWN:  
                # Exit dialogue menu
                if event.key == pygame.K_ESCAPE: 
                    self.active = False
                # Remove the last character from the input text
                elif event.key == pygame.K_BACKSPACE: 
                    self.input_text = self.input_text[:max(0, self.selection_start - 1)] + self.input_text[self.selection_end:]
                    self.selection_start = max(0, self.selection_start - 1)
                    self.selection_end = self.selection_start
                # Submit user input
                elif event.key == pygame.K_RETURN:      
                    print(f'You: {self.input_text}')
                    self.message = get_response(self.input_text)
                    print(f'NPC: {self.message}')
                    self.input_text = ""
                # Move cursor left
                elif event.key == pygame.K_LEFT:  
                    self.selection_start = max(0, self.selection_start - 1)
                    self.selection_end = self.selection_start
                # Move cursor right
                elif event.key == pygame.K_RIGHT:  
                    self.selection_start = min(len(self.input_text), self.selection_start + 1)
                    self.selection_end = self.selection_start
                # CTRL + C (Copy)
                elif event.key == pygame.K_c and pygame.key.get_mods() & pygame.KMOD_CTRL:  # CTRL + C (Copy)
                    pyperclip.copy(self.input_text[self.selection_start:self.selection_end])
                # CTRL + V (Paste)
                elif event.key == pygame.K_v and event.mod & pygame.KMOD_CTRL:
                    paste_text = pyperclip.paste()
                    self.input_text = self.input_text[:self.selection_start] + paste_text + self.input_text[self.selection_end:]
                    self.selection_start += len(paste_text)
                    self.selection_end = self.selection_start
                # CTRL + A (Select All)
                elif event.key == pygame.K_a and pygame.key.get_mods() & pygame.KMOD_CTRL:  
                    self.selection_start = 0
                    self.selection_end = len(self.input_text)
                # Add the Unicode character of the key pressed
                else:
                    self.input_text = self.input_text[:self.selection_start] + event.unicode + self.input_text[self.selection_end:]
                    self.selection_start += 1
                    self.selection_end = self.selection_start
    
    def open_dialogue(self):
        self.active = True
        
    def is_active(self):
        return self.active
    
    def update(self, events, get_response):
        self.input(events, get_response)
        self.draw_input_box()
        if self.message:
            self.draw_chatbox()