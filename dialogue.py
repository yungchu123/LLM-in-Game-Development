import pygame
import pyperclip
import re, threading
from settings import *

class Dialogue_Menu:
    def __init__(self, get_npc_by_name):
        
        # general setup
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font('./font/LycheeSoda.ttf', 30)

        self.active = False
        self.can_open_chat = True  # Flag to prevent immediate re-opening
        self.message = ""
        self.input_text = ""    # Get player input
        
        self.cursor_visible = True
        self.cursor_timer = 0
        self.selection_start = 0  # Start of selected text
        self.selection_end = 0  # End of selected text
        
        self.npc = None
        self.get_npc_by_name = get_npc_by_name
        
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

    def input(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:  
                # Exit dialogue menu
                if event.key == pygame.K_ESCAPE: 
                    self.close_npc_chat()
                # Remove the last character from the input text
                elif event.key == pygame.K_BACKSPACE: 
                    self.input_text = self.input_text[:max(0, self.selection_start - 1)] + self.input_text[self.selection_end:]
                    self.selection_start = max(0, self.selection_start - 1)
                    self.selection_end = self.selection_start
                # Submit user input
                elif event.key == pygame.K_RETURN:
                    if self.input_text == "":
                        self.close_npc_chat()
                        return
                    if not self.npc:
                        match = re.match(r"/(\w+)\s*(.*)", self.input_text)
                        # Send a command to NPC
                        if match:
                            npc_name = match.group(1)
                            user_message = match.group(2)
                            self.npc = self.get_npc_by_name(npc_name)
                            self.npc.get_input(user_message, self)
                        self.close_npc_chat()
                        return
                    print(f'You: {self.input_text}')
                    self.npc.get_input(self.input_text, self)
                    print(f'NPC: {self.message}')
                    self.reset_input()
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
                # Add the displayable character of the key pressed
                elif event.unicode.isprintable():
                    self.input_text = self.input_text[:self.selection_start] + event.unicode + self.input_text[self.selection_end:]
                    self.selection_start += 1
                    self.selection_end = self.selection_start
    
    def start_npc_chat(self, npc_name=None):
        if not self.can_open_chat:
            return
        if npc_name:
            self.npc = self.get_npc_by_name(npc_name)
        self.active = True
    
    def close_npc_chat(self):
        self.active = False
        self.npc = None
        self.npc_name = None
        self.reset_input()
        self.can_open_chat = False
        threading.Timer(0.1, self.enable_chat).start()
    
    def enable_chat(self):
        """Re-enables NPC chat after delay."""
        self.can_open_chat = True
    
    def reset_input(self):
        self.input_text = ""
        self.selection_start = 0
        self.selection_end = 0 
    
    def is_active(self):
        return self.active
    
    def update(self, events):
        self.input(events)
        self.draw_input_box()
        if self.message:
            self.draw_chatbox()