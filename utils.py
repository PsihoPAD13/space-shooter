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
    """
    Телепортация через края (для ограниченного мира)
    В бесконечном мире не нужна, но оставляем для совместимости
    """
    pass

def spawn_position():
    """
    Случайная позиция для спавна врагов в бесконечном мире
    Спавним в радиусе 2 чанков от центра
    """
    radius = CHUNK_SIZE * 2
    x = random.randint(-radius, radius)
    y = random.randint(-radius, radius)
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
    
def spawn_position_with_safety(avoid_x, avoid_y, player_speed_x=0, player_speed_y=0, 
                               min_distance=300, max_attempts=100):
    import random
    import math
    from settings import CHUNK_SIZE
    
    player_speed = math.sqrt(player_speed_x**2 + player_speed_y**2)
    
    # Запрещённый сектор (впереди игрока)
    if player_speed > 0.5:
        player_angle = math.atan2(player_speed_y, player_speed_x)
        forbidden_start = player_angle - math.pi * 0.4
        forbidden_end = player_angle + math.pi * 0.4
    else:
        forbidden_start = None
        forbidden_end = None
    
    for attempt in range(max_attempts):
        angle = random.uniform(0, 2 * math.pi)
        # Увеличиваем минимальную дистанцию для последних врагов
        distance = random.uniform(min_distance, CHUNK_SIZE * 2)
        
        # Проверяем запрещённый сектор
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
        if math.sqrt(dx**2 + dy**2) >= min_distance:
            return x, y
    
    # Если не нашли — спавним на фиксированном расстоянии сбоку
    # (не телепортируемся)
    angle = random.choice([math.pi * 0.3, math.pi * 0.7, math.pi * 1.3, math.pi * 1.7])
    distance = min_distance * 1.2
    x = avoid_x + math.cos(angle) * distance
    y = avoid_y + math.sin(angle) * distance
    return x, y