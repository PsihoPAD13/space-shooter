# minimap.py
import pygame
from settings import WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT

class Minimap:
    def __init__(self, screen, config):
        self.screen = screen
        self.config = config
        
        # Размеры мини-карты
        self.map_width = 150
        self.map_height = 150
        self.map_x = WIDTH - self.map_width - 20
        self.map_y = 20
        
        # Цвета
        self.bg_color = (10, 10, 30, 180)  # Полупрозрачный темный
        self.border_color = (50, 50, 80)
        self.player_color = (0, 255, 0)
        self.enemy_color = (255, 50, 50)
        self.powerup_color = (255, 200, 50)
        self.boss_color = (255, 50, 255)
    
    def draw(self, player_x, player_y, enemies, powerups=None):
        """Рисует мини-карту"""
        
        # Проверяем настройку
        if not self.config.get('graphics.show_minimap', True):
            return
            
        # Создаем поверхность с прозрачностью
        map_surface = pygame.Surface((self.map_width, self.map_height), pygame.SRCALPHA)
        
        # Фон
        pygame.draw.rect(map_surface, self.bg_color, 
                        (0, 0, self.map_width, self.map_height))
        pygame.draw.rect(map_surface, self.border_color, 
                        (0, 0, self.map_width, self.map_height), 2)
        
        # Масштаб
        scale_x = self.map_width / WORLD_WIDTH
        scale_y = self.map_height / WORLD_HEIGHT
        
        # Рисуем врагов
        for enemy in enemies:
            if enemy.health > 0:  # Только живые
                # Позиция на карте
                map_x = enemy.x * scale_x
                map_y = enemy.y * scale_y
                
                # Размер точки зависит от радиуса врага
                size = max(2, min(4, enemy.radius // 5))
                
                # Цвет зависит от типа врага
                if enemy.behavior == 'kamikaze':
                    color = (255, 200, 50)  # Желтый для камикадзе
                elif enemy.behavior == 'tank':
                    color = (255, 100, 100)  # Светло-красный для танка
                elif enemy.behavior == 'sniper':
                    color = (100, 150, 255)  # Синий для снайпера
                else:
                    color = self.enemy_color
                
                pygame.draw.circle(map_surface, color, 
                                 (int(map_x), int(map_y)), size)
        
        # Рисуем бонусы
        if powerups:
            for powerup in powerups:
                map_x = powerup.x * scale_x
                map_y = powerup.y * scale_y
                pygame.draw.circle(map_surface, self.powerup_color, 
                                 (int(map_x), int(map_y)), 2)
        
        # Рисуем игрока
        player_map_x = player_x * scale_x
        player_map_y = player_y * scale_y
        
        # Игрок — зеленая точка с обводкой
        pygame.draw.circle(map_surface, (255, 255, 255), 
                         (int(player_map_x), int(player_map_y)), 4)
        pygame.draw.circle(map_surface, self.player_color, 
                         (int(player_map_x), int(player_map_y)), 3)
        
        # Рамка вокруг игрока (показывает область видимости)
        view_radius = 400 * scale_x  # ~400 пикселей в мире
        pygame.draw.circle(map_surface, (255, 255, 255, 50), 
                         (int(player_map_x), int(player_map_y)), 
                         int(view_radius), 1)
        
        # Отображаем на экране
        self.screen.blit(map_surface, (self.map_x, self.map_y))
        
        # Рисуем подпись
        font = pygame.font.Font(None, 14)
        label = font.render("MAP", True, (100, 100, 120))
        self.screen.blit(label, (self.map_x + 5, self.map_y + 5))
    
    def draw_debug(self, player_x, player_y, enemies):
        """Отладочная версия с координатами"""
        # ... можно добавить если нужно
        pass