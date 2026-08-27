# settings_menu.py
import pygame
from settings import WIDTH, HEIGHT, WHITE, BLACK, GRAY, YELLOW, GREEN, RED, BLUE

class SettingsMenu:
    def __init__(self, screen, config):
        self.screen = screen
        self.config = config
        self.font_title = pygame.font.Font(None, 60)
        self.font_menu = pygame.font.Font(None, 30)
        self.font_small = pygame.font.Font(None, 20)
        self.font_header = pygame.font.Font(None, 26)
        
        self.options = []
        self.selected = 0
        
        self._build_options()
    
    def _build_options(self):
        self.options = [
            # GAME
            {'label': '-- GAME --', 'key': None, 'type': 'header', 'status': 'info'},
            {'label': 'Difficulty', 'key': 'game.difficulty', 'type': 'choice', 'choices': ['easy', 'normal', 'hard'], 'status': 'working'},
            {'label': 'Show FPS', 'key': 'game.show_fps', 'type': 'toggle', 'status': 'working'},
            {'label': 'Fullscreen', 'key': 'game.fullscreen', 'type': 'toggle', 'status': 'planned'},
            
            # SOUND
            {'label': '-- SOUND --', 'key': None, 'type': 'header', 'status': 'info'},
            {'label': 'Sound Volume', 'key': 'game.sound_volume', 'type': 'slider', 'min': 0, 'max': 1, 'step': 0.1, 'status': 'planned'},
            {'label': 'Music Volume', 'key': 'game.music_volume', 'type': 'slider', 'min': 0, 'max': 1, 'step': 0.1, 'status': 'planned'},
            
            # CONTROLS
            {'label': '-- CONTROLS --', 'key': None, 'type': 'header', 'status': 'info'},
            {'label': 'Mouse Control', 'key': 'controls.mouse_control', 'type': 'toggle', 'status': 'working'},
            {'label': 'Mouse Sensitivity', 'key': 'controls.mouse_sensitivity', 'type': 'slider', 'min': 0.5, 'max': 2.0, 'step': 0.1, 'status': 'working'},
            
            # GRAPHICS
            {'label': '-- GRAPHICS --', 'key': None, 'type': 'header', 'status': 'info'},
            {'label': 'Particle Density', 'key': 'graphics.particle_density', 'type': 'slider', 'min': 0.5, 'max': 1.5, 'step': 0.1, 'status': 'working'},
            {'label': 'Show Health Bars', 'key': 'graphics.show_health_bars', 'type': 'toggle', 'status': 'working'},
            {'label': 'Star Density', 'key': 'graphics.star_density', 'type': 'slider', 'min': 0.5, 'max': 2.0, 'step': 0.1, 'status': 'planned'},
            {'label': 'Show Minimap', 'key': 'graphics.show_minimap', 'type': 'toggle', 'status': 'working'},
        ]
    
    def draw_background(self):
        self.screen.fill((20, 20, 40))
        import random
        for _ in range(50):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            brightness = random.randint(50, 150)
            pygame.draw.circle(self.screen, (brightness, brightness, brightness), (x, y), 1)
    
    def draw_title(self):
        title = self.font_title.render("SETTINGS", True, YELLOW)
        title_rect = title.get_rect(center=(WIDTH//2, 30))
        self.screen.blit(title, title_rect)
        
        # Легенда вверху
        y = 60
        working = self.font_small.render("[+] Working", True, GREEN)
        self.screen.blit(working, (WIDTH//2 - 200, y))
        
        planned = self.font_small.render("[ ] Planned", True, GRAY)
        self.screen.blit(planned, (WIDTH//2 - 60, y))
        
        info = self.font_small.render("[-] Info", True, BLUE)
        self.screen.blit(info, (WIDTH//2 + 80, y))
    
    def draw_option(self, option, y, selected=False):
        # Заголовки
        if option['type'] == 'header':
            color = BLUE
            text = self.font_header.render(option['label'], True, color)
            text_rect = text.get_rect(center=(WIDTH//2, y + 5))
            self.screen.blit(text, text_rect)
            return
        
        # Цвет текста
        if option.get('status') == 'planned':
            text_color = (80, 80, 80)
        else:
            text_color = YELLOW if selected else WHITE
        
        font = self.font_menu
        if selected and option.get('status') != 'planned':
            font = pygame.font.Font(None, 34)
        
        # ===== НАЗВАНИЕ =====
        label_text = font.render(option['label'] + ":", True, text_color)
        label_rect = label_text.get_rect(center=(WIDTH//2 - 140, y))
        self.screen.blit(label_text, label_rect)
        
        # ===== ЗНАЧЕНИЕ =====
        value = self.config.get(option['key'])
        
        if option['type'] == 'choice':
            color = GREEN if option.get('status') != 'planned' else GRAY
            value_text = font.render(str(value), True, color)
            value_rect = value_text.get_rect(center=(WIDTH//2 + 100, y))
            self.screen.blit(value_text, value_rect)
            
        elif option['type'] == 'toggle':
            if option.get('status') == 'planned':
                color = GRAY
            else:
                color = GREEN if value else RED
            value_text = font.render("ON" if value else "OFF", True, color)
            value_rect = value_text.get_rect(center=(WIDTH//2 + 100, y))
            self.screen.blit(value_text, value_rect)
            
        elif option['type'] == 'slider':
            slider_width = 120
            slider_x = WIDTH//2 + 20
            slider_y = y
            
            if option.get('status') == 'planned':
                slider_color = (60, 60, 60)
                handle_color = GRAY
            else:
                slider_color = YELLOW
                handle_color = WHITE
            
            pygame.draw.rect(self.screen, (40, 40, 40), 
                           (slider_x, slider_y - 5, slider_width, 10))
            pygame.draw.rect(self.screen, (80, 80, 80), 
                           (slider_x, slider_y - 5, slider_width, 10), 1)
            
            min_val = option.get('min', 0)
            max_val = option.get('max', 1)
            percent = (value - min_val) / (max_val - min_val)
            fill_width = int(slider_width * percent)
            
            if option.get('status') != 'planned':
                pygame.draw.rect(self.screen, slider_color, 
                               (slider_x + 2, slider_y - 3, max(0, fill_width - 4), 6))
            
            handle_x = slider_x + fill_width
            pygame.draw.circle(self.screen, handle_color, (handle_x, slider_y), 7)
            pygame.draw.circle(self.screen, (50, 50, 50), (handle_x, slider_y), 7, 1)
            
            color = WHITE if option.get('status') != 'planned' else GRAY
            value_text = font.render(f"{value:.1f}", True, color)
            value_rect = value_text.get_rect(center=(slider_x + slider_width + 40, y))
            self.screen.blit(value_text, value_rect)
            return
        
        # ===== "SOON" ДЛЯ ПЛАНИРУЕМЫХ =====
        if option.get('status') == 'planned':
            planned_text = self.font_small.render("(soon)", True, GRAY)
            planned_rect = planned_text.get_rect(center=(WIDTH//2 + 180, y))
            self.screen.blit(planned_text, planned_rect)
    
    def draw(self):
        self.draw_background()
        self.draw_title()
        
        y_start = 90
        y_spacing = 35
        
        for i, option in enumerate(self.options):
            y = y_start + i * y_spacing
            self.draw_option(option, y, i == self.selected)
        
        hint = self.font_small.render("ESC: Back | <-/->: Change", True, GRAY)
        hint_rect = hint.get_rect(center=(WIDTH//2, HEIGHT - 18))
        self.screen.blit(hint, hint_rect)
    
    def run(self):
        running = True
        clock = pygame.time.Clock()
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.config.save()
                        return "back"
                    
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.selected = (self.selected - 1) % len(self.options)
                        while self.options[self.selected]['type'] == 'header':
                            self.selected = (self.selected - 1) % len(self.options)
                    
                    if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.selected = (self.selected + 1) % len(self.options)
                        while self.options[self.selected]['type'] == 'header':
                            self.selected = (self.selected + 1) % len(self.options)
                    
                    option = self.options[self.selected]
                    if option.get('status') == 'planned':
                        continue
                    
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self._change_value(option, -1)
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self._change_value(option, 1)
                    if event.key == pygame.K_RETURN:
                        self._change_value(option, 1)
                
                # Мышь
                if event.type == pygame.MOUSEMOTION:
                    mouse_x, mouse_y = event.pos
                    y_start = 90
                    y_spacing = 35
                    for i, option in enumerate(self.options):
                        if option['type'] == 'header':
                            continue
                        y = y_start + i * y_spacing
                        if WIDTH//2 - 250 < mouse_x < WIDTH//2 + 250 and y - 15 < mouse_y < y + 15:
                            self.selected = i
                            break
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_x, mouse_y = event.pos
                    y_start = 90
                    y_spacing = 35
                    
                    for i, option in enumerate(self.options):
                        if option['type'] == 'header':
                            continue
                        y = y_start + i * y_spacing
                        if WIDTH//2 - 250 < mouse_x < WIDTH//2 + 250 and y - 15 < mouse_y < y + 15:
                            self.selected = i
                            if option.get('status') != 'planned':
                                if option['type'] == 'toggle':
                                    self._change_value(option, 1)
                                elif option['type'] == 'choice':
                                    self._change_value(option, 1)
                            break
                    
                    for i, option in enumerate(self.options):
                        if option['type'] == 'slider' and option.get('status') != 'planned':
                            y = 90 + i * 35
                            slider_x = WIDTH//2 + 20
                            slider_width = 120
                            if (slider_x - 15 < mouse_x < slider_x + slider_width + 50 and
                                y - 15 < mouse_y < y + 15):
                                self.selected = i
                                min_val = option.get('min', 0)
                                max_val = option.get('max', 1)
                                percent = (mouse_x - slider_x) / slider_width
                                percent = max(0, min(1, percent))
                                new_value = min_val + percent * (max_val - min_val)
                                step = option.get('step', 0.1)
                                new_value = round(new_value / step) * step
                                new_value = max(min_val, min(max_val, new_value))
                                self.config.set(option['key'], new_value)
                                break
            
            self.draw()
            pygame.display.flip()
            clock.tick(60)
        
        return "back"
    
    def _change_value(self, option, direction):
        if option.get('status') == 'planned':
            return
        
        if option['type'] == 'choice':
            choices = option['choices']
            current = self.config.get(option['key'])
            idx = choices.index(current) if current in choices else 0
            idx = (idx + direction) % len(choices)
            self.config.set(option['key'], choices[idx])
        
        elif option['type'] == 'toggle':
            current = self.config.get(option['key'])
            self.config.set(option['key'], not current)
        
        elif option['type'] == 'slider':
            current = self.config.get(option['key'])
            step = option.get('step', 0.1)
            new_value = current + direction * step
            new_value = round(new_value / step) * step
            new_value = max(option.get('min', 0), min(option.get('max', 1), new_value))
            self.config.set(option['key'], new_value)