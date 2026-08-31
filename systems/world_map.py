# systems/world_map.py
import pygame
import math
from settings import WIDTH, HEIGHT, CHUNK_SIZE

class WorldMap:
    """Большая карта мира - на весь экран"""
    
    def __init__(self, screen, config, waypoint_manager):
        self.screen = screen
        self.config = config
        self.waypoint_manager = waypoint_manager
        self.visible = False
        
        # Карта на весь экран
        self.map_x = 0
        self.map_y = 0
        self.map_width = WIDTH
        self.map_height = HEIGHT
        
        # Масштаб (зум)
        self.map_scale = 0.8
        self.min_scale = 0.1
        self.max_scale = 5.0
        
        # Цвета
        self.bg_color = (10, 10, 30)
        self.border_color = (50, 50, 100)
        self.player_color = (0, 255, 0)
        self.base_colors = {
            'standard': (255, 50, 50),
            'strong': (255, 50, 200),
            'fast': (255, 200, 50),
            'swarm': (200, 50, 255),
        }
        self.chunk_grid_color = (30, 30, 50)
        self.enemy_color = (255, 100, 100)
        self.asteroid_color = (100, 100, 80)
        
        # Для панорамирования
        self.offset_x = 0
        self.offset_y = 0
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        
        # Позиция игрока (обновляется в draw)
        self.player_x = 0
        self.player_y = 0
        
        # Шрифты
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 16)
        self.big_font = pygame.font.Font(None, 48)
    
    def toggle(self):
        """Переключить видимость карты"""
        self.visible = not self.visible
        if self.visible:
            self.offset_x = 0
            self.offset_y = 0
            self.dragging = False
    
    def handle_events(self, event):
        """Обработка событий для карты"""
        if not self.visible:
            return
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:  # ПКМ - установка маркера
                mx, my = event.pos
                
                # Проверяем, не кликнули ли по интерфейсу
                if my < 100 or my > HEIGHT - 100:
                    return
                
                # Конвертируем экранные координаты в мировые
                margin = 100
                center_x = self.player_x + self.offset_x
                center_y = self.player_y + self.offset_y
                half_w = (WIDTH - margin * 2) / (2 * self.map_scale)
                half_h = (HEIGHT - margin * 2 - 100) / (2 * self.map_scale)
                left = center_x - half_w
                top = center_y - half_h
                
                world_x = (mx - margin) / self.map_scale + left
                world_y = (my - margin - 50) / self.map_scale + top
                
                # Добавляем маркер (заменяет старый)
                self.waypoint_manager.add_waypoint(world_x, world_y)
                
            elif event.button == 1:  # ЛКМ - перетаскивание карты
                self.dragging = True
                self.drag_start_x = event.pos[0]
                self.drag_start_y = event.pos[1]
                self.drag_offset_x = self.offset_x
                self.drag_offset_y = self.offset_y
                
            elif event.button == 4:  # Колесо вверх
                self.map_scale = min(self.max_scale, self.map_scale * 1.2)
            elif event.button == 5:  # Колесо вниз
                self.map_scale = max(self.min_scale, self.map_scale / 1.2)
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
        
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                mx, my = event.pos
                dx = mx - self.drag_start_x
                dy = my - self.drag_start_y
                self.offset_x = self.drag_offset_x - dx / self.map_scale
                self.offset_y = self.drag_offset_y - dy / self.map_scale
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.offset_x = 0
                self.offset_y = 0
                self.map_scale = 0.8
            elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                self.map_scale = min(self.max_scale, self.map_scale * 1.2)
            elif event.key == pygame.K_MINUS:
                self.map_scale = max(self.min_scale, self.map_scale / 1.2)
            elif event.key == pygame.K_c:
                self.waypoint_manager.clear_all()
                
    def draw(self, screen, player_x, player_y, enemies, enemy_bases, asteroids, chunk_manager):
        """Рисует большую карту на весь экран"""
        if not self.visible:
            return
            
        # Сохраняем позицию игрока
        self.player_x = player_x
        self.player_y = player_y
        
        # Фон
        screen.fill(self.bg_color)
        
        # Заголовок
        title = self.big_font.render("🌍 WORLD MAP", True, (200, 200, 255))
        title_rect = title.get_rect(center=(WIDTH // 2, 40))
        screen.blit(title, title_rect)
        
        # Подсказка
        close_hint = self.font.render(
            "TAB: Close  |  R: Reset  |  Wheel: Zoom  |  LMB: Drag  |  RMB: Waypoint", 
            True, (100, 100, 150)
        )
        close_rect = close_hint.get_rect(center=(WIDTH // 2, 75))
        screen.blit(close_hint, close_rect)
        
        # Информация о зуме
        zoom_text = self.small_font.render(f"Zoom: {self.map_scale:.1f}x", True, (150, 150, 150))
        screen.blit(zoom_text, (WIDTH - 120, 90))
        
        # Центр карты = игрок + смещение
        center_x = player_x + self.offset_x
        center_y = player_y + self.offset_y
        
        # Рассчитываем видимую область
        margin = 100
        half_w = (WIDTH - margin * 2) / (2 * self.map_scale)
        half_h = (HEIGHT - margin * 2 - 100) / (2 * self.map_scale)
        left = center_x - half_w
        top = center_y - half_h
        right = center_x + half_w
        bottom = center_y + half_h
        
        def world_to_screen(wx, wy):
            sx = (wx - left) * self.map_scale + margin
            sy = (wy - top) * self.map_scale + margin + 50
            return sx, sy
        
        def is_visible_on_screen(sx, sy, size=0):
            """Проверяет, видна ли точка на экране"""
            return sx + size > 0 and sx < self.map_width and sy + size > 0 and sy < self.map_height
        
        def is_visible(wx, wy):
            """Проверяет, виден ли объект в мире"""
            return left < wx < right and top < wy < bottom
        
        # ===== МАРКЕРЫ =====
        self.waypoint_manager.draw_on_map(screen, world_to_screen, is_visible)
        
        # ===== КРУПНАЯ СЕТКА (ЧАНКИ) =====
        chunk_left = int(left // CHUNK_SIZE) - 2
        chunk_top = int(top // CHUNK_SIZE) - 2
        chunk_right = int(right // CHUNK_SIZE) + 2
        chunk_bottom = int(bottom // CHUNK_SIZE) + 2
        
        for cx in range(chunk_left, chunk_right + 1):
            for cy in range(chunk_top, chunk_bottom + 1):
                chunk_wx = cx * CHUNK_SIZE
                chunk_wy = cy * CHUNK_SIZE
                
                sx, sy = world_to_screen(chunk_wx, chunk_wy)
                chunk_px = CHUNK_SIZE * self.map_scale
                
                if not is_visible_on_screen(sx, sy, chunk_px):
                    continue
                
                has_base = False
                chunk = chunk_manager.get_chunk(cx, cy)
                if chunk and chunk.loaded:
                    if chunk.objects.get('enemy_bases'):
                        has_base = True
                
                # Более яркие цвета для чанков
                if cx == 0 and cy == 0:
                    color = (0, 120, 0)  # Ярче зелёный
                elif has_base:
                    color = (120, 30, 30)  # Ярче красный
                else:
                    color = (40, 40, 60)  # Ярче серый
                
                rect = pygame.Rect(sx, sy, chunk_px, chunk_px)
                pygame.draw.rect(screen, color, rect, 2)  # Толще линия
                
                if chunk_px > 30:
                    label = f"{cx},{cy}"
                    text = self.small_font.render(label, True, (80, 80, 120))
                    screen.blit(text, (sx + 3, sy + 3))
                    
        # ===== МЕЛКАЯ СЕТКА (1/8 чанка) =====
        grid_step = CHUNK_SIZE // 8
        grid_px = grid_step * self.map_scale
        
        # Рисуем сетку всегда, если есть место
        if grid_px > 3:
            chunk_left = int(left // CHUNK_SIZE) - 1
            chunk_top = int(top // CHUNK_SIZE) - 1
            chunk_right = int(right // CHUNK_SIZE) + 1
            chunk_bottom = int(bottom // CHUNK_SIZE) + 1
            
            for cx in range(chunk_left, chunk_right + 1):
                for cy in range(chunk_top, chunk_bottom + 1):
                    chunk_wx = cx * CHUNK_SIZE
                    chunk_wy = cy * CHUNK_SIZE
                    
                    sx, sy = world_to_screen(chunk_wx, chunk_wy)
                    chunk_px = CHUNK_SIZE * self.map_scale
                    
                    if sx > self.map_width + 10 or sx + chunk_px < -10 or sy > self.map_height + 10 or sy + chunk_px < -10:
                        continue
                    
                    # Рисуем яркие линии сетки 8x8 внутри чанка
                    for i in range(1, 8):
                        # Вертикальные линии (более яркие)
                        lx = chunk_wx + i * grid_step
                        if is_visible(lx, chunk_wy):
                            x1, y1 = world_to_screen(lx, chunk_wy)
                            x2, y2 = world_to_screen(lx, chunk_wy + CHUNK_SIZE)
                            # Яркость зависит от масштаба
                            alpha = max(50, min(150, int(80 * self.map_scale)))
                            color = (alpha, alpha, alpha + 40)
                            if is_visible_on_screen(x1, y1) or is_visible_on_screen(x2, y2):
                                pygame.draw.line(screen, color, (x1, y1), (x2, y2), 1)
                        
                        # Горизонтальные линии
                        ly = chunk_wy + i * grid_step
                        if is_visible(chunk_wx, ly):
                            x1, y1 = world_to_screen(chunk_wx, ly)
                            x2, y2 = world_to_screen(chunk_wx + CHUNK_SIZE, ly)
                            alpha = max(50, min(150, int(80 * self.map_scale)))
                            color = (alpha, alpha, alpha + 40)
                            if is_visible_on_screen(x1, y1) or is_visible_on_screen(x2, y2):
                                pygame.draw.line(screen, color, (x1, y1), (x2, y2), 1)
                    
                    # Узлы сетки (яркие точки на пересечениях)
                    for i in range(1, 8):
                        for j in range(1, 8):
                            node_wx = chunk_wx + i * grid_step
                            node_wy = chunk_wy + j * grid_step
                            
                            nx, ny = world_to_screen(node_wx, node_wy)
                            
                            if 0 < nx < self.map_width and 0 < ny < self.map_height:
                                # Яркие точки на пересечениях
                                size = max(2, int(3 * self.map_scale))
                                pygame.draw.circle(screen, (100, 100, 180), (int(nx), int(ny)), size)
                                
        # ===== БАЗЫ ВРАГОВ =====
        for base in enemy_bases:
            if not base.alive:
                continue
            
            if is_visible(base.x, base.y):
                sx, sy = world_to_screen(base.x, base.y)
                size = max(4, min(12, int(base.radius * self.map_scale * 0.5)))
                color = self.base_colors.get(base.base_type, (255, 0, 0))
                
                rect = pygame.Rect(sx - size//2, sy - size//2, size, size)
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, (255, 255, 255), rect, 1)
                
                if size > 6:
                    count_text = self.small_font.render(str(base.current_enemies), True, (255, 255, 255))
                    count_rect = count_text.get_rect(center=(sx, sy))
                    screen.blit(count_text, count_rect)
        
        # ===== АСТЕРОИДЫ =====
        for asteroid in asteroids[:50]:
            if is_visible(asteroid.x, asteroid.y):
                sx, sy = world_to_screen(asteroid.x, asteroid.y)
                size = max(1, int(asteroid.radius * self.map_scale * 0.3))
                pygame.draw.circle(screen, self.asteroid_color, (int(sx), int(sy)), max(1, size))
        
        # ===== ВРАГИ =====
        for enemy in enemies[:50]:
            if enemy.health > 0 and is_visible(enemy.x, enemy.y):
                sx, sy = world_to_screen(enemy.x, enemy.y)
                size = max(1, int(enemy.radius * self.map_scale * 0.3))
                pygame.draw.circle(screen, self.enemy_color, (int(sx), int(sy)), max(1, size))
        
        # ===== ИГРОК =====
        if is_visible(player_x, player_y):
            sx, sy = world_to_screen(player_x, player_y)
            
            glow_size = 30
            glow = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            for r in range(15, 0, -3):
                alpha = max(0, 30 - (15 - r) * 4)
                pygame.draw.circle(glow, (0, 255, 0, alpha), (glow_size, glow_size), r)
            screen.blit(glow, (int(sx - glow_size), int(sy - glow_size)))
            
            pygame.draw.circle(screen, (255, 255, 255), (int(sx), int(sy)), 6)
            pygame.draw.circle(screen, self.player_color, (int(sx), int(sy)), 4)
        
        # ===== ИНФОРМАЦИОННАЯ ПАНЕЛЬ =====
        panel_y = HEIGHT - 80
        pygame.draw.rect(screen, (20, 20, 40), (20, panel_y, WIDTH - 40, 60))
        pygame.draw.rect(screen, (50, 50, 80), (20, panel_y, WIDTH - 40, 60), 1)
        
        info_x = 40
        
        # Информация о маркерах в панели
        info_texts = [
            f"Bases: {len([b for b in enemy_bases if b.alive])}",
            f"Enemies: {len(enemies)}",
            f"Chunks: {len(chunk_manager.chunks)}",
            f"Waypoints: {len(self.waypoint_manager.get_waypoints())}",
            f"Player: ({int(player_x)}, {int(player_y)})",
        ]
        for text in info_texts:
            label = self.font.render(text, True, (200, 200, 200))
            screen.blit(label, (info_x, panel_y + 20))
            info_x += 150
        
        # Легенда
        legend_x = 40
        legend_y = panel_y + 5
        legend_items = [
            ("Player", (0, 255, 0)),
            ("Base", (255, 50, 50)),
            ("Enemy", (255, 100, 100)),
            ("Asteroid", (100, 100, 80)),
        ]
        for name, color in legend_items:
            pygame.draw.circle(screen, color, (legend_x + 5, legend_y + 8), 4)
            label = self.small_font.render(name, True, (150, 150, 150))
            screen.blit(label, (legend_x + 12, legend_y + 2))
            legend_x += 70
            