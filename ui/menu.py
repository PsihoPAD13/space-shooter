# menu.py
import pygame
import sys
import random
from settings import WIDTH, HEIGHT, BLACK, WHITE, YELLOW, GRAY, BLUE, GREEN, RED

class Menu:
    def __init__(self, screen, config):  # <-- ДОБАВЛЯЕМ config
        self.screen = screen
        self.config = config  # <-- СОХРАНЯЕМ
        self.clock = pygame.time.Clock()
        self.font_title = pygame.font.Font(None, 80)
        self.font_menu = pygame.font.Font(None, 40)
        self.font_small = pygame.font.Font(None, 24)
        
        # Пункты меню
        self.options = [
            "Start Game",
            "Settings",
            "Controls",
            "Quit"
        ]
        self.selected = 0
        
        # Звезды для фона
        self.stars = []
        for _ in range(100):
            self.stars.append({
                'x': random.randint(0, WIDTH),
                'y': random.randint(0, HEIGHT),
                'size': random.randint(1, 2),
                'speed': random.uniform(0.5, 1.5),
                'phase': random.uniform(0, 6.28)
            })
        
        # Прямоугольники для кликов
        self.option_rects = []
    
    def draw_background(self):
        """Рисует космический фон"""
        self.screen.fill(BLACK)
        
        current_time = pygame.time.get_ticks() * 0.001
        
        for star in self.stars:
            twinkle = 0.5 + 0.5 * (1 + pygame.math.Vector2(
                current_time * star['speed'] + star['phase'],
                0
            ).length() % 1)
            
            brightness = int(50 + 150 * twinkle)
            brightness = max(0, min(255, brightness))
            
            color = (brightness, brightness, brightness)
            pygame.draw.circle(self.screen, color, 
                             (int(star['x']), int(star['y'])), star['size'])
        
        # Туманности
        for i in range(5):
            x = (WIDTH * 0.1 + i * WIDTH * 0.2 + pygame.time.get_ticks() * 0.01 * (i + 1)) % WIDTH
            y = (HEIGHT * 0.2 + i * HEIGHT * 0.15 + pygame.time.get_ticks() * 0.005 * (i + 1)) % HEIGHT
            radius = 80 + 40 * (0.5 + 0.5 * (1 + pygame.math.Vector2(
                pygame.time.get_ticks() * 0.001 + i,
                0
            ).length() % 1))
            
            colors = [
                (80, 20, 150, 40),
                (20, 80, 150, 40),
                (150, 20, 80, 40),
                (20, 150, 80, 40),
                (150, 80, 20, 40),
            ]
            
            glow = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
            color = colors[i % len(colors)]
            pygame.draw.circle(glow, color, (int(radius), int(radius)), int(radius))
            self.screen.blit(glow, (int(x - radius), int(y - radius)))
    
    def draw_title(self):
        """Рисует заголовок с эффектом"""
        title_shadow = self.font_title.render("SPACE SHOOTER", True, (50, 50, 50))
        shadow_rect = title_shadow.get_rect(center=(WIDTH//2 + 3, 100 + 3))
        self.screen.blit(title_shadow, shadow_rect)
        
        pulse = int(50 * (0.5 + 0.5 * (1 + pygame.math.Vector2(
            pygame.time.get_ticks() * 0.003,
            0
        ).length() % 1)))
        pulse = max(0, min(50, pulse))
        
        if (pygame.time.get_ticks() * 0.001) % 3 < 1.5:
            color = (100 + pulse, 100 + pulse // 2, 255)
        else:
            color = (255, 100 + pulse // 2, 100 + pulse)
        
        title = self.font_title.render("SPACE SHOOTER", True, color)
        title_rect = title.get_rect(center=(WIDTH//2, 100))
        self.screen.blit(title, title_rect)
        
        subtitle = self.font_small.render("- Top Down Shooter -", True, YELLOW)
        subtitle_rect = subtitle.get_rect(center=(WIDTH//2, 150))
        self.screen.blit(subtitle, subtitle_rect)
    
    def draw_menu(self):
        """Рисует пункты меню"""
        y_start = 260
        y_spacing = 55
        
        # Показываем рекорд
        high_score = self.config.get_high_score() if hasattr(self, 'config') else 0
        if high_score > 0:
            record_text = self.font_small.render(f"Best Score: {high_score}", True, GRAY)
            record_rect = record_text.get_rect(center=(WIDTH//2, y_start - 30))
            self.screen.blit(record_text, record_rect)
        
        self.option_rects = []
        
        for i, option in enumerate(self.options):
            if i == self.selected:
                color = YELLOW
                size_offset = int(5 * (0.5 + 0.5 * (1 + pygame.math.Vector2(
                    pygame.time.get_ticks() * 0.005 + i,
                    0
                ).length() % 1)))
                font = pygame.font.Font(None, 44 + size_offset)
            else:
                color = WHITE
                font = self.font_menu
            
            text = font.render(option, True, color)
            text_rect = text.get_rect(center=(WIDTH//2, y_start + i * y_spacing))
            self.option_rects.append(text_rect)
            self.screen.blit(text, text_rect)
            
            if i == self.selected:
                arrow = font.render(">", True, YELLOW)
                arrow_rect = arrow.get_rect(right=text_rect.left - 20, centery=text_rect.centery)
                self.screen.blit(arrow, arrow_rect)
    
    def draw_controls(self):
        """Рисует экран с управлением"""
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        title = self.font_title.render("CONTROLS", True, WHITE)
        title_rect = title.get_rect(center=(WIDTH//2, 80))
        self.screen.blit(title, title_rect)
        
        controls = [
            ("W / Up", "Thrust (Gas)"),
            ("A / Left", "Rotate Left"),
            ("D / Right", "Rotate Right"),
            ("SPACE", "Shoot"),
            ("P", "Pause"),
            ("ESC", "Exit / Menu"),
        ]
        
        y = 180
        for key, action in controls:
            key_text = self.font_menu.render(key, True, YELLOW)
            key_rect = key_text.get_rect(right=WIDTH//2 - 50, y=y)
            self.screen.blit(key_text, key_rect)
            
            action_text = self.font_menu.render(action, True, WHITE)
            action_rect = action_text.get_rect(left=WIDTH//2 + 50, y=y)
            self.screen.blit(action_text, action_rect)
            
            y += 45
        
        back = self.font_small.render("Press ESC to return", True, GRAY)
        back_rect = back.get_rect(center=(WIDTH//2, HEIGHT - 50))
        self.screen.blit(back, back_rect)
    
    def run(self):
        """Основной цикл меню"""
        showing_controls = False
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                # --- УПРАВЛЕНИЕ С КЛАВИАТУРЫ ---
                if event.type == pygame.KEYDOWN:
                    if showing_controls:
                        if event.key == pygame.K_ESCAPE:
                            showing_controls = False
                    else:
                        if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                            self.selected = (self.selected + 1) % len(self.options)
                        elif event.key == pygame.K_UP or event.key == pygame.K_w:
                            self.selected = (self.selected - 1) % len(self.options)
                        elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                            if self.selected == 0:
                                return "start"
                            elif self.selected == 1:
                                return "settings"
                            elif self.selected == 2:
                                showing_controls = True
                            elif self.selected == 3:
                                pygame.quit()
                                sys.exit()
                        elif event.key == pygame.K_ESCAPE:
                            pygame.quit()
                            sys.exit()
                
                # --- УПРАВЛЕНИЕ С МЫШКИ ---
                if event.type == pygame.MOUSEMOTION:
                    if not showing_controls:
                        mouse_pos = event.pos
                        for i, rect in enumerate(self.option_rects):
                            if rect.collidepoint(mouse_pos):
                                self.selected = i
                                break
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = event.pos
                    
                    if showing_controls:
                        back_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT - 80, 200, 40)
                        if back_rect.collidepoint(mouse_pos):
                            showing_controls = False
                    else:
                        for i, rect in enumerate(self.option_rects):
                            if rect.collidepoint(mouse_pos):
                                self.selected = i
                                if i == 0:
                                    return "start"
                                elif i == 1:
                                    return "settings"
                                elif i == 2:
                                    showing_controls = True
                                elif i == 3:
                                    pygame.quit()
                                    sys.exit()
            
            self.draw_background()
            self.draw_title()
            
            if showing_controls:
                self.draw_controls()
            else:
                self.draw_menu()
            
            pygame.display.flip()
            self.clock.tick(60)