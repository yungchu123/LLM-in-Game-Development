import pygame

# Initialize Pygame
pygame.init()

# Screen setup
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Key Overlay Example")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
OVERLAY_BG = (50, 50, 50, 200)  # Semi-transparent dark background

# Font setup
pygame.font.init()
font = pygame.font.Font(None, 32)  # Default font, size 32

# Key bindings
key_bindings = {
    "Arrow Keys": "Move Character",
    "Q": "Open Inventory",
    "W": "Use Tool",
    "Space": "Jump / Interact",
    "N": "Open Notes",
    "M": "Open Map"
}

def draw_overlay(surface):
    """Draws a semi-transparent overlay with key mappings."""
    overlay_surface = pygame.Surface((250, 200), pygame.SRCALPHA)  # Transparent surface
    overlay_surface.fill(OVERLAY_BG)  # Apply semi-transparent background
    
    # Draw key bindings
    y_offset = 10
    for key, action in key_bindings.items():
        text_surface = font.render(f"{key}: {action}", True, WHITE)
        overlay_surface.blit(text_surface, (10, y_offset))
        y_offset += 35  # Space between lines

    # Blit overlay to main screen
    surface.blit(overlay_surface, (20, 20))  # Position in top-left corner

# Game loop
running = True
while running:
    screen.fill(BLACK)  # Clear screen

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    draw_overlay(screen)  # Draw overlay every frame

    pygame.display.flip()  # Update display

pygame.quit()
