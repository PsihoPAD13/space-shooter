# world/chunk.py
import json
import os
import random
from settings import CHUNK_SIZE, REGION_CHUNKS

class Chunk:
    """Один чанк мира (8к x 8к пикселей)"""
    
    def __init__(self, chunk_x, chunk_y, seed):
        self.chunk_x = chunk_x
        self.chunk_y = chunk_y
        self.seed = seed
        self.objects = {
            'stars': [],
            'asteroids': [],
            'enemy_bases': [],
            'resources': [],
            'player_base': None,
        }
        self.loaded = False
        self.generated = False
        self.modified = False
    
    def get_world_x(self):
        """Мировая координата X левого края чанка"""
        return self.chunk_x * CHUNK_SIZE
    
    def get_world_y(self):
        """Мировая координата Y верхнего края чанка"""
        return self.chunk_y * CHUNK_SIZE
    
    def generate(self):
        if self.generated:
            return
        
        random.seed(self.seed + self.chunk_x * 100000 + self.chunk_y)
        
        world_x = self.get_world_x()
        world_y = self.get_world_y()
        
        # Звёзды БОЛЬШЕ НЕ ГЕНЕРИРУЕМ — они теперь фоновые
        
        # 1. Астероиды
        if random.random() < 0.4:
            count = random.randint(3, 10)
            for _ in range(count):
                self.objects['asteroids'].append({
                    'x': world_x + random.randint(0, CHUNK_SIZE),
                    'y': world_y + random.randint(0, CHUNK_SIZE),
                    'radius': random.randint(15, 50),
                    'health': random.randint(3, 10)
                })
        
        # 2. База врагов
        if random.random() < 0.1:
            self.objects['enemy_bases'].append({
                'x': world_x + random.randint(200, CHUNK_SIZE - 200),
                'y': world_y + random.randint(200, CHUNK_SIZE - 200),
                'health': 100,
                'spawn_rate': random.randint(30, 60)
            })
        
        # 3. Ресурсы
        for _ in range(random.randint(2, 6)):
            self.objects['resources'].append({
                'x': world_x + random.randint(0, CHUNK_SIZE),
                'y': world_y + random.randint(0, CHUNK_SIZE),
                'type': 'scrap',
                'amount': random.randint(5, 20)
            })
        
        self.generated = True
        self.modified = True
        
    def save(self, world_dir):
        """Сохраняет чанк в файл"""
        if not self.generated:
            return
        
        region_x = self.chunk_x // REGION_CHUNKS
        region_y = self.chunk_y // REGION_CHUNKS
        local_x = self.chunk_x % REGION_CHUNKS
        local_y = self.chunk_y % REGION_CHUNKS
        
        region_dir = f"{world_dir}/regions/region_{region_x}_{region_y}"
        os.makedirs(region_dir, exist_ok=True)
        
        filename = f"{region_dir}/chunk_{local_x}_{local_y}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'chunk_x': self.chunk_x,
                'chunk_y': self.chunk_y,
                'objects': self.objects,
                'seed': self.seed,
                'generated': self.generated,
            }, f, indent=2, ensure_ascii=False)
        
        self.modified = False
    
    def load(self, world_dir):
        """Загружает чанк из файла"""
        region_x = self.chunk_x // REGION_CHUNKS
        region_y = self.chunk_y // REGION_CHUNKS
        local_x = self.chunk_x % REGION_CHUNKS
        local_y = self.chunk_y % REGION_CHUNKS
        
        filename = f"{world_dir}/regions/region_{region_x}_{region_y}/chunk_{local_x}_{local_y}.json"
        
        if not os.path.exists(filename):
            self.generate()
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.objects = data['objects']
                self.seed = data['seed']
                self.generated = data['generated']
                self.loaded = True
                self.modified = False
                #print(f"[CHUNK] Загружен чанк ({self.chunk_x}, {self.chunk_y}) с {len(self.objects['stars'])} звёздами")
        except:
            #print(f"[CHUNK] Ошибка загрузки чанка ({self.chunk_x}, {self.chunk_y}), генерируем заново")
            self.generate()
    
    def unload(self):
        """Выгружает чанк из памяти"""
        if self.modified:
            # Сохраняем изменения
            pass
        self.loaded = False