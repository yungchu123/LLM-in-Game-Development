import pygame 
from settings import *
from player import Player
from overlay import Overlay
from sprites import Generic, Water, WildFlower, Tree, Interaction, Particle
from support import *
from random import randint
from pytmx.util_pygame import load_pygame
from transition import Transition
from soil import SoilLayer
from sky import Rain, Sky
from menu import Menu
from dialogue import Dialogue_Menu
from autonomous_npc import NPC_Manager
from timer import Timer
from grid import Grid
from announcer import Announcer
from notification import NotificationManager
from quest_menu import QuestMenu
from location import Location_Manager

class Level:
    def __init__(self):

        # get the display surface
        self.display_surface = pygame.display.get_surface()

        # sprite groups
        self.all_sprites = CameraGroup()                    # sprites to be drawn
        self.collision_sprites = pygame.sprite.Group()      # sprites with collision
        self.tree_sprites = pygame.sprite.Group()           # interaction with tree sprites
        self.interaction_sprites = pygame.sprite.Group()    # empty space for interactions
        self.location_sprites = pygame.sprite.Group()
  
        self.announcer = Announcer()
        self.notifications = NotificationManager()

        # sky
        self.rain = Rain(self.all_sprites)
        self.raining = False
        self.sky = Sky()

        self.soil_layer = SoilLayer(self.all_sprites)
        self.location = Location_Manager()
        self.guide_active = False
        self.setup()
        self.overlay = Overlay(self.player)
        self.transition = Transition(self.reset, self.player)
        self.quest_menu = QuestMenu(self.player)
        
        # shop
        self.menu = Menu(self.player, self.toggle_shop)
        self.shop_active = False

        
        # audio
        self.success_sound = pygame.mixer.Sound('./audio/success.wav')
        self.success_sound.set_volume(0.3)
        self.background_music = pygame.mixer.Sound('./audio/main_bg.mp3')
        self.background_music.play(loops = -1)
        self.current_bg_music = "main_bg.mp3"
        
        # Timer for npc
        self.npc_timer = Timer(500)
        
        self.grid = Grid(self.player, self.all_sprites, self.interaction_sprites, self.npc_manager.get_npc_by_name, self.announcer.start_event, self.location.get_locations)
        
        self.player_level = 1
        
        # Buffering animation
        self.buffering_animation = import_folder('./graphics/objects/buffering')
        self.buffering_frame_index = 0
        self.buffering_image = self.buffering_animation[self.buffering_frame_index]
        self.is_buffering = False
        

    def setup(self):
        tmx_data = load_pygame('./data/map.tmx')
        
        # Autonomous NPC
        self.npc_manager = NPC_Manager(
                                group = self.all_sprites, 
                                collision_sprites = self.collision_sprites,
                                tree_sprites = self.tree_sprites,
                                interaction_sprites = self.interaction_sprites,
                                soil_layer = self.soil_layer,
                                get_time = self.get_time,
                                get_weather = self.get_weather,
                                get_location = self.location.get_location,
                                get_locations_with_topic = self.location.get_locations_with_topic,
                                get_player_level = self.get_player_level,
                                set_is_buffering = self.set_is_buffering)
        
        # dialogue
        self.dialogue = Dialogue_Menu(get_npc_by_name = self.npc_manager.get_npc_by_name, set_is_buffering = self.set_is_buffering)
        
        # Player
        for obj in tmx_data.get_layer_by_name('Player'):
            if obj.name == 'Start':
                self.player = Player(
                    pos = (obj.x,obj.y), 
                    group = self.all_sprites, 
                    collision_sprites = self.collision_sprites,
                    tree_sprites = self.tree_sprites,
                    interaction_sprites = self.interaction_sprites,
                    location_sprites = self.location_sprites,
                    soil_layer = self.soil_layer,
                    toggle_shop = self.toggle_shop,
                    is_shop_active = self.is_shop_active,
                    dialogue_menu = self.dialogue,
                    add_notification = self.notifications.add_notification,
                    get_npc_by_name = self.npc_manager.get_npc_by_name)
            
            if obj.name == 'Bed':
                Interaction((obj.x,obj.y), (obj.width,obj.height), self.interaction_sprites, {"name": obj.name}, '[N] Sleep')
            
            if obj.name == 'Trader':
                Interaction((obj.x,obj.y), (obj.width,obj.height), self.interaction_sprites, {"name": obj.name}, '[N] Trade with Merchant')
            
            if obj.name == 'Guide':
                Interaction((obj.x,obj.y), (obj.width,obj.height), self.interaction_sprites, {"name": obj.name}, '[N] Open Guide', self.toggle_guide)
        
        # house 
        for layer in ['HouseFloor', 'HouseFurnitureBottom']:
            for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
                Generic((x * TILE_SIZE, y * TILE_SIZE), surf, self.all_sprites, LAYERS['house bottom'])

        for layer in ['HouseWalls', 'HouseFurnitureTop']:
            for x, y, surf in tmx_data.get_layer_by_name(layer).tiles():
                Generic((x * TILE_SIZE, y * TILE_SIZE), surf, self.all_sprites)
    
        # fence
        for x, y, surf in tmx_data.get_layer_by_name('Fence').tiles():
            Generic((x * TILE_SIZE,y * TILE_SIZE), surf, [self.all_sprites, self.collision_sprites])
    
        # water
        water_frames = import_folder('./graphics/water')
        for x, y, surf in tmx_data.get_layer_by_name('Water').tiles():
            Water((x * TILE_SIZE,y * TILE_SIZE), water_frames, self.all_sprites)
    
        # trees 
        for obj in tmx_data.get_layer_by_name('Trees'):
            Tree(
                pos = (obj.x, obj.y), 
                surf = obj.image, 
                groups = [self.all_sprites, self.collision_sprites, self.tree_sprites], 
                name = obj.name,
                player_add = self.player.add_to_inventory)

        # wildflowers 
        for obj in tmx_data.get_layer_by_name('Decoration'):
            WildFlower((obj.x, obj.y), obj.image, [self.all_sprites, self.collision_sprites])
    
        # collion tiles
        for x, y, surf in tmx_data.get_layer_by_name('Collision').tiles():
            Generic((x * TILE_SIZE, y * TILE_SIZE), pygame.Surface((TILE_SIZE, TILE_SIZE)), self.collision_sprites)
        
        # Ground
        for x, y, surf in tmx_data.get_layer_by_name('Ground').tiles():
            Generic((x * TILE_SIZE,y * TILE_SIZE), surf, self.all_sprites, LAYERS['ground'])
            
        # Water
        for x, y, surf in tmx_data.get_layer_by_name('Water').tiles():
            Generic((x * TILE_SIZE,y * TILE_SIZE), surf, self.all_sprites, LAYERS['water'])

        # Hills
        for x, y, surf in tmx_data.get_layer_by_name('Hills').tiles():
            Generic((x * TILE_SIZE,y * TILE_SIZE), surf, self.all_sprites, LAYERS['hills'])
        
        # Trader
        for obj in tmx_data.get_layer_by_name('NPC'):
            if obj.type == 'Trader':
                Generic((obj.x, obj.y), obj.image, self.all_sprites)

        # Rock
        for x, y, surf in tmx_data.get_layer_by_name('Rock').tiles():
            Generic((x * TILE_SIZE, y * TILE_SIZE), surf, [self.all_sprites, self.location_sprites, self.collision_sprites])
            Interaction((x * TILE_SIZE, y * TILE_SIZE), (TILE_SIZE, TILE_SIZE), [self.location_sprites, self.interaction_sprites], {"name": "Location"}, "Area Locked")

        # # Ground Sprite (Floor)
        # Generic(
        #     pos = (0,0),
        #     surf = pygame.image.load('./graphics/world/ground.png').convert_alpha(),
        #     groups = self.all_sprites,
        #     z = LAYERS['ground'])

    def toggle_shop(self):
        self.shop_active = not self.shop_active

    def toggle_guide(self):
        self.guide_active = not self.guide_active

    def is_shop_active(self):
        return self.shop_active

    def plant_collision(self):
        if self.soil_layer.plant_sprites:
            for plant in self.soil_layer.plant_sprites.sprites():
                if plant.harvestable and plant.rect.colliderect(self.player.hitbox):
                    self.player.add_to_inventory(plant.plant_type, "resource", 1)
                    plant.kill()
                    Particle(plant.rect.topleft, plant.image, self.all_sprites, z = LAYERS['main'])
                    self.soil_layer.grid[plant.rect.centery // TILE_SIZE][plant.rect.centerx // TILE_SIZE].remove('P')

    def get_time(self):
        return self.sky.get_time()
    
    def get_weather(self):
        return "raining" if self.raining else "sunny"

    def get_player_level(self):
        return self.player_level

    def set_bg_music(self, filename):
        self.background_music.stop()

        self.background_music = pygame.mixer.Sound(f'./audio/{filename}')

        self.background_music.play(loops = -1)

    def update_bg_music(self):
        location_name = self.player.location.name
     
        if location_name == "Whispering Woods":
            bg_music = "whispering_woods.mp3"
        elif location_name == "Golden Meadow":
            bg_music = "golden_meadow.mp3"
        else:
            bg_music = "main_bg.mp3"
            
        if self.current_bg_music == bg_music:
            return
        
        self.set_bg_music(bg_music)
        self.current_bg_music = bg_music # update previous state

    def draw_buffering(self):
        buffer_rect = self.buffering_image.get_rect(center=(80, 160))
        self.display_surface.blit(self.buffering_image, buffer_rect)

    def animate_buffering(self, dt):
        self.buffering_frame_index += 50 * dt
        if self.buffering_frame_index >= len(self.buffering_animation):
            self.buffering_frame_index = 0

        self.buffering_image = self.buffering_animation[int(self.buffering_frame_index)]

    def set_is_buffering(self, bool):
        self.is_buffering = bool

    def reset(self):
        # plants
        self.soil_layer.update_plants()
        
        # soil
        self.soil_layer.remove_water()      # remove soil water
        
        # weather
        self.raining = randint(0,10) > 7    # randomise rain effect

        # night to day transition
        self.sky.reset()

        # reset apples on the trees
        for tree in self.tree_sprites.sprites():
            for apple in tree.apple_sprites.sprites():
                apple.kill()
            tree.create_fruit()

    def run(self,dt,events):
        
        # drawing logic
        self.display_surface.fill('black')
        self.all_sprites.custom_draw(self.player)
        
        # updates
        if self.shop_active:
            self.menu.update()
        
        if self.guide_active:
            self.overlay.draw_guide()
        
        if self.dialogue.is_active():
            self.dialogue.update(events)
        else:
            # Show overlay only when dialogue is not opened
            self.overlay.update()
            self.quest_menu.draw()
            for event in events:
                self.quest_menu.handle_event(event)
        
        self.all_sprites.update(dt) # calls update() on all children
        self.plant_collision()      # harvest full-grown plant on collision
        
        # rain
        if self.raining:
            self.rain.update()
            self.soil_layer.water_all()
        
        # day to night transition
        # self.sky.display(dt)
        
        # player sleep transition
        if self.player.sleep:
            self.transition.play()
        
        self.announcer.update()
        self.notifications.update()
        
        self.location.check_player_location(self.player)
        self.grid.update()
        
        self.player_level = self.player.level_system.level
        
        self.update_bg_music()
        
        if self.is_buffering:
            self.draw_buffering()
            self.animate_buffering(dt)
        
        # Testing
        # keys = pygame.key.get_pressed()
        # if keys[pygame.K_f] and not self.npc_timer.active:
        #     self.grid.get_human_input('Generate a random event. Then create a quest')
        #     self.npc_timer.activate()
        # self.npc_timer.update()
        # keys = pygame.key.get_pressed()
        # if keys[pygame.K_f] and not self.npc_timer.active:
        #     self.autonomous_npc.get_input('move to the pos (1443, 1450). Then move to (1561,1315).') # original position is (1561,1772)
        #     self.npc_timer.activate()
        # if keys[pygame.K_g] and not self.npc_timer.active:
        #     self.autonomous_npc.get_input('move to the position (1761,1972)')    
        #     self.npc_timer.activate()
        # if keys[pygame.K_h] and not self.npc_timer.active:
        #     self.autonomous_npc.get_input('cultivate the land at (1761,1972). then water it, then plant a corn seed on it')    
        #     self.npc_timer.activate()
        # self.npc_timer.update()
        
class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.math.Vector2()
    
    def custom_draw(self, player):
        # Ensures player is always at the center of the screen
        self.offset.x = player.rect.centerx - SCREEN_WIDTH / 2
        self.offset.y = player.rect.centery - SCREEN_HEIGHT / 2
        
        for layer in LAYERS.values(): # Draw the sprites from the bottom layer first
            for sprite in sorted(self.sprites(), key= lambda sprite: sprite.rect.centery): # Fake 3D: Sprite at lower y-axis stand behind sprite at higher y-axis
                if sprite.z == layer:
                    offset_rect = sprite.rect.copy()
                    offset_rect.center -= self.offset
                    self.display_surface.blit(sprite.image, offset_rect)
                    
                    # anaytics
                    # if isinstance(sprite, Autonomous_NPC):
                    #     pygame.draw.rect(self.display_surface,'red',offset_rect,5)     
                    
                    # if isinstance(sprite, Player):
                    #     pygame.draw.rect(self.display_surface,'red',offset_rect,5)
                    #     hitbox_rect = player.hitbox.copy()
                    #     hitbox_rect.center = offset_rect.center
                    #     pygame.draw.rect(self.display_surface,'green',hitbox_rect,5)
                    #     target_pos = offset_rect.center + PLAYER_TOOL_OFFSET[player.status.split('_')[0]]
                    #     pygame.draw.circle(self.display_surface,'blue',target_pos,5)