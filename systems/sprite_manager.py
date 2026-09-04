# systems/sprite_manager.py
import pygame
import json

class SpriteManager:
    def __init__(self, config_path='assets/config/sprites.json'):
        self.config_path = config_path
        self.sprites = {}
        self.config = {}
        self.load_config()
    
    def load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            # Загружаем все спрайты
            for category in ['ships', 'weapons', 'engines', 'shields']:
                for sprite_id, data in self.config.get(category, {}).items():
                    sprite_path = f"assets/sprites/{data['sprite']}"
                    self.load_sprite(sprite_id, sprite_path)
                   
        except Exception as e:
            print(f"[SPRITE] Ошибка загрузки конфига: {e}")
    
    def load_sprite(self, sprite_id, path):
        try:
            sprite = pygame.image.load(path).convert_alpha()
            self.sprites[sprite_id] = sprite
        except Exception as e:
            print(f"[SPRITE] ❌ {sprite_id}: {e}")
    
    def get(self, sprite_id):
        return self.sprites.get(sprite_id)
    
    def get_config(self, category, sprite_id):
        return self.config.get(category, {}).get(sprite_id)
    
    def get_sprite_data(self, category, sprite_id):
        return self.config.get(category, {}).get(sprite_id)
    
    def get_all_in_category(self, category):
        return list(self.config.get(category, {}).keys())
    
    def get_colors(self):
        return self.config.get('colors', {})
    
    def get_slots(self, category, sprite_id):
        data = self.get_sprite_data(category, sprite_id)
        return data.get('slots', {}) if data else {}
    
    def get_pivot(self, category, sprite_id):
        data = self.get_sprite_data(category, sprite_id)
        return data.get('pivot', [0, 0]) if data else [0, 0]
    
    def get_size(self, category, sprite_id):
        data = self.get_sprite_data(category, sprite_id)
        return data.get('size', [32, 32]) if data else [32, 32]