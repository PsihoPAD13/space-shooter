# entities/base.py
import pygame
import math
import random
from settings import *

class EnemyBase:
    """База-улей — генерирует врагов с ограниченным запасом"""
    
    def __init__(self, x, y, base_type='standard'):
        self.x = x
        self.y = y
        self.base_x = x
        self.base_y = y
        self.base_type = base_type
        self.radius = 50
        self.health = 100
        self.max_health = 100
        self.alive = True
        self.stationary = True
        self.saved_to_file = True  # <-- ДОБАВИТЬ: флаг, что база сохранена в файле
        self.removed_from_file = False  # <-- ДОБАВИТЬ: флаг, что база удалена из файла
        
        # Движение
        self.is_moving = False
        self.target_x = x
        self.target_y = y
        self.move_speed = 0.5
        
        # ===== НАСТРОЙКИ УЛЬЯ =====
        # Разное количество врагов для разных типов
        self.max_enemies = {
            'standard': 8,
            'strong': 5,
            'fast': 10,
            'swarm': 15,
        }.get(base_type, 8)
        
        self.current_enemies = self.max_enemies  # Сколько осталось в улье
        self.spawn_rate = {
            'standard': 60,
            'strong': 90,
            'fast': 40,
            'swarm': 30,
        }.get(base_type, 60)
        
        self.spawn_timer = 0
        self.spawn_range = 300
        self.respawn_delay = 300  # 5 секунд до восстановления одного врага
        self.respawn_timer = 0
        
        # Цвет
        self.colors = {
            'standard': (255, 50, 50),
            'strong': (255, 50, 200),
            'fast': (255, 200, 50),
            'swarm': (200, 50, 255),
        }
        self.color = self.colors.get(base_type, (255, 50, 50))
        
        # Типы врагов
        self.spawn_types = {
            'standard': ['scout', 'tank'],
            'strong': ['tank', 'guardian'],
            'fast': ['scout', 'swarmer'],
            'swarm': ['swarmer', 'scout'],
        }
        self.types = self.spawn_types.get(base_type, ['scout'])
        
        self.hit_flash = 0
        
        # Активные враги от этой базы
        self.active_enemies = []
    
    def update(self, enemies, player_x, player_y, spawn_func):
        if not self.alive:
            return
        
        self._update_movement(player_x, player_y)
        
        # Считаем активных врагов от этой базы
        base_id = id(self)
        self.active_enemies = []
        for enemy in enemies:
            if hasattr(enemy, 'base_id') and enemy.base_id == base_id and enemy.health > 0:
                self.active_enemies.append(enemy)
        
        active_count = len(self.active_enemies)
        
        # ===== ЛОГИКА УЛЬЯ =====
        dist_to_player = math.sqrt((self.x - player_x)**2 + (self.y - player_y)**2)
        is_near = dist_to_player < 800  # Радиус активации
        
        if is_near and self.current_enemies > 0:
            # Улей активен — выпускаем врагов
            if active_count < 3:  # Не больше 3 активных врагов одновременно
                self.spawn_timer += 1
                if self.spawn_timer >= self.spawn_rate:
                    enemy_type = random.choice(self.types)
                    
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.uniform(50, self.spawn_range)
                    spawn_x = self.x + math.cos(angle) * distance
                    spawn_y = self.y + math.sin(angle) * distance
                    
                    enemy = spawn_func(spawn_x, spawn_y, enemy_type)
                    if enemy:
                        enemy.base_id = base_id
                        enemies.append(enemy)
                        self.current_enemies -= 1
                        self.spawn_timer = 0
        else:
            # Игрок далеко — враги возвращаются в улей
            self.spawn_timer = 0
            if active_count > 0:
                for enemy in self.active_enemies[:]:
                    # Враги летят к базе
                    dx = self.x - enemy.x
                    dy = self.y - enemy.y
                    dist = math.sqrt(dx**2 + dy**2)
                    
                    if dist < 20:
                        # Враг достиг базы — удаляем и восстанавливаем запас
                        enemy.health = 0
                        enemies.remove(enemy)
                        self.current_enemies = min(self.max_enemies, self.current_enemies + 1)
                    else:
                        # Летим к базе
                        speed = 2
                        enemy.x += (dx / dist) * speed
                        enemy.y += (dy / dist) * speed
        
        # ===== МЕДЛЕННОЕ ВОССТАНОВЛЕНИЕ ЗАПАСА =====
        if self.current_enemies < self.max_enemies and not is_near:
            self.respawn_timer += 1
            if self.respawn_timer >= self.respawn_delay:
                self.current_enemies += 1
                self.respawn_timer = 0
        
        self.hit_flash = max(0, self.hit_flash - 1)
    
    def _update_movement(self, player_x, player_y):
        """База медленно дрейфует"""
        dx = self.x - self.base_x
        dy = self.y - self.base_y
        dist_from_base = math.sqrt(dx**2 + dy**2)
        
        if dist_from_base > 200:
            self.target_x = self.base_x
            self.target_y = self.base_y
            self.is_moving = True
        
        dx_player = self.x - player_x
        dy_player = self.y - player_y
        dist_to_player = math.sqrt(dx_player**2 + dy_player**2)
        
        if dist_to_player < 400:
            angle = math.atan2(dy_player, dx_player)
            self.target_x = self.x + math.cos(angle) * 100
            self.target_y = self.y + math.sin(angle) * 100
            self.is_moving = True
        
        if self.is_moving:
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            dist = math.sqrt(dx**2 + dy**2)
            
            if dist < 2:
                self.is_moving = False
                self.x = self.target_x
                self.y = self.target_y
            else:
                speed = min(self.move_speed, dist)
                self.x += (dx / dist) * speed
                self.y += (dy / dist) * speed
    
    def take_damage(self, enemies, damage=1, chunk_manager=None, save_callback=None):
        """Получение урона с очисткой врагов при уничтожении"""
        self.health -= damage
        self.hit_flash = 10
        
        if self.health <= 0:
            self.alive = False
            self.cleanup_enemies(enemies)
            
            print(f"[BASE] 🟥 БАЗА УНИЧТОЖЕНА! Координаты: ({int(self.x)}, {int(self.y)})")
            
            # ПРЯМОЕ УДАЛЕНИЕ ИЗ ЧАНКА
            if chunk_manager:
                chunk_x = int(self.x // CHUNK_SIZE)
                chunk_y = int(self.y // CHUNK_SIZE)
                chunk = chunk_manager.get_chunk(chunk_x, chunk_y)
                
                print(f"[BASE] Чанк: {chunk.get_chunk_id()}")
                
                if chunk and chunk.loaded:
                    # ПРЯМО ОБНУЛЯЕМ СПИСОК БАЗ В ЧАНКЕ
                    bases = chunk.objects.get('enemy_bases', [])
                    print(f"[BASE] Баз в чанке до удаления: {len(bases)}")
                    
                    # СОЗДАЁМ НОВЫЙ СПИСОК БЕЗ ЭТОЙ БАЗЫ
                    new_bases = []
                    for base_data in bases:
                        if abs(base_data['x'] - self.x) > 10 or abs(base_data['y'] - self.y) > 10:
                            new_bases.append(base_data)
                        else:
                            print(f"[BASE] ✅ Найдена и удалена база из списка!")
                    
                    # ЗАМЕНЯЕМ СПИСОК
                    chunk.objects['enemy_bases'] = new_bases
                    chunk.modified = True
                    
                    print(f"[BASE] Баз в чанке после удаления: {len(new_bases)}")
                    
                    # ПРИНУДИТЕЛЬНО СОХРАНЯЕМ
                    chunk.save(chunk_manager.world_dir)
                    
                    # ПРОВЕРЯЕМ ФАЙЛ
                    import json
                    import os
                    filename = chunk.get_full_path(chunk_manager.world_dir)
                    if os.path.exists(filename):
                        with open(filename, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            bases_in_file = data.get('objects', {}).get('enemy_bases', [])
                            print(f"[BASE] Баз в файле ПОСЛЕ сохранения: {len(bases_in_file)}")
                            
                            # ЕСЛИ В ФАЙЛЕ ВСЁ ЕЩЕ ЕСТЬ БАЗЫ - ПРИНУДИТЕЛЬНО ПЕРЕЗАПИСЫВАЕМ
                            if bases_in_file:
                                print(f"[BASE] ⚠️ В ФАЙЛЕ ОСТАЛИСЬ БАЗЫ! ПРИНУДИТЕЛЬНАЯ ОЧИСТКА...")
                                # Обновляем объект чанка
                                chunk.objects['enemy_bases'] = []
                                chunk.modified = True
                                chunk.save(chunk_manager.world_dir)
                                print(f"[BASE] ✅ Файл принудительно очищен!")
            
            if save_callback:
                save_callback()
            
            return True
        return False
        
    def draw(self, screen, camera_x=0, camera_y=0):
        if not self.alive:
            return
        
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        if screen_x < -self.radius or screen_x > WIDTH + self.radius or \
           screen_y < -self.radius or screen_y > HEIGHT + self.radius:
            return
        
        if self.hit_flash > 0 and self.hit_flash % 2 == 0:
            color = (255, 255, 255)
        else:
            color = self.color
        
        # Внешнее кольцо
        pygame.draw.circle(screen, self.color, 
                         (int(screen_x), int(screen_y)), self.radius, 3)
        
        # Пульсирующее внутреннее кольцо
        pulse = 1 + 0.1 * math.sin(pygame.time.get_ticks() * 0.003)
        inner_radius = int(self.radius * 0.6 * pulse)
        pygame.draw.circle(screen, self.color, 
                         (int(screen_x), int(screen_y)), inner_radius, 2)
        
        # Центр
        pygame.draw.circle(screen, self.color, 
                         (int(screen_x), int(screen_y)), 8)
        
        # ===== ИНДИКАТОР ЗАПАСА ВРАГОВ =====
        # Круговой индикатор
        start_angle = -90  # Вверх
        percent = self.current_enemies / self.max_enemies
        
        for i in range(self.max_enemies):
            angle = start_angle + (i / self.max_enemies) * 360
            rad = math.radians(angle)
            dot_x = screen_x + math.cos(rad) * (self.radius + 10)
            dot_y = screen_y + math.sin(rad) * (self.radius + 10)
            
            if i < self.current_enemies:
                color_dot = (50, 255, 50)
            else:
                color_dot = (50, 50, 50)
            
            pygame.draw.circle(screen, color_dot, (int(dot_x), int(dot_y)), 3)
        
        # Полоса здоровья
        bar_width = 40
        bar_height = 4
        bar_x = screen_x - bar_width // 2
        bar_y = screen_y - self.radius - 12
        health_percent = self.health / self.max_health
        
        pygame.draw.rect(screen, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 255, 0), 
                        (bar_x, bar_y, bar_width * health_percent, bar_height))
        
        # Тип базы
        font = pygame.font.Font(None, 20)
        label = f"{self.base_type[0].upper()}{self.current_enemies}"
        text = font.render(label, True, (255, 255, 255))
        text_rect = text.get_rect(center=(int(screen_x), int(screen_y)))
        screen.blit(text, text_rect)
    
    def cleanup_enemies(self, enemies):
        removed = 0
        base_id = id(self)
        for enemy in enemies[:]:
            if hasattr(enemy, 'base_id') and enemy.base_id == base_id:
                enemies.remove(enemy)
                removed += 1
        print(f"[BASE] Удалено {removed} врагов улья")
        return removed