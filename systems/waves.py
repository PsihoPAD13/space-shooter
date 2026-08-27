# systems/waves.py
from settings import *

class WaveSystem:
    def __init__(self):
        self.wave_number = 1
        self.enemies_to_spawn = WAVE_ENEMY_COUNT
        self.enemies_spawned = 0
        self.wave_active = True
        self.wave_pause_timer = 0
        self.wave_spawn_timer = 0
    
    def update(self, enemies, spawn_func):
        # ... логика волн
        pass