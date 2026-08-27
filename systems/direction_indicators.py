# systems/direction_indicators.py
import pygame
import math
from settings import WIDTH, HEIGHT

class DirectionIndicators:
    """Система указателей направления на врагов за пределами экрана"""
    
    def __init__(self):
        self.indicators = []
        self.font = pygame.font.Font(None, 20)  # Уменьшили шрифт
        self.small_font = pygame.font.Font(None, 14)
    
    def update(self, player_x, player_y, enemies, camera_x, camera_y):
        """Обновляет указатели для врагов за пределами экрана"""
        self.indicators = []
        
        for enemy in enemies:
            if enemy.health <= 0:
                continue
            
            screen_x = enemy.x - camera_x
            screen_y = enemy.y - camera_y
            
            if -20 < screen_x < WIDTH + 20 and -20 < screen_y < HEIGHT + 20:
                continue
            
            dx = enemy.x - player_x
            dy = enemy.y - player_y
            angle = math.atan2(dy, dx)
            
            indicator_x, indicator_y = self._calculate_edge_position(angle)
            
            # Цвет и метка (без эмодзи)
            if enemy.behavior == 'kamikaze':
                color = (255, 200, 50)
                label = "K"  # Kamikaze
            elif enemy.behavior == 'tank':
                color = (255, 100, 100)
                label = "T"  # Tank
            elif enemy.behavior == 'sniper':
                color = (100, 150, 255)
                label = "S"  # Sniper
            elif enemy.behavior == 'guardian':
                color = (100, 255, 200)
                label = "G"  # Guardian
            elif enemy.behavior == 'swarmer':
                color = (255, 100, 200)
                label = "W"  # Swarmer
            elif enemy.behavior == 'turret':
                color = (255, 150, 100)
                label = "U"  # Turret
            else:
                color = (255, 50, 50)
                label = "*"  # Обычный враг
            
            dist = math.sqrt(dx**2 + dy**2)
            if dist > 1000:
                dist_text = f"{int(dist // 1000)}k"
            else:
                dist_text = f"{int(dist)}"
            
            self.indicators.append({
                'x': indicator_x,
                'y': indicator_y,
                'angle': angle,
                'color': color,
                'label': label,
                'distance': dist_text,
                'enemy': enemy
            })
    
    def _calculate_edge_position(self, angle):
        """Вычисляет позицию указателя на краю экрана"""
        margin = 30
        cx = WIDTH // 2
        cy = HEIGHT // 2
        
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        
        t_values = []
        
        if cos_a > 0:
            t_values.append((WIDTH - margin - cx) / cos_a)
        elif cos_a < 0:
            t_values.append((margin - cx) / cos_a)
        
        if sin_a > 0:
            t_values.append((HEIGHT - margin - cy) / sin_a)
        elif sin_a < 0:
            t_values.append((margin - cy) / sin_a)
        
        t = min([t for t in t_values if t > 0])
        
        x = cx + t * cos_a
        y = cy + t * sin_a
        
        x = max(margin, min(WIDTH - margin, x))
        y = max(margin, min(HEIGHT - margin, y))
        
        return x, y
    
    def draw(self, screen):
        """Рисует все указатели"""
        for indicator in self.indicators:
            x = indicator['x']
            y = indicator['y']
            color = indicator['color']
            label = indicator['label']
            distance = indicator['distance']
            angle = indicator['angle']
            
            # === СТРЕЛКА ===
            size = 12
            
            tip_x = x + math.cos(angle) * size
            tip_y = y + math.sin(angle) * size
            
            left_angle = angle + math.pi * 0.75
            right_angle = angle - math.pi * 0.75
            
            left_x = x + math.cos(left_angle) * size * 0.6
            left_y = y + math.sin(left_angle) * size * 0.6
            right_x = x + math.cos(right_angle) * size * 0.6
            right_y = y + math.sin(right_angle) * size * 0.6
            
            points = [(tip_x, tip_y), (left_x, left_y), (right_x, right_y)]
            pygame.draw.polygon(screen, color, points)
            pygame.draw.polygon(screen, (200, 200, 200), points, 1)
            
            # === МЕТКА ТИПА ВРАГА ===
            label_x = x + math.cos(angle + math.pi * 0.3) * size * 1.8
            label_y = y + math.sin(angle + math.pi * 0.3) * size * 1.8
            
            shadow = self.font.render(label, True, (0, 0, 0))
            shadow_rect = shadow.get_rect(center=(label_x + 1, label_y + 1))
            screen.blit(shadow, shadow_rect)
            
            text = self.font.render(label, True, (255, 255, 255))
            text_rect = text.get_rect(center=(label_x, label_y))
            screen.blit(text, text_rect)
            
            # === ДИСТАНЦИЯ ===
            dist_x = x + math.cos(angle - math.pi * 0.3) * size * 1.8
            dist_y = y + math.sin(angle - math.pi * 0.3) * size * 1.8
            
            dist_shadow = self.small_font.render(distance, True, (0, 0, 0))
            dist_shadow_rect = dist_shadow.get_rect(center=(dist_x + 1, dist_y + 1))
            screen.blit(dist_shadow, dist_shadow_rect)
            
            dist_text = self.small_font.render(distance, True, (200, 200, 200))
            dist_rect = dist_text.get_rect(center=(dist_x, dist_y))
            screen.blit(dist_text, dist_rect)