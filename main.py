# main.py
import pygame
import sys
import math
import random
from settings import (
    WIDTH, HEIGHT, FPS, BLACK, WHITE, RED, GREEN, YELLOW, GRAY, WORLD_WIDTH, WORLD_HEIGHT,
    WAVE_ENEMY_COUNT,
    WAVE_ENEMY_INCREASE,
    WAVE_PAUSE_DURATION,
    WAVE_MAX_ENEMIES,
    WAVE_SPAWN_DELAY_BASE,
    WAVE_SPAWN_DELAY_MIN,
    )
from entities.ship import Ship
from entities.enemy import Enemy
from entities.bullet import Bullet
from world.chunk_starfield import ChunkStarField
from systems.particles import ParticleSystem
from entities.powerups import PowerUpSystem
from utils import check_collision, spawn_position, distance_between
from ui.menu import Menu
from entities.enemy_types import SPAWN_WEIGHTS
from config_manager import ConfigManager
from ui.settings_menu import SettingsMenu
from systems.minimap import Minimap

# Инициализация
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 20)

def spawn_enemy(enemies):
    """Создает врага случайного типа"""
    x, y = spawn_position()
    
    # Выбираем тип врага с учетом весов
    enemy_types = list(SPAWN_WEIGHTS.keys())
    weights = list(SPAWN_WEIGHTS.values())
    enemy_type = random.choices(enemy_types, weights=weights, k=1)[0]
    
    enemies.append(Enemy(x, y, enemy_type))

def show_game_over(screen, score, is_new_record=False, high_score=0):
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(128)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))
    
    title = font.render("GAME OVER", True, RED)
    title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//2 - 80))
    screen.blit(title, title_rect)
    
    # Рекорд
    if is_new_record:
        record_text = font.render("★ NEW RECORD! ★", True, YELLOW)
    else:
        record_text = font.render(f"Best Score: {high_score}", True, WHITE)
    record_rect = record_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 30))
    screen.blit(record_text, record_rect)
    
    # Текущий счет
    score_text = font.render(f"Score: {score}", True, WHITE)
    score_rect = score_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 20))
    screen.blit(score_text, score_rect)
    
    restart_text = font.render("Press SPACE to restart", True, YELLOW)
    restart_rect = restart_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 70))
    screen.blit(restart_text, restart_rect)
    
    menu_text = font.render("Press ESC for menu", True, GRAY)
    menu_rect = menu_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 120))
    screen.blit(menu_text, menu_rect)
    
