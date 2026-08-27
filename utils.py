# utils.py
import math
import random
import pygame
from settings import WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT

def distance(obj1, obj2):
    """Расстояние между двумя объектами с учетом телепортации"""
    dx = obj1.x - obj2.x
    dy = obj1.y - obj2.y
    
    # Учитываем телепортацию для расстояния
    if abs(dx) > WORLD_WIDTH / 2:
        dx = WORLD_WIDTH - abs(dx)
        dx = -dx if obj1.x > obj2.x else dx
    if abs(dy) > WORLD_HEIGHT / 2:
        dy = WORLD_HEIGHT - abs(dy)
        dy = -dy if obj1.y > obj2.y else dy
    
    return math.sqrt(dx**2 + dy**2)

def distance_between(x1, y1, x2, y2):
    """Расстояние между двумя точками"""
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

def check_collision(obj1, obj2, margin=0):
    """Проверка столкновения двух кругов с учетом телепортации"""
    return distance(obj1, obj2) < (obj1.radius + obj2.radius + margin)

def wrap_position(obj):
    """Бесшовная телепортация через края мира"""
    if obj.x < 0:
        obj.x = WORLD_WIDTH
    elif obj.x > WORLD_WIDTH:
        obj.x = 0
    
    if obj.y < 0:
        obj.y = WORLD_HEIGHT
    elif obj.y > WORLD_HEIGHT:
        obj.y = 0

def wrap_position_with_offset(obj, offset_x, offset_y):
    """Телепортирует объект и корректирует смещение"""
    if obj.x < 0:
        obj.x = WORLD_WIDTH
        offset_x += WORLD_WIDTH
    elif obj.x > WORLD_WIDTH:
        obj.x = 0
        offset_x -= WORLD_WIDTH
    
    if obj.y < 0:
        obj.y = WORLD_HEIGHT
        offset_y += WORLD_HEIGHT
    elif obj.y > WORLD_HEIGHT:
        obj.y = 0
        offset_y -= WORLD_HEIGHT
    
    return offset_x, offset_y

def spawn_position():
    """Случайная позиция в мире для спавна врагов"""
    x = random.randint(0, WORLD_WIDTH)
    y = random.randint(0, WORLD_HEIGHT)
    return x, y

def draw_health_bar(screen, x, y, current_health, max_health, width=40, height=5):
    """Рисует полоску здоровья"""
    bar_x = x - width // 2
    bar_y = y - 15
    
    # Фон (красный)
    pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, width, height))
    # Заполнение (зеленое)
    health_percent = max(0, current_health / max_health)
    pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, width * health_percent, height))