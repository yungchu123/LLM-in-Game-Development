import pygame
from settings import *
from timer import Timer

class Menu:
    def __init__(self, player, toggle_menu):

        # general setup
        self.player = player
        self.toggle_menu = toggle_menu
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font('./font/LycheeSoda.ttf', 30)

        # text options
        self.width = 400
        self.space = 10
        self.padding = 8
        
        # shop entries
        self.options = [
            {"name": "corn", "type": "seed"},
            {"name": "tomato", "type": "seed"},
            {"name": "wood", "type": "resource"},
            {"name": "apple", "type": "resource"},
            {"name": "corn", "type": "resource"},
            {"name": "tomato", "type": "resource"}
        ]
        
        self.setup()
        
        # movement
        self.selected_index = 0
        self.timer = Timer(200)
  
    def setup(self):

        # create the text surfaces
        self.text_surfs = []
        self.total_height = 0

        for item in self.options:
            text_surf = self.font.render(item["name"], False, 'Black')
            self.text_surfs.append(text_surf)
            self.total_height += text_surf.get_height() + (self.padding * 2)

        self.total_height += (len(self.text_surfs) - 1) * self.space
        
        # Ensures menu stay in center of screen
        self.menu_top = SCREEN_HEIGHT / 2 - self.total_height / 2
        self.menu_left = SCREEN_WIDTH / 2 - self.width / 2
        self.main_rect = pygame.Rect(self.menu_left, self.menu_top, self.width, self.total_height)
  
        # buy / sell text surface
        self.buy_text = self.font.render('buy',False,'Black')
        self.sell_text =  self.font.render('sell',False,'Black')
  
    def display_money(self):
        text_surf = self.font.render(f'${self.player.money}', False, 'Black')
        text_rect = text_surf.get_rect(midbottom = (SCREEN_WIDTH / 2,SCREEN_HEIGHT - 90))

        pygame.draw.rect(self.display_surface,'White',text_rect.inflate(10,10),0,6)
        self.display_surface.blit(text_surf,text_rect)
  
    def input(self):
        keys = pygame.key.get_pressed()
        self.timer.update()

        if keys[pygame.K_ESCAPE]:
            self.toggle_menu()
            
        if not self.timer.active:
            if keys[pygame.K_UP]:
                self.selected_index -= 1
                if self.selected_index < 0:
                    self.selected_index = len(self.options) - 1
                self.timer.activate()

            if keys[pygame.K_DOWN]:
                self.selected_index += 1
                if self.selected_index >= len(self.options):
                    self.selected_index = 0
                self.timer.activate()
                
            if keys[pygame.K_RETURN]:
                self.timer.activate()

                # get item
                current_item = self.options[self.selected_index]['name']
                current_item_type = self.options[self.selected_index]['type']

                # sell
                if  current_item_type == "resource":
                    item = self.player.get_item(current_item, current_item_type)
                    if item and item['quantity'] > 0:
                        self.player.remove_from_inventory(current_item, current_item_type, 1)
                        self.player.money += SALE_PRICES[current_item]

                # buy
                elif current_item_type == "seed":
                    seed_price = PURCHASE_PRICES[current_item]
                    if self.player.money >= seed_price:
                        self.player.add_to_inventory(current_item, current_item_type, 1)
                        self.player.money -= seed_price

    def show_entry(self, text_surf, top, selected):

        # background
        bg_rect = pygame.Rect(self.main_rect.left,top,self.width,text_surf.get_height() + (self.padding * 2))
        pygame.draw.rect(self.display_surface, 'White',bg_rect, 0, 4)

        # text
        offset = 30
        text_rect = text_surf.get_rect(midleft = (self.main_rect.left + offset,bg_rect.centery))
        self.display_surface.blit(text_surf, text_rect)
       
        # selected
        if selected:
            pygame.draw.rect(self.display_surface,'black',bg_rect,6,4)
            if self.options[self.selected_index]['type'] == "resource": # sell
                pos_rect = self.sell_text.get_rect(midleft = (self.main_rect.left + self.width/2, bg_rect.centery))
                self.display_surface.blit(self.sell_text,pos_rect)
            elif self.options[self.selected_index]['type'] == "seed": # buy
                pos_rect = self.buy_text.get_rect(midleft = (self.main_rect.left + self.width/2, bg_rect.centery))
                self.display_surface.blit(self.buy_text,pos_rect)
        
    def update(self):
        self.input()
        self.display_money()
        
        for text_index, text_surf in enumerate(self.text_surfs):
            top = self.main_rect.top + text_index * (text_surf.get_height() + (self.padding * 2) + self.space)
            self.show_entry(text_surf, top, self.selected_index == text_index)