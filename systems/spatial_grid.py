# systems/spatial_grid.py
import math

class SpatialGrid:
    """Пространственное разделение для оптимизации коллизий"""
    
    def __init__(self, cell_size=200):
        self.cell_size = cell_size
        self.grid = {}
        self.objects = []
    
    def clear(self):
        """Очищает сетку"""
        self.grid.clear()
        self.objects.clear()
    
    def add(self, obj):
        """Добавляет объект в сетку"""
        self.objects.append(obj)
        key = self._get_key(obj.x, obj.y)
        if key not in self.grid:
            self.grid[key] = []
        self.grid[key].append(obj)
    
    def add_bullet(self, bullet):
        """Добавляет пулю (учитывает радиус)"""
        self.objects.append(bullet)
        # Пуля может занимать несколько ячеек
        keys = self._get_keys_for_circle(bullet.x, bullet.y, bullet.radius)
        for key in keys:
            if key not in self.grid:
                self.grid[key] = []
            self.grid[key].append(bullet)
    
    def remove(self, obj):
        """Удаляет объект из сетки"""
        if obj in self.objects:
            self.objects.remove(obj)
        
        # Удаляем из всех ячеек
        for key, objects in list(self.grid.items()):
            if obj in objects:
                objects.remove(obj)
                if not objects:
                    del self.grid[key]
    
    def _get_key(self, x, y):
        """Возвращает ключ ячейки для координат"""
        return (int(x // self.cell_size), int(y // self.cell_size))
    
    def _get_keys_for_circle(self, x, y, radius):
        """Возвращает все ячейки, которые пересекает круг"""
        min_x = int((x - radius) // self.cell_size)
        max_x = int((x + radius) // self.cell_size)
        min_y = int((y - radius) // self.cell_size)
        max_y = int((y + radius) // self.cell_size)
        
        keys = []
        for cx in range(min_x, max_x + 1):
            for cy in range(min_y, max_y + 1):
                keys.append((cx, cy))
        return keys
    
    def get_nearby(self, obj):
        """Возвращает объекты в соседних ячейках"""
        if hasattr(obj, 'radius'):
            keys = self._get_keys_for_circle(obj.x, obj.y, obj.radius)
        else:
            keys = [self._get_key(obj.x, obj.y)]
        
        nearby = []
        seen = set()
        for key in keys:
            if key in self.grid:
                for other in self.grid[key]:
                    if other != obj and id(other) not in seen:
                        nearby.append(other)
                        seen.add(id(other))
        
        return nearby
    
    def get_potential_pairs(self, obj, others):
        """Возвращает потенциальные пары для коллизий"""
        nearby = self.get_nearby(obj)
        pairs = []
        for other in nearby:
            if other in others:
                pairs.append((obj, other))
        return pairs
    
    def update_object(self, obj):
        """Обновляет позицию объекта в сетке"""
        # Удаляем и добавляем заново
        self.remove(obj)
        self.add(obj)