def game_loop(config):
    """Основной игровой цикл"""
    # --- СОЗДАНИЕ ОБЪЕКТОВ ---
    ship = Ship(WORLD_WIDTH//2, WORLD_HEIGHT//2)
    bullets = []
    enemy_bullets = []
    enemies = []
    
    starfield = ChunkStarField()
    particle_system = ParticleSystem()
    powerup_system = PowerUpSystem()
    minimap = Minimap(screen, config)
    
    score = 0
    game_over = False
    running = True
    paused = False
    
    # ===== ПЕРЕМЕННЫЕ ДЛЯ ВОЛН (УПРОЩЕННЫЕ) =====
    wave_number = 1
    enemies_to_spawn = WAVE_ENEMY_COUNT
    enemies_spawned = 0
    wave_active = True
    wave_pause_timer = 0
    wave_spawn_timer = 0
    
    print(f"=== Wave {wave_number} started! ===")
    print(f"Enemies in wave: {enemies_to_spawn}")
    
    # --- ГЛАВНЫЙ ЦИКЛ ---
    while running:
        # --- ОБРАБОТКА СОБЫТИЙ ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            
            if event.type == pygame.KEYDOWN:
                if game_over:
                    if event.key == pygame.K_SPACE:
                        # Перезапуск
                        ship = Ship(WORLD_WIDTH//2, WORLD_HEIGHT//2)
                        bullets = []
                        enemy_bullets = []
                        enemies = []
                        score = 0
                        game_over = False
                        starfield = ChunkStarField()
                        particle_system = ParticleSystem()
                        powerup_system = PowerUpSystem()
                        minimap = Minimap(screen, config)
                        
                        wave_number = 1
                        enemies_to_spawn = WAVE_ENEMY_COUNT
                        enemies_spawned = 0
                        wave_active = True
                        wave_pause_timer = 0
                        wave_spawn_timer = 0
                        
                        print(f"=== Game Restarted ===")
                        print(f"=== Wave {wave_number} started! ===")
                        print(f"Enemies in wave: {enemies_to_spawn}")
                    elif event.key == pygame.K_ESCAPE:
                        return "menu"
                else:
                    if event.key == pygame.K_ESCAPE:
                        return "menu"
                    elif event.key == pygame.K_p:
                        paused = not paused
        
        # --- ЭКРАНЫ ПАУЗЫ И GAME OVER ---
        if game_over:
            is_new_record = False
            if score > config.get_high_score():
                config.set_high_score(score)
                config.save()
                is_new_record = True
            
            screen.fill(BLACK)
            starfield.draw(screen, 0, 0)
            particle_system.draw(screen, 0, 0)
            powerup_system.draw(screen, 0, 0)
            for enemy in enemies:
                enemy.draw(screen, 0, 0)
            for bullet in enemy_bullets:
                bullet.draw(screen)
            
            show_game_over(screen, score, is_new_record, config.get_high_score())
            
            pygame.display.flip()
            clock.tick(FPS)
            continue
        
        if paused:
            screen.fill(BLACK)
            starfield.draw(screen, 0, 0)
            particle_system.draw(screen, 0, 0)
            powerup_system.draw(screen, 0, 0)
            
            pause_text = font.render("PAUSED", True, WHITE)
            pause_rect = pause_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 30))
            screen.blit(pause_text, pause_rect)
            
            continue_text = small_font.render("Press P to continue", True, GRAY)
            continue_rect = continue_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 30))
            screen.blit(continue_text, continue_rect)
            
            pygame.display.flip()
            clock.tick(FPS)
            continue
        
        # --- УПРАВЛЕНИЕ ---
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            ship.rotate_left()
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            ship.rotate_right()
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            ship.thrust()
        else:
            ship.stop_thrust()
        if keys[pygame.K_SPACE]:
            ship.shoot(bullets)
        
        if config.get('controls.mouse_control', True):
            mouse_x, mouse_y = pygame.mouse.get_pos()
            center_x = WIDTH // 2
            center_y = HEIGHT // 2
            dx = mouse_x - center_x
            dy = mouse_y - center_y
            
            if dx != 0 or dy != 0:
                target_angle = math.degrees(math.atan2(dy, dx))
                angle_diff = target_angle - ship.angle
                while angle_diff > 180:
                    angle_diff -= 360
                while angle_diff < -180:
                    angle_diff += 360
                
                sensitivity = config.get('controls.mouse_sensitivity', 1.0)
                if abs(angle_diff) > 2 / sensitivity:
                    if angle_diff > 0:
                        ship.rotate_right()
                    else:
                        ship.rotate_left()
            
            if pygame.mouse.get_pressed()[0]:
                ship.shoot(bullets)
        
        # --- УПРАВЛЕНИЕ ВОЛНАМИ (УПРОЩЕННОЕ) ---
        if not game_over and not paused:
            if not wave_active:
                # Пауза между волнами
                wave_pause_timer += 1
                if wave_pause_timer >= WAVE_PAUSE_DURATION:
                    # Начинаем новую волну
                    wave_number += 1
                    enemies_to_spawn = min(
                        WAVE_ENEMY_COUNT + (wave_number - 1) * WAVE_ENEMY_INCREASE,
                        WAVE_MAX_ENEMIES
                    )
                    enemies_spawned = 0
                    wave_active = True
                    wave_pause_timer = 0
                    wave_spawn_timer = 0
                    print(f"=== Wave {wave_number} started! ===")
                    print(f"Enemies in wave: {enemies_to_spawn}")
            
            if wave_active:
                # Спавним врагов
                wave_spawn_timer += 1
                spawn_delay = max(
                    WAVE_SPAWN_DELAY_MIN,
                    WAVE_SPAWN_DELAY_BASE - wave_number // 2
                )
                
                if wave_spawn_timer >= spawn_delay and enemies_spawned < enemies_to_spawn:
                    spawn_enemy(enemies)
                    enemies_spawned += 1
                    wave_spawn_timer = 0
                    print(f"Spawned {enemies_spawned}/{enemies_to_spawn}")
                
                # Проверяем, закончилась ли волна
                if enemies_spawned >= enemies_to_spawn and len(enemies) == 0:
                    wave_active = False
                    wave_pause_timer = 0
                    print(f"=== Wave {wave_number} complete! ===")
        
        # --- ОБНОВЛЕНИЕ ФИЗИКИ ---
        old_x, old_y = ship.x, ship.y
        ship.update()
        
        offset_x = -(ship.x - old_x)
        offset_y = -(ship.y - old_y)
        
        camera_x = ship.x - WIDTH // 2
        camera_y = ship.y - HEIGHT // 2
        
        starfield.update(ship.x, ship.y, offset_x, offset_y)
        particle_system.update()
        powerup_system.update(ship.x, ship.y)
        
        for bullet in bullets[:]:
            bullet.update()
            if bullet.is_dead():
                bullets.remove(bullet)
        
        for bullet in enemy_bullets[:]:
            bullet.update()
            if bullet.is_dead():
                enemy_bullets.remove(bullet)
        
        # Обновление врагов
        for enemy in enemies[:]:
            enemy.update(ship.x, ship.y)
            enemy.shoot(enemy_bullets, ship.x, ship.y)
            
            if check_collision(ship, enemy, -5):
                ship.health -= 10
                enemy.destroy(particle_system)
                enemies.remove(enemy)
                if ship.health <= 0:
                    particle_system.spawn_explosion(ship.x, ship.y, 80, 8, 
                        [(255, 200, 50), (255, 100, 50), (255, 50, 50)])
                    game_over = True
                continue
            
            if enemy.behavior == 'kamikaze' and enemy.is_exploding:
                dist = distance_between(ship.x, ship.y, enemy.x, enemy.y)
                if dist < enemy.explosion_radius:
                    ship.health -= 30
                    particle_system.spawn_explosion(enemy.x, enemy.y, 60, 8,
                        [(255, 200, 50), (255, 100, 50), (255, 255, 255)])
                    enemies.remove(enemy)
                    if ship.health <= 0:
                        game_over = True
                continue
            
            for bullet in bullets[:]:
                if check_collision(bullet, enemy):
                    if enemy.take_damage():
                        enemy.destroy(particle_system)
                        powerup_system.spawn_from_enemy(enemy.x, enemy.y, 0.3)
                        score += enemy.score_value
                        enemies.remove(enemy)
                    bullets.remove(bullet)
                    break
        
        # Попадания вражеских пуль в игрока
        for bullet in enemy_bullets[:]:
            if check_collision(bullet, ship, -5):
                if 'shield' in powerup_system.active_effects:
                    enemy_bullets.remove(bullet)
                    particle_system.spawn_explosion(bullet.x, bullet.y, 10, 3, 
                        [(50, 150, 255), (255, 255, 255)])
                    continue
                
                ship.health -= 5
                enemy_bullets.remove(bullet)
                particle_system.spawn_explosion(bullet.x, bullet.y, 10, 3, 
                    [(255, 200, 100), (255, 255, 255)])
                
                if ship.health <= 0:
                    particle_system.spawn_explosion(ship.x, ship.y, 80, 8, 
                        [(255, 200, 50), (255, 100, 50), (255, 50, 50)])
                    game_over = True
        
        # Сбор бонусов
        powerup_system.check_collection(ship, particle_system)
        
        # Эффект "Бомба"
        if 'bomb' in powerup_system.active_effects:
            for enemy in enemies[:]:
                enemy.destroy(particle_system)
                score += enemy.score_value
                enemies.remove(enemy)
            particle_system.spawn_explosion(ship.x, ship.y, 100, 10, 
                [(255, 200, 50), (255, 100, 50), (255, 255, 255)])
            del powerup_system.active_effects['bomb']
        
        powerup_system.update_effects(ship)
        
        # --- ОТРИСОВКА ---
        screen.fill(BLACK)
        
        starfield.draw(screen, camera_x, camera_y)
        particle_system.draw(screen, camera_x, camera_y)
        powerup_system.draw(screen, camera_x, camera_y)
        
        ship.draw(screen, camera_x, camera_y, particle_system)
        
        for bullet in bullets:
            bullet.draw(screen, camera_x, camera_y)
        for bullet in enemy_bullets:
            bullet.draw(screen, camera_x, camera_y)
        for enemy in enemies:
            enemy.draw(screen, camera_x, camera_y)
        
        # Мини-карта
        minimap.draw(ship.x, ship.y, enemies, powerup_system.powerups)
        
        # --- UI ---
        # Счет
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        
        # Волна
        wave_text = small_font.render(f"Wave: {wave_number}", True, YELLOW)
        screen.blit(wave_text, (WIDTH // 2 - 40, 10))
        
        # Прогресс волны
        if wave_active:
            progress = f"Enemies: {enemies_spawned}/{enemies_to_spawn}"
            progress_text = small_font.render(progress, True, GRAY)
            screen.blit(progress_text, (WIDTH // 2 - 50, 35))
        else:
            remaining = (WAVE_PAUSE_DURATION - wave_pause_timer) // 60
            if remaining > 0:
                next_wave_text = small_font.render(f"Next wave in: {remaining}s", True, GRAY)
                screen.blit(next_wave_text, (WIDTH // 2 - 60, 35))
            else:
                next_wave_text = small_font.render("Prepare!", True, YELLOW)
                screen.blit(next_wave_text, (WIDTH // 2 - 35, 35))
        
        # HP
        health_text = font.render(f"HP: {ship.health}", True, GREEN if ship.health > 30 else RED)
        screen.blit(health_text, (10, 50))
        
        # Активные эффекты
        y_offset = 90
        for effect, timer in powerup_system.active_effects.items():
            if timer > 0:
                seconds = timer // 60
                effect_text = small_font.render(f"{effect}: {seconds}s", True, YELLOW)
                screen.blit(effect_text, (10, y_offset))
                y_offset += 22
        
        # Координаты
        coord_text = small_font.render(f"World: {int(ship.x)} x {int(ship.y)}", True, GRAY)
        screen.blit(coord_text, (10, HEIGHT - 100))
        
        # Скорость
        speed_val = math.sqrt(ship.speed_x**2 + ship.speed_y**2)
        speed_text = small_font.render(f"Speed: {speed_val:.1f}", True, GRAY)
        screen.blit(speed_text, (10, HEIGHT - 78))
        
        # Враги на экране
        enemy_count = small_font.render(f"Enemies on screen: {len(enemies)}", True, GRAY)
        screen.blit(enemy_count, (10, HEIGHT - 56))
        
        # Чанки
        chunk_count = small_font.render(f"Chunks: {len(starfield.visible_chunks)}", True, GRAY)
        screen.blit(chunk_count, (10, HEIGHT - 34))
        
        # Частицы
        particle_count = small_font.render(f"Particles: {len(particle_system.particles)}", True, GRAY)
        screen.blit(particle_count, (10, HEIGHT - 12))
        
        # FPS
        if config.get('game.show_fps', False):
            fps_text = small_font.render(f"FPS: {int(clock.get_fps())}", True, GRAY)
            fps_rect = fps_text.get_rect(topright=(WIDTH - 10, 10))
            screen.blit(fps_text, fps_rect)
        
        # Управление
        controls = font.render("ESC: Menu | P: Pause", True, GRAY)
        controls_rect = controls.get_rect(bottomright=(WIDTH - 10, HEIGHT - 10))
        screen.blit(controls, controls_rect)
        
        pygame.display.flip()
        clock.tick(FPS)
    
    return "quit"
    
def main():
    config = ConfigManager()
    menu = Menu(screen, config)
 
    while True:
        menu_result = menu.run()
        
        if menu_result == "start":
            game_result = game_loop(config)
            if game_result == "quit":
                break
            elif game_result == "menu":
                continue
        
        elif menu_result == "settings":
            settings_menu = SettingsMenu(screen, config)
            settings_menu.run()
        
        elif menu_result == "quit":
            break
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()