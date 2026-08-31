# world/chunk_manager.py
import pygame
import os
import random
import math
from settings import CHUNK_SIZE, CHUNK_LOAD_RADIUS, WIDTH, HEIGHT, DEBUG_MODE
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
            if DEBUG_MODE:
                print(f"[CHUNK] Загружен чанк {chunk.get_chunk_id()} с {len(chunk.objects['enemy_bases'])} базами")
        
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
        
        # При выгрузке чанков — сохраняем только изменённые
        for key in list(self.chunks.keys()):
            if key not in chunks_to_keep:
                chunk = self.chunks[key]
                if chunk.modified:
                    chunk.save(self.world_dir)  # <-- СОХРАНЯЕМ ТОЛЬКО ИЗМЕНЁННЫЕ
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
        
        if DEBUG_MODE:
            print(f"[CHUNK] Загрузка объектов в радиусе {radius} от ({int(player_x)}, {int(player_y)})")
        
        for dx in range(-chunk_radius, chunk_radius + 1):
            for dy in range(-chunk_radius, chunk_radius + 1):
                cx = chunk_x + dx
                cy = chunk_y + dy
                
                chunk = self.get_chunk(cx, cy)
                if not chunk.generated:
                    chunk.generate()
                    chunk.save(self.world_dir)
                if DEBUG_MODE:
                        print(f"[CHUNK] ✅ СОХРАНЁН чанк {chunk.get_chunk_id()} после генерации")
                
                # Проверяем объекты в чанке
                bases = chunk.objects.get('enemy_bases', [])
                asteroids = chunk.objects.get('asteroids', [])
                
                if DEBUG_MODE and (bases or asteroids):
                    print(f"[CHUNK] Чанк {chunk.get_chunk_id()}: {len(bases)} баз, {len(asteroids)} астероидов")
                
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
                
                for resource in resources:
                    dist = math.sqrt((resource['x'] - player_x)**2 + (resource['y'] - player_y)**2)
                    if dist < radius:
                        exists = False
                        for existing in result['resources']:
                            if abs(existing['x'] - resource['x']) < 10 and abs(existing['y'] - resource['y']) < 10:
                                exists = True
                                break
                        if not exists:
                            result['resources'].append(resource)
        
        if DEBUG_MODE:
            print(f"[CHUNK] Итог: {len(result['enemy_bases'])} баз, {len(result['asteroids'])} астероидов, {len(result['resources'])} ресурсов")
        
        return result
    
    def draw_debug_grid(self, screen, camera_x, camera_y, player_x, player_y):
        """Рисует отладочную сетку чанков"""
        if not DEBUG_MODE:
            return
        
        if self.config is None:
            return
        
        if not self.config.get('game.debug_mode', False):
            return
        
        font = pygame.font.Font(None, 16)  # <-- Теперь pygame импортирован
        
        start_x = int((camera_x) // CHUNK_SIZE) - 1
        start_y = int((camera_y) // CHUNK_SIZE) - 1
        end_x = int((camera_x + WIDTH) // CHUNK_SIZE) + 1
        end_y = int((camera_y + HEIGHT) // CHUNK_SIZE) + 1
        
        for cx in range(start_x, end_x + 1):
            for cy in range(start_y, end_y + 1):
                chunk_x = cx * CHUNK_SIZE - camera_x
                chunk_y = cy * CHUNK_SIZE - camera_y
                
                key = (cx, cy)
                is_generated = key in self.chunks and self.chunks[key].generated
                
                if cx == 0 and cy == 0:
                    color = (0, 255, 0)
                elif is_generated:
                    color = (255, 255, 255)
                else:
                    color = (100, 100, 100)
                
                rect = pygame.Rect(chunk_x, chunk_y, CHUNK_SIZE, CHUNK_SIZE)
                pygame.draw.rect(screen, color, rect, 1)
                
                if cx % 2 == 0 and cy % 2 == 0:
                    label = f"{cx},{cy}"
                    text = font.render(label, True, (100, 100, 100))
                    screen.blit(text, (chunk_x + 5, chunk_y + 5))
                
                has_base = False
                if key in self.chunks and self.chunks[key].loaded:
                    if self.chunks[key].objects.get('enemy_bases'):
                        has_base = True
                
                if has_base:
                    pygame.draw.circle(screen, (255, 0, 0), 
                                     (int(chunk_x + CHUNK_SIZE//2), int(chunk_y + CHUNK_SIZE//2)), 
                                     10, 2)
                    base_count = len(self.chunks[key].objects.get('enemy_bases', []))
                    count_text = font.render(str(base_count), True, (255, 0, 0))
                    screen.blit(count_text, (chunk_x + CHUNK_SIZE//2 - 5, chunk_y + CHUNK_SIZE//2 - 10))
        
        player_chunk_x = int(player_x // CHUNK_SIZE)
        player_chunk_y = int(player_y // CHUNK_SIZE)
        pos_text = font.render(f"Player chunk: {player_chunk_x}, {player_chunk_y}", True, (255, 255, 0))
        screen.blit(pos_text, (10, HEIGHT - 80))
        
    def check_saved_chunks(self):
        """Проверяет, какие чанки сохранены на диск"""
        if not DEBUG_MODE:
            return
        
        import os
        saved_count = 0
        for chunk in self.chunks.values():
            filename = chunk.get_full_path(self.world_dir)
            if os.path.exists(filename):
                saved_count += 1
                if DEBUG_MODE:
                    print(f"[CHUNK] ✅ Чанк {chunk.get_chunk_id()} сохранён в {filename}")
            else:
                if DEBUG_MODE:
                    print(f"[CHUNK] ❌ Чанк {chunk.get_chunk_id()} НЕ сохранён!")
        
        print(f"[CHUNK] Сохранено чанков: {saved_count}/{len(self.chunks)}")
        
    def remove_base_from_chunk(self, base_x, base_y):
        """Удаляет базу из чанка по координатам и сохраняет"""
        from settings import DEBUG_MODE
        
        chunk_x = int(base_x // CHUNK_SIZE)
        chunk_y = int(base_y // CHUNK_SIZE)
        chunk = self.get_chunk(chunk_x, chunk_y)
        
        if chunk and chunk.loaded:
            result = chunk.remove_base(base_x, base_y, self.world_dir)
            if DEBUG_MODE and result:
                print(f"[CHUNK] ✅ База удалена из чанка {chunk.get_chunk_id()} и сохранена")
            return result
        return False
        
    def save_modified_chunks(self):
        """Сохраняет только изменённые чанки"""
        print(f"[CHUNK] 💾 Сохранение изменённых чанков...")
        
        saved_count = 0
        for chunk in self.chunks.values():
            if chunk.modified and chunk.generated:
                chunk.save(self.world_dir)
                saved_count += 1
                print(f"[CHUNK] 💾 Сохранён чанк {chunk.get_chunk_id()}")
        
        print(f"[CHUNK] 💾 Сохранено {saved_count} чанков")
        return saved_count
        
    def save_chunk_immediately(self, chunk_x, chunk_y):
        """Принудительно сохраняет конкретный чанк на диск"""
        from settings import DEBUG_MODE
        
        chunk = self.get_chunk(chunk_x, chunk_y)
        if chunk and chunk.generated:
            chunk.save(self.world_dir)
            if DEBUG_MODE:
                print(f"[CHUNK] ✅ Принудительно сохранён чанк ({chunk_x}, {chunk_y})")
            return True
        return False
        