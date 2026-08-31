# core/game.py
import pygame
import sys
import math
import random
from settings import *
from config_manager import ConfigManager
from entities.ship import Ship
from entities.enemy import Enemy
from entities.bullet import Bullet
from entities.powerups import PowerUpSystem
from systems.particles import ParticleSystem
from systems.minimap import Minimap
from world.starfield_background import BackgroundStars
from world.chunk_manager import ChunkManager
from core.camera import Camera
from utils import check_collision, distance_between, spawn_position
from systems.direction_indicators import DirectionIndicators
from entities.enemy_manager import EnemyManager
from entities.base import EnemyBase
from entities.player_base import PlayerBase
from systems.fuel import FuelSystem
from entities.asteroid import Asteroid
from systems.world_map import WorldMap
from systems.waypoints import Waypoint, WaypointManager

# Инициализация шрифтов (глобально для HUD)
pygame.font.init()
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 20)


class Game:
    def __init__(self, screen, config):
        self.screen = screen
        self.config = config
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_over = False
        self.paused = False

        # ===== ЗВЁЗДЫ (ФОН) =====
        self.starfield = BackgroundStars()

        # ===== МАРКЕРЫ =====
        self.waypoint_manager = WaypointManager()
        
        # ===== БОЛЬШАЯ КАРТА =====
        self.world_map = WorldMap(self.screen, config, self.waypoint_manager)  # <-- ПЕРЕДАЁМ
               
        # ===== МИР И ЧАНКИ =====
        self.chunk_manager = ChunkManager()

        # ===== КОРАБЛЬ =====
        self.ship = Ship(0, 0)
        self.camera = Camera(self.ship.x, self.ship.y, WIDTH, HEIGHT)

        # ===== ИГРОВЫЕ СИСТЕМЫ =====
        self.particles = ParticleSystem()
        self.powerups = PowerUpSystem()
        self.minimap = Minimap(self.screen, config)
        self.indicators = DirectionIndicators()

        # ===== СЛОЖНОСТЬ =====
        self.difficulty = config.get('game.difficulty', 'normal')
        self._apply_difficulty()
        
        # ===== МЕНЕДЖЕР ВРАГОВ =====
        self.enemy_manager = EnemyManager()

        # ===== СПИСКИ ОБЪЕКТОВ =====
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.asteroids = []      # <-- ДОБАВИТЬ
        self.enemy_bases = []

        # ===== БАЗА ИГРОКА =====
        from utils import spawn_position_with_safety
        from settings import DEBUG_MODE
        
        bx, by = spawn_position_with_safety(0, 0, 0, 0, min_distance=500)
        self.player_base = PlayerBase(bx, by)
        if DEBUG_MODE:
            print(f"[BASE] База игрока создана в ({int(bx)}, {int(by)})")
        
        # ===== ПРИНУДИТЕЛЬНАЯ ЗАГРУЗКА ЧАНКОВ =====
        self.chunks_loaded = False
        
        # Загружаем чанки вокруг игрока
        self.chunk_manager.update(self.ship.x, self.ship.y)
        
        # Загружаем базы из всех загруженных чанков
        self._force_load_chunk_objects()
        self.chunks_loaded = True
        
        # ===== ЕСЛИ НЕТ БАЗ - СОЗДАЁМ ТЕСТОВУЮ =====
        if len(self.enemy_bases) == 0:
            from settings import DEBUG_MODE
            if DEBUG_MODE:
                print(f"[GAME] ⚠️ НЕТ БАЗ! СОЗДАЮ ТЕСТОВУЮ...")
            test_base = EnemyBase(
                self.ship.x + 800,
                self.ship.y + 800,
                'standard'
            )
            self.enemy_bases.append(test_base)
            if DEBUG_MODE:
                print(f"[GAME] Тестовая база создана в ({int(test_base.x)}, {int(test_base.y)})")
                
        # ===== ЗАГРУЗКА ОБЪЕКТОВ ИЗ ЧАНКОВ =====
        self._load_chunk_objects()

        # ===== НАЧАЛЬНЫЕ ОБЪЕКТЫ (если чанки пустые) =====
        if len(self.asteroids) < 10:
            self._init_asteroids()
            
        # ===== ИГРОВЫЕ ПЕРЕМЕННЫЕ =====
        self.score = 0
        self.keys = pygame.key.get_pressed()
        self.mouse_pressed = False

        # ===== ТОПЛИВО =====
        self.fuel_system = FuelSystem(max_fuel=100)

        # ===== АСТЕРОИДЫ =====
        self._init_asteroids()

        # ===== ИНИЦИАЛИЗАЦИЯ БАЗ ВРАГОВ =====
        #self._init_bases()
        
        # ============================================================
        #  ОБРАБОТКА СОБЫТИЙ
        # ============================================================

    def handle_events(self):
        """Обработка событий"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # СОХРАНЯЕМ ВСЁ ПРИ ВЫХОДЕ
                self._save_modified_chunks()
                self._save_player_chunk()
                self.running = False
                return "quit"

            # Передаём события карте
            self.world_map.handle_events(event)
            
            # TAB - переключение карты (обрабатываем ДО передачи в world_map)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    self.world_map.toggle()
                    if self.world_map.visible:
                        self.paused = True
                    else:
                        self.paused = False
                    # Не передаём событие дальше
                    continue
                    
            # Передаём события карте (только если она видна)
            if self.world_map.visible:
                self.world_map.handle_events(event)
                # Если карта видна - не обрабатываем другие события
                continue
                        
            if event.type == pygame.KEYDOWN:
                # Чит-коды (только в режиме отладки)
                if self.config.get('game.debug_mode', False):
                    self._handle_cheats(event)

                # Стандартные клавиши
                if self.game_over:
                    if event.key == pygame.K_SPACE:
                        self._restart()
                    elif event.key == pygame.K_ESCAPE:
                        return "menu"
                else:
                    if event.key == pygame.K_ESCAPE:
                        return "menu"
                    elif event.key == pygame.K_p:
                        self.paused = not self.paused

            # Клик мыши для стрельбы
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.mouse_pressed = True
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.mouse_pressed = False

        return None

    def _handle_cheats(self, event):
        """Обработка чит-кодов"""
        from settings import DEBUG_MODE
        if not DEBUG_MODE:
            return
        
        if event.key == pygame.K_F1:
            self._activate_bomb()
            print("[CHEAT] 💥 Bomb activated!")
        elif event.key == pygame.K_F2:
            self.ship.health = self.ship.max_health
            print("[CHEAT] ❤️ Health restored!")
        elif event.key == pygame.K_F3:
            self.score += 50
            print(f"[CHEAT] ⭐ +50 points! Score: {self.score}")
        elif event.key == pygame.K_F4:
            for enemy in self.enemies[:]:
                enemy.destroy(self.particles)
                self.score += enemy.score_value
                self.enemies.remove(enemy)
            print(f"[CHEAT] 👾 All enemies killed! Score: {self.score}")
        elif event.key == pygame.K_F5:
            for _ in range(5):
                self._spawn_enemy()
            print("[CHEAT] 🌀 Spawned 5 enemies!")
        elif event.key == pygame.K_F6:
            print("[CHEAT] 🔄 Принудительная загрузка баз из файлов...")
            self._force_load_chunk_objects()
            print(f"[CHEAT] ✅ Загружено баз: {len(self.enemy_bases)}")
        elif event.key == pygame.K_F7:
            print("[CHEAT] 🧹 Принудительная очистка файлов...")
            for chunk in self.chunk_manager.chunks.values():
                if chunk.loaded:
                    bases = chunk.objects.get('enemy_bases', [])
                    chunk.objects['enemy_bases'] = [b for b in bases if b.get('health', 0) > 0]
                    chunk.modified = True
                    chunk.save(self.chunk_manager.world_dir)
            print("[CHEAT] ✅ Очистка завершена!")
            
    # ============================================================
    #  УПРАВЛЕНИЕ
    # ============================================================

    def _handle_controls(self):
        """Обработка управления с клавиатуры и мыши"""
        keys = self.keys

        # Клавиатура
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.ship.rotate_left()
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.ship.rotate_right()
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.ship.thrust()
        else:
            self.ship.stop_thrust()
        if keys[pygame.K_SPACE]:
            self.ship.shoot(self.bullets)

        # Мышь
        if self.config.get('controls.mouse_control', True):
            mouse_x, mouse_y = pygame.mouse.get_pos()
            world_mouse_x = mouse_x + self.camera.x
            world_mouse_y = mouse_y + self.camera.y
            self.ship.aim_at(world_mouse_x, world_mouse_y)

            if self.mouse_pressed:
                self.ship.shoot(self.bullets)
        
        # Варп (Shift)
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            if self.fuel_system.activate_warp():
                self.ship.set_warp(True)
        else:
            if self.fuel_system.warp_active:
                self.fuel_system.deactivate_warp()
                self.ship.set_warp(False)
                
    # ============================================================
    #  ИГРОВЫЕ МЕХАНИКИ
    # ============================================================

    def _init_bases(self):
        """Создаёт начальные ульи с проверкой расстояний"""
        from utils import spawn_position_with_safety

        for _ in range(random.randint(3, 5)):
            x, y = spawn_position_with_safety(
                self.ship.x,
                self.ship.y,
                self.ship.speed_x,
                self.ship.speed_y,
                min_distance=800,
                max_attempts=50,
                existing_bases=self.enemy_bases,  # Проверяем другие базы
                base_separation=600               # Минимум 600 между базами
            )
            base_type = random.choice(['standard', 'strong', 'fast', 'swarm'])
            base = EnemyBase(x, y, base_type)
            self.enemy_bases.append(base)
            print(f"[BASE] Улей типа {base_type} создан в ({int(x)}, {int(y)}) с {base.max_enemies} врагами")
            
    def _init_asteroids(self):
        """Создаёт начальные астероиды"""
        for _ in range(15):
            x = random.randint(-2000, 2000)
            y = random.randint(-2000, 2000)
            # Не спавним рядом с игроком
            if abs(x) < 500 and abs(y) < 500:
                continue
            self.asteroids.append(Asteroid(x, y))
            
    def _force_load_base_from_file(self, chunk_x, chunk_y):
        """Прямая загрузка базы из файла чанка"""
        from entities.base import EnemyBase
        from settings import DEBUG_MODE
        import json
        import os
        
        chunk = self.chunk_manager.get_chunk(chunk_x, chunk_y)
        filename = chunk.get_full_path(self.chunk_manager.world_dir)
        
        if not os.path.exists(filename):
            if DEBUG_MODE:
                print(f"[DEBUG] Файл {filename} не существует")
            return False
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                bases = data.get('objects', {}).get('enemy_bases', [])
                
                if not bases:
                    if DEBUG_MODE:
                        print(f"[DEBUG] В файле {filename} нет баз")
                    return False
                
                if DEBUG_MODE:
                    print(f"[DEBUG] Найдено {len(bases)} баз в файле {filename}")
                
                loaded = 0
                for base_data in bases:
                    # Проверяем, загружена ли уже эта база
                    exists = False
                    for existing in self.enemy_bases:
                        if abs(existing.x - base_data['x']) < 10 and abs(existing.y - base_data['y']) < 10:
                            exists = True
                            break
                    
                    if not exists:
                        base = EnemyBase(
                            base_data['x'],
                            base_data['y'],
                            base_data.get('base_type', 'standard')
                        )
                        base.health = base_data.get('health', 100)
                        base.max_health = base_data.get('max_health', 100)
                        base.current_enemies = base_data.get('current_enemies', base.max_enemies)
                        self.enemy_bases.append(base)
                        loaded += 1
                        if DEBUG_MODE:
                            print(f"[DEBUG] ✅ ПРИНУДИТЕЛЬНО ЗАГРУЖЕНА база {base.base_type} в ({int(base.x)}, {int(base.y)})")
                
                if DEBUG_MODE:
                    print(f"[DEBUG] Загружено {loaded} новых баз из файла")
                return True
                
        except Exception as e:
            if DEBUG_MODE:
                print(f"[DEBUG] Ошибка загрузки файла {filename}: {e}")
            return False

    def _load_chunk_objects(self):
        """Загружает объекты из чанков (обёртка для _force_load_chunk_objects)"""
        self._force_load_chunk_objects()
        
    def _force_load_chunk_objects(self):
        """Принудительно загружает все объекты из загруженных чанков (7x7)"""
        from entities.base import EnemyBase
        from entities.asteroid import Asteroid
        from settings import DEBUG_MODE
        
        if DEBUG_MODE:
            print(f"[GAME] === ПРИНУДИТЕЛЬНАЯ ЗАГРУЗКА ===")
        
        # Перезагружаем чанки из файлов
        for key, chunk in list(self.chunk_manager.chunks.items()):
            if chunk.loaded:
                chunk.load(self.chunk_manager.world_dir)
        
        # НЕ ОЧИЩАЕМ ВСЕ БАЗЫ! Только добавляем новые
        # self.enemy_bases.clear()  <-- УБИРАЕМ
        
        loaded_bases = 0
        skipped_bases = 0
        
        for chunk in self.chunk_manager.chunks.values():
            if not chunk.loaded:
                continue
            
            for base_data in chunk.objects.get('enemy_bases', []):
                # Проверяем, есть ли уже такая база в игре
                exists = False
                for base in self.enemy_bases:
                    if abs(base.x - base_data['x']) < 10 and abs(base.y - base_data['y']) < 10:
                        exists = True
                        # Проверяем, не уничтожена ли она
                        if not base.alive and base.removed_from_file:
                            # Если база уничтожена и удалена из файла - пропускаем
                            skipped_bases += 1
                            if DEBUG_MODE:
                                print(f"[GAME] ⏭️ Пропускаем уничтоженную базу ({int(base.x)}, {int(base.y)})")
                        break
                
                if not exists:
                    # Новая база - загружаем
                    base = EnemyBase(
                        base_data['x'], 
                        base_data['y'], 
                        base_data.get('base_type', 'standard')
                    )
                    base.health = base_data.get('health', 100)
                    base.max_health = base_data.get('max_health', 100)
                    base.current_enemies = base_data.get('current_enemies', base.max_enemies)
                    self.enemy_bases.append(base)
                    loaded_bases += 1
                    if DEBUG_MODE:
                        print(f"[GAME] ✅ НОВАЯ БАЗА {base.base_type} в ({int(base.x)}, {int(base.y)})")
        
        if DEBUG_MODE:
            print(f"[GAME] Итог: +{loaded_bases} новых баз, пропущено {skipped_bases} уничтоженных")
            
    def spawn_enemy(self, x, y, enemy_type=None, difficulty_multiplier=1.0):
        """Создаёт врага указанного типа"""
        if enemy_type is None:
            enemy_type = self.get_random_type()
        
        if enemy_type not in self.enemy_types:
            print(f"[ENEMY_MANAGER] Ошибка: тип '{enemy_type}' не найден")
            return None
        
        enemy = Enemy(x, y, enemy_type, difficulty_multiplier)
        return enemy
        
    def _spawn_enemy_with_base(self, x, y, enemy_type):
        """Создаёт врага для базы с привязкой"""
        enemy = self.enemy_manager.spawn_enemy(
            x, y, enemy_type,
            self.difficulty_multiplier  # <-- ПЕРЕДАЁМ СЛОЖНОСТЬ
        )
        if enemy:
            self.enemies.append(enemy)
        return enemy
        
    def _activate_bomb(self):
        """Активирует бомбу"""
        for enemy in self.enemies[:]:
            enemy.destroy(self.particles)
            self.score += enemy.score_value
            self.enemies.remove(enemy)

        self.particles.spawn_explosion(
            self.ship.x, self.ship.y,
            count=100,
            speed=10,
            colors=[(255, 200, 50), (255, 100, 50), (255, 255, 255)]
        )
        self.powerups.active_effects['bomb'] = 1

    def _apply_difficulty(self):
        """Применяет настройки сложности"""
        if self.difficulty == 'easy':
            self.difficulty_multiplier = 0.5
            self.enemy_spawn_modifier = 0.7
            self.damage_modifier = 0.5
            self.health_modifier = 1.5
            print("[DIFFICULTY] Легкая сложность")
        elif self.difficulty == 'normal':
            self.difficulty_multiplier = 1.0
            self.enemy_spawn_modifier = 1.0
            self.damage_modifier = 1.0
            self.health_modifier = 1.0
            print("[DIFFICULTY] Нормальная сложность")
        elif self.difficulty == 'hard':
            self.difficulty_multiplier = 1.5
            self.enemy_spawn_modifier = 1.5
            self.damage_modifier = 1.5
            self.health_modifier = 0.7
            print("[DIFFICULTY] Сложная сложность")
        else:
            self.difficulty_multiplier = 1.0
            self.enemy_spawn_modifier = 1.0
            self.damage_modifier = 1.0
            self.health_modifier = 1.0
            
    def _restart(self):
        """Перезапуск игры"""
        self.game_over = False
        self.score = 0
        self.ship = Ship(0, 0)
        self.particles = ParticleSystem()
        self.powerups = PowerUpSystem()
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.asteroids = []
        self.enemy_bases = []
        self.camera = Camera(self.ship.x, self.ship.y, WIDTH, HEIGHT)
        
        # Пересоздаём чанки и загружаем объекты
        self.chunk_manager = ChunkManager(config=self.config)
        self._load_chunk_objects()
        
        # Пересоздаём базу игрока
        from utils import spawn_position_with_safety
        bx, by = spawn_position_with_safety(0, 0, 0, 0, min_distance=500)
        self.player_base = PlayerBase(bx, by)
        
    # ============================================================
    #  ОБНОВЛЕНИЕ
    # ============================================================

    def update(self):
        # Если карта открыта - обновляем только чанки (для фона)
        if self.world_map.visible:
            # Обновляем чанки чтобы карта показывала актуальные данные
            self.chunk_manager.update(self.ship.x, self.ship.y)
            return
        
        if self.paused or self.game_over:
            return
            
        # Управление
        self.keys = pygame.key.get_pressed()
        self._handle_controls()

        # Сохраняем старую позицию для параллакса
        old_x, old_y = self.ship.x, self.ship.y

        # Обновление корабля
        self.ship.update()

        # Смещение для параллакса
        offset_x = -(self.ship.x - old_x)
        offset_y = -(self.ship.y - old_y)

        # Обновление звёзд
        self.starfield.update(self.ship.x, self.ship.y, offset_x, offset_y)

        # Обновление камеры
        self.camera.update(self.ship.x, self.ship.y)

        # ===== ОБНОВЛЕНИЕ ЧАНКОВ =====
        old_chunk_x = int(self.ship.x // CHUNK_SIZE)
        old_chunk_y = int(self.ship.y // CHUNK_SIZE)
        
        self.chunk_manager.update(self.ship.x, self.ship.y)
        
        new_chunk_x = int(self.ship.x // CHUNK_SIZE)
        new_chunk_y = int(self.ship.y // CHUNK_SIZE)
        
        # ПРИ ПЕРЕХОДЕ В НОВЫЙ ЧАНК - ЗАГРУЖАЕМ БАЗЫ
        if old_chunk_x != new_chunk_x or old_chunk_y != new_chunk_y:
            print(f"[GAME] Переход в новый чанк ({new_chunk_x}, {new_chunk_y})")
            self._force_load_chunk_objects()
        
        # ===== КАЖДЫЕ 5 СЕКУНД ПРОВЕРЯЕМ ЧТО БАЗЫ ЕСТЬ =====
        if len(self.enemy_bases) < 2 and pygame.time.get_ticks() % 300 == 0:
            print(f"[GAME] Баз мало ({len(self.enemy_bases)}), загрузка...")
            self._force_load_chunk_objects()

        # Обновление баз врагов
        for base in self.enemy_bases[:]:
            base.update(self.enemies, self.ship.x, self.ship.y, self._spawn_enemy_with_base)

        # Обновление базы игрока
        self.player_base.update(self.ship, self.particles)

        # Обновление частиц и бонусов
        self.particles.update()
        self.powerups.update(self.ship.x, self.ship.y)

        # Обновление пуль
        self._update_bullets()

        # Управление врагами
        self._update_enemies()

        # Управление вражескими пулями
        self._update_enemy_bullets()

        # Проверка попаданий по базам
        self._check_base_hits()

        # Сбор бонусов
        self.powerups.check_collection(self.ship, self.particles)

        # Обработка бомбы
        if 'bomb' in self.powerups.active_effects:
            self._activate_bomb()
            del self.powerups.active_effects['bomb']

        # Обновление эффектов на корабле
        self.powerups.update_effects(self.ship)

        # Обновление указателей направления
        self.indicators.update(
            self.ship.x,
            self.ship.y,
            self.enemies,
            self.camera.x,
            self.camera.y,
            self.enemy_bases
        )

        # ===== КОЛЛИЗИИ =====
        self._check_all_collisions()

        # Обновление топлива
        self.fuel_system.update(
            self.ship,
            self.ship.engine_on,
            self.particles
        )
        
    # ============================================================
    #  ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ДЛЯ UPDATE
    # ============================================================

    def _update_bullets(self):
        """Обновление пуль игрока"""
        for bullet in self.bullets[:]:
            bullet.update()
            if bullet.is_dead():
                self.bullets.remove(bullet)

    def _update_enemy_bullets(self):
        """Обновление вражеских пуль"""
        for bullet in self.enemy_bullets[:]:
            bullet.update()
            
            # Если пуля умерла — удаляем и пропускаем
            if bullet.is_dead():
                self.enemy_bullets.remove(bullet)
                continue
            
            # Проверка попадания в игрока
            if not check_collision(bullet, self.ship, -5):
                continue
            
            # Попадание!
            if 'shield' in self.powerups.active_effects:
                self.enemy_bullets.remove(bullet)
                self.particles.spawn_explosion(
                    bullet.x, bullet.y, 10, 3,
                    [(50, 150, 255), (255, 255, 255)]
                )
                continue

            self.ship.health -= 5
            self.enemy_bullets.remove(bullet)
            self.particles.spawn_explosion(
                bullet.x, bullet.y, 10, 3,
                [(255, 200, 100), (255, 255, 255)]
            )

            if self.ship.health <= 0:
                self.game_over = True
                
    def _update_enemies(self):
        """Обновление всех врагов"""
        for enemy in self.enemies[:]:
            enemy.update(self.ship.x, self.ship.y)
            enemy.shoot(self.enemy_bullets, self.ship.x, self.ship.y)

            # Проверка столкновения с кораблём
            if check_collision(self.ship, enemy, -5):
                self.ship.health -= 10
                enemy.destroy(self.particles)
                self.enemies.remove(enemy)
                if self.ship.health <= 0:
                    self.game_over = True
                continue

            # Камикадзе взрыв
            if enemy.behavior == 'kamikaze' and enemy.is_exploding:
                dist = distance_between(self.ship.x, self.ship.y, enemy.x, enemy.y)
                if dist < enemy.explosion_radius:
                    self.ship.health -= 30
                    enemy.destroy(self.particles)
                    self.enemies.remove(enemy)
                    if self.ship.health <= 0:
                        self.game_over = True
                continue

            # Попадания пуль во врага
            for bullet in self.bullets[:]:
                if check_collision(bullet, enemy):
                    if enemy.take_damage():
                        enemy.destroy(self.particles)
                        self.powerups.spawn_from_enemy(enemy.x, enemy.y, 0.3)
                        self.score += enemy.score_value
                        self.enemies.remove(enemy)
                    self.bullets.remove(bullet)
                    break

        # Удаление "застрявших" врагов
        self._cleanup_far_enemies()

    def _cleanup_far_enemies(self):
        """Удаляет или телепортирует врагов, улетевших слишком далеко"""
        for enemy in self.enemies[:]:
            dx = enemy.x - self.ship.x
            dy = enemy.y - self.ship.y
            dist = math.sqrt(dx**2 + dy**2)

            if dist > 8000:
                print(f"[ENEMY] Удалён далёкий враг {enemy.enemy_type} на расстоянии {int(dist)}")
                self.enemies.remove(enemy)
                self.score += enemy.score_value // 2
                continue

            speed = math.sqrt(enemy.speed_x**2 + enemy.speed_y**2)
            if dist > 3000 and speed < 0.1:
                from utils import spawn_position_with_safety
                x, y = spawn_position_with_safety(
                    self.ship.x,
                    self.ship.y,
                    self.ship.speed_x,
                    self.ship.speed_y,
                    min_distance=400
                )
                enemy.x = x
                enemy.y = y
                print(f"[ENEMY] Телепорт застрявшего врага {enemy.enemy_type}")
    
    def _check_base_hits(self):
        """Проверка попаданий по базам"""
        for bullet in self.bullets[:]:
            for base in self.enemy_bases[:]:
                if not base.alive:
                    continue

                dx = bullet.x - base.x
                dy = bullet.y - base.y
                dist = math.sqrt(dx**2 + dy**2)

                if dist < base.radius + bullet.radius:
                    base.take_damage(
                        self.enemies, 
                        1, 
                        self.chunk_manager,
                        self._save_modified_chunks
                    )
                    self.bullets.remove(bullet)

                    self.particles.spawn_explosion(
                        bullet.x, bullet.y,
                        count=5,
                        speed=2,
                        colors=[(255, 200, 100), (255, 255, 255)]
                    )

                    if not base.alive:
                        self.score += 50
                        self.particles.spawn_explosion(
                            base.x, base.y,
                            count=60,
                            speed=8,
                            colors=[(255, 50, 50), (255, 200, 50), (255, 255, 255)]
                        )
                        
                        # ДОПОЛНИТЕЛЬНО СОХРАНЯЕМ ЧАНК ИГРОКА
                        self._save_player_chunk()
                        
                        print(f"[BASE] База уничтожена! +50 очков")

                    break
                    
    def _check_asteroid_collision(self, asteroid, obj, margin=0):
        """Проверка столкновения с астероидом"""
        dx = asteroid.x - obj.x
        dy = asteroid.y - obj.y
        dist = math.sqrt(dx**2 + dy**2)
        return dist < (asteroid.radius + obj.radius + margin)

    def _check_all_collisions(self):
        from utils import circle_collision, circle_polygon_collision, resolve_collision
        
        # ===== 1. ПУЛИ ИГРОКА VS ВРАГИ =====
        for bullet in self.bullets[:]:
            for enemy in self.enemies[:]:
                if enemy.health <= 0:
                    continue
                
                if circle_collision(bullet, enemy):
                    enemy.health -= 1
                    self.bullets.remove(bullet)
                    
                    self.particles.spawn_explosion(
                        bullet.x, bullet.y, 5, 2,
                        [(255, 255, 100), (255, 200, 50)]
                    )
                    
                    if enemy.health <= 0:
                        enemy.destroy(self.particles)
                        self.powerups.spawn_from_enemy(enemy.x, enemy.y, 0.3)
                        self.score += enemy.score_value
                        self.enemies.remove(enemy)
                    break
        
        # ===== 2. ПУЛИ ИГРОКА VS БАЗЫ =====
        for bullet in self.bullets[:]:
            for base in self.enemy_bases[:]:
                if not base.alive:
                    continue
                
                if circle_collision(bullet, base):
                    base.take_damage(
                        self.enemies, 
                        1, 
                        self.chunk_manager,
                        self._save_modified_chunks  # <-- ИСПРАВЛЕНО
                    )
                    base.hit_flash = 10
                    self.bullets.remove(bullet)
                    
                    self.particles.spawn_explosion(
                        bullet.x, bullet.y, 5, 2,
                        [(255, 200, 100), (255, 255, 255)]
                    )
                    
                    if not base.alive:
                        self.score += 50
                        self.particles.spawn_explosion(
                            base.x, base.y, 60, 8,
                            [(255, 50, 50), (255, 200, 50), (255, 255, 255)]
                        )
                        self._save_modified_chunks()  # <-- ДОБАВЛЕНО
                    break
        
        # ===== 3. ПУЛИ ИГРОКА VS АСТЕРОИДЫ =====
        for bullet in self.bullets[:]:
            for asteroid in self.asteroids[:]:
                if circle_polygon_collision(bullet, asteroid.get_vertices()):
                    asteroid.health -= 1
                    self.bullets.remove(bullet)
                    
                    self.particles.spawn_explosion(
                        bullet.x, bullet.y, 3, 1,
                        [(150, 130, 100), (200, 180, 150)]
                    )
                    
                    if asteroid.health <= 0:
                        resources = asteroid.destroy(self.particles)
                        self.player_base.resources['scrap'] += resources
                        self.asteroids.remove(asteroid)
                        self.score += 5
                    break
        
        # ===== 4. КОРАБЛЬ VS ВРАГИ =====
        ship_vertices = self.ship.get_vertices()
        for enemy in self.enemies[:]:
            if enemy.health <= 0:
                continue
            
            if circle_polygon_collision(enemy, ship_vertices, -5):
                if 'shield' in self.powerups.active_effects:
                    enemy.health -= int(3 * self.damage_modifier)
                    if enemy.health <= 0:
                        enemy.destroy(self.particles)
                        self.score += enemy.score_value
                        self.enemies.remove(enemy)
                    continue
                
                damage = int(10 * self.damage_modifier)
                self.ship.health -= damage
                enemy.health = 0
                enemy.destroy(self.particles)
                self.enemies.remove(enemy)
                
                if self.ship.health <= 0:
                    self.game_over = True
        
        # ===== 5. КОРАБЛЬ VS АСТЕРОИДЫ =====
        for asteroid in self.asteroids[:]:
            if circle_polygon_collision(asteroid, ship_vertices, -5):
                self.ship.health -= 5
                asteroid.health = 0
                resources = asteroid.destroy(self.particles)
                self.player_base.resources['scrap'] += resources
                self.asteroids.remove(asteroid)
                
                if self.ship.health <= 0:
                    self.game_over = True
        
        # ===== 6. КОРАБЛЬ VS БАЗЫ =====
        for base in self.enemy_bases[:]:
            if not base.alive:
                continue
            
            if circle_collision(self.ship, base, -10):
                if 'shield' in self.powerups.active_effects:
                    self.particles.spawn_explosion(
                        base.x, base.y, 20, 5,
                        [(50, 150, 255), (255, 255, 255)]
                    )
                    base.take_damage(
                        self.enemies, 
                        5, 
                        self.chunk_manager,
                        self._save_modified_chunks  # <-- ИСПРАВЛЕНО
                    )
                    continue
                
                self.ship.health -= 20
                base.take_damage(
                    self.enemies, 
                    10, 
                    self.chunk_manager,
                    self._save_modified_chunks  # <-- ИСПРАВЛЕНО
                )
                
                self.particles.spawn_explosion(
                    self.ship.x, self.ship.y, 30, 5,
                    [(255, 200, 100), (255, 255, 255)]
                )
                
                if not base.alive:
                    self._save_modified_chunks()  # <-- ДОБАВЛЕНО
                
                if self.ship.health <= 0:
                    self.game_over = True
        
        # ===== 7. ВРАЖЕСКИЕ ПУЛИ VS КОРАБЛЬ =====
        for bullet in self.enemy_bullets[:]:
            if bullet.is_dead():
                continue
            
            if circle_polygon_collision(bullet, ship_vertices, -5):
                if 'shield' in self.powerups.active_effects:
                    self.particles.spawn_explosion(
                        bullet.x, bullet.y, 10, 3,
                        [(50, 150, 255), (255, 255, 255)]
                    )
                    self.enemy_bullets.remove(bullet)
                    continue
                
                damage = int(5 * self.damage_modifier)
                self.ship.health -= damage
                self.enemy_bullets.remove(bullet)
                self.particles.spawn_explosion(
                    bullet.x, bullet.y, 10, 3,
                    [(255, 200, 100), (255, 255, 255)]
                )
                
                if self.ship.health <= 0:
                    self.game_over = True
        
        # ===== 8. ВРАГИ VS ВРАГИ (отталкивание) =====
        for i, enemy1 in enumerate(self.enemies):
            for enemy2 in self.enemies[i+1:]:
                if enemy1.health <= 0 or enemy2.health <= 0:
                    continue
                
                if circle_collision(enemy1, enemy2, -5):
                    resolve_collision(enemy1, enemy2, 2)
        
        # ===== 9. ВРАЖЕСКИЕ ПУЛИ VS ПУЛИ ИГРОКА =====
        for bullet in self.bullets[:]:
            for enemy_bullet in self.enemy_bullets[:]:
                if circle_collision(bullet, enemy_bullet):
                    self.bullets.remove(bullet)
                    self.enemy_bullets.remove(enemy_bullet)
                    self.particles.spawn_explosion(
                        bullet.x, bullet.y, 5, 2,
                        [(255, 255, 255), (200, 200, 200)]
                    )
                    break
    
    def _debug_check_chunk_file(self, chunk_x, chunk_y):
        """Прямая проверка файла чанка на наличие баз"""
        from settings import DEBUG_MODE
        if not DEBUG_MODE:
            return
        
        import json
        import os
        
        chunk = self.chunk_manager.get_chunk(chunk_x, chunk_y)
        filename = chunk.get_full_path(self.chunk_manager.world_dir)
        
        if os.path.exists(filename):
            print(f"[DEBUG] Файл чанка {chunk.get_chunk_id()} существует: {filename}")
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                bases = data.get('objects', {}).get('enemy_bases', [])
                print(f"[DEBUG] В файле найдено баз: {len(bases)}")
                for base in bases:
                    print(f"  - База на ({int(base['x'])}, {int(base['y'])}) типа {base.get('base_type')}")
                
                # Проверяем, загружена ли эта база в игру
                loaded = False
                for game_base in self.enemy_bases:
                    if abs(game_base.x - base['x']) < 10 and abs(game_base.y - base['y']) < 10:
                        loaded = True
                        break
                
                if not loaded and bases:
                    print(f"[DEBUG] ⚠️ База из файла НЕ ЗАГРУЖЕНА в игру!")
                    # Принудительно загружаем
                    from entities.base import EnemyBase
                    for base_data in bases:
                        base = EnemyBase(
                            base_data['x'],
                            base_data['y'],
                            base_data.get('base_type', 'standard')
                        )
                        base.health = base_data.get('health', 100)
                        base.max_health = base_data.get('max_health', 100)
                        base.current_enemies = base_data.get('current_enemies', base.max_enemies)
                        self.enemy_bases.append(base)
                        print(f"[DEBUG] ✅ ПРИНУДИТЕЛЬНО ЗАГРУЖЕНА база {base.base_type} в ({int(base.x)}, {int(base.y)})")
        else:
            print(f"[DEBUG] Файл чанка {chunk.get_chunk_id()} НЕ СУЩЕСТВУЕТ")

    def _save_modified_chunks(self):
        """Сохраняет только изменённые чанки"""
        from settings import DEBUG_MODE
        
        if DEBUG_MODE:
            print(f"[SAVE] Сохранение изменённых чанков...")
        
        saved = self.chunk_manager.save_modified_chunks()
        
        if DEBUG_MODE:
            print(f"[SAVE] Сохранено {saved} чанков")
        return saved

    def _save_player_chunk(self):
        """Сохраняет чанк в котором находится игрок"""
        from settings import DEBUG_MODE
        
        chunk_x = int(self.ship.x // CHUNK_SIZE)
        chunk_y = int(self.ship.y // CHUNK_SIZE)
        
        if DEBUG_MODE:
            print(f"[SAVE] Сохранение чанка игрока ({chunk_x}, {chunk_y})...")
        
        self.chunk_manager.save_chunk_immediately(chunk_x, chunk_y)
        
    # ============================================================
    #  ОТРИСОВКА
    # ============================================================

    def draw(self):
        """Отрисовка всего"""
        self.screen.fill(BLACK)

        camera_x = self.camera.x
        camera_y = self.camera.y

        # Звёзды
        self.starfield.draw(self.screen, camera_x, camera_y)

        # ===== ОТЛАДОЧНАЯ СЕТКА ЧАНКОВ =====
        self.chunk_manager.draw_debug_grid(self.screen, camera_x, camera_y, self.ship.x, self.ship.y)
        
        # Астероиды
        for asteroid in self.asteroids:
            asteroid.draw(self.screen, camera_x, camera_y)

        # Частицы
        self.particles.draw(self.screen, camera_x, camera_y)

        # Бонусы
        self.powerups.draw(self.screen, camera_x, camera_y)

        # Корабль
        self.ship.draw(self.screen, camera_x, camera_y, self.particles)

        # Пули
        for bullet in self.bullets:
            bullet.draw(self.screen, camera_x, camera_y)
        for bullet in self.enemy_bullets:
            bullet.draw(self.screen, camera_x, camera_y)

        # Базы
        for base in self.enemy_bases:
            base.draw(self.screen, camera_x, camera_y)

        # База игрока
        self.player_base.draw(self.screen, camera_x, camera_y)

        # Враги
        for enemy in self.enemies:
            enemy.draw(
                self.screen,
                camera_x,
                camera_y,
                self.ship.x,
                self.ship.y
            )

        # Мини-карта
        self.minimap.draw(
            self.screen,
            self.ship.x,
            self.ship.y,
            self.enemies,
            self.powerups.powerups,
            self.player_base.x,  # <-- БАЗА ИГРОКА
            self.player_base.y,
            self.camera,
            self.enemy_bases
        )

        # Маркеры на игровом поле
        self.waypoint_manager.draw_in_game(
            self.screen,
            self.ship.x,
            self.ship.y,
            camera_x,
            camera_y
        )
        
        # Указатели направления
        self.indicators.draw(self.screen)

        # HP базы под прицелом
        self._draw_base_hp()

        # HUD
        self._draw_hud()

        # Game Over
        if self.game_over:
            self._draw_game_over()

        # ===== БОЛЬШАЯ КАРТА (поверх всего) =====
        self.world_map.draw(
            self.screen,
            self.ship.x,
            self.ship.y,
            self.enemies,
            self.enemy_bases,
            self.asteroids,
            self.chunk_manager
        )
        
        pygame.display.flip()
        self.clock.tick(FPS)

    def _draw_base_hp(self):
        """Отображает HP базы под прицелом"""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        camera_x, camera_y = self.camera.x, self.camera.y
        world_mouse_x = mouse_x + camera_x
        world_mouse_y = mouse_y + camera_y

        font = pygame.font.Font(None, 20)
        
        for base in self.enemy_bases:
            if not base.alive:
                continue

            dx = world_mouse_x - base.x
            dy = world_mouse_y - base.y
            dist = math.sqrt(dx**2 + dy**2)

            if dist < base.radius + 30:
                # Фон для текста
                hp_text = font.render(f"BASE HP: {int(base.health)}/{int(base.max_health)}", True, (255, 255, 255))
                hp_rect = hp_text.get_rect(center=(mouse_x, mouse_y - 50))
                
                # Тень
                shadow_rect = hp_rect.copy()
                shadow_rect.x += 1
                shadow_rect.y += 1
                shadow = font.render(f"BASE HP: {int(base.health)}/{int(base.max_health)}", True, (0, 0, 0))
                self.screen.blit(shadow, shadow_rect)
                
                # Основной текст
                self.screen.blit(hp_text, hp_rect)
                break
                
    def _draw_hud(self):
        """Рисует интерфейс"""
        
        hud_font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 18)
        
        # ===== ЛЕВЫЙ ВЕРХНИЙ УГОЛ =====
        score_text = hud_font.render(f"SCORE: {self.score}", True, (255, 255, 100))
        self.screen.blit(score_text, (15, 15))
        
        hp_color = (50, 255, 50) if self.ship.health > 30 else (255, 50, 50)
        hp_text = hud_font.render(f"HP: {self.ship.health}", True, hp_color)
        self.screen.blit(hp_text, (15, 40))
        
        # Топливо (под HP)
        self.fuel_system.draw_hud(self.screen)
        
        # ===== ПРАВЫЙ ВЕРХНИЙ УГОЛ (с отступом от мини-карты) =====
        minimap_width = 150
        right_x = WIDTH - minimap_width - 30
        
        enemy_text = hud_font.render(f"ENEMIES: {len(self.enemies)}", True, (255, 100, 100))
        enemy_rect = enemy_text.get_rect(topright=(right_x, 15))
        self.screen.blit(enemy_text, enemy_rect)
        
        bases_alive = sum(1 for b in self.enemy_bases if b.alive)
        bases_text = hud_font.render(f"BASES: {bases_alive}", True, (255, 200, 100))
        bases_rect = bases_text.get_rect(topright=(right_x, 40))
        self.screen.blit(bases_text, bases_rect)
        
        if self.config.get('game.show_fps', False):
            fps_text = small_font.render(f"FPS: {int(self.clock.get_fps())}", True, (100, 100, 100))
            fps_rect = fps_text.get_rect(topright=(right_x, 65))
            self.screen.blit(fps_text, fps_rect)
        
        if self.config.get('game.debug_mode', False):
            debug_text = small_font.render("DEBUG", True, (255, 200, 50))
            debug_rect = debug_text.get_rect(topright=(right_x, 90))
            self.screen.blit(debug_text, debug_rect)
        
        # ===== ЛЕВЫЙ НИЖНИЙ УГОЛ =====
        speed_val = math.sqrt(self.ship.speed_x**2 + self.ship.speed_y**2)
        speed_text = small_font.render(f"SPEED: {speed_val:.1f}", True, (150, 150, 150))
        self.screen.blit(speed_text, (15, HEIGHT - 30))
        
        # ===== ПРАВЫЙ НИЖНИЙ УГОЛ =====
        controls_text = small_font.render("ESC: Menu | P: Pause", True, (100, 100, 100))
        controls_rect = controls_text.get_rect(bottomright=(WIDTH - 15, HEIGHT - 15))
        self.screen.blit(controls_text, controls_rect)
        
        # ===== ЦЕНТР ВВЕРХУ =====
        if self.paused:
            pause_text = hud_font.render("PAUSED", True, (255, 255, 255))
            pause_rect = pause_text.get_rect(center=(WIDTH // 2, 30))
            self.screen.blit(pause_text, pause_rect)
        
        # ===== АКТИВНЫЕ ЭФФЕКТЫ (под топливом) =====
        effects_colors = {
            'shield': (50, 150, 255),
            'triple_shot': (255, 200, 50),
            'speed_boost': (50, 255, 150),
            'bomb': (255, 100, 200),
            'magnet': (200, 100, 255),
        }
        
        y_offset = 115  # Под HP (40) и топливом
        for effect, timer in self.powerups.active_effects.items():
            if timer > 0:
                seconds = timer // 60
                color = effects_colors.get(effect, (255, 255, 255))
                effect_text = small_font.render(f"{effect.upper()}: {seconds}s", True, color)
                self.screen.blit(effect_text, (15, y_offset))
                y_offset += 20
        
        # ===== DEBUG MODE (читы внизу) =====
        if self.config.get('game.debug_mode', False):
            cheats_text = small_font.render(
                "F1:Bomb  F2:Heal  F3:+50  F4:Kill  F5:Spawn  F6:Reload",
                True, (80, 80, 80)
            )
            cheats_rect = cheats_text.get_rect(center=(WIDTH // 2, HEIGHT - 15))
            self.screen.blit(cheats_text, cheats_rect)
            
            pos_text = small_font.render(f"POS: ({int(self.ship.x)}, {int(self.ship.y)})", True, (80, 80, 80))
            pos_rect = pos_text.get_rect(bottomleft=(15, HEIGHT - 55))
            self.screen.blit(pos_text, pos_rect)
            
        # Подсказка по карте
        map_hint = small_font.render("TAB: World Map | RMB: Set Waypoint", True, (80, 80, 100))
        map_rect = map_hint.get_rect(center=(WIDTH // 2, HEIGHT - 40))
        self.screen.blit(map_hint, map_rect)   
        
    def _draw_game_over(self):
        """Экран Game Over — чистый и понятный"""
        # Затемнение
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Шрифты
        title_font = pygame.font.Font(None, 72)
        big_font = pygame.font.Font(None, 48)
        medium_font = pygame.font.Font(None, 32)
        
        # Заголовок
        title = title_font.render("GAME OVER", True, (255, 50, 50))
        title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//2 - 80))
        self.screen.blit(title, title_rect)
        
        # Счёт
        score_text = big_font.render(f"SCORE: {self.score}", True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 10))
        self.screen.blit(score_text, score_rect)
        
        # Подсказки
        restart_text = medium_font.render("Press SPACE to restart", True, (255, 255, 100))
        restart_rect = restart_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 50))
        self.screen.blit(restart_text, restart_rect)
        
        menu_text = medium_font.render("Press ESC for menu", True, (150, 150, 150))
        menu_rect = menu_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 95))
        self.screen.blit(menu_text, menu_rect)
        
    # ============================================================
    #  ЗАПУСК
    # ============================================================

    def run(self):
        """Запускает игровой цикл"""
        while self.running:
            result = self.handle_events()
            if result == "menu":
                return "menu"
            elif result == "quit":
                return "quit"

            self.update()
            self.draw()

        return "quit"
        

