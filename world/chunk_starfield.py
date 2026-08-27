# chunk_starfield.py
import pygame
import random
import math
from settings import (
    WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT, 
    CHUNK_SIZE, CHUNK_LOAD_RADIUS, STARS_PER_CHUNK, STAR_LAYERS,
    PARALLAX_SPEED_MULTIPLIER  
)

class Star:
    """Отдельная звезда с параллаксом"""
    def __init__(self, x, y, speed, size, brightness, color_variation=0):
        self.x = x
        self.y = y
        self.speed = speed  # Скорость параллакса (0.2 - 1.0)
        self.size = size
        self.brightness = brightness
        self.color_offset = color_variation
        
        # Для плавного движения
        self.offset_x = 0
        self.offset_y = 0
    
    def update(self, offset_x, offset_y):
        """Обновляет позицию звезды с параллаксом"""
        # Двигаем звезду с учетом скорости параллакса
        self.x += offset_x * self.speed * PARALLAX_SPEED_MULTIPLIER
        self.y += offset_y * self.speed * PARALLAX_SPEED_MULTIPLIER
        
        # Бесшовная телепортация
        self.x = self.x % WORLD_WIDTH
        self.y = self.y % WORLD_HEIGHT
    
    def draw(self, screen, camera_x, camera_y):
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        # Проверяем видимость
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

class Chunk:
    """Чанк - кусок мира с звездами"""
    def __init__(self, chunk_x, chunk_y):
        self.chunk_x = chunk_x
        self.chunk_y = chunk_y
        self.stars = []
        self.loaded = False
        
        # Координаты чанка в пикселях
        self.world_x = chunk_x * CHUNK_SIZE
        self.world_y = chunk_y * CHUNK_SIZE
    
    def generate(self):
        """Генерирует звезды в чанке"""
        self.stars = []
        
        for layer_config in STAR_LAYERS:
            speed, size_range, brightness_min, brightness_max, color_prob = layer_config
            
            # Количество звезд этого слоя в чанке
            stars_in_layer = max(2, STARS_PER_CHUNK // len(STAR_LAYERS))
            
            for _ in range(stars_in_layer):
                # Случайная позиция внутри чанка
                x = self.world_x + random.randint(0, CHUNK_SIZE)
                y = self.world_y + random.randint(0, CHUNK_SIZE)
                
                size = random.randint(1, size_range)
                brightness = random.randint(brightness_min, brightness_max)
                # Скорость параллакса для этой звезды
                layer_speed = speed * random.uniform(0.7, 1.3)
                
                color_variation = random.randint(1, 3) if random.random() < color_prob else 0
                
                self.stars.append(Star(x, y, layer_speed, size, brightness, color_variation))
        
        self.loaded = True
    
    def update(self, offset_x, offset_y):
        """Обновляет все звезды в чанке с параллаксом"""
        for star in self.stars:
            star.update(offset_x, offset_y)
    
    def unload(self):
        """Выгружает чанк (освобождает память)"""
        self.stars = []
        self.loaded = False
    
    def get_center_distance(self, player_x, player_y):
        """Расстояние от центра чанка до игрока"""
        center_x = self.world_x + CHUNK_SIZE // 2
        center_y = self.world_y + CHUNK_SIZE // 2
        return math.sqrt((player_x - center_x)**2 + (player_y - center_y)**2)

class ChunkStarField:
    """Система чанков для звезд с параллаксом"""
    def __init__(self):
        self.chunks = {}
        self.visible_chunks = set()
        self.previous_player_chunk = None
        
        # Смещение для параллакса (накапливается)
        self.accumulated_offset_x = 0
        self.accumulated_offset_y = 0
    
    def get_chunk_key(self, chunk_x, chunk_y):
        return (chunk_x, chunk_y)
    
    def get_chunk_at(self, x, y):
        """Получает координаты чанка для позиции в мире"""
        chunk_x = x // CHUNK_SIZE
        chunk_y = y // CHUNK_SIZE
        
        # Нормализуем для бесшовного мира
        chunk_x = chunk_x % (WORLD_WIDTH // CHUNK_SIZE)
        chunk_y = chunk_y % (WORLD_HEIGHT // CHUNK_SIZE)
        
        return chunk_x, chunk_y
    
    def get_or_create_chunk(self, chunk_x, chunk_y):
        """Получает чанк, создает если его нет"""
        key = self.get_chunk_key(chunk_x, chunk_y)
        
        if key not in self.chunks:
            chunk = Chunk(chunk_x, chunk_y)
            chunk.generate()
            self.chunks[key] = chunk
        elif not self.chunks[key].loaded:
            self.chunks[key].generate()
        
        return self.chunks[key]
    
    def update(self, player_x, player_y, offset_x, offset_y):
        """Обновляет чанки вокруг игрока и применяет параллакс"""
        # Накопливаем смещение для параллакса
        self.accumulated_offset_x += offset_x
        self.accumulated_offset_y += offset_y
        
        # Обновляем все загруженные чанки с параллаксом
        for chunk_key in self.visible_chunks:
            chunk = self.chunks.get(chunk_key)
            if chunk and chunk.loaded:
                # Применяем накопленное смещение ко всем звездам в чанке
                chunk.update(offset_x, offset_y)
        
        current_chunk = self.get_chunk_at(player_x, player_y)
        
        # Если игрок перешел в другой чанк
        if current_chunk != self.previous_player_chunk:
            self.previous_player_chunk = current_chunk
            
            # Определяем чанки для загрузки
            chunks_to_load = set()
            cx, cy = current_chunk
            
            for dx in range(-CHUNK_LOAD_RADIUS, CHUNK_LOAD_RADIUS + 1):
                for dy in range(-CHUNK_LOAD_RADIUS, CHUNK_LOAD_RADIUS + 1):
                    if dx*dx + dy*dy <= CHUNK_LOAD_RADIUS * CHUNK_LOAD_RADIUS:
                        chunk_x = (cx + dx) % (WORLD_WIDTH // CHUNK_SIZE)
                        chunk_y = (cy + dy) % (WORLD_HEIGHT // CHUNK_SIZE)
                        chunks_to_load.add((chunk_x, chunk_y))
            
            # Загружаем нужные чанки
            for chunk_key in chunks_to_load:
                if chunk_key not in self.chunks:
                    chunk_x, chunk_y = chunk_key
                    chunk = Chunk(chunk_x, chunk_y)
                    chunk.generate()
                    self.chunks[chunk_key] = chunk
                elif not self.chunks[chunk_key].loaded:
                    self.chunks[chunk_key].generate()
            
            # Выгружаем чанки, которые далеко
            chunks_to_unload = []
            for chunk_key, chunk in self.chunks.items():
                if chunk_key not in chunks_to_load and chunk.loaded:
                    chunks_to_unload.append(chunk_key)
            
            for chunk_key in chunks_to_unload:
                self.chunks[chunk_key].unload()
            
            # Обновляем видимые чанки
            self.visible_chunks = chunks_to_load
    
    def draw(self, screen, camera_x, camera_y):
        """Рисует звезды из загруженных чанков"""
        for chunk_key in self.visible_chunks:
            chunk = self.chunks.get(chunk_key)
            if chunk and chunk.loaded:
                for star in chunk.stars:
                    star.draw(screen, camera_x, camera_y)
    
    def get_all_stars(self):
        """Возвращает все звезды из загруженных чанков (для отладки)"""
        stars = []
        for chunk_key in self.visible_chunks:
            chunk = self.chunks.get(chunk_key)
            if chunk and chunk.loaded:
                stars.extend(chunk.stars)
        return stars