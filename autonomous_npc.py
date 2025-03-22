import pygame
from settings import *
from support import *
from timer import Timer
from sprites import TextSprite, Interaction, QuestStatusSprite, QuestionMarkSprite
from quest import TalkQuest, CollectQuest, QuestionQuest, QuestStatus
from question import Question
from system_message_template import CONVERSATIONAL_ROLE_TEMPLATE, ASSISTANT_ROLE_TEMPLATE, QUESTIONER_ROLE_TEMPLATE
from pytmx.util_pygame import load_pygame
from pathfinding import find_path
import json, configparser

from langchain.prompts import PromptTemplate
from langchain.tools.base import StructuredTool
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import threading

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

class Autonomous_NPC(pygame.sprite.Sprite):
    def __init__(self, pos, attributes, group, collision_sprites, tree_sprites, interaction_sprites, soil_layer, get_time, get_weather, get_location, get_locations_with_topic, get_player_level):
        self.group = group
        super().__init__(group)

        self.import_assets()
        self.status = 'down_idle' # Initial animation image
        self.frame_index = 0

        # general setup (same as player)
        self.image = self.animations[self.status][self.frame_index]
        self.rect = self.image.get_rect(center = pos)
        self.z = LAYERS['main']

        # handle npc movements
        self.create_collision_grid()
        self.path = []
        self.stepx = 0         # X distance from destination 
        self.stepy = 0         # Y distance from destination 
        
        # movement attributes
        self.direction = pygame.math.Vector2()
        self.pos = pygame.math.Vector2(self.rect.center)
        self.speed = 200
        
        # npc set up
        self.npc_attributes = attributes
        self.name_text = TextSprite(self.pos, group, BLUE, self.npc_attributes['name'])
        self.npc_setup()
        
        # collision
        self.hitbox = self.rect.copy().inflate((-126,-70))
        self.collision_sprites = collision_sprites
        
        # timers
        self.timers =  {
            'tool use': Timer(1000),
            'seed use': Timer(1000),
            'generate question': Timer(10000, self.llm_generate_question),
            'generate quest': Timer(10000, self.llm_generate_quest)
        }
         
        # inventory
        self.item_inventory = {
            'wood':   0,
            'apple':  0,
            'corn':   0,
            'tomato': 0
        }
        self.seed_inventory = {
            'corn':   5,
            'tomato': 5
        }
        self.money = 200
        
        # interaction
        self.tree_sprites = tree_sprites
        self.interaction_sprites = interaction_sprites
        self.sleep = False
        self.soil_layer = soil_layer
        self.dialogue_message = ""      # Message for player
        
        self.interaction_sprite = Interaction(
                                        (self.rect.x,self.rect.y), (self.rect.width, self.rect.height), self.interaction_sprites, 
                                        {"name": "NPC", "npc_name": self.npc_attributes['name']}, 
                                        f"[N] Talk to {self.npc_attributes['name']}")
        
        # Question
        self.question = None
        self.generating_question = False  # Flag to indicate generation is in progress
        self.question_sprite = None
        
        # Quest
        self.quest = None
        self.quest_status_sprite = None
        self.generating_quest = None
        self.get_locations_with_topic = get_locations_with_topic
        self.get_player_level = get_player_level        
        # if self.npc_attributes['name'] == "Alira Windell":
        #     # quest = CollectQuest(self.npc_attributes['name'], "hoe", "tool", [{"money": 100}, {"experience": 100}, {"name": "corn", "type": "resource", "quantity": 5}], 1)
        #     quest = QuestionQuest(
        #         npc_name = self.npc_attributes['name'],
        #         rewards = [{"money": 100}, {"experience": 100}, {"name": "corn", "type": "resource", "quantity": 5}], 
        #         target_quantity = 1, 
        #         question_topic = None)
        #     self.assign_quest(quest)
        # else:
        #     quest = CollectQuest(self.npc_attributes['name'], "apple", "resource", [{"money": 100}, {"experience": 15}, {"name": "hoe", "type": "tool", "quantity": 1}], 1)
        #     self.assign_quest(quest)
        
        # Prompt template
        self.get_time = get_time
        self.get_weather = get_weather
        self.get_location = get_location                # for npc to generate location-specific question
        self.prompt_template = PromptTemplate(
            input_variables=["query"],
            template=f"""
Current time: {self.get_time()}
Current weather: {self.get_weather()}
                
A player has come to you. Here is his prompt: {{query}}.
                
Rules:
- Limit to 75 words
- Do not use bullet points or markdown annotations.            

What is your response?
            """
        )
    
    def __str__(self):
        return f"NPC Name: {self.npc_attributes['name']}"
    
    def import_assets(self):
        self.animations = {'up': [],'down': [],'left': [],'right': [],
                    'right_idle':[],'left_idle':[],'up_idle':[],'down_idle':[],
                    'right_hoe':[],'left_hoe':[],'up_hoe':[],'down_hoe':[],
                    'right_axe':[],'left_axe':[],'up_axe':[],'down_axe':[],
                    'right_water':[],'left_water':[],'up_water':[],'down_water':[]}

        # Import image surface into animations dict
        for animation in self.animations.keys():
            full_path = './graphics/character/' + animation
            self.animations[animation] = import_folder(full_path)
    
    def get_target_pos(self):

        self.target_pos = self.rect.center + PLAYER_TOOL_OFFSET[self.status.split('_')[0]]
    
    def collision(self, direction):
        for sprite in self.collision_sprites.sprites():
            if hasattr(sprite, 'hitbox'):
                if sprite.hitbox.colliderect(self.hitbox):
                    if direction == 'horizontal':
                        if self.direction.x > 0: # moving right
                            self.hitbox.right = sprite.hitbox.left
                        if self.direction.x < 0: # moving left
                            self.hitbox.left = sprite.hitbox.right
                        self.rect.centerx = self.hitbox.centerx
                        self.pos.x = self.hitbox.centerx

                    if direction == 'vertical':
                        if self.direction.y > 0: # moving down
                            self.hitbox.bottom = sprite.hitbox.top
                        if self.direction.y < 0: # moving up
                            self.hitbox.top = sprite.hitbox.bottom
                        self.rect.centery = self.hitbox.centery
                        self.pos.y = self.hitbox.centery  
    
    def animate(self, dt):
        # Two key issues to note:
        # 1. frame_index will be floating as it uses delta time
        # 2. frame_index will keep growing
        self.frame_index += 4 * dt
        if self.frame_index >= len(self.animations[self.status]):
            self.frame_index = 0

        self.image = self.animations[self.status][int(self.frame_index)]
    
    def get_status(self):
        # if the player is not moving
        if self.direction.magnitude() == 0:
            self.status = self.status.split('_')[0] + '_idle'
        
        # tool use
        if self.timers['tool use'].active:
            self.status = self.status.split('_')[0] + '_' + self.selected_tool
    
    def update_timers(self):
        for timer in self.timers.values():
            timer.update()
    
    def create_collision_grid(self):
        # Use for calculating path for movement
        tmx_data = load_pygame('./data/map.tmx')
        h_tiles, v_tiles = tmx_data.width, tmx_data.height
        
        self.grid = [[[] for _ in range(h_tiles)] for _ in range(v_tiles)]
        for x, y, _ in load_pygame('./data/map.tmx').get_layer_by_name('Collision').tiles():
            self.grid[y][x].append('C')
    
    def assign_quest(self, quest):
        self.quest = quest
        
        if self.quest_status_sprite:
            self.quest_status_sprite.kill() # remove old sprite
            
        self.quest_status_sprite = QuestStatusSprite(self.pos, self.group, self.quest)
    
    def assign_quest_to_player(self, player):
        if self.quest.status == QuestStatus.NOT_STARTED:
            player.accept_quest(self.quest)
    
    def move_to(self, endx, endy):
        """
        Make the character to end position with x and y coordinate in a 2D vector space
        """
        self.path = find_path(self.grid, start={'x': self.pos.x, 'y': self.pos.y}, end={'x': endx, 'y': endy})
        # while True:
        #     if not len(self.path) and not self.stepx and not self.stepy:
        #         break
        duration = 500 * len(self.path)
        self.timer_wrapper(duration)
        return f"The current position is {self.pos.x}, {self.pos.y}"
    
    def use_tool(self, tool):
        """
        Use a tool. The tools can be 
        1. hoe (to cultivate a soil into farmable land)
        2. axe (to chop trees)
        3. water (to water a farmable land)
        """
        self.selected_tool = tool
        
        self.timers['tool use'].activate()
        
        if self.selected_tool == 'hoe':
            self.soil_layer.get_hit(self.target_pos)
            return "soil cultivated successfully"
        
        if self.selected_tool == 'axe':
            for tree in self.tree_sprites.sprites():
                if tree.rect.collidepoint(self.target_pos):
                    tree.damage()
        
        if self.selected_tool == 'water':
            self.soil_layer.water(self.target_pos)
            return "soil watered successfully"
    
    def use_seed(self, seed) -> str:
        """
        Plant a seed on a cultivated soil. The seeds can be 
        1. corn
        2. tomato
        """
        self.timers['seed use'].activate()
        
        if self.seed_inventory[seed] > 0:
            self.soil_layer.plant_seed(self.target_pos, seed)
            self.seed_inventory[seed] -= 1
            return f"{seed} seed is planted successfully"
        else:
            return f"not even {seed} seed in inventory"
    
    def generate_question(self, question_text: str, options: list, correct_answer: str, hint: str, explanation: str):
        """
        Generate a multiple-choice question for player to solve
        
        Args:
            question_text: The question to be asked.
            options: A list of 4 choices for multiple-choice questions. 
            correct_answer: The correct answer.
            hint: A hint to help the player.
            explanation: Step-by-step explanation of the answer.
        """
        topic = self.get_location(self.pos).topic
        print('------------------------------------------------------------------------------------------')
        print(f"Qn: {question_text}\nOptions: {options}\nAns: {correct_answer}\nTopic: {topic}\nHint: {hint}\nExplanation: {explanation}")
        print('------------------------------------------------------------------------------------------')
        self.question = Question(
            question_text=question_text,
            topic=topic,
            hint=hint,
            explanation=explanation,
            options=options,
            correct_answer=correct_answer  
        )
        self.messages.append(f"generated a question: {question_text}, {options}, {correct_answer}, {hint}, {explanation}")
        self.question_sprite = QuestionMarkSprite(self.pos, self.group)
        
        return "question generated successfully"
    
    def generate_quest(self, quantity: int, question_topic: str = None):
        """
        Generate a multiple-choice question for player to solve
        
        Args:
            quantity: Number of questions to solve
            question_topic: Topic of questions to solve
        """
        rewards = [{"experience": 8 * quantity}, {"money": 12 * quantity}]
        print('------------------------------------------------------------------------------------------')
        print(f"Quest Type: Question\nQuantity: {quantity}\nQuestion Topic: {question_topic}\nReward: {rewards}")
        print('------------------------------------------------------------------------------------------')
        quest = QuestionQuest(
            npc_name = self.npc_attributes['name'],
            rewards = rewards, 
            target_quantity = quantity, 
            question_topic = question_topic)
        self.assign_quest(quest)
        self.messages.append(f"generated a quest: {quantity}, {question_topic}")
        return "quest generated successfully"
    
    def timer_wrapper(self, duration):
        # Create delay in lang chain tools calling
        llm_timer = Timer(duration)
        llm_timer.activate()
        while llm_timer.active:
            llm_timer.update()
    
    def update_steps(self):
        if not self.path or self.stepx != 0 or self.stepy != 0:
            return
        endx, endy = self.path.pop(0)   # Get the next location in the path found
        startx, starty = self.pos.x, self.pos.y
        
        # Compute step distances
        self.stepx = abs(endx-startx)
        self.stepy = abs(endy-starty)
        
        # Determine movement direction
        self.direction.x = 1 if endx > startx else -1
        self.direction.y = 1 if endy > starty else -1
        
        if self.direction.y == 1:
            self.status = 'down'
        else:
            self.status = 'up'
        if startx - 10 <= endx <= startx + 10: # Give more animation time to vertical movement
            pass
        elif self.direction.x == 1:
            self.status = 'right'
        else:
            self.status = 'left'
    
    def move(self, dt):
        if self.stepx > 0:
            move_x = min(self.speed * dt, self.stepx) * self.direction.x
            self.pos.x = int(self.pos.x + move_x)
            self.hitbox.centerx = round(self.pos.x)
            self.rect.centerx = self.hitbox.centerx
            self.collision('horizontal')
            
            self.stepx -= abs(move_x)
            if self.stepx <= 0: 
                self.stepx = 0
                self.direction.x = 0

        if self.stepy > 0:
            move_y = min(self.speed * dt, self.stepy) * self.direction.y
            self.pos.y = int(self.pos.y + move_y)
            self.hitbox.centery = round(self.pos.y)
            self.rect.centery = self.hitbox.centery
            self.collision('vertical')
            
            self.stepy -= abs(move_y)
            if self.stepy <= 0: 
                self.stepy = 0
                self.direction.y = 0
        
        # Update Interaction Sprite around him
        self.interaction_sprite.rect.topleft = (self.rect.x, self.rect.y)
    
    def load_learning(self, filename="config.ini"):
        config = configparser.ConfigParser()
        config.read(filename)
        self.enable_context = config.getboolean("Learning", "ENABLE_CONTEXT")
        return dict(config["Learning"]) if "Learning" in config else {}
    
    def npc_setup(self):      
        llm = ChatOpenAI(model="gpt-4o-mini")
        
        system_message = self.get_system_message()
        self.messages = [SystemMessage(system_message)]
        tools = [
            StructuredTool.from_function(self.move_to), 
            StructuredTool.from_function(self.use_tool),
            StructuredTool.from_function(self.use_seed)]
        if self.npc_attributes.get('role', '') == "Questioner":
            tools.append(StructuredTool.from_function(self.generate_question))
        if self.npc_attributes.get('role', '') == "Quest":
            tools.append(StructuredTool.from_function(self.generate_quest))
        llm_with_tools = llm.bind_tools(tools, parallel_tool_calls=False)   # Run tool calling synchronously
        self.agent = create_react_agent(llm_with_tools, tools=tools)
    
    def get_system_message(self):
        learning = self.load_learning()
        role = self.npc_attributes.get('role', '')  # Safe access
        
        if role == "Assistant":
            with open("locations.json", "r") as file:  # Change filename if necessary
                locations = json.load(file)

            # Filter and format locations (ignoring empty descriptions)
            location_info = "\n".join(
                f"{i + 1}. {data['name']} - {data['description']}." +
                (f" (Unlocked at level {data['level_unlock']})" if "level_unlock" in data else "")
                for i, (_, data) in enumerate(locations.items()) if data["description"]
            )
            return ASSISTANT_ROLE_TEMPLATE.format(npc_attributes=self.npc_attributes, location_info=location_info)
        elif role == "Questioner":
            return QUESTIONER_ROLE_TEMPLATE.format(npc_attributes=self.npc_attributes, subject=learning['subject'], target_audience=learning['target_audience'])
        else:
            return CONVERSATIONAL_ROLE_TEMPLATE.format(npc_attributes=self.npc_attributes)
    
    def llm_generate_question(self):
        print("Generating a question ...")
        
        location = self.get_location(self.pos)
        
        context_instruction = ""
        if self.enable_context:
            context_instruction = f"""
Make context specific question
- Location: {location.name}
- Occuputation: {self.npc_attributes['occupation']}
- Phrase the question in first person perspective, using words like 'I' or 'me'.
            """
        
        prompt_template = PromptTemplate(
            input_variables=["query"],
            template=f"""
Generate a new question with a topic on {location.topic}

{{context_instruction}}

Keep the hint to one sentence.
Keep the explanation to not more than 70 words.
For each options, use only strings (NO objects) and keep the length of string up to 24
Do not use bullet points or markdown annotations.

Here is the past conversation history: {{conversation_history}}    
Try to make a new question
            """)
        
        formatted_query = prompt_template.format(conversation_history = self.messages, context_instruction=context_instruction)
 
        def execute_llm():
            result = self.agent.invoke(
                {"messages": formatted_query},
                {"recursion_limit": 10}
            )
            
            self.generating_question = False
        
        timer = threading.Timer(1, execute_llm)
        timer.start()
    
    def llm_generate_quest(self):
        print("Generating a quest ...")

        topics = "\n".join(f"{location.topic} unlocked at level {location.level_unlock}" for location in self.get_locations_with_topic())
        
        prompt_template = PromptTemplate(
            input_variables=["query"],
            template="""
Generate a new quest where player solve questions to complete it.
Choose number of questions between 2 to 10.

To generate a quest with topic, you have to ensure that player's level is at least the topic's level unlock.

Here are the topics:
{topics}

Here is the player's current level: {player_level}

Here is the past conversation history: {conversation_history}
Try to make a new quest with different topics and quantity.
            """)
        
        formatted_query = prompt_template.format(conversation_history = self.messages, topics = topics, player_level = self.get_player_level())
 
        def execute_llm():
            result = self.agent.invoke(
                {"messages": formatted_query},
                {"recursion_limit": 10}
            )
            
            self.generating_quest = False
        
        timer = threading.Timer(1, execute_llm)
        timer.start()
    
    def scheduled_input(self, query):
        formatted_query = self.prompt_template.format(query=query)
        self.messages.append(HumanMessage(content=formatted_query))

        result = self.agent.invoke(
            {"messages": self.messages},
            {"recursion_limit": 10}
        )
        
        for m in result['messages']:
            m.pretty_print()
        ai_response = result['messages'][-1].content
        self.dialogue_message = ai_response
        self.messages.append(ai_response)
    
    def get_user_input(self, query, delay=1.0):
        """Asychronous Feature: Schedules the get_input() function using a timer."""
        timer = threading.Timer(delay, self.scheduled_input, args=[query])
        timer.start()
    
    def update(self, dt):
        self.get_status()
        self.update_timers()
        self.update_steps()
        self.get_target_pos()
        
        self.move(dt)
        self.animate(dt)
        
        if self.npc_attributes.get('role', '') == "Questioner" and getattr(self.question, "status", None) != "not attempted" and not self.timers['generate question'].active and not self.generating_question:
            if self.question_sprite:
                self.question_sprite.kill()
            self.timers['generate question'].activate()
            self.generating_question = True
        
        if self.npc_attributes.get('role', '') == "Quest" and self.quest == None and not self.timers['generate quest'].active and not self.generating_quest:
            self.timers['generate quest'].activate()
            self.generating_quest = True

