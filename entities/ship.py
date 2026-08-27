# ship.py
import math
import pygame
import random
from settings import (
    SHIP_ACCELERATION, SHIP_FRICTION, SHIP_MAX_SPEED, 
    SHIP_ROTATION_SPEED, SHIP_RADIUS, SHIP_MAX_HEALTH,
    SHOOT_DELAY, WORLD_WIDTH, WORLD_HEIGHT, 
    WIDTH, HEIGHT,
    WHITE, BLUE, YELLOW, RED, GREEN
)
from entities.bullet import Bullet
from utils import draw_health_bar, wrap_position
from systems.particles import ParticleSystem  # Для аннотации типов

class Ship:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0
        self.speed_x = 0
        self.speed_y = 0
        self.radius = SHIP_RADIUS
        self.health = SHIP_MAX_HEALTH
        self.max_health = SHIP_MAX_HEALTH
        
        self.shoot_cooldown = 0
        self.shoot_delay = SHOOT_DELAY
        
        self.engine_on = False
        self.max_speed = SHIP_MAX_SPEED  # <-- ДОБАВЛЯЕМ
        self.shield_active = False  # <-- ДОБАВЛЯЕМ
    
    def update(self):
        # Применяем трение
        self.speed_x *= SHIP_FRICTION
        self.speed_y *= SHIP_FRICTION
        
        # Ограничиваем скорость с учетом max_speed
        speed = math.sqrt(self.speed_x**2 + self.speed_y**2)
        if speed > self.max_speed:  # <-- ИСПОЛЬЗУЕМ self.max_speed
            self.speed_x = (self.speed_x / speed) * self.max_speed
            self.speed_y = (self.speed_y / speed) * self.max_speed
            
        # Обновляем позицию
        self.x += self.speed_x
        self.y += self.speed_y
        
        # Бесшовная телепортация через края
        wrap_position(self)
        
        # Обновляем кулдаун стрельбы
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
    
    def rotate_left(self):
        self.angle -= SHIP_ROTATION_SPEED
    
    def rotate_right(self):
        self.angle += SHIP_ROTATION_SPEED
    
    def thrust(self):
        angle_rad = math.radians(self.angle)
        self.speed_x += math.cos(angle_rad) * SHIP_ACCELERATION
        self.speed_y += math.sin(angle_rad) * SHIP_ACCELERATION
        self.engine_on = True
    
    def stop_thrust(self):
        self.engine_on = False
    
    def shoot(self, bullets):
        if self.shoot_cooldown == 0:
            angle_rad = math.radians(self.angle)
            offset = self.radius + 5
            
            bullet_x = self.x + math.cos(angle_rad) * offset
            bullet_y = self.y + math.sin(angle_rad) * offset
            
            bullet_speed = 10
            bullets.append(Bullet(
                bullet_x, 
                bullet_y,
                self.speed_x + math.cos(angle_rad) * bullet_speed,
                self.speed_y + math.sin(angle_rad) * bullet_speed
            ))
            self.shoot_cooldown = self.shoot_delay
    
    def draw(self, screen, camera_x=0, camera_y=0, particle_system=None):
        # Координаты с учетом камеры
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        # Если корабль не виден на экране - не рисуем
        if screen_x < -50 or screen_x > WIDTH + 50 or screen_y < -50 or screen_y > HEIGHT + 50:
            return
        
        angle_rad = math.radians(self.angle)
        
        # Нос корабля
        nose_x = screen_x + math.cos(angle_rad) * self.radius
        nose_y = screen_y + math.sin(angle_rad) * self.radius
        
        # Левый и правый борта
        left_angle = angle_rad + math.radians(140)
        right_angle = angle_rad - math.radians(140)
        
        left_x = screen_x + math.cos(left_angle) * self.radius
        left_y = screen_y + math.sin(left_angle) * self.radius
        right_x = screen_x + math.cos(right_angle) * self.radius
        right_y = screen_y + math.sin(right_angle) * self.radius
        
        # Рисуем корпус
        points = [(nose_x, nose_y), (left_x, left_y), (right_x, right_y)]
        pygame.draw.polygon(screen, WHITE, points, 2)
        
        # Рисуем пламя двигателя с частицами
        if self.engine_on and particle_system:
            angle_rad = math.radians(self.angle)
            flame_angle = angle_rad + math.radians(180)
            flame_x = self.x + math.cos(flame_angle) * self.radius
            flame_y = self.y + math.sin(flame_angle) * self.radius
            
            # Создаем частицы двигателя
            particle_system.spawn_spark_trail(
                flame_x, flame_y, 
                (255, 150, 50),  # Оранжевый
                speed=3,
                count=3
            )
            particle_system.spawn_smoke_trail(
                flame_x, flame_y,
                count=2,
                speed=1
            )
        
        # Рисуем кабину
        cockpit_x = screen_x + math.cos(angle_rad) * (self.radius * 0.4)
        cockpit_y = screen_y + math.sin(angle_rad) * (self.radius * 0.4)
        pygame.draw.circle(screen, BLUE, (int(cockpit_x), int(cockpit_y)), 4)
        
        # Полоса здоровья
        draw_health_bar(screen, screen_x, screen_y - self.radius - 10, 
                       self.health, self.max_health)
                       
        # Рисуем щит (если активен)
        if self.shield_active:
            screen_x = self.x - camera_x
            screen_y = self.y - camera_y
            shield_radius = self.radius + 10
            shield_alpha = 50 + 30 * math.sin(pygame.time.get_ticks() * 0.005)
            
            shield_surf = pygame.Surface((shield_radius * 2, shield_radius * 2), pygame.SRCALPHA)
            shield_color = (50, 150, 255, int(shield_alpha))
            pygame.draw.circle(shield_surf, shield_color, 
                             (shield_radius, shield_radius), shield_radius, 3)
            screen.blit(shield_surf, (int(screen_x - shield_radius), int(screen_y - shield_radius)))
