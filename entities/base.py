# entities/base.py
import pygame
import math
import random
from settings import *

class EnemyBase:
    """База врагов — генератор врагов в мире"""
    
    def __init__(self, x, y, base_type='standard'):
        self.x = x
        self.y = y
        self.base_type = base_type
        self.radius = 50
        self.health = 100
        self.max_health = 100
        self.alive = True
        
        # Настройки базы
        self.spawn_rate = 60  # Кадров между спавнами
        self.spawn_timer = 0
        self.max_enemies = 5  # Максимум врагов от этой базы
        self.enemies_spawned = []  # Ссылки на врагов (для контроля)
        self.spawn_range = 300  # Радиус спавна вокруг базы
        
        # Цвет зависит от типа
        self.colors = {
            'standard': (255, 50, 50),
            'strong': (255, 50, 200),
            'fast': (255, 200, 50),
            'swarm': (200, 50, 255),
        }
        self.color = self.colors.get(base_type, (255, 50, 50))
        
        # Типы врагов, которых спавнит база
        self.spawn_types = {
            'standard': ['scout', 'tank'],
            'strong': ['tank', 'guardian'],
            'fast': ['scout', 'swarmer'],
            'swarm': ['swarmer', 'scout'],
        }
        self.types = self.spawn_types.get(base_type, ['scout'])
    
    def update(self, enemies, player_x, player_y, spawn_func):
        """Обновляет базу — спавнит врагов с контролем количества"""
        if not self.alive:
            return
        
        # ===== СЧИТАЕМ ТОЛЬКО ЖИВЫХ ВРАГОВ ОТ ЭТОЙ БАЗЫ =====
        alive_enemies = []
        for enemy in enemies:
            # Проверяем, что враг жив и создан этой базой
            if hasattr(enemy, 'base_id') and enemy.base_id == id(self) and enemy.health > 0:
                alive_enemies.append(enemy)
        
        alive_count = len(alive_enemies)
        
        # ===== ЕСЛИ ВРАГОВ МЕНЬШЕ МАКСИМУМА — СПАВНИМ =====
        if alive_count < self.max_enemies:
            self.spawn_timer += 1
            if self.spawn_timer >= self.spawn_rate:
                # Выбираем тип врага
                enemy_type = random.choice(self.types)
                
                # Позиция вокруг базы
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(50, self.spawn_range)
                spawn_x = self.x + math.cos(angle) * distance
                spawn_y = self.y + math.sin(angle) * distance
                
                # Создаём врага
                enemy = spawn_func(spawn_x, spawn_y, enemy_type)
                if enemy:
                    enemy.base_id = id(self)  # Привязываем к базе
                    enemies.append(enemy)
                    self.spawn_timer = 0
                    print(f"[BASE] Спавн {enemy_type} (всего живых: {alive_count + 1}/{self.max_enemies})")
    
    def take_damage(self, enemies, damage=1):
        """Получение урона с очисткой врагов при уничтожении"""
        self.health -= damage
        
        if hasattr(self, 'hit_flash'):
            self.hit_flash = 10
        
        if self.health <= 0:
            self.alive = False
            # Очищаем врагов базы
            self.cleanup_enemies(enemies)
            print(f"[BASE] База уничтожена! Очищено врагов")
            return True
        return False
    
    def draw(self, screen, camera_x=0, camera_y=0):
        """Рисует базу с эффектами"""
        if not self.alive:
            return
        
        # Обновляем мигание
        if hasattr(self, 'hit_flash') and self.hit_flash > 0:
            self.hit_flash -= 1
        
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        if screen_x < -self.radius or screen_x > WIDTH + self.radius or \
           screen_y < -self.radius or screen_y > HEIGHT + self.radius:
            return
        
        # Если база мигает — рисуем белым
        if hasattr(self, 'hit_flash') and self.hit_flash > 0 and self.hit_flash % 2 == 0:
            color = (255, 255, 255)
        else:
            color = self.color
        
        # Внешнее кольцо
        pygame.draw.circle(screen, self.color, 
                         (int(screen_x), int(screen_y)), self.radius, 3)
        
        # Внутреннее кольцо (пульсирует)
        pulse = 1 + 0.1 * math.sin(pygame.time.get_ticks() * 0.003)
        inner_radius = int(self.radius * 0.6 * pulse)
        pygame.draw.circle(screen, self.color, 
                         (int(screen_x), int(screen_y)), inner_radius, 2)
        
        # Центр
        pygame.draw.circle(screen, self.color, 
                         (int(screen_x), int(screen_y)), 8)
        
        # Полоса здоровья
        bar_width = 40
        bar_height = 4
        bar_x = screen_x - bar_width // 2
        bar_y = screen_y - self.radius - 12
        health_percent = self.health / self.max_health
        
        pygame.draw.rect(screen, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 255, 0), 
                        (bar_x, bar_y, bar_width * health_percent, bar_height))
        
        # Тип базы (буква)
        font = pygame.font.Font(None, 20)
        label = self.base_type[0].upper()
        text = font.render(label, True, (255, 255, 255))
        text_rect = text.get_rect(center=(int(screen_x), int(screen_y)))
        screen.blit(text, text_rect)
        
    def cleanup_enemies(self, enemies):
        """Удаляет всех врагов, привязанных к этой базе"""
        removed = 0
        for enemy in enemies[:]:
            if hasattr(enemy, 'base_id') and enemy.base_id == id(self):
                # Удаляем врага (можно добавить эффект исчезновения)
                enemies.remove(enemy)
                removed += 1
        if removed > 0:
            print(f"[BASE] Удалено {removed} врагов при уничтожении базы")
        return removed