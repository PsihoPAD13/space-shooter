# main.py
import pygame
import sys
from settings import WIDTH, HEIGHT
from core.game import Game
from ui.menu import Menu
from ui.settings_menu import SettingsMenu
from config_manager import ConfigManager

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Space Universe")
    
    config = ConfigManager()
    
    while True:
        menu = Menu(screen, config)
        menu_result = menu.run()
        
        if menu_result == "start":
            game = Game(screen, config)
            game_result = game.run()
            
            if game_result == "quit":
                break
            elif game_result == "menu":
                continue
        
        elif menu_result == "settings":
            settings_menu = SettingsMenu(screen, config)
            settings_menu.run()
        
        elif menu_result == "quit":
            break
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()