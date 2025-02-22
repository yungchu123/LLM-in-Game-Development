import pygame
from settings import *
from support import *
from timer import Timer
from sprites import TextSprite, ToolTipSprite
from quest import TalkQuest, CollectQuest
from level_system import LevelSystem

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, group, collision_sprites, tree_sprites, interaction_sprites, soil_layer, toggle_shop, is_shop_active, dialogue_menu, add_notification):
        super().__init__(group)

        self.import_assets()
        self.status = 'down_idle' # Initial animation image
        self.frame_index = 0

        # general setup
        self.image = self.animations[self.status][self.frame_index]
        self.rect = self.image.get_rect(center = pos)
        self.z = LAYERS['main']

        # movement attributes
        self.direction = pygame.math.Vector2()
        self.pos = pygame.math.Vector2(self.rect.center)
        self.speed = 200
        
        # name text setup
        self.name = "Player"
        self.name_text = TextSprite(self.pos, group, BLACK, self.name)
        
        # tool tip set up
        self.tooltip = ToolTipSprite(self, group)
        
        # collision
        self.hitbox = self.rect.copy().inflate((-126,-70))
        self.collision_sprites = collision_sprites
        
        # timers
        self.timers =  {
            'tool use': Timer(1000, self.use_tool),
            'seed use': Timer(1000, self.use_seed),
            'inventory switch': Timer(200),
            'interact': Timer(200)
        }
        
        # inventory
        self.inventory = [
            {"name": "hoe", "type": "tool", "quantity": 1},
            {"name": "axe", "type": "tool", "quantity": 1},
            {"name": "water", "type": "tool", "quantity": 1},
            {"name": "corn", "type": "seed", "quantity": 5},
            {"name": "tomato", "type": "seed", "quantity": 5},
            {"name": "wood", "type": "resource", "quantity": 0},
            {"name": "apple", "type": "resource", "quantity": 0},
            {"name": "corn", "type": "resource", "quantity": 0},
            {"name": "tomato", "type": "resource", "quantity": 0},
        ]
        
        self.inventory_index = 0
        self.selected_item = self.inventory[self.inventory_index]
        self.money = 200
        
        # interaction
        self.tree_sprites = tree_sprites
        self.interaction_sprites = interaction_sprites
        self.sleep = False
        self.soil_layer = soil_layer
        self.toggle_shop = toggle_shop
        self.is_shop_active = is_shop_active
        self.dialogue_menu = dialogue_menu
        self.add_notification = add_notification
        
        # Stats
        self.talked_to_npcs = {}    # NPCs the player has interacted with
        self.interacted_obj = {}
        
        # Quests
        self.quests = []
        self.completed_quests = []
        
        self.level_system = LevelSystem(add_notification=self.add_notification)

    def gain_experience(self, amount):
        """Wrapper to gain experience via the LevelSystem."""
        self.level_system.gain_experience(amount)

    def use_tool(self):
        # print(f"tool use: {self.selected_item['name']}")
        if self.selected_item['name'] == 'hoe':
            self.soil_layer.get_hit(self.target_pos)
        
        if self.selected_item['name'] == 'axe':
            for tree in self.tree_sprites.sprites():
                if tree.rect.collidepoint(self.target_pos):
                    tree.damage()
        
        if self.selected_item['name'] == 'water':
            self.soil_layer.water(self.target_pos)
    
    def get_target_pos(self):

        self.target_pos = self.rect.center + PLAYER_TOOL_OFFSET[self.status.split('_')[0]]
    
    def use_seed(self):
        # print(f"seed use: {self.selected_item['name']}")
        if self.selected_item['quantity'] > 0:
            self.soil_layer.plant_seed(self.target_pos, self.selected_item['name'])
            self.selected_item['quantity'] -= 1

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

    def animate(self, dt):
        # Two key issues to note:
        # 1. frame_index will be floating as it uses delta time
        # 2. frame_index will keep growing
        self.frame_index += 4 * dt
        if self.frame_index >= len(self.animations[self.status]):
            self.frame_index = 0

        self.image = self.animations[self.status][int(self.frame_index)]
        
    def input(self):
        if self.is_shop_active() or self.dialogue_menu.is_active():
            return
        
        keys = pygame.key.get_pressed()

        if not self.timers['tool use'].active:
            if keys[pygame.K_UP]:
                self.direction.y = -1
                self.status = 'up'
            elif keys[pygame.K_DOWN]:
                self.direction.y = 1
                self.status = 'down'
            else:
                self.direction.y = 0

            if keys[pygame.K_RIGHT]:
                self.direction.x = 1
                self.status = 'right'
            elif keys[pygame.K_LEFT]:
                self.direction.x = -1
                self.status = 'left'
            else:
                self.direction.x = 0
                                 
            # change inventory
            # Key note: Use timer to avoid registering event more than once with each key press
            if keys[pygame.K_q] and not self.timers['inventory switch'].active:
                self.timers['inventory switch'].activate()
                self.inventory_index = (self.inventory_index - 1) % len(self.inventory)
                self.selected_item = self.inventory[self.inventory_index]
            
            if keys[pygame.K_w] and not self.timers['inventory switch'].active:
                self.timers['inventory switch'].activate()
                self.inventory_index = (self.inventory_index + 1) % len(self.inventory)
                self.selected_item = self.inventory[self.inventory_index]
                
            # action (use seed or use tool)
            if keys[pygame.K_SPACE] and not self.timers['tool use'].active:
                type = self.selected_item['type']
                if type == 'tool':
                    self.timers['tool use'].activate()
                    self.direction = pygame.math.Vector2() # stop player from moving during tool use
                    self.frame_index = 0                   # play new animation
                elif type == 'seed':
                    self.timers['seed use'].activate()
                    self.direction = pygame.math.Vector2()
                    self.frame_index = 0   
            
            # if keys[pygame.K_RETURN]:
            #     self.dialogue_menu.start_npc_chat()
            
            # interact with interaction sprites
            if keys[pygame.K_n] and not self.timers['interact'].active:
                collided_interaction_sprites = [s for s in self.interaction_sprites if self.hitbox.colliderect(s.rect)]
                if collided_interaction_sprites:
                    if collided_interaction_sprites[0].prop['name'] == 'Trader':
                        self.toggle_shop()
                    if collided_interaction_sprites[0].prop['name'] == 'Bed':
                        self.status = 'left_idle'
                        self.sleep = True
                    if collided_interaction_sprites[0].prop['name'] == "NPC":
                        npc_name = collided_interaction_sprites[0].prop['npc_name']
                        if npc_name:
                            self.dialogue_menu.start_npc_chat(self, npc_name)
                            if npc_name not in self.talked_to_npcs:
                                self.talked_to_npcs[npc_name] = 0
                            self.talked_to_npcs[npc_name] += 1
                    else:
                        collided_interaction_sprites[0].func()
                    self.timers['interact'].activate()
                    
    
    def add_to_inventory(self, item_name, item_type, quantity=1):
        """
        Adds an item to the player's inventory. If the item already exists and is stackable, increase quantity.
        
        :param item_name: Name of the item to add (e.g., "corn").
        :param item_type: Type of the item (e.g., "seed", "tool").
        :param quantity: Amount to add (default = 1).
        """
        self.add_notification(f"{item_name} +{quantity}")
        for item in self.inventory:
            if item["name"] == item_name and item["type"] == item_type:
                if "quantity" in item:  # If item is stackable (like seeds)
                    item["quantity"] += quantity
                return  # Exit function if item is found and updated
        
        # If the item is new, add it to inventory
        new_item = {"name": item_name, "type": item_type}
        if item_type in ["seed", "resource"]:  # Stackable items
            new_item["quantity"] = quantity
        self.inventory.append(new_item)
    
    def add_money(self, quantity):
        self.money += quantity
        self.add_notification(f"money +{quantity}")
    
    def remove_from_inventory(self, item_name, item_type, quantity=1):
        """
        Removes an item or reduces its quantity in the inventory.
        
        :param item_name: Name of the item to remove.
        :param item_type: Type of the item (e.g., "seed", "tool").
        :param quantity: Amount to remove (default = 1).
        """
        for item in self.inventory:
            if item["name"] == item_name and item["type"] == item_type:
                if "quantity" in item:  # If item is stackable
                    item["quantity"] -= quantity
                return  # Exit after modifying the inventory
    
    def get_item(self, item_name, item_type):
        """
        Returns the first item in the inventory that matches the given name and type.

        :param item_name: Name of the item to search for.
        :param item_type: Type of the item to search for.
        :return: The matching item dictionary or None if not found.
        """
        for item in self.inventory:
            if item["name"] == item_name and item["type"] == item_type:
                return item  # Return the first match
        return None  # If no match is found
    
    def accept_quest(self, quest):
        quest.start_quest(self)
        self.quests.append(quest)
    
    def update_quests(self):
        for quest in self.quests:
            quest.update_progress(self)
    
    def get_status(self):
        # if the player is not moving
        if self.direction.magnitude() == 0:
            self.status = self.status.split('_')[0] + '_idle'
        
        # tool use
        if self.timers['tool use'].active:
            self.status = self.status.split('_')[0] + '_' + self.selected_item['name']

    def update_timers(self):
        for timer in self.timers.values():
            timer.update()

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

    def move(self,dt):

        # normalizing a vector
        # Rationale: so diagonal movement will have the same vector as horizontal and vertical movement
        if self.direction.magnitude() > 0:
            self.direction = self.direction.normalize()

        # horizontal movement
        self.pos.x += self.direction.x * self.speed * dt
        self.hitbox.centerx = round(self.pos.x)
        self.rect.centerx = self.hitbox.centerx
        self.collision('horizontal')

        # vertical movement
        self.pos.y += self.direction.y * self.speed * dt
        self.hitbox.centery = round(self.pos.y)
        self.rect.centery = self.hitbox.centery
        self.collision('vertical')
        
    def get_tool_tip(self):
        # Check for collision with interaction sprites. If yes, display tool tip
        collided_sprites = [s for s in self.interaction_sprites if self.hitbox.colliderect(s.rect)]
        if collided_sprites:
            self.tooltip.update_text(collided_sprites[0].tool_tip)
            self.tooltip.show()  
        else:
            self.tooltip.hide()  

    def update(self, dt):
        self.input()
        self.get_status()
        self.get_tool_tip()
        self.update_timers()
        self.get_target_pos()
        self.update_quests()
        
        self.move(dt)
        self.animate(dt)