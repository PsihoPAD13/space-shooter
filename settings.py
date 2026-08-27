# settings.py
import pygame

# Размеры окна
WIDTH, HEIGHT = 900, 700
FPS = 60

# Размеры мира (30к x 30к)
WORLD_WIDTH = 30000
WORLD_HEIGHT = 30000

# ===== НАСТРОЙКИ ЧАНКОВ =====
CHUNK_SIZE = 500  # Размер одного чанка в пикселях
CHUNK_LOAD_RADIUS = 3  # Сколько чанков подгружать вокруг игрока

# ===== НАСТРОЙКИ ЗВЕЗДНОГО ПОЛЯ =====
PARALLAX_SPEED_MULTIPLIER = 0.1
STARS_PER_CHUNK = 50  # Количество звезд в одном чанке
STAR_LAYERS = [
    # (скорость, макс_размер, мин_яркость, макс_яркость, шанс_цвета)
    (0.2, 1, 20, 60, 0.5),      # Дальние звезды
    (0.35, 1, 40, 90, 0.6),     # Дальние-средние
    (0.55, 2, 60, 140, 0.7),    # Средние
    (0.8, 2, 100, 200, 0.8),    # Близкие
    (1.0, 3, 150, 255, 0.9),    # Очень близкие
]

# ===== НАСТРОЙКИ КОРАБЛЯ =====
SHIP_ACCELERATION = 0.2
SHIP_FRICTION = 0.99
SHIP_MAX_SPEED = 8
SHIP_ROTATION_SPEED = 3
SHIP_RADIUS = 15
SHIP_MAX_HEALTH = 100
SHOOT_DELAY = 10
BULLET_SPEED = 10
BULLET_LIFE = 60
BULLET_RADIUS = 4

# ===== НАСТРОЙКИ ВРАГОВ =====
ENEMY_RADIUS = 20
ENEMY_BASE_SPEED = 1.5
ENEMY_MAX_HEALTH = 3
ENEMY_SHOOT_DELAY_MIN = 30
ENEMY_SHOOT_DELAY_MAX = 90
ENEMY_BULLET_SPEED = 5
ENEMY_SPAWN_DELAY_START = 60
ENEMY_SPAWN_DELAY_MIN = 20

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 150, 255)
YELLOW = (255, 255, 50)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)

# ===== НАСТРОЙКИ ЧАСТИЦ =====
EXPLOSION_COUNT = 40  # Количество частиц во взрыве
EXPLOSION_SPEED = 6   # Скорость разлета
TRAIL_COUNT = 5       # Частиц в следе

# ===== НАСТРОЙКИ БОНУСОВ =====
POWERUP_SPAWN_DELAY = 300  # Кадров между спавном (300 = 5 секунд)
POWERUP_DROP_CHANCE = 0.3   # Шанс выпадения из врага
POWERUP_LIFETIME = 600      # Кадров жизни бонуса (600 = 10 секунд)

# ===== НАСТРОЙКИ ВРАГОВ =====
ENEMY_TYPES_WEIGHTS = {
    'scout': 30,
    'tank': 15,
    'sniper': 10,
    'kamikaze': 8,
    'swarmer': 20,
    'guardian': 5,
    'turret': 5
}

# ===== НАСТРОЙКИ ГРАФИКИ =====
PARTICLE_DENSITY = 1.0
STAR_DENSITY = 1.0
SHOW_HEALTH_BARS = True

# ===== НАСТРОЙКИ ВОЛН =====
WAVE_ENEMY_COUNT = 5  # Базовое количество врагов в волне
WAVE_ENEMY_INCREASE = 2  # На сколько врагов больше с каждой волной
WAVE_PAUSE_DURATION = 180  # Пауза между волнами (в кадрах = 3 секунды)
WAVE_MAX_ENEMIES = 30  # Максимум врагов в волне
WAVE_SPAWN_DELAY_BASE = 30  # Задержка между спавном врагов в волне
WAVE_SPAWN_DELAY_MIN = 5  # Минимальная задержка