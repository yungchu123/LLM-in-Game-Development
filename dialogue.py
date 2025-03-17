import pygame
import pyperclip
import re, threading
from quest import QuestStatus
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
        
        # box dimensions for input box
        self.BOX_X = CHATBOX_MARGIN
        self.BOX_Y = SCREEN_HEIGHT - INPUT_BOX_HEIGHT - CHATBOX_MARGIN
        self.BOX_WIDTH = SCREEN_WIDTH - 2 * CHATBOX_MARGIN
        self.BOX_HEIGHT = INPUT_BOX_HEIGHT
        
        self.quest_active = False
        self.question_active = False
        
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
        if self.npc:
            # Wrap text to fit inside the chatbox
            wrapped_text = self.wrap_text(f"{self.npc.npc_attributes['name']}: {self.message}", chatbox_rect.width - 40)
            
            # Render each line inside the chatbox
            y_offset = chatbox_rect.y + 20  # Start position for text inside box
            for line in wrapped_text:
                npc_surface = self.font.render(line, True, WHITE)
                self.display_surface.blit(npc_surface, (chatbox_rect.x + 20, y_offset))
                y_offset += self.font.get_height() + 5  # Space between lines

    def draw_input_box(self):
        """Draw the player input box."""
        color = WHITE 
        input_box_rect = pygame.Rect(self.BOX_X, self.BOX_Y, self.BOX_WIDTH, self.BOX_HEIGHT)
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

    def draw_progress_box(self):
        # Draw background box
        progress_box_rect = pygame.Rect(self.BOX_X, self.BOX_Y, self.BOX_WIDTH, self.BOX_HEIGHT)
        pygame.draw.rect(self.display_surface, GREY, progress_box_rect, border_radius=10)
        pygame.draw.rect(self.display_surface, BLACK, progress_box_rect, width=3, border_radius=10)
        
        progress = self.npc.quest.progress
        target = self.npc.quest.target_quantity
        filled_width = (progress / target) * self.BOX_WIDTH if target > 0 else 0
        
        # Draw progress box
        if progress > 0:
            pygame.draw.rect(self.display_surface, GREEN, (self.BOX_X, self.BOX_Y, filled_width, self.BOX_HEIGHT), border_radius=5)
            
        # Render progress text
        progress_text = self.font.render(f"{progress} / {target}", True, BLACK)
        text_x = self.BOX_X + self.BOX_WIDTH // 2 - progress_text.get_width() // 2
        text_y = self.BOX_Y + self.BOX_HEIGHT // 2 - progress_text.get_height() // 2
        self.display_surface.blit(progress_text, (text_x, text_y))

    def draw_claim_reward_box(self):   
        # Draw background box
        self.claim_reward_box_rect = pygame.Rect(self.BOX_X, self.BOX_Y, self.BOX_WIDTH, self.BOX_HEIGHT)
        pygame.draw.rect(self.display_surface, GREEN, self.claim_reward_box_rect, border_radius=10)
        pygame.draw.rect(self.display_surface, BLACK, self.claim_reward_box_rect, width=3, border_radius=10)
        
        # Render text
        text = self.font.render("Claim reward", True, BLACK)
        text_x = self.BOX_X + self.BOX_WIDTH // 2 - text.get_width() // 2
        text_y = self.BOX_Y + self.BOX_HEIGHT // 2 - text.get_height() // 2
        self.display_surface.blit(text, (text_x, text_y))

    def draw_buttons(self):
        # Define button rects
        self.accept_button_rect = pygame.Rect(self.BOX_X, self.BOX_Y, self.BOX_WIDTH // 2, self.BOX_HEIGHT)
        self.decline_button_rect = pygame.Rect(self.BOX_X + self.BOX_WIDTH // 2, self.BOX_Y, self.BOX_WIDTH // 2, self.BOX_HEIGHT)
        
        # Draw Accept Button
        pygame.draw.rect(self.display_surface, GREEN, self.accept_button_rect, border_radius=10)
        pygame.draw.rect(self.display_surface, BLACK, self.accept_button_rect, width=3, border_radius=10)

        # Draw Decline Button
        pygame.draw.rect(self.display_surface, RED, self.decline_button_rect, border_radius=10)
        pygame.draw.rect(self.display_surface, BLACK, self.decline_button_rect, width=3, border_radius=10)

        # Button Text
        accept_text = self.font.render("Accept", True, WHITE)
        decline_text = self.font.render("Decline", True, WHITE)
        
        # Center text inside buttons
        self.display_surface.blit(
            accept_text,
            (self.accept_button_rect.centerx - accept_text.get_width() // 2, self.accept_button_rect.centery - accept_text.get_height() // 2),
        )
        self.display_surface.blit(
            decline_text,
            (self.decline_button_rect.centerx - decline_text.get_width() // 2, self.decline_button_rect.centery - decline_text.get_height() // 2),
        )
    
    def draw_question_options(self):
        # Define button properties
        num_buttons = len(self.npc.question.options)  # Get number of options
        button_width = self.BOX_WIDTH // num_buttons  # Divide available space
        button_height = self.BOX_HEIGHT
        button_y = self.BOX_Y
        
        self.button_rects = []  # Store button rects for event handling
        
        for i, option in enumerate(self.npc.question.options):
            # Calculate button position
            button_x = self.BOX_X + i * button_width
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            self.button_rects.append(button_rect)  # Store rect
            
            # Draw button
            btn_color = GREY
            if i == self.npc.question.selected != -1:
                btn_color = GREEN if self.npc.question.status == "correct" else RED
            
            pygame.draw.rect(self.display_surface, btn_color, button_rect, border_radius=10)
            pygame.draw.rect(self.display_surface, WHITE, button_rect, width=3, border_radius=10)
            
            # Render button text
            option_text = self.font.render(option, True, WHITE)
            
            # Center text inside button
            self.display_surface.blit(
                option_text,
                (button_rect.centerx - option_text.get_width() // 2, button_rect.centery - option_text.get_height() // 2),
            )

    def input(self, events):
        for event in events:
            # Exit dialogue menu
            if event.type == pygame.KEYDOWN:  
                if event.key == pygame.K_ESCAPE: 
                    self.close_npc_chat()
            
        if self.question_active and self.npc_has_question():
            self.handle_question_input(events)
        elif self.quest_active and self.npc_has_quest():
            self.handle_event_input(events)
        else:
            self.handle_text_input(events)

    def handle_question_input(self, events):
        if self.npc.question.status != "not attempted":
            return
        
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, button_rect in enumerate(self.button_rects):
                    if button_rect.collidepoint(event.pos):
                        if self.npc.question.check_answer(i, self.player):
                            self.message = f"Correct! {self.npc.question.explanation}"
                        else:
                            self.message = f"Incorrect. {self.npc.question.explanation}"
    
    def handle_text_input(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                # Remove the last character from the input text
                if event.key == pygame.K_BACKSPACE: 
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
                            self.npc.get_user_input(user_message)
                        self.close_npc_chat()
                        return
                    self.npc.get_user_input(self.input_text)
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
    
    def handle_event_input(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.npc.quest.status == QuestStatus.NOT_STARTED:
                    if self.accept_button_rect.collidepoint(event.pos):
                        self.npc.assign_quest_to_player(self.player)
                        self.close_npc_chat()
                    elif self.decline_button_rect.collidepoint(event.pos):
                        self.close_npc_chat()
                elif self.npc.quest.status == QuestStatus.COMPLETED:
                    if self.claim_reward_box_rect.collidepoint(event.pos):
                        self.npc.quest.grant_reward(self.player)
                        self.npc.quest = None       # Remove quest from NPC here for simplicity
                        self.message = ""           # Remove quest name from message
                        self.close_npc_chat()
        
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

    def start_npc_chat(self, player, npc_name, quest = False, question = False):
        if not self.can_open_chat:
            return
        self.npc = self.get_npc_by_name(npc_name)
        self.player = player
        
        # Check if have quest
        if question and self.npc_has_question():
            self.question_active = True
            self.message = self.npc.question.question_text
            self.option_colors = [GREY, GREY, GREY, GREY]
        elif quest and self.npc_has_quest():
            self.quest_active = True
            self.message = self.npc.quest.description
            
        self.active = True
    
    def close_npc_chat(self):
        self.active = False
        self.quest_active = False
        self.question_active = False
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
    
    def npc_has_quest(self):
        return self.npc.quest != None
    
    def npc_has_question(self):
        return self.npc.question != None
    
    def update(self, events):
        self.input(events)
        if self.question_active and self.npc_has_question():
            self.draw_question_options()
        elif self.quest_active and self.npc_has_quest():
            self.message = self.npc.quest.description   # display quest description
            if self.npc.quest.status == QuestStatus.NOT_STARTED:
                self.draw_buttons()
            elif self.npc.quest.status == QuestStatus.IN_PROGRESS:
                self.draw_progress_box()
            elif self.npc.quest.status == QuestStatus.COMPLETED:
                self.draw_claim_reward_box()
        else:
            self.message = self.npc.dialogue_message    # display dialogue message
            self.draw_input_box()
            
        if self.message:
            self.draw_chatbox()