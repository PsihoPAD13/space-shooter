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

        # ===== МЕНЕДЖЕР ВРАГОВ =====
        self.enemy_manager = EnemyManager()

        # ===== СПИСКИ ОБЪЕКТОВ =====
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.asteroids = []      # <-- ДОБАВИТЬ
        self.enemy_bases = []

        # ===== ЗАГРУЗКА ОБЪЕКТОВ ИЗ ЧАНКОВ =====
        self._load_chunk_objects()

        # ===== НАЧАЛЬНЫЕ ОБЪЕКТЫ (если чанки пустые) =====
        if len(self.enemy_bases) < 3:
            self._init_bases()
        
        if len(self.asteroids) < 10:
            self._init_asteroids()
            
        # ===== ИГРОВЫЕ ПЕРЕМЕННЫЕ =====
        self.score = 0
        self.keys = pygame.key.get_pressed()
        self.mouse_pressed = False

        # ===== БАЗА ИГРОКА =====
        from utils import spawn_position_with_safety
        bx, by = spawn_position_with_safety(
            0, 0, 0, 0,
            min_distance=800,           # Дальше от центра
            existing_bases=None,        # Пока нет других баз
            base_separation=600
        )
        self.player_base = PlayerBase(bx, by)
        print(f"[BASE] База игрока создана в ({int(bx)}, {int(by)})")
        
        # ===== ТОПЛИВО =====
        self.fuel_system = FuelSystem(max_fuel=100)

        # ===== АСТЕРОИДЫ =====
        self._init_asteroids()

        # ===== ИНИЦИАЛИЗАЦИЯ БАЗ ВРАГОВ =====
        self._init_bases()
        
        # ============================================================
        #  ОБРАБОТКА СОБЫТИЙ
        # ============================================================

    def handle_events(self):
        """Обработка событий"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return "quit"

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
            
    def _load_chunk_objects(self):
        """Загружает объекты из чанков вокруг игрока"""
        from entities.base import EnemyBase
        from entities.asteroid import Asteroid
        
        # Загружаем чанки вокруг игрока
        self.chunk_manager.update(self.ship.x, self.ship.y)
        
        # Получаем объекты в радиусе
        radius = CHUNK_SIZE * 2
        objects = self.chunk_manager.get_objects_in_radius(self.ship.x, self.ship.y, radius)
        
        # Загружаем базы
        for base_data in objects['enemy_bases']:
            base = EnemyBase(
                base_data['x'], 
                base_data['y'], 
                base_data.get('base_type', 'standard')
            )
            base.health = base_data.get('health', 100)
            base.max_health = base_data.get('max_health', 100)
            base.current_enemies = base_data.get('current_enemies', base.max_enemies)
            self.enemy_bases.append(base)
            print(f"[GAME] Загружена база из чанка в ({int(base_data['x'])}, {int(base_data['y'])})")
        
        # Загружаем астероиды
        for ast_data in objects['asteroids']:
            asteroid = Asteroid(
                ast_data['x'], 
                ast_data['y'],
                ast_data.get('radius'),
                ast_data.get('health')
            )
            self.asteroids.append(asteroid)
        
        print(f"[GAME] Загружено: {len(self.enemy_bases)} баз, {len(self.asteroids)} астероидов")
        
    def _spawn_enemy(self):
        """Создаёт врага с учётом направления движения игрока и других врагов"""
        from utils import spawn_position_with_safety

        enemy_type = self.enemy_manager.get_random_type(self.enemies)
        min_dist = 600 if enemy_type == 'sniper' else 350

        x, y = spawn_position_with_safety(
            self.ship.x,
            self.ship.y,
            self.ship.speed_x,
            self.ship.speed_y,
            min_distance=min_dist,
            forbidden_angle=60,  # 60 градусов впереди
            enemies=self.enemies,  # Проверка на других врагов
            enemy_separation=150
        )

        enemy = self.enemy_manager.spawn_enemy(x, y, enemy_type)
        if enemy:
            self.enemies.append(enemy)

    def _spawn_enemy_with_base(self, x, y, enemy_type):
        """Создаёт врага для базы с привязкой"""
        enemy = self.enemy_manager.spawn_enemy(x, y, enemy_type)
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
        self.asteroids = []      # <-- ДОБАВИТЬ
        self.enemy_bases = []
        self.camera = Camera(self.ship.x, self.ship.y, WIDTH, HEIGHT)
        self._init_bases()
        self._init_asteroids()   # <-- ДОБАВИТЬ
        
        # Пересоздаём базу игрока
        from utils import spawn_position_with_safety
        bx, by = spawn_position_with_safety(0, 0, 0, 0, min_distance=500)
        self.player_base = PlayerBase(bx, by)
    
    # ============================================================
    #  ОБНОВЛЕНИЕ
    # ============================================================

    def update(self):
        """Обновление всей игровой логики"""
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

        # Обновление чанков
        old_chunk_x = int(self.ship.x // CHUNK_SIZE)
        old_chunk_y = int(self.ship.y // CHUNK_SIZE)
        self.chunk_manager.update(self.ship.x, self.ship.y)
        new_chunk_x = int(self.ship.x // CHUNK_SIZE)
        new_chunk_y = int(self.ship.y // CHUNK_SIZE)
        
        # Если перешли в новый чанк — загружаем объекты
        if old_chunk_x != new_chunk_x or old_chunk_y != new_chunk_y:
            self._load_chunk_objects()
            
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

        # ===== ОБНОВЛЕНИЕ АСТЕРОИДОВ =====
        for asteroid in self.asteroids[:]:
            asteroid.update()
            
            # Проверка столкновения с пулями
            for bullet in self.bullets[:]:
                if self._check_asteroid_collision(asteroid, bullet):
                    if asteroid.take_damage():
                        resources = asteroid.destroy(self.particles)
                        self.player_base.resources['scrap'] += resources
                        self.asteroids.remove(asteroid)
                        self.score += 5
                    self.bullets.remove(bullet)
                    break
            
            # Проверка столкновения с кораблём
            if self._check_asteroid_collision(asteroid, self.ship, margin=-5):
                self.ship.health -= 5
                resources = asteroid.destroy(self.particles)
                self.player_base.resources['scrap'] += resources
                self.asteroids.remove(asteroid)
                if self.ship.health <= 0:
                    self.game_over = True

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
                    base.take_damage(self.enemies, 1)
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
                        print(f"[BASE] База уничтожена! +50 очков")

                    break

    def _check_asteroid_collision(self, asteroid, obj, margin=0):
        """Проверка столкновения с астероидом"""
        dx = asteroid.x - obj.x
        dy = asteroid.y - obj.y
        dist = math.sqrt(dx**2 + dy**2)
        return dist < (asteroid.radius + obj.radius + margin)

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
            None,
            self.camera,
            self.enemy_bases
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
                "F1:Bomb  F2:Heal  F3:+50  F4:Kill  F5:Spawn",
                True, (80, 80, 80)
            )
            cheats_rect = cheats_text.get_rect(center=(WIDTH // 2, HEIGHT - 15))
            self.screen.blit(cheats_text, cheats_rect)
            
            pos_text = small_font.render(f"POS: ({int(self.ship.x)}, {int(self.ship.y)})", True, (80, 80, 80))
            pos_rect = pos_text.get_rect(bottomleft=(15, HEIGHT - 55))
            self.screen.blit(pos_text, pos_rect)
            
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