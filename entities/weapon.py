# entities/weapon.py
import pygame
import math
from settings import *

class Weapon:
    def __init__(self, weapon_id, sprite_manager, slot_offset=(0, 0)):
        self.weapon_id = weapon_id
        self.sprite_manager = sprite_manager
        self.slot_offset = slot_offset
        
        # Загружаем данные из JSON
        self.data = sprite_manager.get_sprite_data('weapons', weapon_id)
        if not self.data:
            print(f"[WEAPON] ❌ Не найдено: {weapon_id}")
            self.data = {'type': 'static', 'stats': {'damage': 10}}
        
        self.weapon_type = self.data.get('type', 'static')
        self.sprite = sprite_manager.get(weapon_id)
        self.pivot = self.data.get('pivot', [8, 8])
        self.angle = 0
    
    def aim(self, target_x, target_y, ship_x, ship_y, ship_angle=0):
        if self.weapon_type == 'turret':
            dx = target_x - (ship_x + self.slot_offset[0])
            dy = target_y - (ship_y + self.slot_offset[1])
            self.angle = math.degrees(math.atan2(dy, dx))
        else:
            self.angle = ship_angle
    
    def draw(self, screen, ship_x, ship_y, ship_angle, camera_x=0, camera_y=0):
        ship_angle_rad = math.radians(ship_angle)
        offset_x = self.slot_offset[0] * math.cos(ship_angle_rad) - self.slot_offset[1] * math.sin(ship_angle_rad)
        offset_y = self.slot_offset[0] * math.sin(ship_angle_rad) + self.slot_offset[1] * math.cos(ship_angle_rad)
        
        screen_x = ship_x + offset_x - camera_x
        screen_y = ship_y + offset_y - camera_y
        
        if screen_x < -50 or screen_x > WIDTH + 50 or \
           screen_y < -50 or screen_y > HEIGHT + 50:
            return
        
        if self.sprite:
            # Угол для отрисовки
            if self.weapon_type == 'static':
                draw_angle = ship_angle
            else:
                draw_angle = self.angle
            
            rotated = pygame.transform.rotate(self.sprite, -draw_angle - 90)
            rect = rotated.get_rect(center=(screen_x, screen_y))
            screen.blit(rotated, rect)
            
    def shoot(self, bullets, ship_x, ship_y, ship_angle, ship_speed_x=0, ship_speed_y=0):
        # Определяем угол стрельбы
        if self.weapon_type == 'static':
            angle_rad = math.radians(ship_angle)
        else:
            angle_rad = math.radians(self.angle)
        
        # Позиция пушки с учётом поворота корабля
        ship_angle_rad = math.radians(ship_angle)
        offset_x = self.slot_offset[0] * math.cos(ship_angle_rad) - self.slot_offset[1] * math.sin(ship_angle_rad)
        offset_y = self.slot_offset[0] * math.sin(ship_angle_rad) + self.slot_offset[1] * math.cos(ship_angle_rad)
        
        # Длина ствола (от центра пушки до дула)
        barrel_length = 8
        
        # Позиция вылета пули
        bullet_x = ship_x + offset_x + math.cos(angle_rad) * barrel_length
        bullet_y = ship_y + offset_y + math.sin(angle_rad) * barrel_length
        
        # Скорость пули
        bullet_speed = 10
        speed_x = math.cos(angle_rad) * bullet_speed + ship_speed_x * 0.3
        speed_y = math.sin(angle_rad) * bullet_speed + ship_speed_y * 0.3
        
        from entities.bullet import Bullet
        bullets.append(Bullet(bullet_x, bullet_y, speed_x, speed_y))
        