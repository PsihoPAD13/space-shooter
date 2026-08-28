# world/chunk_manager.py
import os
import random
from settings import CHUNK_SIZE, CHUNK_LOAD_RADIUS
from world.chunk import Chunk

class ChunkManager:
    def __init__(self, world_dir='world_data'):
        self.world_dir = world_dir
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
        
        #print(f"[CHUNK] Мир инициализирован, сид: {self.world_seed}")
    
    def get_chunk(self, chunk_x, chunk_y):
        key = (chunk_x, chunk_y)
        
        if key not in self.chunks:
            chunk = Chunk(chunk_x, chunk_y, self.world_seed)
            chunk.load(self.world_dir)
            self.chunks[key] = chunk
            #print(f"[CHUNK] Загружен чанк ({chunk_x}, {chunk_y}), звёзд: {len(chunk.objects['stars'])}")
        
        return self.chunks[key]
    
    def update(self, player_x, player_y):
        """Обновляет загруженные чанки вокруг игрока"""
        # Определяем чанк игрока
        chunk_x = int(player_x // CHUNK_SIZE)
        chunk_y = int(player_y // CHUNK_SIZE)
        
        #print(f"[CHUNK] Игрок в чанке ({chunk_x}, {chunk_y}), позиция: ({player_x:.0f}, {player_y:.0f})")
        
        # Загружаем чанки в радиусе
        chunks_to_keep = set()
        for dx in range(-self.load_radius, self.load_radius + 1):
            for dy in range(-self.load_radius, self.load_radius + 1):
                cx = chunk_x + dx
                cy = chunk_y + dy
                chunks_to_keep.add((cx, cy))
                self.get_chunk(cx, cy)
        
        #print(f"[CHUNK] Загружено чанков: {len(self.chunks)}")
        
        # Выгружаем чанки, которые вышли за радиус
        for key in list(self.chunks.keys()):
            if key not in chunks_to_keep:
                chunk = self.chunks[key]
                if chunk.modified:
                    chunk.save(self.world_dir)
                chunk.unload()
                del self.chunks[key]
        
        #print(f"[CHUNK] После выгрузки: {len(self.chunks)} чанков в памяти")
    
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
        
        #print(f"[CHUNK] Всего звёзд в загруженных чанках: {len(result['stars'])}")
        return result
        
    def get_objects_in_radius(self, player_x, player_y, radius):
        """Получает все объекты в радиусе вокруг игрока"""
        result = {
            'asteroids': [],
            'enemy_bases': [],
            'resources': [],
        }
        
        # Определяем чанки в радиусе
        chunk_radius = int(radius // CHUNK_SIZE) + 1
        chunk_x = int(player_x // CHUNK_SIZE)
        chunk_y = int(player_y // CHUNK_SIZE)
        
        for dx in range(-chunk_radius, chunk_radius + 1):
            for dy in range(-chunk_radius, chunk_radius + 1):
                cx = chunk_x + dx
                cy = chunk_y + dy
                chunk = self.get_chunk(cx, cy)
                
                if chunk and chunk.loaded:
                    # Проверяем расстояние до объектов в чанке
                    for asteroid in chunk.objects.get('asteroids', []):
                        dist = math.sqrt((asteroid['x'] - player_x)**2 + (asteroid['y'] - player_y)**2)
                        if dist < radius:
                            result['asteroids'].append(asteroid)
                    
                    for base in chunk.objects.get('enemy_bases', []):
                        dist = math.sqrt((base['x'] - player_x)**2 + (base['y'] - player_y)**2)
                        if dist < radius:
                            result['enemy_bases'].append(base)
                    
                    for resource in chunk.objects.get('resources', []):
                        dist = math.sqrt((resource['x'] - player_x)**2 + (resource['y'] - player_y)**2)
                        if dist < radius:
                            result['resources'].append(resource)
        
        return result