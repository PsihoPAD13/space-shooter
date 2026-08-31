# world/chunk.py
import json
import os
import random
from settings import CHUNK_SIZE, REGION_CHUNKS, DEBUG_MODE  # <-- ДОБАВИТЬ ИМПОРТ

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
        return self.chunk_x * CHUNK_SIZE
    
    def get_world_y(self):
        return self.chunk_y * CHUNK_SIZE
    
    def get_chunk_id(self):
        return f"({self.chunk_x}, {self.chunk_y})"
    
    def get_filename(self):
        """Возвращает имя файла для сохранения"""
        return f"chunk_{self.chunk_x}_{self.chunk_y}.json"
        
    def get_region_path(self, world_dir):
        """Возвращает путь к папке региона"""
        import math
        region_x = math.floor(self.chunk_x / REGION_CHUNKS)
        region_y = math.floor(self.chunk_y / REGION_CHUNKS)
        return f"{world_dir}/regions/region_{region_x}_{region_y}"
        
    def get_full_path(self, world_dir):
        """Возвращает полный путь к файлу чанка"""
        region_dir = self.get_region_path(world_dir)
        return f"{region_dir}/{self.get_filename()}"
        
    def generate(self):
        if self.generated:
            if DEBUG_MODE:
                print(f"[CHUNK] Чанк {self.get_chunk_id()} уже сгенерирован")
            return
        
        if DEBUG_MODE:
            print(f"[CHUNK] Генерация чанка {self.get_chunk_id()}...")
        
        random.seed(self.seed + self.chunk_x * 100000 + self.chunk_y)
        
        world_x = self.get_world_x()
        world_y = self.get_world_y()
        
        # 1. Астероиды
        if random.random() < 0.6:
            count = random.randint(5, 15)
            for _ in range(count):
                self.objects['asteroids'].append({
                    'x': world_x + random.randint(100, CHUNK_SIZE - 100),
                    'y': world_y + random.randint(100, CHUNK_SIZE - 100),
                    'radius': random.randint(20, 60),
                    'health': random.randint(3, 10)
                })
            if DEBUG_MODE:
                print(f"[CHUNK] Сгенерировано {count} астероидов")
        
        # 2. База врагов (ОДНА на чанк)
        if self.chunk_x == 0 and self.chunk_y == 0:
            if DEBUG_MODE:
                print(f"[CHUNK] Центральный чанк (0,0) - без базы")
        else:
            if random.random() < 0.4:
                base_x = world_x + random.randint(300, CHUNK_SIZE - 300)
                base_y = world_y + random.randint(300, CHUNK_SIZE - 300)
                base_type = random.choice(['standard', 'strong', 'fast', 'swarm'])
                self.objects['enemy_bases'].append({
                    'x': base_x,
                    'y': base_y,
                    'base_type': base_type,
                    'health': 100,
                    'max_health': 100,
                    'current_enemies': {
                        'standard': 8,
                        'strong': 5,
                        'fast': 10,
                        'swarm': 15,
                    }.get(base_type, 8),
                    'max_enemies': {
                        'standard': 8,
                        'strong': 5,
                        'fast': 10,
                        'swarm': 15,
                    }.get(base_type, 8),
                    'spawn_rate': {
                        'standard': 60,
                        'strong': 90,
                        'fast': 40,
                        'swarm': 30,
                    }.get(base_type, 60)
                })
                if DEBUG_MODE:
                    print(f"[CHUNK] База {base_type} в чанке {self.get_chunk_id()} на позиции ({int(base_x)}, {int(base_y)})")
            else:
                if DEBUG_MODE:
                    print(f"[CHUNK] Чанк {self.get_chunk_id()} без базы (шанс не сработал)")
        
        # 3. Ресурсы
        resource_count = random.randint(3, 8)
        for _ in range(resource_count):
            self.objects['resources'].append({
                'x': world_x + random.randint(0, CHUNK_SIZE),
                'y': world_y + random.randint(0, CHUNK_SIZE),
                'type': 'scrap',
                'amount': random.randint(5, 20)
            })
        if DEBUG_MODE:
            print(f"[CHUNK] Сгенерировано {resource_count} ресурсов")
        
        self.generated = True
        self.modified = True
        if DEBUG_MODE:
            print(f"[CHUNK] Чанк {self.get_chunk_id()} сгенерирован!")
    
    def save(self, world_dir):
        """Сохраняет чанк в файл"""
        if not self.generated:
            print(f"[CHUNK] ⚠️ Чанк {self.get_chunk_id()} не сгенерирован")
            return
        
        # ПРОВЕРЯЕМ БАЗЫ НА ЖИВОСТЬ
        bases = self.objects.get('enemy_bases', [])
        # Удаляем базы с health <= 0 или alive = False
        filtered_bases = []
        for base in bases:
            # Проверяем, есть ли такая база в игре
            from core.game import Game  # Временный импорт для проверки
            # Просто проверяем health
            if base.get('health', 100) > 0:
                filtered_bases.append(base)
            else:
                print(f"[CHUNK] 🧹 Удалена мёртвая база ({int(base['x'])}, {int(base['y'])})")
        
        if len(filtered_bases) != len(bases):
            self.objects['enemy_bases'] = filtered_bases
            self.modified = True
            print(f"[CHUNK] 🧹 Очищено {len(bases) - len(filtered_bases)} мёртвых баз")
        
        bases_before = len(bases)
        bases_after = len(filtered_bases)
        print(f"[CHUNK] 💾 Сохранение чанка {self.get_chunk_id()}, баз: {bases_before} -> {bases_after}")
        
        region_dir = self.get_region_path(world_dir)
        os.makedirs(region_dir, exist_ok=True)
        
        filename = self.get_full_path(world_dir)
        
        data = {
            'chunk_x': self.chunk_x,
            'chunk_y': self.chunk_y,
            'objects': self.objects,
            'seed': self.seed,
            'generated': self.generated,
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.modified = False
            print(f"[CHUNK] ✅ Чанк сохранён: {filename}")
            
        except Exception as e:
            print(f"[CHUNK] ❌ ОШИБКА сохранения: {e}")
            
    def load(self, world_dir):
        """Загружает чанк из файла"""
        filename = self.get_full_path(world_dir)
        
        if not os.path.exists(filename):
            if DEBUG_MODE:
                print(f"[CHUNK] Файл {filename} не найден, генерирую новый")
            self.generate()
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.objects = data.get('objects', self.objects)
                self.seed = data.get('seed', self.seed)
                self.generated = data.get('generated', True)
                self.loaded = True
                self.modified = False
                
                if DEBUG_MODE:
                    bases = self.objects.get('enemy_bases', [])
                    print(f"[CHUNK] Загружен чанк {self.get_chunk_id()} из {filename} с {len(bases)} базами")
                    for base in bases:
                        print(f"  - База на ({int(base['x'])}, {int(base['y'])}) типа {base.get('base_type')}")
        except Exception as e:
            if DEBUG_MODE:
                print(f"[CHUNK] Ошибка загрузки чанка {self.get_chunk_id()}: {e}")
            self.generate()
            
    def unload(self):
        if self.modified:
            pass
        self.loaded = False
        
    def remove_base(self, base_x, base_y, world_dir=None):
        """Удаляет базу из объектов чанка по координатам и сохраняет"""
        bases = self.objects.get('enemy_bases', [])
        for i, base_data in enumerate(bases):
            if abs(base_data['x'] - base_x) < 10 and abs(base_data['y'] - base_y) < 10:
                del bases[i]
                self.modified = True
                
                from settings import DEBUG_MODE
                if DEBUG_MODE:
                    print(f"[CHUNK] База удалена из чанка {self.get_chunk_id()}")
                
                # ПРИНУДИТЕЛЬНО СОХРАНЯЕМ
                if world_dir:
                    self.save(world_dir)
                    if DEBUG_MODE:
                        print(f"[CHUNK] ✅ Чанк сохранён после удаления базы")
                return True
        return False
        
        