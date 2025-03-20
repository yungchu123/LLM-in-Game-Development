import pygame, sys
from settings import *
from level import Level

class Game:
    def __init__(self):
        # Initialize pygame and set up the screen
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Math Harvest")
        self.clock = pygame.time.Clock()
        self.level = Level()

    def run(self):
        while True:
            events = pygame.event.get()  # Collect all events
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            dt = self.clock.tick() / 1000
            self.level.run(dt, events)
            pygame.display.update()



if __name__ == "__main__":
    game = Game()
    game.run()