class NPC_Manager:
    def __init__(self, group, collision_sprites, tree_sprites, interaction_sprites, soil_layer, get_time, get_weather, get_location, get_locations_with_topic, get_player_level):
        self.npcs = pygame.sprite.Group()
        self.setup(group, collision_sprites, tree_sprites, interaction_sprites, soil_layer, get_time, get_weather, get_location, get_locations_with_topic, get_player_level)
    
    def setup(self, group, collision_sprites, tree_sprites, interaction_sprites, soil_layer, get_time, get_weather, get_location, get_locations_with_topic, get_player_level):    
        # Load NPC profiles from JSON
        with open("npc_profiles.json", "r") as file:
            npc_data = json.load(file)
        
        tmx_data = load_pygame('./data/map.tmx')
        
        for obj in tmx_data.get_layer_by_name('NPC'):
            if obj.type == 'NPC':
                if obj.name in npc_data:
                    npc = Autonomous_NPC((obj.x, obj.y), npc_data[obj.name], group, collision_sprites, tree_sprites, interaction_sprites, soil_layer, get_time, get_weather, get_location, get_locations_with_topic, get_player_level)
                    self.npcs.add(npc)
                else:
                    print("NPC not found in json data")
    
    def get_npc_by_name(self, npc_name):
        for npc in self.npcs:
            if npc.npc_attributes['name'] == npc_name:
                return npc
        return None