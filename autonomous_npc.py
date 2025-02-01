import pygame
from settings import *
from support import *
from timer import Timer
from pytmx.util_pygame import load_pygame
from pathfinding import find_path

from langchain.tools.base import StructuredTool
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import threading

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

class Autonomous_NPC(pygame.sprite.Sprite):
    def __init__(self, pos, group, collision_sprites
                 #, , tree_sprites, interaction_sprites, soil_layer, toggle_shop, toggle_dialogue
                ):
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
        self.stepx = 0
        self.stepy = 0
        
        # npc set up
        self.npc_setup()
        
        # movement attributes
        self.direction = pygame.math.Vector2()
        self.pos = pygame.math.Vector2(self.rect.center)
        self.speed = 200
        
        # collision
        self.hitbox = self.rect.copy().inflate((-126,-70))
        self.collision_sprites = collision_sprites
        
        # timers
        self.timers =  {
            'tool use': Timer(1000, self.use_tool),
            'tool switch': Timer(200),
            'seed use': Timer(1000, self.use_seed),
            'seed switch': Timer(200)
        }
        
        # tools
        self.tools = ['hoe', 'axe', 'water']
        self.tool_index = 0
        self.selected_tool = self.tools[self.tool_index]
        
        # seeds
        self.seeds = ['corn', 'tomato']
        self.seed_index = 0
        self.selected_seed = self.seeds[self.seed_index]
        
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
        # self.tree_sprites = tree_sprites
        # self.interaction_sprites = interaction_sprites
        # self.sleep = False
        # self.soil_layer = soil_layer
        # self.toggle_shop = toggle_shop
        # self.toggle_dialogue = toggle_dialogue
    
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
    
    def use_tool(self):
        if self.selected_tool == 'hoe':
            self.soil_layer.get_hit(self.target_pos)
        
        if self.selected_tool == 'axe':
            for tree in self.tree_sprites.sprites():
                if tree.rect.collidepoint(self.target_pos):
                    tree.damage()
        
        if self.selected_tool == 'water':
            self.soil_layer.water(self.target_pos)
    
    def get_target_pos(self):

        self.target_pos = self.rect.center + PLAYER_TOOL_OFFSET[self.status.split('_')[0]]
    
    def use_seed(self):
        
        if self.seed_inventory[self.selected_seed] > 0:
            self.soil_layer.plant_seed(self.target_pos, self.selected_seed)
            self.seed_inventory[self.selected_seed] -= 1
    
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
    
    def create_collision_grid(self):
        ground = pygame.image.load('./graphics/world/ground.png')
        h_tiles, v_tiles = ground.get_width() // TILE_SIZE, ground.get_height() // TILE_SIZE
        
        self.grid = [[[] for col in range(h_tiles)] for row in range(v_tiles)]
        for x, y, _ in load_pygame('./data/map.tmx').get_layer_by_name('Collision').tiles():
            self.grid[y][x].append('C')
    
    def move_to(self, endx, endy):
        """Invoke this tool Asynchronously.
        Make the character to end position with x and y coordinate in a 2D vector space"""
        print("move to tool is used")
        self.path = find_path(self.grid, start={'x': self.pos.x, 'y': self.pos.y}, end={'x': endx, 'y': endy})
        self.update_steps()
        print(self.stepx, self.stepy)
        while True:
            if self.stepx == 0 and self.stepy == 0:
                break
        print("tools completed successfully")
        
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
        # print(self.stepx, self.stepy, self.pos.x, self.pos.y)
        if self.stepx > 0:
            move_x = self.speed * dt * self.direction.x
            self.pos.x = int(self.pos.x + move_x)
            self.hitbox.centerx = round(self.pos.x)
            self.rect.centerx = self.hitbox.centerx
            self.collision('horizontal')
            
            self.stepx -= abs(move_x)
            if self.stepx < 0: 
                self.stepx = 0
                self.direction.x = 0

        if self.stepy > 0:
            move_y = self.speed * dt * self.direction.y
            self.pos.y = int(self.pos.y + move_y)
            self.hitbox.centery = round(self.pos.y)
            self.rect.centery = self.hitbox.centery
            self.collision('vertical')
            
            self.stepy -= abs(move_y)
            if self.stepy < 0: 
                self.stepy = 0
                self.direction.y = 0
    
    def npc_setup(self):      
        llm = ChatOpenAI(model="gpt-4o-mini")
        self.agent = create_react_agent(llm, tools=[StructuredTool.from_function(self.move_to)])
        self.conversation_history = []
        
    def scheduled_input(self, query):
        self.messages = [HumanMessage(query)]
        print(query)
        result = self.agent.invoke(
            {"messages": [HumanMessage(query)]},
            {"recursion_limit": 10}
        )
        print(result)
    
    def get_input(self, query, delay=1.0):
        """Asychronous Feature: Schedules the get_input() function using a timer."""
        timer = threading.Timer(delay, self.scheduled_input, args=[query])
        timer.start()
    
    def update(self, dt):
        self.get_status()
        self.update_steps()
        self.move(dt)
        self.animate(dt)
        