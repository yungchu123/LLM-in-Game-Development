import pygame
import heapq
from settings import *

def a_star(grid, start, end, tile_size):
    """A* pathfinding algorithm using collision grid and tile size"""

    start_grid = (int(start['x'] // TILE_SIZE), int(start['y'] // TILE_SIZE))
    end_grid = (int(end['x'] // TILE_SIZE), int(end['y'] // TILE_SIZE))

    rows, cols = len(grid), len(grid[0])
    open_set = []
    heapq.heappush(open_set, (0, start_grid))  # (f-score, (grid_x, grid_y))

    came_from = {}  # Stores path history
    g_score = {start_grid: 0}
    f_score = {start_grid: heuristic(start_grid, end_grid)}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == end_grid:
            return reconstruct_path(came_from, current)

        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  # 4-directional movement
            neighbor = (current[0] + dx, current[1] + dy)

            # Check if within grid bounds
            if not (0 <= neighbor[0] < cols and 0 <= neighbor[1] < rows):
                continue
            
            # Check if the tile is blocked
            if "C" in grid[neighbor[1]][neighbor[0]]:
                continue  # Skip blocked tiles

            temp_g_score = g_score[current] + 1  # Assume uniform movement cost

            if neighbor not in g_score or temp_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = temp_g_score
                f_score[neighbor] = temp_g_score + heuristic(neighbor, end_grid)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return []  # No path found

def heuristic(a, b):
    """Manhattan distance heuristic"""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def reconstruct_path(came_from, current):
    """Reconstructs the path from end to start"""
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    return path[::-1]  # Return reversed path (start -> end)

def convert_pathgrid_to_coordinates(path):
    res = []
    # Convert pathgrid to coordinates of center point
    for pathgrid in path:
        x = pathgrid[0] * TILE_SIZE + TILE_SIZE/2
        y = pathgrid[1] * TILE_SIZE + TILE_SIZE/2
        res.append((x, y))
    return res

def find_path(grid, start, end):
    path = a_star(grid, start, end, TILE_SIZE)
    if not path:
        return []

    path_coordinates = convert_pathgrid_to_coordinates(path)
    # Return the original destination coordinate and exclude the start destination coordinate
    return path_coordinates[1:-1] + [(end['x'], end['y'])]

# Testing
# from pytmx.util_pygame import load_pygame

# pygame.init()
# screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# ground = pygame.image.load('./graphics/world/ground.png')
# h_tiles = ground.get_width() // TILE_SIZE
# v_tiles = ground.get_height() // TILE_SIZE
# grid = [[[] for col in range(h_tiles)] for row in range(v_tiles)]

# for x, y, _ in load_pygame('./data/map.tmx').get_layer_by_name('Collision').tiles():
#     grid[y][x].append('C')  # Marking collision tiles

# start = {'x': 1561.0, 'y': 1772.0}
# end = {'x': 1561, 'y': 1256}
# print(find_path(grid, start, end))