# entities/player_base.py
import pygame
import math
from settings import *

class PlayerBase:
    """База игрока — точка восстановления и апгрейдов"""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 40
        self.health = 200
        self.max_health = 200
        self.alive = True
        
        # Восстановление
        self.repair_rate = 1  # HP за тик
        self.repair_cooldown = 0
        self.repair_delay = 30  # Кадров между восстановлением
        
        # Апгрейды
        self.upgrades = {
            'repair_speed': 1,   # Уровень восстановления
            'shield_power': 0,   # Мощность щита базы
            'turret_count': 0,   # Количество турелей
            'storage': 0,        # Вместимость ресурсов
        }
        
        # Ресурсы
        self.resources = {
            'scrap': 0,
            'crystal': 0,
            'fuel': 0,
        }
        
        # Визуальные эффекты
        self.pulse = 0
        self.glow_radius = self.radius
    
    def update(self, ship, particle_system=None):
        """Обновление базы"""
        self.pulse += 0.02
        self.glow_radius = self.radius + 5 * math.sin(self.pulse)
        
        # Восстановление HP корабля
        if self.repair_cooldown <= 0:
            if ship.health < ship.max_health:
                ship.health = min(ship.max_health, ship.health + self.repair_rate)
                self.repair_cooldown = self.repair_delay
                
                # Эффект восстановления
                if particle_system:
                    particle_system.spawn_explosion(
                        ship.x, ship.y,
                        count=3,
                        speed=1,
                        colors=[(50, 255, 50), (255, 255, 255)]
                    )
        else:
            self.repair_cooldown -= 1
        
        # Эффект восстановления вокруг базы
        if particle_system and self.repair_cooldown == 0:
            angle = math.radians(pygame.time.get_ticks() * 0.05 % 360)
            px = self.x + math.cos(angle) * (self.radius + 20)
            py = self.y + math.sin(angle) * (self.radius + 20)
            particle_system.spawn_spark_trail(
                px, py,
                (50, 255, 100),
                speed=1,
                count=1
            )
    
    def draw(self, screen, camera_x=0, camera_y=0):
        """Рисует базу"""
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        if screen_x < -100 or screen_x > WIDTH + 100 or \
           screen_y < -100 or screen_y > HEIGHT + 100:
            return
        
        # Свечение
        glow_size = int(self.glow_radius * 2.5)
        glow = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        glow_color = (50, 200, 255, 30)
        pygame.draw.circle(glow, glow_color, (glow_size, glow_size), glow_size)
        screen.blit(glow, (int(screen_x - glow_size), int(screen_y - glow_size)))
        
        # Внешнее кольцо
        pygame.draw.circle(screen, (50, 150, 255), 
                         (int(screen_x), int(screen_y)), 
                         int(self.glow_radius), 2)
        
        # Внутреннее кольцо (пульсирующее)
        inner_radius = int(self.radius * 0.8)
        pygame.draw.circle(screen, (100, 200, 255), 
                         (int(screen_x), int(screen_y)), 
                         inner_radius, 2)
        
        # Центр
        pygame.draw.circle(screen, (50, 150, 255), 
                         (int(screen_x), int(screen_y)), 10)
        
        # Крест
        size = 15
        pygame.draw.line(screen, (150, 220, 255), 
                       (int(screen_x - size), int(screen_y)), 
                       (int(screen_x + size), int(screen_y)), 2)
        pygame.draw.line(screen, (150, 220, 255), 
                       (int(screen_x), int(screen_y - size)), 
                       (int(screen_x), int(screen_y + size)), 2)
        
        # Полоса здоровья базы
        bar_width = 50
        bar_height = 4
        bar_x = screen_x - bar_width // 2
        bar_y = screen_y - self.radius - 15
        health_percent = self.health / self.max_health
        
        pygame.draw.rect(screen, (50, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 200, 50), 
                        (bar_x, bar_y, bar_width * health_percent, bar_height))
        
        # Метка
        font = pygame.font.Font(None, 16)
        label = font.render("BASE", True, (100, 200, 255))
        label_rect = label.get_rect(center=(int(screen_x), int(screen_y + self.radius + 20)))
        screen.blit(label, label_rect)
        
        # Расстояние до игрока (если далеко)
        # (будет отображаться в HUD)
    
    def is_near(self, x, y, radius=100):
        """Проверка, находится ли точка рядом с базой"""
        dx = x - self.x
        dy = y - self.y
        return math.sqrt(dx**2 + dy**2) < radius
    
    def take_damage(self, damage):
        """Получение урона"""
        self.health -= damage
        if self.health <= 0:
            self.alive = False
            return True
        return False