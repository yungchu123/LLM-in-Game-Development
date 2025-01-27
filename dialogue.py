import pygame
from settings import *

class Dialogue_Menu:
    def __init__(self, toggle_dialogue_menu):
        
        # general setup
        self.toggle_dialogue_menu = toggle_dialogue_menu
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font('./font/LycheeSoda.ttf', 30)

        self.message = "Hello"
        self.input_text = ""    # Get player input
        
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

    def input(self, events, get_response):
        for event in events:
            if event.type == pygame.KEYDOWN:  
                # Exit dialogue menu
                if event.key == pygame.K_ESCAPE: 
                    self.toggle_dialogue_menu()
                # Remove the last character from the input text
                elif event.key == pygame.K_BACKSPACE: 
                    self.input_text = self.input_text[:-1]
                # Submit user input
                elif event.key == pygame.K_RETURN:      
                    print(f'You: {self.input_text}')
                    self.message = get_response(self.input_text)
                    print(f'NPC: {self.message}')
                    self.input_text = ""
                # Add the Unicode character of the key pressed
                else:
                    self.input_text += event.unicode
        
    def update(self, events, get_response):
        self.input(events, get_response)
        self.draw_chatbox()
        self.draw_input_box()