# world/starfield_background.py
import pygame
import random
import math
from settings import WIDTH, HEIGHT, STAR_LAYERS, STAR_SPAWN_RADIUS_MULTIPLIER

class StarLayer:
    """Один слой звёзд с определённой скоростью параллакса"""
    
    def __init__(self, count, speed, min_size, max_size, min_bright, max_bright, color_chance):
        self.count = count
        self.speed = speed
        self.min_size = min_size
        self.max_size = max_size
        self.min_bright = min_bright
        self.max_bright = max_bright
        self.color_chance = color_chance
        
        self.stars = []
        self.spawn_radius = max(WIDTH, HEIGHT) * STAR_SPAWN_RADIUS_MULTIPLIER
        
        # Генерируем звёзды слоя
        self.generate_stars(0, 0)
    
    def generate_stars(self, center_x, center_y):
        """Генерирует звёзды слоя вокруг заданной точки"""
        self.stars = []
        
        for _ in range(self.count):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, self.spawn_radius)
            
            x = center_x + math.cos(angle) * distance
            y = center_y + math.sin(angle) * distance
            
            size = random.randint(self.min_size, self.max_size)
            brightness = random.randint(self.min_bright, self.max_bright)
            
            # Случайный цветовой оттенок
            if random.random() < self.color_chance:
                color_variation_type = random.choice([
                    (brightness, brightness, min(255, brightness + 50)),
                    (min(255, brightness + 50), brightness, brightness),
                    (brightness, min(255, brightness + 50), brightness),
                ])
            else:
                color_variation_type = (brightness, brightness, brightness)
            
            self.stars.append({
                'x': x,
                'y': y,
                'size': size,
                'brightness': brightness,
                'color': color_variation_type,
                'phase': random.uniform(0, 6.28)
            })
    
    def update(self, player_x, player_y, offset_x, offset_y):
        """Обновляет позиции звёзд с учётом скорости слоя"""
        for star in self.stars:
            star['x'] += offset_x * self.speed
            star['y'] += offset_y * self.speed
            
            # Если звезда улетела далеко — телепортируем
            dx = star['x'] - player_x
            dy = star['y'] - player_y
            dist = math.sqrt(dx**2 + dy**2)
            
            if dist > self.spawn_radius:
                angle = math.atan2(dy, dx) + math.pi + random.uniform(-0.3, 0.3)
                new_dist = self.spawn_radius * 0.9
                star['x'] = player_x + math.cos(angle) * new_dist
                star['y'] = player_y + math.sin(angle) * new_dist
    
    def draw(self, screen, camera_x, camera_y):
        """Рисует звёзды слоя"""
        current_time = pygame.time.get_ticks() * 0.001
        
        for star in self.stars:
            screen_x = star['x'] - camera_x
            screen_y = star['y'] - camera_y
            
            if -10 < screen_x < WIDTH + 10 and -10 < screen_y < HEIGHT + 10:
                # Мерцание
                twinkle = 0.7 + 0.3 * math.sin(current_time * 0.5 + star['phase'])
                brightness = int(star['brightness'] * twinkle)
                
                color = (
                    min(255, int(star['color'][0] * twinkle)),
                    min(255, int(star['color'][1] * twinkle)),
                    min(255, int(star['color'][2] * twinkle))
                )
                
                pygame.draw.circle(screen, color, 
                                 (int(screen_x), int(screen_y)), 
                                 star['size'])


class BackgroundStars:
    """Система звёзд с параллаксом (слои из настроек)"""
    
    def __init__(self):
        self.layers = []
        
        # Создаём слои из настроек
        for layer_config in STAR_LAYERS:
            count, speed, min_size, max_size, min_bright, max_bright, color_chance = layer_config
            layer = StarLayer(
                count=count,
                speed=speed,
                min_size=min_size,
                max_size=max_size,
                min_bright=min_bright,
                max_bright=max_bright,
                color_chance=color_chance
            )
            self.layers.append(layer)
        
        #print(f"[STARS] Система параллакса инициализирована, слоёв: {len(self.layers)}")
    
    def update(self, player_x, player_y, offset_x, offset_y):
        """Обновляет все слои звёзд"""
        for layer in self.layers:
            layer.update(player_x, player_y, offset_x, offset_y)
    
    def draw(self, screen, camera_x, camera_y):
        """Рисует все слои звёзд"""
        for layer in self.layers:
            layer.draw(screen, camera_x, camera_y)