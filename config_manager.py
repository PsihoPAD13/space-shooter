# config_manager.py
import json
import os

class ConfigManager:
    """Управление настройками игры"""
    
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.default_config = {
            'game': {
                'difficulty': 'normal',
                'sound_volume': 0.7,
                'music_volume': 0.5,
                'fullscreen': False,
                'show_fps': False,
                'high_score': 0,
                'debug_mode': False,
            },
            'controls': {
                'mouse_control': True,
                'keyboard_control': True,
                'mouse_sensitivity': 1.0,
            },
            'graphics': {
                'particle_density': 1.0,
                'star_density': 1.0,
                'show_health_bars': True,
                'show_minimap': True,
            }
        }
        
        # Проверяем, существует ли файл
        if not os.path.exists(self.config_file):
            # Если нет — создаём с настройками по умолчанию
            self.config = self.default_config.copy()
            self.save()
        else:
            # Если есть — загружаем
            self.config = self.load()
    
    def load(self):
        """Загружает настройки из файла"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Обновляем дефолтные значения, если чего-то нет
                    return self._merge_configs(self.default_config, config)
            except:
                return self.default_config.copy()
        return self.default_config.copy()
    
    def save(self):
        """Сохраняет настройки в файл"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except:
            return False
    
    def _merge_configs(self, default, user):
        """Рекурсивно объединяет настройки"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def get(self, key, default=None):
        """Получает значение по ключу (разделение точкой)"""
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except:
            return default
    
    def set(self, key, value):
        """Устанавливает значение по ключу"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save()
    
    def get_high_score(self):
        """Возвращает текущий рекорд"""
        return self.config.get('game', {}).get('high_score', 0)
    
    def set_high_score(self, score):
        """Обновляет рекорд, если он больше текущего"""
        current = self.get_high_score()
        if score > current:
            self.set('game.high_score', score)
            return True  # Рекорд побит
        return False