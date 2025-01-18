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

class Level:
    def __init__(self):

        # get the display surface
        self.display_surface = pygame.display.get_surface()

        # sprite groups
        self.all_sprites = CameraGroup()                    # sprites to be drawn
        self.collision_sprites = pygame.sprite.Group()      # sprites with collision
        self.tree_sprites = pygame.sprite.Group()           # interaction with tree sprites
        self.interaction_sprites = pygame.sprite.Group()    # empty space for interactions
  
        self.soil_layer = SoilLayer(self.all_sprites)
        self.setup()
        self.overlay = Overlay(self.player)
        self.transition = Transition(self.reset, self.player)
        
        # sky
        self.rain = Rain(self.all_sprites)
        self.raining = False
        self.sky = Sky()

    def setup(self):
        tmx_data = load_pygame('./data/map.tmx')
        
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
                player_add = self.player_add)

        # wildflowers 
        for obj in tmx_data.get_layer_by_name('Decoration'):
            WildFlower((obj.x, obj.y), obj.image, [self.all_sprites, self.collision_sprites])
    
        # collion tiles
        for x, y, surf in tmx_data.get_layer_by_name('Collision').tiles():
            Generic((x * TILE_SIZE, y * TILE_SIZE), pygame.Surface((TILE_SIZE, TILE_SIZE)), self.collision_sprites)
    
        # Player
        for obj in tmx_data.get_layer_by_name('Player'):
            if obj.name == 'Start':
                self.player = Player(
                    pos = (obj.x,obj.y), 
                    group = self.all_sprites, 
                    collision_sprites = self.collision_sprites,
                    tree_sprites = self.tree_sprites,
                    interaction_sprites = self.interaction_sprites,
                    soil_layer = self.soil_layer)
            
            if obj.name == 'Bed':
                Interaction((obj.x,obj.y), (obj.width,obj.height), self.interaction_sprites, obj.name)
        
        # Ground Sprite (Floor)
        Generic(
            pos = (0,0),
            surf = pygame.image.load('./graphics/world/ground.png').convert_alpha(),
            groups = self.all_sprites,
            z = LAYERS['ground'])

    def player_add(self, item, amount):
        self.player.item_inventory[item] += amount
        print(f'{item} added. New inventory: {self.player.item_inventory}')

    def plant_collision(self):
        if self.soil_layer.plant_sprites:
            for plant in self.soil_layer.plant_sprites.sprites():
                if plant.harvestable and plant.rect.colliderect(self.player.hitbox):
                    self.player_add(plant.plant_type, 1)
                    plant.kill()
                    Particle(plant.rect.topleft, plant.image, self.all_sprites, z = LAYERS['main'])
                    self.soil_layer.grid[plant.rect.centery // TILE_SIZE][plant.rect.centerx // TILE_SIZE].remove('P')

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

    def run(self,dt):
        
        # drawing logic
        self.display_surface.fill('black')
        self.all_sprites.custom_draw(self.player)
        self.all_sprites.update(dt) # calls update() on all children
        self.plant_collision()      # harvest full-grown plant on collision
        
        self.overlay.display()
        
        # rain
        if self.raining:
            self.rain.update()
            self.soil_layer.water_all()
        
        # day to night transition
        self.sky.display(dt)
        
        # player sleep transition
        if self.player.sleep:
            self.transition.play()
        
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
                    # if sprite == player:
                    #     pygame.draw.rect(self.display_surface,'red',offset_rect,5)
                    #     hitbox_rect = player.hitbox.copy()
                    #     hitbox_rect.center = offset_rect.center
                    #     pygame.draw.rect(self.display_surface,'green',hitbox_rect,5)
                    #     target_pos = offset_rect.center + PLAYER_TOOL_OFFSET[player.status.split('_')[0]]
                    #     pygame.draw.circle(self.display_surface,'blue',target_pos,5)