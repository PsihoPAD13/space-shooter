# entities/enemy_types.py
import pygame

# Типы врагов с координатами для отрисовки
ENEMY_TYPES = {
    'scout': {
        'name': 'Scout',
        'radius': 15,
        'speed': 3.0,
        'health': 2,
        'max_health': 2,
        'color': (100, 255, 100),
        # Координаты точек относительно центра (x, y)
        # Ромб
        'vertices': [
            (0, -15),   # Верх
            (10, 0),    # Право
            (0, 15),    # Низ
            (-10, 0),   # Лево
        ],
        'behavior': 'chase',
        'shoot_delay': 60,
        'score': 10,
        'max_on_screen': 8,
        'description': 'Fast but weak'
    },
    'tank': {
        'name': 'Tank',
        'radius': 30,
        'speed': 1.2,
        'health': 8,
        'max_health': 8,
        'color': (255, 100, 100),
        # Шестиугольник
        'vertices': [
            (0, -30),
            (26, -15),
            (26, 15),
            (0, 30),
            (-26, 15),
            (-26, -15),
        ],
        'behavior': 'chase',
        'shoot_delay': 30,
        'score': 20,
        'max_on_screen': 4,
        'description': 'Slow but tough'
    },
    'sniper': {
        'name': 'Sniper',
        'radius': 18,
        'speed': 0.5,
        'health': 3,
        'max_health': 3,
        'color': (100, 150, 255),
        # Квадрат со скошенными углами
        'vertices': [
            (-12, -18),
            (12, -18),
            (18, -12),
            (18, 12),
            (12, 18),
            (-12, 18),
            (-18, 12),
            (-18, -12),
        ],
        'behavior': 'stationary',
        'shoot_delay': 15,
        'score': 15,
        'max_on_screen': 3,
        'description': 'Stays back and shoots'
    },
    'kamikaze': {
        'name': 'Kamikaze',
        'radius': 14,
        'speed': 4.5,
        'health': 1,
        'max_health': 1,
        'color': (255, 200, 50),
        # Острый треугольник вперёд
        'vertices': [
            (14, 0),
            (-10, -10),
            (-10, 10),
        ],
        'behavior': 'kamikaze',
        'shoot_delay': 999,
        'score': 15,
        'max_on_screen': 5,
        'description': 'Charges and explodes'
    },
    'swarmer': {
        'name': 'Swarmer',
        'radius': 10,
        'speed': 5.0,
        'health': 1,
        'max_health': 1,
        'color': (255, 100, 200),
        # Маленький ромб с вырезом
        'vertices': [
            (0, -10),
            (6, 0),
            (0, 10),
            (-6, 0),
        ],
        'behavior': 'chase',
        'shoot_delay': 999,
        'score': 8,
        'max_on_screen': 12,
        'description': 'Fast and tiny'
    },
    'guardian': {
        'name': 'Guardian',
        'radius': 25,
        'speed': 2.0,
        'health': 5,
        'max_health': 5,
        'color': (100, 255, 200),
        # Звезда
        'vertices': [
            (0, -25),
            (6, -8),
            (22, -8),
            (10, 4),
            (14, 20),
            (0, 12),
            (-14, 20),
            (-10, 4),
            (-22, -8),
            (-6, -8),
        ],
        'behavior': 'orbit',
        'shoot_delay': 40,
        'score': 25,
        'max_on_screen': 2,
        'description': 'Orbits around player'
    },
    'turret': {
        'name': 'Turret',
        'radius': 22,
        'speed': 0.0,
        'health': 6,
        'max_health': 6,
        'color': (255, 150, 100),
        # Восьмиугольник
        'vertices': [
            (0, -22),
            (16, -16),
            (22, 0),
            (16, 16),
            (0, 22),
            (-16, 16),
            (-22, 0),
            (-16, -16),
        ],
        'behavior': 'stationary',
        'shoot_delay': 10,
        'score': 30,
        'max_on_screen': 2,
        'description': 'Stationary, rapid fire'
    }
}

# Веса для спавна
SPAWN_WEIGHTS = {
    'scout': 30,
    'tank': 15,
    'sniper': 8,
    'kamikaze': 12,
    'swarmer': 25,
    'guardian': 5,
    'turret': 5
}