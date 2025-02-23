import pygame
from support import import_folder
from sprites import Generic, Interaction
from quest import InteractQuest
from random import choice
from settings import *

class FireSprite(Generic):
    def __init__(self, pos, groups, player):
        [self.all_sprites, self.interaction_sprites] = groups
        self.name = "fire_sprite"
        self.player = player
        self.pos = pos
        
        # Animation
        SCALE_FACTOR = 2.5
        self.animation = [pygame.transform.scale(img, 
                            (img.get_width() * SCALE_FACTOR, img.get_height() * SCALE_FACTOR)) 
                            for img in import_folder('./graphics/objects/fire')]
        self.frame_index = 0
        self.image = self.animation[self.frame_index]
        
        super().__init__(pos, self.image, self.all_sprites)
        self.interaction_sprite = None
    
    def animate(self, dt):
        self.frame_index += 4 * dt
        if self.frame_index >= len(self.animation):
            self.frame_index = 0

        self.image = self.animation[int(self.frame_index)]
    
    def interact(self):
        self.kill()
        if self.interaction_sprite:
            self.interaction_sprite.kill()
        self.player.interacted_obj[self.name] += 1
    
    def update(self, dt):
        self.animate(dt)
        if not self.interaction_sprite:
            for quest in self.player.quests:
                if isinstance(quest, InteractQuest):
                    self.interaction_sprite = Interaction(self.pos, (TILE_SIZE, TILE_SIZE), self.interaction_sprites, {"name": self.name}, "[N] Put out fire", self.interact)

class CoinSprite(Generic):
    def __init__(self, pos, groups, player):
        [self.all_sprites, self.interaction_sprites] = groups
        self.name = "coin_sprite"
        self.player = player
        self.pos = pos
        
        # Animation
        SCALE_FACTOR = 2.5
        self.animation = [pygame.transform.scale(img, 
                            (img.get_width() * SCALE_FACTOR, img.get_height() * SCALE_FACTOR)) 
                            for img in import_folder('./graphics/objects/coin')]
        self.frame_index = 0
        self.image = self.animation[self.frame_index]
        
        super().__init__(pos, self.image, self.all_sprites)
        self.interaction_sprite = None
        
    def animate(self, dt):
        self.frame_index += 4 * dt
        if self.frame_index >= len(self.animation):
            self.frame_index = 0

        self.image = self.animation[int(self.frame_index)]
    
    def interact(self):
        self.kill()
        if self.interaction_sprite:
            self.interaction_sprite.kill()
        self.player.interacted_obj[self.name] += 1
        self.player.add_money(1)
    
    def update(self, dt):
        self.animate(dt)
        if not self.interaction_sprite:
            for quest in self.player.quests:
                if isinstance(quest, InteractQuest):
                    self.interaction_sprite = Interaction(self.pos, (TILE_SIZE, TILE_SIZE), self.interaction_sprites, {"name": self.name}, "[N] Pick up coin", self.interact)

class SnowPuddleSprite(Generic):
    def __init__(self, pos, groups, player):
        [self.all_sprites, self.interaction_sprites] = groups
        self.name = "snow_puddle_sprite"
        self.player = player
        self.pos = pos
        
        # Animation
        self.image = choice(import_folder('./graphics/objects/snow_puddle'))   
        super().__init__(pos, self.image, self.all_sprites)
        self.interaction_sprite = None
        
    def interact(self):
        self.kill()
        if self.interaction_sprite:
            self.interaction_sprite.kill()
        self.player.interacted_obj[self.name] += 1
    
    def update(self, dt):
        if not self.interaction_sprite:
            for quest in self.player.quests:
                if isinstance(quest, InteractQuest):
                    self.interaction_sprite = Interaction(self.pos, (TILE_SIZE, TILE_SIZE), self.interaction_sprites, {"name": self.name}, "[N] Clear the snow", self.interact)