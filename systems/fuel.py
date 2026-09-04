# systems/fuel.py
import pygame
import random
from settings import *

class FuelSystem:
    """Система топлива и варпа"""
    
    def __init__(self, max_fuel=100):
        self.max_fuel = max_fuel
        self.fuel = max_fuel
        self.warp_active = False
        self.warp_cooldown = 0
        self.warp_delay = 60  # Кадров между варпами
        
        # Расход топлива
        self.thrust_consumption = 0.01   # За кадр при движении
        self.warp_consumption = 0.05     # За кадр в варпе
        self.idle_recovery = 0.0001       # Восстановление при стоянии
    
    def update(self, ship, is_thrusting, particle_system=None):
        """Обновление топлива"""
        # Восстановление на базе или в покое
        if not is_thrusting and not self.warp_active:
            self.fuel = min(self.max_fuel, self.fuel + self.idle_recovery)
        
        # Расход при движении
        if is_thrusting:
            self.fuel = max(0, self.fuel - self.thrust_consumption)
        
        # Расход в варпе
        if self.warp_active:
            self.fuel = max(0, self.fuel - self.warp_consumption)
            
            # Эффекты варпа
            if particle_system and pygame.time.get_ticks() % 3 == 0:
                particle_system.spawn_explosion(
                    ship.x + random.randint(-20, 20),
                    ship.y + random.randint(-20, 20),
                    count=5,
                    speed=2,
                    colors=[(100, 200, 255), (255, 255, 255)]
                )
        
        # Обновление кулдауна варпа
        if self.warp_cooldown > 0:
            self.warp_cooldown -= 1
    
    def has_fuel(self):
        """Проверяет, есть ли топливо для движения"""
        return self.fuel > 0.1
        
    def activate_warp(self):
        """Активация варпа"""
        if self.warp_cooldown <= 0 and self.fuel > 20:
            self.warp_active = True
            return True
        return False
    
    def deactivate_warp(self):
        """Деактивация варпа"""
        self.warp_active = False
        self.warp_cooldown = self.warp_delay
    
    def get_fuel_percent(self):
        """Процент топлива"""
        return self.fuel / self.max_fuel
    
    def draw_hud(self, screen):
        """Рисует индикатор топлива в HUD"""
        bar_width = 120
        bar_height = 10
        bar_x = 15
        bar_y = 75  # Под HP (50) + отступ
        
        pygame.draw.rect(screen, (30, 30, 30), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height), 1)
        
        percent = self.get_fuel_percent()
        if percent > 0.3:
            color = (50, 255, 100)
        elif percent > 0.1:
            color = (255, 200, 50)
        else:
            color = (255, 50, 50)
            
        fill_width = int((bar_width - 2) * percent)
        if fill_width > 0:
            pygame.draw.rect(screen, color, 
                            (bar_x + 1, bar_y + 1, fill_width, bar_height - 2))
        
        font = pygame.font.Font(None, 16)
        fuel_text = font.render(f"FUEL: {int(self.fuel)}%", True, (200, 200, 200))
        screen.blit(fuel_text, (bar_x, bar_y - 18))
        
        if self.warp_active:
            warp_font = pygame.font.Font(None, 16)
            warp_text = warp_font.render("WARP ACTIVE", True, (100, 200, 255))
            screen.blit(warp_text, (bar_x + bar_width + 10, bar_y - 2))
        elif self.warp_cooldown > 0:
            warp_font = pygame.font.Font(None, 16)
            cd_text = warp_font.render(f"WARP: {self.warp_cooldown//60+1}s", True, (80, 80, 80))
            screen.blit(cd_text, (bar_x + bar_width + 10, bar_y - 2))