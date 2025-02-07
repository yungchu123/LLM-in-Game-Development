import pygame
from settings import *
from random import randint, choice
from timer import Timer

class Generic(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups, z = LAYERS['main']):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft = pos)
        self.z = z
        self.hitbox = self.rect.copy().inflate(-self.rect.width * 0.2, -self.rect.height * 0.75)

class Interaction(Generic):
    def __init__(self, pos, size, groups, prop):
        surf = pygame.Surface(size)
        super().__init__(pos, surf, groups)
        self.prop = prop

class Water(Generic):
    def __init__(self, pos, frames, groups):

        #animation setup
        self.frames = frames
        self.frame_index = 0

        # sprite setup
        super().__init__(
                pos = pos, 
                surf = self.frames[self.frame_index], 
                groups = groups, 
                z = LAYERS['water'])
    
    def animate(self, dt):
        self.frame_index += 4 * dt
        if self.frame_index >= len(self.frames):
            self.frame_index = 0

        self.image = self.frames[int(self.frame_index)]
        
    def update(self, dt):
        self.animate(dt)
        
class WildFlower(Generic):
    def __init__(self, pos, surf, groups):
        super().__init__(pos, surf, groups)
        self.hitbox = self.rect.copy().inflate(-20,-self.rect.height * 0.9)

class Particle(Generic):
    def __init__(self, pos, surf, groups, z, duration = 200):
        super().__init__(pos, surf, groups, z)
        self.timer = Timer(duration, self.kill) # removes particle after timer times out
        self.timer.activate()

        # white surface 
        mask_surf = pygame.mask.from_surface(self.image)
        new_surf = mask_surf.to_surface()
        new_surf.set_colorkey((0,0,0))
        self.image = new_surf

    def update(self,dt):
        self.timer.update()

class Tree(Generic):
    def __init__(self, pos, surf, groups, name, player_add):
        super().__init__(pos, surf, groups)
        self.all_sprites = self.groups()[0]
        
        # tree attributes
        self.health = 5
        self.alive = True
        stump_path = f'./graphics/stumps/{name.lower()}.png'
        self.stump_surf = pygame.image.load(stump_path).convert_alpha()
        
        # apples
        self.apple_surf = pygame.image.load('./graphics/fruit/apple.png')
        self.apple_pos = APPLE_POS[name]
        self.apple_sprites = pygame.sprite.Group()
        self.create_fruit()
        
        self.player_add = player_add
        
        # sounds
        self.axe_sound = pygame.mixer.Sound('./audio/axe.mp3')
    
    def damage(self):
        
        # damaging the tree
        self.health -= 1

        # play sound
        self.axe_sound.play()

        # remove an apple
        if len(self.apple_sprites.sprites()) > 0:
            random_apple = choice(self.apple_sprites.sprites())
            Particle(
                pos = random_apple.rect.topleft,
                surf = random_apple.image, 
                groups = self.all_sprites, 
                z = LAYERS['fruit'])
            random_apple.kill()
            self.player_add('apple', "resource", 1)
    
    def check_death(self):
        if self.health <= 0:
            print('tree chopped')
            Particle(self.rect.topleft, self.image, self.all_sprites, LAYERS['fruit'], 300)
            self.image = self.stump_surf
            self.rect = self.image.get_rect(midbottom = self.rect.midbottom)
            self.hitbox = self.rect.copy().inflate(-10,-self.rect.height * 0.6)
            self.alive = False
            self.player_add('wood', "resource", 1)

    def update(self,dt):
        if self.alive:
            self.check_death()
    
    def create_fruit(self):
        for pos in self.apple_pos:
            # randomly generate apple relative to tree pos
            if randint(0,10) < 2:
                x = pos[0] + self.rect.left
                y = pos[1] + self.rect.top
                Generic(
                    pos = (x,y), 
                    surf = self.apple_surf, 
                    groups = [self.apple_sprites,self.all_sprites],
                    z = LAYERS['fruit'])
                
class TextSprite(pygame.sprite.Sprite):
    def __init__(self, pos, groups, color=WHITE, text="Hello!"):
        super().__init__(groups)
        font = pygame.font.Font(None, 30)
        self.text = text
        self.pos = pos
        self.z = LAYERS['name text']
        self.image = font.render(self.text, True, color)
        self.rect = self.image.get_rect(center=(self.pos.x, self.pos.y - 40))  # Above the character

    def update(self, dt):
        # Update position above the character
        self.rect.center = (self.pos.x, self.pos.y - 40)

class ToolTipSprite(pygame.sprite.Sprite):
    def __init__(self, player, groups, text="Press N to interact"):
        super().__init__(groups)
        self.player = player
        self.text = text
        self.z = LAYERS['tool tip']
        self.font = pygame.font.Font(None, 24)  # Default pygame font, size 24
        self.image = self.font.render(self.text, True, (255, 255, 255))  # White text
        self.rect = self.image.get_rect(topright=(self.player.rect.left + 50, self.player.rect.top + 20))  # Position top left abover player
        self.visible = False  # Default: Hidden

    def update(self, dt):
        """Update tooltip position & visibility."""
        if self.visible:
            self.rect.topright = (self.player.rect.left + 50, self.player.rect.top + 20)
        else:
            self.image = pygame.Surface((0, 0))  # Hide tooltip

    def update_text(self, text):
        self.text = text

    def show(self):
        """Show the tooltip."""
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        self.image = pygame.Surface((text_surface.get_width() + 15, text_surface.get_height() + 15))
        self.image.fill(GREEN)  # Background Color
        text_rect = text_surface.get_rect(center=(self.image.get_width() // 2, self.image.get_height() // 2))
        self.image.blit(text_surface, text_rect.topleft) # Center text inside box
        self.visible = True

    def hide(self):
        """Hide the tooltip."""
        self.image = pygame.Surface((0, 0))
        self.visible = False