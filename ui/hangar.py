# ui/hangar.py
import pygame
from settings import WIDTH, HEIGHT

class Hangar:
    def __init__(self, screen, ship, sprite_manager, hangar_state=None):
        self.screen = screen
        self.ship = ship
        self.sprite_manager = sprite_manager
        self.active = True
        self.hangar_state = hangar_state  # Состояние из игры
        
        # Категории
        self.categories = ['ships', 'weapons', 'engines', 'shields']
        self.category_names = ['Корпус', 'Пушка', 'Двигатель', 'Щит']
        self.selected_category = 0
        self.selected_part = 0
        
        # Загружаем состояние или создаём новое
        if self.hangar_state:
            self.current_parts = self.hangar_state.get('current_parts', {})
            self.selected_indices = self.hangar_state.get('selected_indices', {})
        else:
            self.current_parts = {
                'ships': 'player_base',
                'weapons': 'weapon_static',
                'engines': 'engine_small',
                'shields': 'shield_basic'
            }
            self.selected_indices = {
                'ships': 0,
                'weapons': 0,
                'engines': 0,
                'shields': 0
            }
        
        # Обновляем списки
        self.update_part_lists()
        
        # Восстанавливаем выбранный индекс для текущей категории
        cat = self.categories[self.selected_category]
        self.selected_part = self.selected_indices.get(cat, 0)
        
        # Шрифты
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 20)
    
    def update_part_lists(self):
        """Обновляет списки доступных деталей для каждой категории"""
        self.part_lists = {}
        for cat in self.categories:
            parts = self.sprite_manager.get_all_in_category(cat)
            self.part_lists[cat] = parts if parts else []
        
        # Проверяем, что выбранные детали существуют
        for cat in self.categories:
            part_list = self.part_lists.get(cat, [])
            if not part_list:
                continue
            
            if cat in self.current_parts:
                current = self.current_parts[cat]
                if current not in part_list:
                    self.current_parts[cat] = part_list[0]
                    self.selected_indices[cat] = 0
            else:
                self.current_parts[cat] = part_list[0]
                self.selected_indices[cat] = 0
    
    def handle_event(self, event):
        if not self.active:
            return
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Сохраняем состояние перед закрытием
                self._save_state()
                self.active = False
                return
            
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                self.selected_category = (self.selected_category - 1) % len(self.categories)
                cat = self.categories[self.selected_category]
                self.selected_part = self.selected_indices.get(cat, 0)
                
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                self.selected_category = (self.selected_category + 1) % len(self.categories)
                cat = self.categories[self.selected_category]
                self.selected_part = self.selected_indices.get(cat, 0)
                
            elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                cat = self.categories[self.selected_category]
                part_list = self.part_lists.get(cat, [])
                if part_list:
                    self.selected_part = (self.selected_part - 1) % len(part_list)
                    self.selected_indices[cat] = self.selected_part
                    
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                cat = self.categories[self.selected_category]
                part_list = self.part_lists.get(cat, [])
                if part_list:
                    self.selected_part = (self.selected_part + 1) % len(part_list)
                    self.selected_indices[cat] = self.selected_part
                    
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                self._apply_selection()
    
    def _save_state(self):
        """Сохраняет текущее состояние в hangar_state"""
        if self.hangar_state is not None:
            self.hangar_state['current_parts'] = self.current_parts.copy()
            self.hangar_state['selected_indices'] = self.selected_indices.copy()
            print("[HANGAR] Состояние сохранено")
    
    def _apply_selection(self):
        cat = self.categories[self.selected_category]
        part_list = self.part_lists.get(cat, [])
        if not part_list:
            print(f"[HANGAR] Нет деталей в категории {cat}")
            return
        
        part_id = part_list[self.selected_part if self.selected_part < len(part_list) else 0]
        self.current_parts[cat] = part_id
        self.selected_indices[cat] = self.selected_part
        
        print(f"[HANGAR] Установлен {cat}: {part_id}")
        self._update_ship()
        # Сохраняем состояние после применения
        self._save_state()
    
    def _update_ship(self):
        """Обновляет корабль в соответствии с выбранными деталями"""
        hull_id = self.current_parts.get('ships', 'player_base')
        
        # Применяем корпус
        self.ship._apply_hull(hull_id)
        self.ship.update_speed()  # <-- ДОБАВЛЯЕМ
        
        # Применяем оружие
        weapon_id = self.current_parts.get('weapons', 'weapon_static')
        self.ship.set_weapon(weapon_id)
        
        # Применяем двигатель (пока просто логируем)
        engine_id = self.current_parts.get('engines', 'engine_small')
        engine_data = self.sprite_manager.get_sprite_data('engines', engine_id)
        if engine_data:
            print(f"[HANGAR] Двигатель: {engine_id}")
        
        # Применяем щит
        shield_id = self.current_parts.get('shields', 'shield_basic')
        shield_data = self.sprite_manager.get_sprite_data('shields', shield_id)
        if shield_data:
            print(f"[HANGAR] Щит: {shield_id}")
    
    def draw(self):
        if not self.active:
            return
        
        # Затемнение
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        # Заголовок
        title = self.font.render("🛠️ АНГАР", True, (255, 255, 255))
        title_rect = title.get_rect(center=(WIDTH // 2, 40))
        self.screen.blit(title, title_rect)
        
        # Корабль
        ship_x = WIDTH // 2 - 80
        ship_y = HEIGHT // 2 - 80
        if self.ship.sprite:
            sprite = self.ship.sprite
            if sprite.get_width() < 100:
                sprite = pygame.transform.scale(sprite, (100, 100))
            rotated = pygame.transform.rotate(sprite, -self.ship.angle - 90)
            self.screen.blit(rotated, (ship_x, ship_y))
        
        # Информация о корабле
        info_y = HEIGHT // 2 + 100
        stats_text = self.small_font.render("Характеристики:", True, (200, 200, 200))
        self.screen.blit(stats_text, (WIDTH // 2 - 80, info_y))
        
        hull_id = self.current_parts.get('ships', 'player_base')
        hull_data = self.sprite_manager.get_sprite_data('ships', hull_id)
        if hull_data:
            stats = hull_data.get('stats', {})
            hp = stats.get('hp', 0)
            speed = stats.get('speed', 1.0)
            stat_line = self.small_font.render(f"HP: {hp} | Speed: {speed}", True, (150, 150, 150))
            self.screen.blit(stat_line, (WIDTH // 2 - 80, info_y + 25))
        
        # Слоты (справа)
        slot_x = WIDTH // 2 + 130
        slot_y = 100
        for i, cat in enumerate(self.categories):
            color = (255, 255, 100) if i == self.selected_category else (200, 200, 200)
            
            cat_text = self.small_font.render(self.category_names[i], True, color)
            self.screen.blit(cat_text, (slot_x, slot_y + i * 45))
            
            part_list = self.part_lists.get(cat, [])
            if part_list:
                if i == self.selected_category:
                    idx = self.selected_part if self.selected_part < len(part_list) else 0
                else:
                    saved_id = self.current_parts.get(cat)
                    if saved_id in part_list:
                        idx = part_list.index(saved_id)
                    else:
                        idx = 0
                part_id = part_list[idx]
                part_data = self.sprite_manager.get_sprite_data(cat, part_id)
                part_name = part_data.get('name', part_id) if part_data else part_id
            else:
                part_name = "Нет деталей"
            
            part_text = self.small_font.render(part_name, True, (150, 150, 150))
            self.screen.blit(part_text, (slot_x + 90, slot_y + i * 45))
        
        # Подсказка
        hint = self.small_font.render("↑↓ выбрать  ←→ изменить  ENTER: применить  ESC: выйти", True, (80, 80, 80))
        hint_rect = hint.get_rect(center=(WIDTH // 2, HEIGHT - 30))
        self.screen.blit(hint, hint_rect)