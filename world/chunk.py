# world/chunk.py
import json
import math
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
            'outposts': [],  # <-- ДОБАВЛЯЕМ
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
            return
        
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
        
        # 2. БАЗЫ ВРАГОВ
        if self.chunk_x == 0 and self.chunk_y == 0:
            if DEBUG_MODE:
                print(f"[CHUNK] Центральный чанк (0,0) - без баз")
        else:
            # Больше баз в чанке для комплексов
            base_count = random.choices([0, 1, 2, 3, 4, 5], weights=[10, 20, 25, 20, 15, 10])[0]
            
            if DEBUG_MODE:
                print(f"[CHUNK] Чанк {self.get_chunk_id()}: будет {base_count} баз")
            
            if base_count > 0:
                base_positions = []
                for _ in range(base_count):
                    attempts = 0
                    while attempts < 30:
                        base_x = world_x + random.randint(200, CHUNK_SIZE - 200)
                        base_y = world_y + random.randint(200, CHUNK_SIZE - 200)
                        
                        too_close = False
                        for bx, by in base_positions:
                            dist = math.sqrt((base_x - bx)**2 + (base_y - by)**2)
                            if dist < 350:  # Минимальное расстояние между базами
                                too_close = True
                                break
                        
                        if not too_close:
                            base_positions.append((base_x, base_y))
                            break
                        attempts += 1
                
                # Создаём базы (могут быть разных типов)
                for bx, by in base_positions:
                    base_type = random.choice(['standard', 'strong', 'fast', 'swarm'])
                    self.objects['enemy_bases'].append({
                        'x': bx,
                        'y': by,
                        'base_type': base_type,
                        'unique_id': f"{int(bx)}_{int(by)}_{base_type}",  # <-- УНИКАЛЬНЫЙ ID
                        'health': 100,
                        'max_health': 100,
                        'current_enemies': {
                            'standard': 6,
                            'strong': 4,
                            'fast': 8,
                            'swarm': 10,
                        }.get(base_type, 6),
                        'max_enemies': {
                            'standard': 6,
                            'strong': 4,
                            'fast': 8,
                            'swarm': 10,
                        }.get(base_type, 6),
                        'spawn_rate': {
                            'standard': 60,
                            'strong': 90,
                            'fast': 40,
                            'swarm': 30,
                        }.get(base_type, 60)
                    })
                
                if DEBUG_MODE:
                    print(f"[CHUNK] Чанк {self.get_chunk_id()}: {len(base_positions)} баз")
                    for bx, by in base_positions:
                        print(f"  - База на ({int(bx)}, {int(by)})")
        
        # 3. Ресурсы
        resource_count = random.randint(3, 8)
        for _ in range(resource_count):
            self.objects['resources'].append({
                'x': world_x + random.randint(0, CHUNK_SIZE),
                'y': world_y + random.randint(0, CHUNK_SIZE),
                'type': 'scrap',
                'amount': random.randint(5, 20)
            })
        
        # ===== 4. АВАНПОСТЫ (НОВОЕ) =====
        # Только не в центральном чанке
        if self.chunk_x != 0 or self.chunk_y != 0:
            # 15% шанс на аванпост в чанке
            if random.random() < 0.15:
                outpost_x = world_x + random.randint(200, CHUNK_SIZE - 200)
                outpost_y = world_y + random.randint(200, CHUNK_SIZE - 200)
                outpost_type = random.choice(['trade', 'mission', 'repair'])
                
                self.objects['outposts'].append({
                    'x': outpost_x,
                    'y': outpost_y,
                    'outpost_type': outpost_type,
                    'resources': {
                        'scrap': random.randint(50, 200),
                        'crystal': random.randint(10, 50),
                        'fuel': random.randint(30, 100),
                    },
                    'missions': self._generate_missions_for_outpost()
                })
                
                if DEBUG_MODE:
                    print(f"[CHUNK] Чанк {self.get_chunk_id()} сгенерирован!")
                    print(f"[CHUNK]    Астероидов: {len(self.objects['asteroids'])}")
                    print(f"[CHUNK]    Баз: {len(self.objects['enemy_bases'])}")
                    print(f"[CHUNK]    Аванпостов: {len(self.objects['outposts'])}")
                            
        self.generated = True
        self.modified = True

    def _generate_missions_for_outpost(self):
        """Генерирует миссии для аванпоста"""
        import random
        mission_templates = [
            {
                'type': 'kill',
                'name': 'Очистка сектора',
                'description': 'Уничтожьте 10 врагов в секторе',
                'target': 10,
                'reward': {'scrap': 30, 'crystal': 5},
                'progress': 0,
                'active': True
            },
            {
                'type': 'collect',
                'name': 'Сбор ресурсов',
                'description': 'Соберите 50 единиц скрапа',
                'target': 50,
                'reward': {'scrap': 10, 'crystal': 10},
                'progress': 0,
                'active': True
            },
            {
                'type': 'destroy_base',
                'name': 'Уничтожение базы',
                'description': 'Уничтожьте вражескую базу в секторе',
                'target': 1,
                'reward': {'scrap': 50, 'crystal': 20},
                'progress': 0,
                'active': True
            },
            {
                'type': 'explore',
                'name': 'Исследование',
                'description': 'Посетите 3 новых чанка',
                'target': 3,
                'reward': {'scrap': 20, 'crystal': 15},
                'progress': 0,
                'active': True
            },
        ]
        count = random.randint(2, 3)
        return random.sample(mission_templates, min(count, len(mission_templates)))
        
    def save(self, world_dir):
        """Сохраняет чанк в файл"""
        if not self.generated:
            print(f"[CHUNK] ⚠️ Чанк {self.get_chunk_id()} не сгенерирован")
            return
        
        # Проверяем, что базы действительно удалены из памяти
        bases = self.objects.get('enemy_bases', [])
        print(f"[CHUNK] 💾 Сохранение чанка {self.get_chunk_id()}, баз в памяти: {len(bases)}")
        for b in bases:
            print(f"  - ({int(b['x'])}, {int(b['y'])})")
        
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
            print(f"[CHUNK]    Баз в файле: {len(self.objects.get('enemy_bases', []))}")
            
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
        
        