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
from entities.weapon import Weapon

class Ship:
    def __init__(self, x, y, sprite_manager=None):
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
        self.warp_max_speed = SHIP_MAX_SPEED * 10
        
        self.shoot_cooldown = 0
        self.shoot_delay = SHOOT_DELAY
        
        self.engine_on = False
        
        # Спрайт корабля
        self.sprite_manager = sprite_manager
        self.sprite = None
        self.current_hull = 'player_base'
        self.current_weapon = 'weapon_static'
        self.current_engine = 'engine_small'
        self.current_shield = 'shield_basic'
        
        # Загружаем начальный корпус
        self._apply_hull(self.current_hull)
        
        # Оружие
        self.weapons = []
        self._init_weapons()
            
        self.shoot_cooldown = 0
        self.shoot_delay = SHOOT_DELAY

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
        # Нормализуем угол в диапазон 0-360
        self.angle %= 360
    
    def rotate_right(self):
        self.angle += SHIP_ROTATION_SPEED
        self.angle %= 360
    
    def thrust(self, has_fuel=True):
        """Тяга (только если есть топливо)"""
        if not has_fuel:
            self.engine_on = False
            return
        
        angle_rad = math.radians(self.angle)
        self.speed_x += math.cos(angle_rad) * SHIP_ACCELERATION
        self.speed_y += math.sin(angle_rad) * SHIP_ACCELERATION
        self.engine_on = True
    
    def stop_thrust(self):
        self.engine_on = False
    
    def _apply_hull(self, hull_id):
        """Применяет корпус из JSON"""
        if not self.sprite_manager:
            return
        
        data = self.sprite_manager.get_sprite_data('ships', hull_id)
        if data:
            self.sprite = self.sprite_manager.get(hull_id)
            self.radius = data.get('size', [64, 64])[0] // 2
            self.current_hull = hull_id
            print(f"[SHIP] Корпус: {hull_id}, радиус: {self.radius}")
    
    def _init_weapons(self):
        """Создаёт оружие из слотов корпуса"""
        self.weapons = []
        
        if not self.sprite_manager:
            return
        
        # Получаем слоты из конфига корпуса
        hull_data = self.sprite_manager.get_sprite_data('ships', self.current_hull)
        if not hull_data:
            return
        
        slots = hull_data.get('slots', {})
        for slot_id, slot_data in slots.items():
            if slot_data.get('type') == 'weapon':
                weapon = Weapon(
                    self.current_weapon,
                    self.sprite_manager,
                    (slot_data['x'], slot_data['y'])
                )
                self.weapons.append(weapon)
                print(f"[SHIP] Добавлена пушка в слот {slot_id}")
    
    def set_weapon(self, weapon_id):
        """Меняет оружие на корабле"""
        self.current_weapon = weapon_id
        # Пересоздаём оружие
        self._init_weapons()    
    
    def aim_weapons(self, target_x, target_y):
        """Наводит всё оружие на цель"""
        for weapon in self.weapons:
            weapon.aim(target_x, target_y, self.x, self.y, self.angle)
    
    def shoot(self, bullets):
        if self.shoot_cooldown == 0:
            for weapon in self.weapons:
                weapon.shoot(bullets, self.x, self.y, self.angle, self.speed_x, self.speed_y)
            self.shoot_cooldown = self.shoot_delay
            
    def draw(self, screen, camera_x=0, camera_y=0, particle_system=None):
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        if screen_x < -50 or screen_x > WIDTH + 50 or \
           screen_y < -50 or screen_y > HEIGHT + 50:
            return
        
        angle_rad = math.radians(self.angle)
        
        # ===== РИСУЕМ СПРАЙТ =====
        if self.sprite:
            # Поворачиваем спрайт на 90 градусов, т.к. в Inkscape смотрит вверх
            # А в Pygame 0 градусов = вправо
            rotated = pygame.transform.rotate(self.sprite, -self.angle)  # <-- ИСПРАВЛЕНО
            rect = rotated.get_rect(center=(screen_x, screen_y))
            screen.blit(rotated, rect)
        else:
            # Fallback: ASCII отрисовка
            nose_x = screen_x + math.cos(angle_rad) * self.radius
            nose_y = screen_y + math.sin(angle_rad) * self.radius
            
            left_angle = angle_rad + math.radians(140)
            right_angle = angle_rad - math.radians(140)
            
            left_x = screen_x + math.cos(left_angle) * self.radius
            left_y = screen_y + math.sin(left_angle) * self.radius
            right_x = screen_x + math.cos(right_angle) * self.radius
            right_y = screen_y + math.sin(right_angle) * self.radius
            
            points = [(nose_x, nose_y), (left_x, left_y), (right_x, right_y)]
            pygame.draw.polygon(screen, WHITE, points, 2)
        
        # ===== РИСУЕМ ОРУЖИЕ =====
        for weapon in self.weapons:
            weapon.draw(screen, self.x, self.y, self.angle, camera_x, camera_y)
        
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
            self.warp_multiplier = 10.0
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
