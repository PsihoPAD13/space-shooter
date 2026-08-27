# starfield.py
import pygame
import random
import math
from settings import WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT, STAR_LAYERS

class Star:
    """Отдельная звезда"""
    def __init__(self, x, y, speed, size, brightness, color_variation=0):
        self.x = x
        self.y = y
        self.speed = speed
        self.size = size
        self.brightness = brightness
        self.color_offset = color_variation
    
    def draw(self, screen, camera_x, camera_y):
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        # Проверяем видимость на экране
        if -10 < screen_x < WIDTH + 10 and -10 < screen_y < HEIGHT + 10:
            # Выбор цвета
            if self.color_offset == 0:
                color = (self.brightness, self.brightness, self.brightness)
            elif self.color_offset == 1:  # Голубые
                color = (self.brightness, self.brightness, min(255, self.brightness + 50))
            elif self.color_offset == 2:  # Желтые
                color = (min(255, self.brightness + 50), self.brightness, self.brightness)
            elif self.color_offset == 3:  # Красные
                color = (min(255, self.brightness + 30), self.brightness // 2, self.brightness // 2)
            else:
                color = (self.brightness, self.brightness, self.brightness)
            
            pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), self.size)
            
            # Свечение для крупных звезд
            if self.size >= 3 and random.random() < 0.3:
                glow_color = (color[0] // 2, color[1] // 2, color[2] // 2)
                pygame.draw.circle(screen, glow_color, (int(screen_x), int(screen_y)), self.size + 2, 1)

class StarField:
    """Система звезд - всегда вокруг камеры"""
    def __init__(self, start_x=0, start_y=0):
        self.stars = []
        self.layers_config = STAR_LAYERS
        self.spawn_radius = max(WIDTH, HEIGHT) * 2
        
        # Генерируем звезды вокруг начальной позиции
        self.generate_stars(start_x, start_y)
    
    def generate_stars(self, center_x, center_y):
        """Генерирует звезды вокруг заданной точки"""
        self.stars = []
        
        for layer_config in self.layers_config:
            count, speed, size_range, brightness_min, brightness_max, color_prob = layer_config
            
            for _ in range(count):
                # Случайное расстояние и угол
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(0, self.spawn_radius)
                
                # Позиция звезды относительно центра
                x = center_x + math.cos(angle) * distance
                y = center_y + math.sin(angle) * distance
                
                # Нормализуем координаты в пределах мира (бесшовность)
                x = x % WORLD_WIDTH
                y = y % WORLD_HEIGHT
                
                # Случайные параметры звезды
                size = random.randint(1, size_range)
                brightness = random.randint(brightness_min, brightness_max)
                layer_speed = speed * random.uniform(0.7, 1.3)
                
                # Цветной оттенок
                color_variation = random.randint(1, 3) if random.random() < color_prob else 0
                
                self.stars.append(Star(x, y, layer_speed, size, brightness, color_variation))
    
    def update(self, offset_x, offset_y, camera_x, camera_y):
        """Обновляет звезды - двигает их с параллаксом"""
        for star in self.stars:
            star.x += offset_x * star.speed
            star.y += offset_y * star.speed
            
            # Бесшовная телепортация
            star.x = star.x % WORLD_WIDTH
            star.y = star.y % WORLD_HEIGHT
        
        # Если камера слишком далеко ушла от звезд - регенерируем
        if self.stars:
            # Проверяем первую звезду (она репрезентативна)
            first = self.stars[0]
            dx = abs(first.x - camera_x)
            dy = abs(first.y - camera_y)
            
            # Если звезды слишком далеко от камеры - обновляем
            if dx > self.spawn_radius * 0.7 or dy > self.spawn_radius * 0.7:
                self.generate_stars(camera_x, camera_y)
    
    def draw(self, screen, camera_x, camera_y):
        """Рисует звезды с учетом камеры"""
        for star in self.stars:
            star.draw(screen, camera_x, camera_y)