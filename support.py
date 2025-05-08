from os import walk
import pygame
import os

# when the order of image surface matters
def import_folder(path):
    surface_list = []

    for _, _, img_files in walk(path):
        img_files.sort(key=lambda name: int(os.path.splitext(name)[0]))
        
        for image in img_files:
            image_path  = path + '/' + image
            image_surface = pygame.image.load(image_path)
            surface_list.append(image_surface)
            
    return surface_list

# when we need key values to access image surface
def import_folder_dict(path):
    surface_dict = {}

    for _, __, img_files in walk(path):
        for image in img_files:
            full_path = path + '/' + image
            image_surf = pygame.image.load(full_path).convert_alpha()
            surface_dict[image.split('.')[0]] = image_surf

    return surface_dict