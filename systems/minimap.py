# systems/minimap.py
import pygame
from settings import WIDTH, HEIGHT, CHUNK_SIZE

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
        self.bg_color = (10, 10, 30, 180)
        self.border_color = (50, 50, 80)
        self.player_color = (0, 255, 0)
        self.enemy_color = (255, 50, 50)
        self.powerup_color = (255, 200, 50)
        self.boss_color = (255, 50, 255)
        self.base_color = (100, 200, 255)
    
    def draw(self, screen, player_x, player_y, enemies, powerups=None, 
             base_x=None, base_y=None, camera=None, enemy_bases=None):
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
        
        # Определяем область отображения (3x3 чанка вокруг игрока)
        view_radius = CHUNK_SIZE * 1.5  # 3 чанка
        left = player_x - view_radius
        top = player_y - view_radius
        right = player_x + view_radius
        bottom = player_y + view_radius
        view_width = right - left
        view_height = bottom - top
        
        # Масштаб
        scale_x = self.map_width / view_width if view_width > 0 else 1
        scale_y = self.map_height / view_height if view_height > 0 else 1
        
        # Рисуем врагов
        for enemy in enemies:
            if enemy.health > 0:
                # Позиция на карте
                map_x = (enemy.x - left) * scale_x
                map_y = (enemy.y - top) * scale_y
                
                # Проверяем, что враг в зоне видимости
                if 0 < map_x < self.map_width and 0 < map_y < self.map_height:
                    size = max(2, min(4, enemy.radius // 5))
                    
                    if enemy.behavior == 'kamikaze':
                        color = (255, 200, 50)
                    elif enemy.behavior == 'tank':
                        color = (255, 100, 100)
                    elif enemy.behavior == 'sniper':
                        color = (100, 150, 255)
                    else:
                        color = self.enemy_color
                    
                    pygame.draw.circle(map_surface, color, 
                                     (int(map_x), int(map_y)), size)
        
        # Рисуем бонусы
        if powerups:
            for powerup in powerups:
                map_x = (powerup.x - left) * scale_x
                map_y = (powerup.y - top) * scale_y
                if 0 < map_x < self.map_width and 0 < map_y < self.map_height:
                    pygame.draw.circle(map_surface, self.powerup_color, 
                                     (int(map_x), int(map_y)), 2)
        
        # Рисуем базу игрока
        if base_x is not None and base_y is not None:
            map_x = (base_x - left) * scale_x
            map_y = (base_y - top) * scale_y
            if 0 < map_x < self.map_width and 0 < map_y < self.map_height:
                pygame.draw.circle(map_surface, self.base_color, 
                                 (int(map_x), int(map_y)), 5)
                pygame.draw.circle(map_surface, self.base_color, 
                                 (int(map_x), int(map_y)), 8, 1)
        
        # Рисуем игрока
        player_map_x = (player_x - left) * scale_x
        player_map_y = (player_y - top) * scale_y
        
        if 0 < player_map_x < self.map_width and 0 < player_map_y < self.map_height:
            pygame.draw.circle(map_surface, (255, 255, 255), 
                             (int(player_map_x), int(player_map_y)), 4)
            pygame.draw.circle(map_surface, self.player_color, 
                             (int(player_map_x), int(player_map_y)), 3)
        
        # Отображаем на экране
        screen.blit(map_surface, (self.map_x, self.map_y))
        
        # Рисуем подпись
        font = pygame.font.Font(None, 14)
        label = font.render("MAP", True, (100, 100, 120))
        screen.blit(label, (self.map_x + 5, self.map_y + 5))
        
        # ===== БАЗЫ ВРАГОВ =====
        if enemy_bases:
            for base in enemy_bases:
                if base.alive:
                    map_x = (base.x - left) * scale_x
                    map_y = (base.y - top) * scale_y
                    if 0 < map_x < self.map_width and 0 < map_y < self.map_height:
                        # Квадрат для базы (в отличие от круга для врагов)
                        size = 6
                        color = (255, 0, 0)
                        pygame.draw.rect(map_surface, color, 
                                       (int(map_x - size//2), int(map_y - size//2), size, size))
                        # Обводка
                        pygame.draw.rect(map_surface, (255, 255, 255), 
                                       (int(map_x - size//2), int(map_y - size//2), size, size), 1)