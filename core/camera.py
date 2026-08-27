# core/camera.py
class Camera:
    def __init__(self, x, y, width, height):
        self.x = x - width // 2
        self.y = y - height // 2
        self.width = width
        self.height = height
    
    def update(self, target_x, target_y):
        self.x = target_x - self.width // 2
        self.y = target_y - self.height // 2