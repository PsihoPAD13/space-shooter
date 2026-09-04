# entities/base.py
import pygame
import math
import random
from settings import *

class EnemyBase:
    """База-улей с гексагональным дизайном и возможностью соединения"""
    
    # Соседние позиции для гексагональной сетки
    HEX_DIRECTIONS = [
        (1, 0), (0.5, 0.866), (-0.5, 0.866),
        (-1, 0), (-0.5, -0.866), (0.5, -0.866)
    ]
    
    def __init__(self, x, y, base_type='standard', parent=None):
        self.x = x
        self.y = y
        self.base_x = x
        self.base_y = y
        self.base_type = base_type
        self.radius = 45
        self.health = 100
        self.max_health = 100
        self.alive = True
        self.stationary = True
        # Уникальный ID для связи с файлом
        self.unique_id = f"{int(x)}_{int(y)}_{base_type}"  # <-- УНИКАЛЬНЫЙ ID
                
        # Движение (ДОБАВИТЬ ЭТИ СТРОКИ)
        self.is_moving = False
        self.target_x = x
        self.target_y = y
        self.move_speed = 0.5
        
        # Связи с другими базами
        self.parent = parent  # Главная база в комплексе
        self.children = []    # Дочерние базы
        self.connected = False
        self.connection_distance = self.radius * 1.8
        
        # Настройки улья
        self.max_enemies = {
            'standard': 6,
            'strong': 4,
            'fast': 8,
            'swarm': 10,
        }.get(base_type, 6)
        
        self.current_enemies = self.max_enemies
        self.spawn_rate = {
            'standard': 60,
            'strong': 90,
            'fast': 40,
            'swarm': 30,
        }.get(base_type, 60)
        
        self.spawn_timer = 0
        self.spawn_range = 250
        self.respawn_delay = 300
        self.respawn_timer = 0
        
        # Цвета
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
        self.active_enemies = []
        self.pulse = 0
        self.module_angle = 0
        
        # Если есть родитель - копируем его цвет
        if parent:
            self.color = parent.color
            self.base_type = parent.base_type
            self.connected = True
    
    def get_hex_center(self, direction):
        """Получить позицию соседнего гексагона"""
        dx, dy = self.HEX_DIRECTIONS[direction]
        return (self.x + dx * self.connection_distance, 
                self.y + dy * self.connection_distance)
    
    def connect_to(self, other):
        """Соединить две базы (other становится дочерней)"""
        if other not in self.children and other != self.parent:
            self.children.append(other)
            other.parent = self
            other.connected = True
            other.color = self.color
            other.base_type = self.base_type
            from settings import DEBUG_MODE
            if DEBUG_MODE:
                print(f"[BASE] 🔗 Соединены: ({int(self.x)}, {int(self.y)}) -> ({int(other.x)}, {int(other.y)})")
                
    def is_connected_to(self, other):
        """Проверить соединение"""
        return other in self.children or self.parent == other
    
    def get_complex_size(self):
        """Получить размер комплекса"""
        size = 1
        for child in self.children:
            size += child.get_complex_size()
        return size
    
    def update(self, enemies, player_x, player_y, spawn_func):
        if not self.alive:
            return
        
        self._update_movement(player_x, player_y)
        self.pulse += 0.02
        self.module_angle += 0.01
        
        # Считаем активных врагов
        base_id = id(self)
        self.active_enemies = []
        for enemy in enemies:
            if hasattr(enemy, 'base_id') and enemy.base_id == base_id and enemy.health > 0:
                self.active_enemies.append(enemy)
        
        active_count = len(self.active_enemies)
        dist_to_player = math.sqrt((self.x - player_x)**2 + (self.y - player_y)**2)
        is_near = dist_to_player < 700
        
        # Спавн врагов
        if is_near and self.current_enemies > 0:
            if active_count < 3:
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
            self.spawn_timer = 0
            if active_count > 0:
                for enemy in self.active_enemies[:]:
                    dx = self.x - enemy.x
                    dy = self.y - enemy.y
                    dist = math.sqrt(dx**2 + dy**2)
                    if dist < 20:
                        enemy.health = 0
                        enemies.remove(enemy)
                        self.current_enemies = min(self.max_enemies, self.current_enemies + 1)
                    else:
                        speed = 2
                        enemy.x += (dx / dist) * speed
                        enemy.y += (dy / dist) * speed
        
        if self.current_enemies < self.max_enemies and not is_near:
            self.respawn_timer += 1
            if self.respawn_timer >= self.respawn_delay:
                self.current_enemies += 1
                self.respawn_timer = 0
        
        self.hit_flash = max(0, self.hit_flash - 1)
        
        # Обновляем дочерние базы
        for child in self.children[:]:
            if child.alive:
                child.update(enemies, player_x, player_y, spawn_func)
    
    def cleanup_enemies(self, enemies):
        """Удаляет всех врагов, привязанных к этой базе"""
        removed = 0
        base_id = id(self)
        for enemy in enemies[:]:
            if hasattr(enemy, 'base_id') and enemy.base_id == base_id:
                enemies.remove(enemy)
                removed += 1
        
        # Также удаляем врагов дочерних баз
        for child in self.children:
            if child.alive:
                child.cleanup_enemies(enemies)
        
        return removed
    
    def _update_movement(self, player_x, player_y):
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
        self.health -= damage
        self.hit_flash = 10
        
        if self.health <= 0:
            self.alive = False
            self.cleanup_enemies(enemies)
            
            print(f"[BASE] 🟥 БАЗА УНИЧТОЖЕНА! Координаты: ({int(self.x)}, {int(self.y)})")
            print(f"[BASE] Unique ID: {self.unique_id}")
            
            # Удаляем из родителя
            if self.parent:
                if self in self.parent.children:
                    self.parent.children.remove(self)
                self.parent = None
            
            # Удаляем из файла
            if chunk_manager and not hasattr(self, 'removed_from_file'):
                chunk_x = int(self.x // CHUNK_SIZE)
                chunk_y = int(self.y // CHUNK_SIZE)
                chunk = chunk_manager.get_chunk(chunk_x, chunk_y)
                
                print(f"[BASE] Чанк: {chunk.get_chunk_id()}")
                
                if chunk and chunk.loaded:
                    bases = chunk.objects.get('enemy_bases', [])
                    print(f"[BASE] Баз в чанке ДО удаления: {len(bases)}")
                    
                    # Ищем базу по unique_id
                    found = False
                    for i, base_data in enumerate(bases):
                        if base_data.get('unique_id') == self.unique_id:
                            print(f"[BASE] Найдена база по unique_id!")
                            del bases[i]
                            found = True
                            chunk.modified = True
                            self.removed_from_file = True
                            print(f"[BASE] Баз в чанке ПОСЛЕ удаления: {len(bases)}")
                            break
                    
                    if found:
                        chunk.save(chunk_manager.world_dir)
                        print(f"[BASE] ✅ Чанк сохранён после удаления базы")
                    else:
                        print(f"[BASE] ⚠️ База НЕ НАЙДЕНА по unique_id!")
                        # Принудительно удаляем по координатам
                        new_bases = []
                        for b in bases:
                            dx = abs(b['x'] - self.x)
                            dy = abs(b['y'] - self.y)
                            if dx >= 10 or dy >= 10:
                                new_bases.append(b)
                        chunk.objects['enemy_bases'] = new_bases
                        chunk.modified = True
                        chunk.save(chunk_manager.world_dir)
                        print(f"[BASE] ✅ Принудительно удалены близкие базы")
                else:
                    print(f"[BASE] ⚠️ Чанк не загружен!")
            
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
        
        pulse_scale = 1 + 0.05 * math.sin(self.pulse)
        base_radius = int(self.radius * pulse_scale)
        
        # Рисуем связи с дочерними базами
        if self.children:
            for child in self.children:
                if child.alive:
                    child_screen_x = child.x - camera_x
                    child_screen_y = child.y - camera_y
                    
                    # Энергетическая линия
                    pygame.draw.line(screen, (60, 60, 120), 
                                   (screen_x, screen_y), 
                                   (child_screen_x, child_screen_y), 2)
                    
                    # Эффект энергии (бегущая точка)
                    t = (pygame.time.get_ticks() % 1000) / 1000
                    energy_x = screen_x + (child_screen_x - screen_x) * t
                    energy_y = screen_y + (child_screen_y - screen_y) * t
                    pygame.draw.circle(screen, (150, 150, 255), 
                                     (int(energy_x), int(energy_y)), 4)
                                     
        # ===== 1. СОЕДИНИТЕЛЬНЫЕ ЛИНИИ =====
        if self.connected and self.parent:
            # Линия к родителю
            parent_screen_x = self.parent.x - camera_x
            parent_screen_y = self.parent.y - camera_y
            pygame.draw.line(screen, (60, 60, 100), 
                           (screen_x, screen_y), 
                           (parent_screen_x, parent_screen_y), 3)
            
            # Эффект энергии на линии
            t = (pygame.time.get_ticks() % 1000) / 1000
            energy_x = screen_x + (parent_screen_x - screen_x) * t
            energy_y = screen_y + (parent_screen_y - screen_y) * t
            pygame.draw.circle(screen, (150, 150, 255), 
                             (int(energy_x), int(energy_y)), 4)
        
        # ===== 2. ВНЕШНИЙ ГЕКСАГОН =====
        hex_points = []
        for i in range(6):
            angle = math.radians(60 * i - 30 + self.module_angle * 20)
            px = screen_x + math.cos(angle) * base_radius
            py = screen_y + math.sin(angle) * base_radius
            hex_points.append((px, py))
        
        # Тень гексагона
        shadow_points = [(px + 2, py + 2) for px, py in hex_points]
        pygame.draw.polygon(screen, (20, 20, 40), shadow_points)
        
        # Основной гексагон
        pygame.draw.polygon(screen, color, hex_points, 3)
        pygame.draw.polygon(screen, (100, 100, 150), hex_points, 1)
        
        # ===== 3. ВНУТРЕННИЕ МОДУЛИ =====
        module_radius = int(base_radius * 0.22)
        for i in range(6):
            angle = math.radians(60 * i + self.module_angle * 20)
            mx = screen_x + math.cos(angle) * base_radius * 0.6
            my = screen_y + math.sin(angle) * base_radius * 0.6
            
            mod_points = []
            for j in range(6):
                a = math.radians(60 * j + 30)
                px = mx + math.cos(a) * module_radius
                py = my + math.sin(a) * module_radius
                mod_points.append((px, py))
            
            if i < self.current_enemies % 6:
                mod_color = color
            else:
                mod_color = (40, 40, 60)
            
            pygame.draw.polygon(screen, mod_color, mod_points, 2)
            pygame.draw.polygon(screen, (80, 80, 120), mod_points, 1)
        
        # ===== 4. ЦЕНТР =====
        pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), int(base_radius * 0.2), 2)
        pygame.draw.circle(screen, (50, 50, 80), (int(screen_x), int(screen_y)), int(base_radius * 0.15))
        
        cross_size = int(base_radius * 0.15)
        pygame.draw.line(screen, color, 
                       (screen_x - cross_size, screen_y), 
                       (screen_x + cross_size, screen_y), 2)
        pygame.draw.line(screen, color, 
                       (screen_x, screen_y - cross_size), 
                       (screen_x, screen_y + cross_size), 2)
        
        # ===== 5. ИНДИКАТОР ЗАПАСА ВРАГОВ =====
        for i in range(self.max_enemies):
            angle = -math.pi / 2 + (i / self.max_enemies) * 2 * math.pi
            dot_x = screen_x + math.cos(angle) * (base_radius + 12)
            dot_y = screen_y + math.sin(angle) * (base_radius + 12)
            
            if i < self.current_enemies:
                dot_color = (50, 255, 50)
                dot_size = 4
            else:
                dot_color = (30, 30, 30)
                dot_size = 3
            
            pygame.draw.circle(screen, dot_color, (int(dot_x), int(dot_y)), dot_size)
        
        # ===== 6. ПОЛОСА ЗДОРОВЬЯ =====
        bar_width = 50
        bar_height = 5
        bar_x = screen_x - bar_width // 2
        bar_y = screen_y - base_radius - 15
        health_percent = self.health / self.max_health
        
        pygame.draw.rect(screen, (40, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        if health_percent > 0.5:
            health_color = (0, 255, 50)
        elif health_percent > 0.25:
            health_color = (255, 200, 50)
        else:
            health_color = (255, 50, 50)
        pygame.draw.rect(screen, health_color, 
                        (bar_x, bar_y, int(bar_width * health_percent), bar_height))
        pygame.draw.rect(screen, (80, 80, 100), (bar_x, bar_y, bar_width, bar_height), 1)
        
        # ===== 7. ТИП И РАЗМЕР КОМПЛЕКСА =====
        font = pygame.font.Font(None, 16)
        if self.parent:
            label = f"{self.get_complex_size()}x"
        else:
            label = f"{self.base_type[0].upper()}{self.current_enemies}/{self.max_enemies}"
        text = font.render(label, True, (200, 200, 220))
        text_rect = text.get_rect(center=(int(screen_x), int(screen_y + base_radius + 25)))
        screen.blit(text, text_rect)