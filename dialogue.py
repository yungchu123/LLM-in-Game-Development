import pygame
import pyperclip
import re, threading
from quest import QuestStatus
from settings import *

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from openai import OpenAI

class Dialogue_Menu:
    def __init__(self, get_npc_by_name, set_is_buffering):
        
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
        
        self.set_is_buffering = set_is_buffering
        
        # box dimensions for input box
        self.BOX_X = CHATBOX_MARGIN
        self.BOX_Y = SCREEN_HEIGHT - INPUT_BOX_HEIGHT - CHATBOX_MARGIN
        self.BOX_WIDTH = SCREEN_WIDTH - 2 * CHATBOX_MARGIN
        self.BOX_HEIGHT = INPUT_BOX_HEIGHT
        
        self.quest_active = False
        self.question_active = False
        
        # Audio Generation
        self.client = OpenAI()
        self.text_sound = None
        self.text_channel = None
        
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
                
            # Display quest rewards if have quest
            if self.quest_active and self.npc_has_quest():
                rewards = self.npc.quest.rewards
                rewards_str = ", ".join(f"{k}: {v}" for reward in rewards for k, v in reward.items())
                npc_surface = self.font.render(f"Rewards: {rewards_str}", True, YELLOW)
                self.display_surface.blit(npc_surface, (chatbox_rect.x + 20, y_offset))

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
        self.claim_reward_box_rect = self.draw_button(
            x=self.BOX_X, 
            y=self.BOX_Y, 
            width=self.BOX_WIDTH, 
            height=self.BOX_HEIGHT,
            text="Claim reward", 
            border_radius=10, 
            background_color=GREEN, 
            border_color=BLACK, 
            text_color=BLACK)

    def draw_accept_decline_box(self):
        self.accept_button_rect = self.draw_button(
            x=self.BOX_X, 
            y=self.BOX_Y, 
            width=self.BOX_WIDTH // 2, 
            height=self.BOX_HEIGHT,
            text="Accept", 
            border_radius=10, 
            background_color=GREEN, 
            border_color=BLACK, 
            text_color=WHITE)
        
        self.decline_button_rect = self.draw_button(
            x=self.BOX_X + self.BOX_WIDTH // 2, 
            y=self.BOX_Y, 
            width=self.BOX_WIDTH // 2, 
            height=self.BOX_HEIGHT,
            text="Decline", 
            border_radius=10, 
            background_color=RED, 
            border_color=BLACK, 
            text_color=WHITE)
    
    def draw_question_options(self):
        # Define button properties
        num_columns = 2  # Two options per row
        num_rows = 2  # Two rows
        
        button_width = self.BOX_WIDTH // num_columns # Divide available space
        button_height = (SCREEN_HEIGHT-self.BOX_Y) // num_rows
        button_y = self.BOX_Y
        
        self.button_rects = []  # Store button rects for event handling
        
        for i, option in enumerate(self.npc.question.options):
            row = i // num_columns  
            col = i % num_columns
            
            button_x = self.BOX_X + col * button_width  # Position based on column
            button_y = self.BOX_Y + row * button_height  
            
            btn_color = GREY
            
            # an option has been selected by player
            if i == self.npc.question.selected:
                btn_color = GREEN if self.npc.question.status == "correct" else RED
                
            # show correct option if player chose wrong
            if self.npc.question.selected != -1 and str(self.npc.question.options[i]).strip().lower() == str(self.npc.question.correct_answer).strip().lower():
                btn_color = GREEN
            
            # hide options if player unlock fifty fifty
            if self.npc.question.fifty_fifty_unlocked and i in self.npc.question.removed_options:
                option = ""
            
            button_rect = self.draw_button(
                x=button_x, 
                y=button_y, 
                width=button_width, 
                height=button_height,
                text=option, 
                border_radius=10, 
                background_color=btn_color, 
                border_color=WHITE, 
                text_color=WHITE)
            
            self.button_rects.append(button_rect)  # Store rect
        
        # display hint if player unlock hint
        if self.npc.question.hint_unlocked:
            self.draw_button(
                x=CHATBOX_MARGIN,
                y=30,
                width=SCREEN_WIDTH - 2 * CHATBOX_MARGIN,
                height=60,
                text=self.npc.question.hint,
                border_radius=10,
                background_color=WHITE,
                border_color=BLACK,
                text_color=BLACK)
        
        # Draw Hint Button
        self.hint_button_rect = self.draw_button(
            x=CHATBOX_MARGIN, 
            y=SCREEN_HEIGHT - CHATBOX_HEIGHT - CHATBOX_MARGIN - INPUT_BOX_HEIGHT - 80, 
            width=180, 
            height=60,
            text="Hint (-50)", 
            border_radius=10, 
            background_color=WHITE if not self.npc.question.hint_unlocked else GREEN, 
            border_color=BLACK, 
            text_color=BLACK)
        
        # Draw 50/50 Button
        self.fifty_fifty_button_rect = self.draw_button(
            x=CHATBOX_MARGIN + 220, 
            y=SCREEN_HEIGHT - CHATBOX_HEIGHT - CHATBOX_MARGIN - INPUT_BOX_HEIGHT - 80, 
            width=180, 
            height=60,
            text="50/50 (-100)", 
            border_radius=10, 
            background_color=WHITE if not self.npc.question.fifty_fifty_unlocked else GREEN, 
            border_color=BLACK, 
            text_color=BLACK)
        
        # Display Gold
        money_text = self.font.render(f'Money: {self.player.money}', True, BLACK)
        self.display_surface.blit(money_text, (CHATBOX_MARGIN, SCREEN_HEIGHT - CHATBOX_HEIGHT - CHATBOX_MARGIN - INPUT_BOX_HEIGHT - 110))
    
    def draw_info_box(self):
        self.draw_button(
            x=30,
            y=30, 
            width=180, 
            height=60,
            text="[ESC] Exit", 
            border_radius=10, 
            background_color=(200, 200, 200), 
            border_color=(200, 200, 200), 
            text_color=(120, 120, 120))
    
    def draw_button(self, x, y, width, height, text, border_radius, background_color, border_color, text_color):
        button_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.display_surface, background_color, button_rect, border_radius=border_radius)
        pygame.draw.rect(self.display_surface, border_color, button_rect, width=3, border_radius=border_radius)
        button_text = self.font.render(text, True, text_color)
        self.display_surface.blit(
            button_text,
            (button_rect.centerx - button_text.get_width() // 2, button_rect.centery - button_text.get_height() // 2),  # Center text
        )
        
        return button_rect

    def update_message(self, message):
        self.message = message
        
        if message == "":
            return
        
        self.set_is_buffering(True)
        timer = threading.Timer(1, self.generate_audio, args=['npc_dialogue.mp3', message])
        timer.start()

    def generate_audio(self, filename, message): 
        response = self.client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=self.npc.npc_attributes['voice'],
            input=message
        )
        response.stream_to_file(filename)
        
        self.set_is_buffering(False)
        self.play_audio('npc_dialogue.mp3')

    def play_audio(self, filename):
        # Stop existing audio from playing
        self.stop_audio()
        self.text_sound = pygame.mixer.Sound(filename)
        self.text_channel = self.text_sound.play()
    
    def stop_audio(self):
        if self.text_channel and self.text_channel.get_busy():
            self.text_channel.stop()

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
                        # disable options from fifty
                        if self.npc.question.fifty_fifty_unlocked:
                            if i in self.npc.question.removed_options:
                                return
                        if self.npc.question.check_answer(i, self.player):
                            self.update_message(f"Correct! {self.npc.question.explanation}")
                        else:
                            self.update_message(f"Incorrect. {self.npc.question.explanation}")
                if self.hint_button_rect.collidepoint(event.pos):
                    self.npc.question.get_hint(self.player)
                elif self.fifty_fifty_button_rect.collidepoint(event.pos):
                    self.npc.question.get_fifty_fifty(self.player)
    
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
            # self.message = self.npc.question.question_text
            self.update_message(self.npc.question.question_text)
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
        self.stop_audio()
    
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
        self.draw_info_box()
        if self.question_active and self.npc_has_question():
            self.draw_question_options()
        elif self.quest_active and self.npc_has_quest():
            self.message = self.npc.quest.description   # display quest description
            if self.npc.quest.status == QuestStatus.NOT_STARTED:
                self.draw_accept_decline_box()
            elif self.npc.quest.status == QuestStatus.IN_PROGRESS:
                self.draw_progress_box()
            elif self.npc.quest.status == QuestStatus.COMPLETED:
                self.draw_claim_reward_box()
        else:
            if self.message != self.npc.dialogue_message:
                self.update_message(self.npc.dialogue_message)    # display dialogue message
            self.draw_input_box()
            
        if self.message:
            self.draw_chatbox()