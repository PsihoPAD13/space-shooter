# powerups.py
import pygame
import random
import math
from settings import WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT, WHITE

class PowerUp:
    """Базовый класс бонуса"""
    def __init__(self, x, y, powerup_type):
        self.x = x
        self.y = y
        self.type = powerup_type
        self.radius = 15
        self.speed = 1.5
        self.angle = 0
        self.collected = False
        self.lifetime = 600
        self.pulse = 0
        self.current_radius = self.radius
        
        # Цвет и символ для каждого типа (используем ASCII)
        self.types = {
            'health': {
                'color': (255, 50, 50),
                'symbol': '+',    # Вместо ♥
                'name': 'Health +25'
            },
            'shield': {
                'color': (50, 150, 255),
                'symbol': 'S',    # Вместо 🛡
                'name': 'Shield'
            },
            'triple_shot': {
                'color': (255, 200, 50),
                'symbol': '3',    # Вместо ✦
                'name': 'Triple Shot'
            },
            'speed_boost': {
                'color': (50, 255, 150),
                'symbol': '>',    # Вместо ⚡
                'name': 'Speed Boost'
            },
            'bomb': {
                'color': (255, 100, 200),
                'symbol': '!',    # Вместо 💥
                'name': 'Bomb'
            },
            'magnet': {
                'color': (200, 100, 255),
                'symbol': 'M',    # Вместо 🧲
                'name': 'Magnet'
            }
        }
    
    def update(self):
        """Обновляет бонус"""
        self.angle += 0.02
        self.pulse += 0.05
        self.lifetime -= 1
        
        # Медленное движение вниз
        self.y += self.speed * 0.3
        
        # Пульсация радиуса
        self.current_radius = self.radius + 3 * math.sin(self.pulse)
    
    def draw(self, screen, camera_x=0, camera_y=0):
        """Рисует бонус"""
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        # Проверка видимости
        if screen_x < -50 or screen_x > WIDTH + 50 or screen_y < -50 or screen_y > HEIGHT + 50:
            return
        
        # Данные типа бонуса
        type_data = self.types.get(self.type, self.types['health'])
        color = type_data['color']
        
        # Свечение
        glow_size = int(self.current_radius * 1.5)
        glow = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        glow_color = (color[0], color[1], color[2], 50)
        pygame.draw.circle(glow, glow_color, (glow_size, glow_size), glow_size)
        screen.blit(glow, (int(screen_x - glow_size), int(screen_y - glow_size)))
        
        # Основной круг с пульсацией
        pygame.draw.circle(screen, color, 
                          (int(screen_x), int(screen_y)), 
                          int(self.current_radius), 2)
        
        # Заливка с прозрачностью
        inner = pygame.Surface((int(self.current_radius * 2), int(self.current_radius * 2)), pygame.SRCALPHA)
        inner_color = (color[0], color[1], color[2], 80)
        pygame.draw.circle(inner, inner_color, 
                          (int(self.current_radius), int(self.current_radius)), 
                          int(self.current_radius - 2))
        screen.blit(inner, (int(screen_x - self.current_radius), int(screen_y - self.current_radius)))
        
        # Символ (увеличенный шрифт для читаемости)
        font = pygame.font.Font(None, 32)
        symbol = type_data['symbol']
        text = font.render(symbol, True, WHITE)
        text_rect = text.get_rect(center=(int(screen_x), int(screen_y)))
        screen.blit(text, text_rect)

class PowerUpSystem:
    """Система управления бонусами"""
    def __init__(self):
        self.powerups = []
        self.spawn_timer = 0
        self.spawn_delay = 300
        self.active_effects = {}
    
    def spawn_powerup(self, x, y):
        """Создает случайный бонус в указанной позиции"""
        types = ['health', 'shield', 'triple_shot', 'speed_boost', 'bomb', 'magnet']
        weights = [30, 20, 15, 15, 10, 10]
        
        powerup_type = random.choices(types, weights=weights, k=1)[0]
        self.powerups.append(PowerUp(x, y, powerup_type))
    
    def spawn_random(self):
        """Создает бонус в случайном месте"""
        x = random.randint(50, WORLD_WIDTH - 50)
        y = random.randint(50, WORLD_HEIGHT - 50)
        self.spawn_powerup(x, y)
    
    def spawn_from_enemy(self, x, y, chance=0.3):
        """Шанс выпадения бонуса из врага"""
        if random.random() < chance:
            self.spawn_powerup(x, y)
    
    def update(self, player_x, player_y):
        """Обновляет все бонусы"""
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_delay:
            self.spawn_random()
            self.spawn_timer = 0
        
        for powerup in self.powerups[:]:
            powerup.update()
            if powerup.lifetime <= 0:
                self.powerups.remove(powerup)
    
    def check_collection(self, ship, particle_system=None):
        """Проверяет сбор бонусов игроком"""
        collected = []
        
        for powerup in self.powerups[:]:
            dx = ship.x - powerup.x
            dy = ship.y - powerup.y
            dist = math.sqrt(dx**2 + dy**2)
            
            collect_radius = ship.radius + powerup.radius + 10
            
            # Эффект магнита
            if 'magnet' in self.active_effects:
                collect_radius *= 2.5
            
            if dist < collect_radius:
                powerup.collected = True
                collected.append(powerup)
                self.powerups.remove(powerup)
                
                if particle_system:
                    particle_system.spawn_explosion(
                        powerup.x, powerup.y,
                        count=15,
                        speed=3,
                        colors=[powerup.types[powerup.type]['color'], (255, 255, 255)]
                    )
                
                self.apply_effect(ship, powerup.type)
        
        return collected
    
    def apply_effect(self, ship, effect_type):
        """Применяет эффект бонуса к игроку"""
        if effect_type == 'health':
            ship.health = min(ship.max_health, ship.health + 25)
            
        elif effect_type == 'shield':
            self.active_effects['shield'] = 300
            ship.shield_active = True
            
        elif effect_type == 'triple_shot':
            self.active_effects['triple_shot'] = 600
            
        elif effect_type == 'speed_boost':
            self.active_effects['speed_boost'] = 400
            
        elif effect_type == 'bomb':
            self.active_effects['bomb'] = 1
            
        elif effect_type == 'magnet':
            self.active_effects['magnet'] = 400
    
    def update_effects(self, ship):
        """Обновляет активные эффекты"""
        for effect in list(self.active_effects.keys()):
            self.active_effects[effect] -= 1
            if self.active_effects[effect] <= 0:
                del self.active_effects[effect]
                if effect == 'shield':
                    ship.shield_active = False
                elif effect == 'speed_boost':
                    ship.max_speed = 8
        
        if 'speed_boost' in self.active_effects:
            ship.max_speed = 12
        else:
            ship.max_speed = 8
        
        if 'shield' in self.active_effects:
            ship.shield_active = True
    
    def draw(self, screen, camera_x=0, camera_y=0):
        """Рисует все бонусы"""
        for powerup in self.powerups:
            powerup.draw(screen, camera_x, camera_y)
    
    def clear(self):
        """Очищает все бонусы"""
        self.powerups.clear()
        self.active_effects.clear()