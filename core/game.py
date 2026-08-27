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
from systems.direction_indicators import DirectionIndicators  # <-- ДОБАВЛЯЕМ
from entities.enemy_manager import EnemyManager  # <-- ДОБАВЛЯЕМ
from entities.base import EnemyBase  # <-- ДОБАВЛЯЕМ

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

        # ===== ЗВЁЗДЫ (ФОН, НЕ В ЧАНКАХ) =====
        self.starfield = BackgroundStars()  # <-- 500 звёзд
        
        # ===== МИР И ЧАНКИ =====
        self.chunk_manager = ChunkManager()

        # ===== КОРАБЛЬ (СТАРТУЕТ В ЦЕНТРЕ МИРА) =====
        self.ship = Ship(0, 0)
        self.camera = Camera(self.ship.x, self.ship.y, WIDTH, HEIGHT)

        # ===== ИГРОВЫЕ СИСТЕМЫ =====
        self.particles = ParticleSystem()
        self.powerups = PowerUpSystem()
        self.minimap = Minimap(self.screen, config)
        self.indicators = DirectionIndicators()  # <-- ДОБАВЛЯЕМ

        # ===== СПИСКИ ОБЪЕКТОВ =====
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.asteroids = []  # Будут добавлены позже

        # ===== ИГРОВЫЕ ПЕРЕМЕННЫЕ =====
        self.score = 0
        self.keys = pygame.key.get_pressed()
        self.mouse_pressed = False
        
        # ===== МЕНЕДЖЕР ВРАГОВ =====
        self.enemy_manager = EnemyManager()

        # ===== БАЗЫ ВРАГОВ =====
        self.enemy_bases = []
        self._init_bases()

    def handle_events(self):
        """Обработка событий"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return "quit"

            if event.type == pygame.KEYDOWN:
                # ===== ЧИТ-КОДЫ (только в режиме отладки) =====
                if self.config.get('game.debug_mode', False):
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
                
                # ===== СТАНДАРТНЫЕ КЛАВИШИ =====
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

    def _activate_bomb(self):
        """Активирует бомбу"""
        # Уничтожаем всех врагов
        for enemy in self.enemies[:]:
            enemy.destroy(self.particles)
            self.score += enemy.score_value
            self.enemies.remove(enemy)
        
        # Визуальный эффект
        self.particles.spawn_explosion(
            self.ship.x, self.ship.y,
            count=100,
            speed=10,
            colors=[(255, 200, 50), (255, 100, 50), (255, 255, 255)]
        )
        
        # Добавляем бонус "бомба" в активные эффекты
        self.powerups.active_effects['bomb'] = 1

    def _restart(self):
        """Перезапуск игры"""
        self.game_over = False
        self.score = 0
        self.ship = Ship(0, 0)
        self.particles = ParticleSystem()
        self.powerups = PowerUpSystem()
        self.waves = WaveSystem()
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.camera = Camera(self.ship.x, self.ship.y, WIDTH, HEIGHT)

    def _init_bases(self):
        """Создаёт начальные базы врагов"""
        from utils import spawn_position_with_safety
        
        # Создаём 3-5 баз в разных местах
        for _ in range(random.randint(3, 5)):
            x, y = spawn_position_with_safety(
                self.ship.x, 
                self.ship.y,
                self.ship.speed_x,
                self.ship.speed_y,
                min_distance=800,
                max_attempts=50
            )
            base_type = random.choice(['standard', 'strong', 'fast', 'swarm'])
            base = EnemyBase(x, y, base_type)
            self.enemy_bases.append(base)
            print(f"[BASE] Создана база типа {base_type} в ({int(x)}, {int(y)})")

    def _spawn_enemy(self):
        """Создаёт врага с учётом направления движения игрока"""
        from utils import spawn_position_with_safety
        
        enemy_type = self.enemy_manager.get_random_type(self.enemies)
        
        min_dist = 600 if enemy_type == 'sniper' else 300
        
        # Передаём скорость игрока для определения направления
        x, y = spawn_position_with_safety(
            self.ship.x, 
            self.ship.y,
            self.ship.speed_x,  # <-- Скорость игрока по X
            self.ship.speed_y,  # <-- Скорость игрока по Y
            min_distance=min_dist
        )
        
        enemy = self.enemy_manager.spawn_enemy(x, y, enemy_type)
        if enemy:
            self.enemies.append(enemy)
        
    def update(self):
        """Обновление всей игровой логики"""
        if self.paused or self.game_over:
            return

        # ===== УПРАВЛЕНИЕ =====
        self.keys = pygame.key.get_pressed()
        self._handle_controls()

        # ===== СОХРАНЯЕМ СТАРУЮ ПОЗИЦИЮ ДЛЯ ПАРАЛЛАКСА =====
        old_x, old_y = self.ship.x, self.ship.y

        # ===== ОБНОВЛЕНИЕ КОРАБЛЯ =====
        self.ship.update()

        # ===== ВЫЧИСЛЯЕМ СМЕЩЕНИЕ ДЛЯ ПАРАЛЛАКСА =====
        offset_x = -(self.ship.x - old_x)
        offset_y = -(self.ship.y - old_y)

        # ===== ОБНОВЛЕНИЕ ЗВЁЗД (с параллаксом) =====
        self.starfield.update(self.ship.x, self.ship.y, offset_x, offset_y)

        # ===== ОБНОВЛЕНИЕ КАМЕРЫ =====
        self.camera.update(self.ship.x, self.ship.y)

        # ===== ОБНОВЛЕНИЕ ЧАНКОВ =====
        self.chunk_manager.update(self.ship.x, self.ship.y)

        # ===== ОБНОВЛЕНИЕ БАЗ (ВМЕСТО ВОЛН) =====
        for base in self.enemy_bases[:]:
            base.update(self.enemies, self.ship.x, self.ship.y, self._spawn_enemy_with_base)

        # ===== ОБНОВЛЕНИЕ ЧАСТИЦ =====
        self.particles.update()

        # ===== ОБНОВЛЕНИЕ БОНУСОВ =====
        self.powerups.update(self.ship.x, self.ship.y)

        # ===== ОБНОВЛЕНИЕ ПУЛЬ =====
        for bullet in self.bullets[:]:
            bullet.update()
            if bullet.is_dead():
                self.bullets.remove(bullet)

        for bullet in self.enemy_bullets[:]:
            bullet.update()
            if bullet.is_dead():
                self.enemy_bullets.remove(bullet)
                
        # ===== ОБНОВЛЕНИЕ БАЗ =====
        for base in self.enemy_bases[:]:
            base.update(self.enemies, self.ship.x, self.ship.y, self._spawn_enemy_with_base)

        # ===== УДАЛЕНИЕ "ЗАСТРЯВШИХ" ВРАГОВ =====
        # Если враг слишком далеко и не двигается — удаляем его
        for enemy in self.enemies[:]:
            dx = enemy.x - self.ship.x
            dy = enemy.y - self.ship.y
            dist = math.sqrt(dx**2 + dy**2)
            
            # Если враг дальше 8000 пикселей — удаляем
            if dist > 8000:
                print(f"[ENEMY] Удалён далёкий враг {enemy.enemy_type} на расстоянии {int(dist)}")
                self.enemies.remove(enemy)
                # Даём компенсацию (чтобы волна не застряла)
                self.score += enemy.score_value // 2
                continue
            
            # Если враг почти не двигается и далеко — телепортируем
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

        # ===== ОБНОВЛЕНИЕ ВРАГОВ =====
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

        # ===== ОБНОВЛЕНИЕ УКАЗАТЕЛЕЙ =====
        self.indicators.update(
            self.ship.x, 
            self.ship.y, 
            self.enemies, 
            self.camera.x, 
            self.camera.y
        )

        # ===== ВРАЖЕСКИЕ ПУЛИ ПО ИГРОКУ =====
        for bullet in self.enemy_bullets[:]:
            if check_collision(bullet, self.ship, -5):
                if 'shield' in self.powerups.active_effects:
                    self.enemy_bullets.remove(bullet)
                    self.particles.spawn_explosion(bullet.x, bullet.y, 10, 3,
                        [(50, 150, 255), (255, 255, 255)])
                    continue

                self.ship.health -= 5
                self.enemy_bullets.remove(bullet)
                self.particles.spawn_explosion(bullet.x, bullet.y, 10, 3,
                    [(255, 200, 100), (255, 255, 255)])

                if self.ship.health <= 0:
                    self.game_over = True

        # ===== СБОР БОНУСОВ =====
        self.powerups.check_collection(self.ship, self.particles)

        # ===== БОМБА =====
        if 'bomb' in self.powerups.active_effects:
            for enemy in self.enemies[:]:
                enemy.destroy(self.particles)
                self.score += enemy.score_value
                self.enemies.remove(enemy)
            self.particles.spawn_explosion(self.ship.x, self.ship.y, 100, 10,
                [(255, 200, 50), (255, 100, 50), (255, 255, 255)])
            del self.powerups.active_effects['bomb']

        # ===== ОБНОВЛЕНИЕ ЭФФЕКТОВ НА КОРАБЛЕ =====
        self.powerups.update_effects(self.ship)
        
        # ===== ПОПАДАНИЯ ПУЛЬ ПО БАЗАМ =====
        for bullet in self.bullets[:]:
            for base in self.enemy_bases[:]:
                if not base.alive:
                    continue
                
                dx = bullet.x - base.x
                dy = bullet.y - base.y
                dist = math.sqrt(dx**2 + dy**2)
                
                if dist < base.radius + bullet.radius:
                    # Урон по базе (передаём список врагов)
                    base.take_damage(self.enemies, 1)  # <-- ПЕРЕДАЁМ ENEMIES
                    self.bullets.remove(bullet)
                    
                    # Эффект попадания
                    self.particles.spawn_explosion(
                        bullet.x, bullet.y,
                        count=5,
                        speed=2,
                        colors=[(255, 200, 100), (255, 255, 255)]
                    )
                    
                    # Если база уничтожена
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
        
    def _spawn_enemy_with_base(self, x, y, enemy_type):
        """Создаёт врага для базы"""
        enemy = self.enemy_manager.spawn_enemy(x, y, enemy_type)
        if enemy:
            self.enemies.append(enemy)
        return enemy
        
    def _handle_controls(self):
        """Обработка управления с клавиатуры и мыши"""
        keys = self.keys

        # ===== КЛАВИАТУРА =====
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

        # ===== МЫШКА =====
        if self.config.get('controls.mouse_control', True):
            mouse_x, mouse_y = pygame.mouse.get_pos()
            world_mouse_x = mouse_x + self.camera.x
            world_mouse_y = mouse_y + self.camera.y
            self.ship.aim_at(world_mouse_x, world_mouse_y)

            if self.mouse_pressed:
                self.ship.shoot(self.bullets)

    def draw(self):
        """Отрисовка всего"""
        self.screen.fill(BLACK)

        camera_x = self.camera.x
        camera_y = self.camera.y

        # ===== ЗВЁЗДЫ (из чанков) =====
        self.starfield.draw(self.screen, camera_x, camera_y)
        #print(f"[DRAW] Рисуем звёзды, камера: ({camera_x:.0f}, {camera_y:.0f})")  # <-- ДОБАВЬ

        # ===== ЧАСТИЦЫ =====
        self.particles.draw(self.screen, camera_x, camera_y)

        # ===== БОНУСЫ =====
        self.powerups.draw(self.screen, camera_x, camera_y)

        # ===== КОРАБЛЬ =====
        self.ship.draw(self.screen, camera_x, camera_y, self.particles)

        # ===== ПУЛИ =====
        for bullet in self.bullets:
            bullet.draw(self.screen, camera_x, camera_y)
        for bullet in self.enemy_bullets:
            bullet.draw(self.screen, camera_x, camera_y)
        
        # ===== БАЗЫ =====
        for base in self.enemy_bases:
            base.draw(self.screen, camera_x, camera_y)
            
        # ===== ВРАГИ =====
        for enemy in self.enemies:
            enemy.draw(
                self.screen, 
                camera_x, 
                camera_y,
                self.ship.x,  # <-- Передаём позицию игрока
                self.ship.y
            )

        # ===== МИНИ-КАРТА =====
        self.minimap.draw(
            self.screen, 
            self.ship.x, 
            self.ship.y, 
            self.enemies, 
            self.powerups.powerups,
            None,  # База игрока (пока нет)
            self.camera,
            self.enemy_bases  # <-- Передаём базы
        )
        
        # ===== УКАЗАТЕЛИ НАПРАВЛЕНИЯ =====
        self.indicators.draw(self.screen)  # <-- ДОБАВЛЯЕМ
        
        # ===== ОТОБРАЖЕНИЕ HP БАЗЫ ПОД ПРИЦЕЛОМ =====
        mouse_x, mouse_y = pygame.mouse.get_pos()
        world_mouse_x = mouse_x + camera_x
        world_mouse_y = mouse_y + camera_y
        
        for base in self.enemy_bases:
            if not base.alive:
                continue
            
            dx = world_mouse_x - base.x
            dy = world_mouse_y - base.y
            dist = math.sqrt(dx**2 + dy**2)
            
            if dist < base.radius + 20:
                # Показываем HP базы
                hp_text = small_font.render(
                    f"Base HP: {int(base.health)}/{int(base.max_health)}", 
                    True, (255, 255, 255)
                )
                hp_rect = hp_text.get_rect(center=(mouse_x, mouse_y - 40))
                self.screen.blit(hp_text, hp_rect)
                break
                
        # ===== HUD =====
        self._draw_hud()

        # ===== GAME OVER =====
        if self.game_over:
            self._draw_game_over()

        pygame.display.flip()
        self.clock.tick(FPS)

    def _draw_hud(self):
        """Рисует интерфейс"""
        # ===== СЧЁТ =====
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))

        # ===== HP =====
        health_text = font.render(f"HP: {self.ship.health}", True, GREEN if self.ship.health > 30 else RED)
        self.screen.blit(health_text, (10, 50))

        # ===== БАЗЫ =====
        bases_alive = sum(1 for b in self.enemy_bases if b.alive)
        bases_text = small_font.render(f"Bases: {bases_alive}", True, YELLOW)
        self.screen.blit(bases_text, (WIDTH // 2 - 40, 10))

        # ===== ВРАГИ НА ЭКРАНЕ =====
        enemy_count = small_font.render(f"Enemies: {len(self.enemies)}", True, GRAY)
        self.screen.blit(enemy_count, (WIDTH // 2 - 40, 35))

        # ===== АКТИВНЫЕ ЭФФЕКТЫ =====
        y_offset = 90
        for effect, timer in self.powerups.active_effects.items():
            if timer > 0:
                seconds = timer // 60
                effect_text = small_font.render(f"{effect}: {seconds}s", True, YELLOW)
                self.screen.blit(effect_text, (10, y_offset))
                y_offset += 22

        # ===== СКОРОСТЬ =====
        speed_val = math.sqrt(self.ship.speed_x**2 + self.ship.speed_y**2)
        speed_text = small_font.render(f"Speed: {speed_val:.1f}", True, GRAY)
        self.screen.blit(speed_text, (10, HEIGHT - 78))

        # ===== ВРАГИ =====
        enemy_count = small_font.render(f"Enemies: {len(self.enemies)}", True, GRAY)
        self.screen.blit(enemy_count, (10, HEIGHT - 56))

        # ===== ЧИТ-КОДЫ (только в режиме отладки) =====
        if self.config.get('game.debug_mode', False):
            cheats_text = small_font.render(
                "F1:Bomb F2:Heal F3:+50 F4:Kill F5:Spawn", 
                True, (80, 80, 80)
            )
            cheats_rect = cheats_text.get_rect(center=(WIDTH // 2, HEIGHT - 40))
            self.screen.blit(cheats_text, cheats_rect)

        # ===== РЕЖИМ ОТЛАДКИ =====
        if self.config.get('game.debug_mode', False):
            debug_text = small_font.render("DEBUG", True, (200, 200, 50))
            self.screen.blit(debug_text, (WIDTH - 80, 10))

        # ===== FPS =====
        if self.config.get('game.show_fps', False):
            fps_text = small_font.render(f"FPS: {int(self.clock.get_fps())}", True, GRAY)
            fps_rect = fps_text.get_rect(topright=(WIDTH - 10, 10))
            self.screen.blit(fps_text, fps_rect)

        # ===== УПРАВЛЕНИЕ =====
        controls = font.render("ESC: Menu | P: Pause", True, GRAY)
        controls_rect = controls.get_rect(bottomright=(WIDTH - 10, HEIGHT - 10))
        self.screen.blit(controls, controls_rect)

    def _draw_game_over(self):
        """Экран Game Over"""
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        title = font.render("GAME OVER", True, RED)
        title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//2 - 60))
        self.screen.blit(title, title_rect)

        score_text = font.render(f"Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(WIDTH//2, HEIGHT//2))
        self.screen.blit(score_text, score_rect)

        restart_text = font.render("Press SPACE to restart", True, YELLOW)
        restart_rect = restart_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 60))
        self.screen.blit(restart_text, restart_rect)

        menu_text = font.render("Press ESC for menu", True, GRAY)
        menu_rect = menu_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 120))
        self.screen.blit(menu_text, menu_rect)

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