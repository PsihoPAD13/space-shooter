# bullet.py
import pygame
from settings import BULLET_RADIUS, BULLET_LIFE, YELLOW, WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT
from utils import wrap_position

class Bullet:
    def __init__(self, x, y, speed_x, speed_y):
        self.x = x
        self.y = y
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.radius = BULLET_RADIUS
        self.life = BULLET_LIFE
    
    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.life -= 1
        
        # Бесшовная телепортация пуль
        wrap_position(self)
    
    def draw(self, screen, camera_x=0, camera_y=0):
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        # Рисуем только если пуля на экране
        if -10 < screen_x < WIDTH + 10 and -10 < screen_y < HEIGHT + 10:
            pygame.draw.circle(screen, YELLOW, (int(screen_x), int(screen_y)), self.radius)
            pygame.draw.circle(screen, (255, 255, 100), (int(screen_x), int(screen_y)), self.radius + 2, 1)
    
    def is_dead(self):
        return self.life <= 0