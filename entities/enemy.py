# enemy.py
import math
import random
import pygame
from settings import (
    ENEMY_RADIUS, ENEMY_BASE_SPEED, ENEMY_MAX_HEALTH,
    ENEMY_SHOOT_DELAY_MIN, ENEMY_SHOOT_DELAY_MAX,
    ENEMY_BULLET_SPEED, WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT,
    RED, GREEN
)
from entities.bullet import Bullet
from utils import draw_health_bar, distance, wrap_position
from entities.enemy_types import ENEMY_TYPES

class Enemy:
    def __init__(self, x, y, enemy_type='scout'):
        # Загружаем данные типа
        type_data = ENEMY_TYPES.get(enemy_type, ENEMY_TYPES['scout'])
        
        self.x = x
        self.y = y
        self.enemy_type = enemy_type
        self.radius = type_data['radius']
        self.health = type_data['health']
        self.max_health = type_data['max_health']
        self.speed = type_data['speed']
        self.color = type_data['color']
        self.behavior = type_data['behavior']
        self.shoot_delay = type_data['shoot_delay']
        self.score_value = type_data['score']
        
        self.shoot_cooldown = random.randint(0, self.shoot_delay)
        
        # Начальное направление
        angle = random.uniform(0, 2 * math.pi)
        self.speed_x = math.cos(angle) * self.speed * 0.5
        self.speed_y = math.sin(angle) * self.speed * 0.5
        
        # Для орбиты
        self.orbit_angle = random.uniform(0, 2 * math.pi)
        self.orbit_radius = random.randint(100, 200)
        
        # Для камикадзе
        self.explosion_radius = 80
        self.is_exploding = False
        
        # Для стационарных
        self.shoot_timer = 0
    
    def update(self, player_x, player_y):
        # Обновляем в зависимости от поведения
        if self.behavior == 'chase':
            self._update_chase(player_x, player_y)
        elif self.behavior == 'stationary':
            self._update_stationary(player_x, player_y)
        elif self.behavior == 'kamikaze':
            self._update_kamikaze(player_x, player_y)
        elif self.behavior == 'orbit':
            self._update_orbit(player_x, player_y)
        
        # Телепортация через края
        wrap_position(self)
        
        # Кулдаун стрельбы
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
    
    def _update_chase(self, player_x, player_y):
        """Преследование игрока"""
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist > 0:
            # Чем дальше, тем сильнее ускорение
            acceleration = 0.05 + 0.02 * (dist / 500)
            self.speed_x += (dx / dist) * min(acceleration, 0.1)
            self.speed_y += (dy / dist) * min(acceleration, 0.1)
            
            # Ограничиваем скорость
            speed = math.sqrt(self.speed_x**2 + self.speed_y**2)
            if speed > self.speed:
                self.speed_x = (self.speed_x / speed) * self.speed
                self.speed_y = (self.speed_y / speed) * self.speed
        
        self.x += self.speed_x
        self.y += self.speed_y
    
    def _update_stationary(self, player_x, player_y):
        """Стоит на месте и стреляет"""
        # Очень медленное движение (дрейф)
        self.x += self.speed_x * 0.02
        self.y += self.speed_y * 0.02
        
        # Если уплыл далеко - телепортируем к игроку
        dx = player_x - self.x
        dy = player_y - self.y
        if math.sqrt(dx**2 + dy**2) > 600:
            self.x = player_x + dx * 0.3
            self.y = player_y + dy * 0.3
    
    def _update_kamikaze(self, player_x, player_y):
        """Летит к игроку и взрывается при приближении"""
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist > 0:
            # Ускоряется к игроку
            acceleration = 0.1
            self.speed_x += (dx / dist) * acceleration
            self.speed_y += (dy / dist) * acceleration
            
            speed = math.sqrt(self.speed_x**2 + self.speed_y**2)
            if speed > self.speed:
                self.speed_x = (self.speed_x / speed) * self.speed
                self.speed_y = (self.speed_y / speed) * self.speed
        
        self.x += self.speed_x
        self.y += self.speed_y
        
        # Проверка на взрыв
        if dist < self.explosion_radius and not self.is_exploding:
            self.is_exploding = True
    
    def _update_orbit(self, player_x, player_y):
        """Кружится вокруг игрока"""
        self.orbit_angle += 0.015
        
        target_x = player_x + math.cos(self.orbit_angle) * self.orbit_radius
        target_y = player_y + math.sin(self.orbit_angle) * self.orbit_radius
        
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist > 0:
            self.speed_x += (dx / dist) * 0.05
            self.speed_y += (dy / dist) * 0.05
            
            speed = math.sqrt(self.speed_x**2 + self.speed_y**2)
            if speed > self.speed:
                self.speed_x = (self.speed_x / speed) * self.speed
                self.speed_y = (self.speed_y / speed) * self.speed
        
        self.x += self.speed_x
        self.y += self.speed_y
    
    def shoot(self, enemy_bullets, player_x, player_y):
        """Стрельба"""
        if self.shoot_cooldown > 0:
            return
        
        # Камикадзе не стреляет
        if self.behavior == 'kamikaze':
            return
        
        # Стационарные стреляют чаще
        if self.behavior == 'stationary':
            self.shoot_cooldown = self.shoot_delay // 2
        else:
            self.shoot_cooldown = self.shoot_delay
        
        # Расчет направления с учетом телепортации
        dx = player_x - self.x
        dy = player_y - self.y
        
        if abs(dx) > WORLD_WIDTH / 2:
            dx = WORLD_WIDTH - abs(dx)
            dx = -dx if self.x > player_x else dx
        if abs(dy) > WORLD_HEIGHT / 2:
            dy = WORLD_HEIGHT - abs(dy)
            dy = -dy if self.y > player_y else dy
        
        dist = math.sqrt(dx**2 + dy**2)
        if dist > 0:
            # Разная скорость пуль для разных врагов
            bullet_speed = ENEMY_BULLET_SPEED
            if self.behavior == 'sniper':
                bullet_speed = ENEMY_BULLET_SPEED * 1.5  # Быстрее
            elif self.behavior == 'tank':
                bullet_speed = ENEMY_BULLET_SPEED * 0.7  # Медленнее
            
            enemy_bullets.append(Bullet(
                self.x,
                self.y,
                (dx / dist) * bullet_speed,
                (dy / dist) * bullet_speed
            ))
    
    def draw(self, screen, camera_x=0, camera_y=0):
        """Рисует врага"""
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        if screen_x < -50 or screen_x > WIDTH + 50 or screen_y < -50 or screen_y > HEIGHT + 50:
            return
        
        # Разные формы для разных типов
        if self.behavior == 'stationary':
            # Квадрат для стационарных
            half = self.radius
            points = [
                (screen_x - half, screen_y - half),
                (screen_x + half, screen_y - half),
                (screen_x + half, screen_y + half),
                (screen_x - half, screen_y + half)
            ]
            pygame.draw.polygon(screen, self.color, points, 2)
            pygame.draw.polygon(screen, self.color, points, 1)
            
        elif self.behavior == 'kamikaze':
            # Треугольник (острие к игроку)
            angle = math.atan2(self.speed_y, self.speed_x)
            points = [
                (screen_x + math.cos(angle) * self.radius, screen_y + math.sin(angle) * self.radius),
                (screen_x + math.cos(angle + 2.5) * self.radius, screen_y + math.sin(angle + 2.5) * self.radius),
                (screen_x + math.cos(angle - 2.5) * self.radius, screen_y + math.sin(angle - 2.5) * self.radius)
            ]
            pygame.draw.polygon(screen, self.color, points, 2)
            pygame.draw.polygon(screen, self.color, points, 1)
            
        else:
            # Ромб для остальных
            points = [
                (screen_x, screen_y - self.radius),
                (screen_x + self.radius, screen_y),
                (screen_x, screen_y + self.radius),
                (screen_x - self.radius, screen_y)
            ]
            pygame.draw.polygon(screen, self.color, points, 2)
            pygame.draw.polygon(screen, self.color, points, 1)
        
        # Полоса здоровья
        if self.max_health > 1:
            draw_health_bar(screen, screen_x, screen_y - self.radius - 8, 
                           self.health, self.max_health, width=30)
        
        # Эффект взрыва для камикадзе
        if self.is_exploding:
            pygame.draw.circle(screen, (255, 200, 50), 
                             (int(screen_x), int(screen_y)), 
                             self.explosion_radius, 3)
    
    def take_damage(self, damage=1):
        """Получение урона"""
        self.health -= damage
        return self.health <= 0
    
    def is_dead(self):
        return self.health <= 0
    
    def destroy(self, particle_system):
        """Уничтожение врага со взрывом"""
        # Взрыв с цветами врага
        colors = [
            self.color,
            (255, 200, 50),
            (255, 255, 255)
        ]
        
        count = 20 if self.radius < 20 else 35
        
        particle_system.spawn_explosion(
            self.x, self.y,
            count=count,
            speed=5,
            colors=colors
        )
        
        # Дополнительные искры для камикадзе
        if self.behavior == 'kamikaze':
            particle_system.spawn_explosion(
                self.x, self.y,
                count=50,
                speed=8,
                colors=[(255, 200, 50), (255, 100, 50), (255, 255, 255)]
            )