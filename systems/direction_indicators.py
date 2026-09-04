# systems/direction_indicators.py
import pygame
import math
from settings import WIDTH, HEIGHT

class DirectionIndicators:
    """Система указателей направления на врагов и базы за пределами экрана"""
    
    def __init__(self):
        self.indicators = []
        self.font = pygame.font.Font(None, 20)
        self.small_font = pygame.font.Font(None, 14)
    
    def update(self, player_x, player_y, enemies, camera_x, camera_y, enemy_bases=None):
        """Обновляет указатели для объектов за пределами экрана"""
        self.indicators = []
        
        # ===== ВРАГИ =====
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
            
            # Цвет и метка
            if enemy.behavior == 'kamikaze':
                color = (255, 200, 50)
                label = "K"
            elif enemy.behavior == 'tank':
                color = (255, 100, 100)
                label = "T"
            elif enemy.behavior == 'sniper':
                color = (100, 150, 255)
                label = "S"
            elif enemy.behavior == 'guardian':
                color = (100, 255, 200)
                label = "G"
            elif enemy.behavior == 'swarmer':
                color = (255, 100, 200)
                label = "W"
            elif enemy.behavior == 'turret':
                color = (255, 150, 100)
                label = "U"
            else:
                color = (255, 50, 50)
                label = "E"
            
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
                'type': 'enemy'
            })
        
        # ===== БАЗЫ ВРАГОВ =====
        if enemy_bases:
            for base in enemy_bases:
                continue
                if not base.alive:
                    continue
                
                screen_x = base.x - camera_x
                screen_y = base.y - camera_y
                
                if -30 < screen_x < WIDTH + 30 and -30 < screen_y < HEIGHT + 30:
                    continue
                
                dx = base.x - player_x
                dy = base.y - player_y
                angle = math.atan2(dy, dx)
                
                indicator_x, indicator_y = self._calculate_edge_position(angle)
                
                # Цвет базы
                base_colors = {
                    'standard': (255, 50, 50),
                    'strong': (255, 50, 200),
                    'fast': (255, 200, 50),
                    'swarm': (200, 50, 255),
                }
                color = base_colors.get(base.base_type, (255, 0, 0))
                
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
                    'label': 'B',  # База
                    'distance': dist_text,
                    'type': 'base',
                    'base_type': base.base_type,
                    'enemies': base.current_enemies
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
            obj_type = indicator['type']
            
            # ===== СТРЕЛКА =====
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
            
            # Для баз делаем двойную стрелку
            if obj_type == 'base':
                # Основная стрелка
                pygame.draw.polygon(screen, color, points)
                pygame.draw.polygon(screen, (255, 255, 255), points, 1)
                
                # Дополнительная стрелка (внутренняя)
                inner_size = size * 0.6
                inner_tip_x = x + math.cos(angle) * inner_size
                inner_tip_y = y + math.sin(angle) * inner_size
                inner_left_x = x + math.cos(left_angle) * inner_size * 0.6
                inner_left_y = y + math.sin(left_angle) * inner_size * 0.6
                inner_right_x = x + math.cos(right_angle) * inner_size * 0.6
                inner_right_y = y + math.sin(right_angle) * inner_size * 0.6
                inner_points = [(inner_tip_x, inner_tip_y), (inner_left_x, inner_left_y), (inner_right_x, inner_right_y)]
                pygame.draw.polygon(screen, (255, 255, 255), inner_points)
            else:
                # Обычная стрелка для врагов
                pygame.draw.polygon(screen, color, points)
                pygame.draw.polygon(screen, (200, 200, 200), points, 1)
            
            # ===== МЕТКА =====
            label_x = x + math.cos(angle + math.pi * 0.3) * size * 1.8
            label_y = y + math.sin(angle + math.pi * 0.3) * size * 1.8
            
            shadow = self.font.render(label, True, (0, 0, 0))
            shadow_rect = shadow.get_rect(center=(label_x + 1, label_y + 1))
            screen.blit(shadow, shadow_rect)
            
            text = self.font.render(label, True, (255, 255, 255))
            text_rect = text.get_rect(center=(label_x, label_y))
            screen.blit(text, text_rect)
            
            # ===== ДИСТАНЦИЯ =====
            dist_x = x + math.cos(angle - math.pi * 0.3) * size * 1.8
            dist_y = y + math.sin(angle - math.pi * 0.3) * size * 1.8
            
            dist_shadow = self.small_font.render(distance, True, (0, 0, 0))
            dist_shadow_rect = dist_shadow.get_rect(center=(dist_x + 1, dist_y + 1))
            screen.blit(dist_shadow, dist_shadow_rect)
            
            dist_text = self.small_font.render(distance, True, (200, 200, 200))
            dist_rect = dist_text.get_rect(center=(dist_x, dist_y))
            screen.blit(dist_text, dist_rect)
            
            # ===== ДЛЯ БАЗ: КОЛИЧЕСТВО ВРАГОВ =====
            if obj_type == 'base' and indicator.get('enemies', 0) > 0:
                count_x = x + math.cos(angle) * size * 2.8
                count_y = y + math.sin(angle) * size * 2.8
                
                count_text = self.small_font.render(str(indicator['enemies']), True, (50, 255, 50))
                count_rect = count_text.get_rect(center=(count_x, count_y))
                screen.blit(count_text, count_rect)