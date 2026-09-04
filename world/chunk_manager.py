# world/chunk_manager.py
import pygame
import os
import random
import math
from settings import CHUNK_SIZE, CHUNK_LOAD_RADIUS, WIDTH, HEIGHT
from world.chunk import Chunk

class ChunkManager:
    def __init__(self, world_dir='world_data', config=None):
        self.world_dir = world_dir
        self.config = config
        self.chunks = {}
        self.load_radius = CHUNK_LOAD_RADIUS
        
        os.makedirs(f"{world_dir}/regions", exist_ok=True)
        
        seed_file = f"{world_dir}/world_seed.txt"
        if os.path.exists(seed_file):
            with open(seed_file, 'r') as f:
                self.world_seed = int(f.read().strip())
        else:
            self.world_seed = random.randint(0, 99999999)
            with open(seed_file, 'w') as f:
                f.write(str(self.world_seed))
    
    def get_chunk(self, chunk_x, chunk_y):
        key = (chunk_x, chunk_y)
        
        if key not in self.chunks:
            chunk = Chunk(chunk_x, chunk_y, self.world_seed)
            chunk.load(self.world_dir)
            self.chunks[key] = chunk
        
        return self.chunks[key]
    
    def update(self, player_x, player_y):
        
        chunk_x = int(player_x // CHUNK_SIZE)
        chunk_y = int(player_y // CHUNK_SIZE)
        
        chunks_to_keep = set()
        for dx in range(-self.load_radius, self.load_radius + 1):
            for dy in range(-self.load_radius, self.load_radius + 1):
                cx = chunk_x + dx
                cy = chunk_y + dy
                chunks_to_keep.add((cx, cy))
                chunk = self.get_chunk(cx, cy)
                if not chunk.generated:
                    chunk.generate()
                    chunk.save(self.world_dir)
        
        # Выгружаем чанки, которые вышли из радиуса
        for key in list(self.chunks.keys()):
            if key not in chunks_to_keep:
                chunk = self.chunks[key]
                if chunk.modified:
                    chunk.save(self.world_dir)
                chunk.unload()
                del self.chunks[key]
                
    def save_all(self):
        for chunk in self.chunks.values():
            if chunk.modified:
                chunk.save(self.world_dir)
    
    def get_all_objects(self, player_x, player_y):
        result = {
            'stars': [],
            'asteroids': [],
            'enemy_bases': [],
            'resources': [],
        }
        
        for chunk in self.chunks.values():
            if chunk.loaded:
                for key in result:
                    result[key].extend(chunk.objects.get(key, []))
        
        return result
    
    def load_all_objects_in_radius(self, player_x, player_y, radius):
        """Принудительно загружает все объекты из чанков в радиусе"""
        result = {
            'asteroids': [],
            'enemy_bases': [],
            'resources': [],
        }
        
        chunk_radius = int(radius // CHUNK_SIZE) + 1
        chunk_x = int(player_x // CHUNK_SIZE)
        chunk_y = int(player_y // CHUNK_SIZE)
                
        for dx in range(-chunk_radius, chunk_radius + 1):
            for dy in range(-chunk_radius, chunk_radius + 1):
                cx = chunk_x + dx
                cy = chunk_y + dy
                
                chunk = self.get_chunk(cx, cy)
                if not chunk.generated:
                    chunk.generate()
                    chunk.save(self.world_dir)
                
                # Проверяем объекты в чанке
                bases = chunk.objects.get('enemy_bases', [])
                asteroids = chunk.objects.get('asteroids', [])
                
                for asteroid in asteroids:
                    dist = math.sqrt((asteroid['x'] - player_x)**2 + (asteroid['y'] - player_y)**2)
                    if dist < radius:
                        exists = False
                        for existing in result['asteroids']:
                            if abs(existing['x'] - asteroid['x']) < 10 and abs(existing['y'] - asteroid['y']) < 10:
                                exists = True
                                break
                        if not exists:
                            result['asteroids'].append(asteroid)
                
                for base in bases:
                    dist = math.sqrt((base['x'] - player_x)**2 + (base['y'] - player_y)**2)
                    if dist < radius:
                        exists = False
                        for existing in result['enemy_bases']:
                            if abs(existing['x'] - base['x']) < 10 and abs(existing['y'] - base['y']) < 10:
                                exists = True
                                break
                        if not exists:
                            result['enemy_bases'].append(base)
                
                for resource in chunk.objects.get('resources', []):
                    dist = math.sqrt((resource['x'] - player_x)**2 + (resource['y'] - player_y)**2)
                    if dist < radius:
                        exists = False
                        for existing in result['resources']:
                            if abs(existing['x'] - resource['x']) < 10 and abs(existing['y'] - resource['y']) < 10:
                                exists = True
                                break
                        if not exists:
                            result['resources'].append(resource)
        
        return result
                   
    def remove_base_from_chunk(self, base_x, base_y):
        """Удаляет базу из чанка по координатам и сохраняет"""
        
        chunk_x = int(base_x // CHUNK_SIZE)
        chunk_y = int(base_y // CHUNK_SIZE)
        chunk = self.get_chunk(chunk_x, chunk_y)
        
        if chunk and chunk.loaded:
            return result
        return False
        
    def save_modified_chunks(self):
        """Сохраняет только изменённые чанки"""
        
        saved_count = 0
        for chunk in self.chunks.values():
            if chunk.modified and chunk.generated:
                chunk.save(self.world_dir)
                saved_count += 1
        
        return saved_count
        
    def save_chunk_immediately(self, chunk_x, chunk_y):
        """Принудительно сохраняет конкретный чанк на диск"""
        
        chunk = self.get_chunk(chunk_x, chunk_y)
        if chunk and chunk.generated:
            chunk.save(self.world_dir)
            return True
        return False
        