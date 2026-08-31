# utils.py
import math
import random
import pygame
from settings import WIDTH, HEIGHT, CHUNK_SIZE

def distance(obj1, obj2):
    """Расстояние между двумя объектами"""
    dx = obj1.x - obj2.x
    dy = obj1.y - obj2.y
    return math.sqrt(dx**2 + dy**2)

def distance_between(x1, y1, x2, y2):
    """Расстояние между двумя точками"""
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

def check_collision(obj1, obj2, margin=0):
    """Проверка столкновения двух кругов"""
    return distance(obj1, obj2) < (obj1.radius + obj2.radius + margin)

def wrap_position(obj):
    """Телепортация через края (для ограниченного мира)"""
    pass

def spawn_position():
    """Случайная позиция для спавна врагов в бесконечном мире"""
    radius = CHUNK_SIZE * 2
    x = random.randint(-radius, radius)
    y = random.randint(-radius, radius)
    return x, y

def draw_health_bar(screen, x, y, current_health, max_health, width=40, height=5):
    """Рисует полоску здоровья"""
    bar_x = x - width // 2
    bar_y = y - 15
    
    pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, width, height))
    health_percent = max(0, current_health / max_health)
    pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, width * health_percent, height))

def spawn_position_with_safety(avoid_x, avoid_y, player_speed_x=0, player_speed_y=0, 
                               min_distance=300, max_attempts=100, 
                               forbidden_angle=60,
                               enemies=None,
                               enemy_separation=150,
                               existing_bases=None,
                               base_separation=400):
    """
    Улучшенный спавн с проверкой на:
    - направление движения игрока
    - расстояние до других врагов
    - расстояние до баз
    - безопасную зону вокруг игрока
    """
    
    player_speed = math.sqrt(player_speed_x**2 + player_speed_y**2)
    forbidden_rad = math.radians(forbidden_angle)
    
    if player_speed > 0.5:
        player_angle = math.atan2(player_speed_y, player_speed_x)
        forbidden_start = player_angle - forbidden_rad
        forbidden_end = player_angle + forbidden_rad
    else:
        forbidden_start = None
        forbidden_end = None
    
    occupied_positions = []
    if enemies:
        for enemy in enemies:
            occupied_positions.append((enemy.x, enemy.y))
    
    if existing_bases:
        for base in existing_bases:
            if base.alive:
                occupied_positions.append((base.x, base.y))
    
    for attempt in range(max_attempts):
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(min_distance, min_distance * 3)
        
        if forbidden_start is not None:
            angle_norm = angle % (2 * math.pi)
            start = forbidden_start % (2 * math.pi)
            end = forbidden_end % (2 * math.pi)
            
            if start < end:
                in_forbidden = start < angle_norm < end
            else:
                in_forbidden = angle_norm > start or angle_norm < end
            
            if in_forbidden:
                continue
        
        x = avoid_x + math.cos(angle) * distance
        y = avoid_y + math.sin(angle) * distance
        
        dx = x - avoid_x
        dy = y - avoid_y
        if math.sqrt(dx**2 + dy**2) < min_distance:
            continue
        
        too_close = False
        for ox, oy in occupied_positions:
            edx = x - ox
            edy = y - oy
            dist = math.sqrt(edx**2 + edy**2)
            
            is_base = False
            if existing_bases:
                for base in existing_bases:
                    if base.alive and abs(base.x - ox) < 1 and abs(base.y - oy) < 1:
                        is_base = True
                        break
            
            min_dist = base_separation if is_base else enemy_separation
            
            if dist < min_dist:
                too_close = True
                break
        
        if too_close:
            continue
        
        return x, y
    
    side_angles = [
        math.pi * 0.25,
        math.pi * 0.75,
        math.pi * 1.25,
        math.pi * 1.75,
    ]
    angle = random.choice(side_angles)
    distance = min_distance * 2
    x = avoid_x + math.cos(angle) * distance
    y = avoid_y + math.sin(angle) * distance
    return x, y

# ===== ФУНКЦИИ КОЛЛИЗИЙ =====

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

def circle_polygon_collision(circle, vertices, margin=0):
    """Проверка столкновения круга с многоугольником"""
    for vx, vy in vertices:
        if point_in_circle(vx, vy, circle, margin):
            return True
    
    for i in range(len(vertices)):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % len(vertices)]
        if circle_line_collision(circle, x1, y1, x2, y2, margin):
            return True
    
    return False

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