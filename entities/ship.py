# entities/ship.py
import math
import pygame
import random
from settings import (
    SHIP_ACCELERATION, SHIP_FRICTION, SHIP_MAX_SPEED,
    SHIP_ROTATION_SPEED, SHIP_RADIUS, SHIP_MAX_HEALTH,
    SHOOT_DELAY, WIDTH, HEIGHT,
    WHITE, BLUE, YELLOW, RED, GREEN
)
from entities.bullet import Bullet
from utils import draw_health_bar

class Ship:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0
        self.weapon_angle = 0
        self.speed_x = 0
        self.speed_y = 0
        self.radius = SHIP_RADIUS
        self.health = SHIP_MAX_HEALTH
        self.max_health = SHIP_MAX_HEALTH
        self.max_speed = SHIP_MAX_SPEED
        self.shield_active = False
        self.warp_multiplier = 1.0  # Множитель скорости (1 = норма, 5 = варп)
        self.normal_max_speed = SHIP_MAX_SPEED
        self.warp_max_speed = SHIP_MAX_SPEED * 5
        
        self.shoot_cooldown = 0
        self.shoot_delay = SHOOT_DELAY
        
        self.engine_on = False
    
    def aim_at(self, target_x, target_y):
        """Наводит оружие на цель"""
        dx = target_x - self.x
        dy = target_y - self.y
        
        if dx != 0 or dy != 0:
            self.weapon_angle = math.degrees(math.atan2(dy, dx))
    
    def update(self):
        # Применяем трение
        self.speed_x *= SHIP_FRICTION
        self.speed_y *= SHIP_FRICTION
        
        # Ограничиваем скорость
        speed = math.sqrt(self.speed_x**2 + self.speed_y**2)
        if speed > self.max_speed:
            self.speed_x = (self.speed_x / speed) * self.max_speed
            self.speed_y = (self.speed_y / speed) * self.max_speed
        
        # Обновляем позицию
        self.x += self.speed_x
        self.y += self.speed_y
        
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
            angle_rad = math.radians(self.weapon_angle)
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
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
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
        
        # Корпус
        points = [(nose_x, nose_y), (left_x, left_y), (right_x, right_y)]
        pygame.draw.polygon(screen, WHITE, points, 2)
        
        # Пламя двигателя
        if self.engine_on and particle_system:
            flame_angle = angle_rad + math.radians(180)
            flame_x = self.x + math.cos(flame_angle) * self.radius
            flame_y = self.y + math.sin(flame_angle) * self.radius
            
            particle_system.spawn_spark_trail(
                flame_x, flame_y,
                (255, 150, 50),
                speed=3,
                count=3
            )
            particle_system.spawn_smoke_trail(
                flame_x, flame_y,
                count=2,
                speed=1
            )
        
        # Щит
        if self.shield_active:
            shield_radius = self.radius + 10
            shield_alpha = 50 + 30 * math.sin(pygame.time.get_ticks() * 0.005)
            shield_surf = pygame.Surface((shield_radius * 2, shield_radius * 2), pygame.SRCALPHA)
            shield_color = (50, 150, 255, int(shield_alpha))
            pygame.draw.circle(shield_surf, shield_color,
                             (shield_radius, shield_radius), shield_radius, 3)
            screen.blit(shield_surf, (int(screen_x - shield_radius), int(screen_y - shield_radius)))
        
        # Кабина
        cockpit_x = screen_x + math.cos(angle_rad) * (self.radius * 0.4)
        cockpit_y = screen_y + math.sin(angle_rad) * (self.radius * 0.4)
        pygame.draw.circle(screen, BLUE, (int(cockpit_x), int(cockpit_y)), 4)
        
        # Полоса здоровья
        draw_health_bar(screen, screen_x, screen_y - self.radius - 10,
                       self.health, self.max_health)
                       
    def set_warp(self, active):
        """Включение/выключение варпа"""
        if active:
            self.warp_multiplier = 5.0
            self.max_speed = self.warp_max_speed
        else:
            self.warp_multiplier = 1.0
            self.max_speed = self.normal_max_speed

    def is_warping(self):
        return self.warp_multiplier > 1.0
        
    def get_vertices(self):
        """Возвращает вершины корабля для полигональной коллизии"""
        angle_rad = math.radians(self.angle)
        
        # Нос
        nose_x = self.x + math.cos(angle_rad) * self.radius
        nose_y = self.y + math.sin(angle_rad) * self.radius
        
        # Левый и правый борта
        left_angle = angle_rad + math.radians(140)
        right_angle = angle_rad - math.radians(140)
        
        left_x = self.x + math.cos(left_angle) * self.radius
        left_y = self.y + math.sin(left_angle) * self.radius
        right_x = self.x + math.cos(right_angle) * self.radius
        right_y = self.y + math.sin(right_angle) * self.radius
        
        return [(nose_x, nose_y), (left_x, left_y), (right_x, right_y)]
    
    def get_collision_radius(self):
        """Возвращает радиус коллизии (с учетом щита)"""
        if self.shield_active:
            return self.radius + 10
        return self.radius

    def circle_collision(obj1, obj2, margin=0):
        """Проверка столкновения двух круговых объектов"""
        dx = obj1.x - obj2.x
        dy = obj1.y - obj2.y
        dist = math.sqrt(dx**2 + dy**2)
        return dist < (obj1.radius + obj2.radius + margin)

    def point_in_circle(px, py, circle, margin=0):
        """Проверка, находится ли точка внутри круга"""
        dx = px - circle.x
        dy = py - circle.y
        dist = math.sqrt(dx**2 + dy**2)
        return dist < (circle.radius + margin)

    def circle_polygon_collision(circle, vertices, margin=0):
        """Проверка столкновения круга с многоугольником"""
        # Проверяем вершины многоугольника
        for vx, vy in vertices:
            if point_in_circle(vx, vy, circle, margin):
                return True
        
        # Проверяем ребра многоугольника
        for i in range(len(vertices)):
            x1, y1 = vertices[i]
            x2, y2 = vertices[(i + 1) % len(vertices)]
            if circle_line_collision(circle, x1, y1, x2, y2, margin):
                return True
        
        return False

    def circle_line_collision(circle, x1, y1, x2, y2, margin=0):
        """Проверка столкновения круга с линией"""
        dx = x2 - x1
        dy = y2 - y1
        length_sq = dx**2 + dy**2
        
        if length_sq == 0:
            return point_in_circle(x1, y1, circle, margin)
        
        t = ((circle.x - x1) * dx + (circle.y - y1) * dy) / length_sq
        t = max(0, min(1, t))
        
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        
        return point_in_circle(proj_x, proj_y, circle, margin)

    def get_collision_normal(obj1, obj2):
        """Возвращает нормаль столкновения между двумя объектами"""
        dx = obj2.x - obj1.x
        dy = obj2.y - obj1.y
        dist = math.sqrt(dx**2 + dy**2)
        if dist == 0:
            return (0, -1)
        return (dx / dist, dy / dist)

    def resolve_collision(obj1, obj2, overlap=0.5):
        """Разрешает столкновение, раздвигая объекты"""
        normal = get_collision_normal(obj1, obj2)
        obj1.x -= normal[0] * overlap
        obj1.y -= normal[1] * overlap
        obj2.x += normal[0] * overlap
        obj2.y += normal[1] * overlap