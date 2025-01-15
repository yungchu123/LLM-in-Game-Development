from os import walk
import pygame

def import_folder(path):
    surface_list = []

    for _, _, img_files in walk(path):
        for image in img_files:
            image_path  = path + '/' + image
            image_surface = pygame.image.load(image_path)
            surface_list.append(image_surface)
            
    return surface_list