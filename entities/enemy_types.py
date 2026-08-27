# enemy_types.py
import pygame

# Типы врагов
ENEMY_TYPES = {
    'scout': {
        'name': 'Scout',
        'radius': 15,
        'speed': 3.0,
        'health': 2,
        'max_health': 2,
        'color': (100, 255, 100),
        'behavior': 'chase',
        'shoot_delay': 60,
        'score': 10,
        'description': 'Fast but weak'
    },
    'tank': {
        'name': 'Tank',
        'radius': 30,
        'speed': 1.2,
        'health': 8,
        'max_health': 8,
        'color': (255, 100, 100),
        'behavior': 'chase',
        'shoot_delay': 30,
        'score': 20,
        'description': 'Slow but tough'
    },
    'sniper': {
        'name': 'Sniper',
        'radius': 18,
        'speed': 0.5,
        'health': 3,
        'max_health': 3,
        'color': (100, 150, 255),
        'behavior': 'stationary',
        'shoot_delay': 15,
        'score': 15,
        'description': 'Stays back and shoots'
    },
    'kamikaze': {
        'name': 'Kamikaze',
        'radius': 14,
        'speed': 4.5,
        'health': 1,
        'max_health': 1,
        'color': (255, 200, 50),
        'behavior': 'kamikaze',
        'shoot_delay': 999,
        'score': 15,
        'description': 'Charges and explodes'
    },
    'swarmer': {
        'name': 'Swarmer',
        'radius': 10,
        'speed': 5.0,
        'health': 1,
        'max_health': 1,
        'color': (255, 100, 200),
        'behavior': 'chase',
        'shoot_delay': 999,
        'score': 8,
        'description': 'Fast and tiny'
    },
    'guardian': {
        'name': 'Guardian',
        'radius': 25,
        'speed': 2.0,
        'health': 5,
        'max_health': 5,
        'color': (100, 255, 200),
        'behavior': 'orbit',
        'shoot_delay': 40,
        'score': 25,
        'description': 'Orbits around player'
    },
    'turret': {
        'name': 'Turret',
        'radius': 22,
        'speed': 0.0,
        'health': 6,
        'max_health': 6,
        'color': (255, 150, 100),
        'behavior': 'stationary',
        'shoot_delay': 10,
        'score': 30,
        'description': 'Stationary, rapid fire'
    }
}

# Веса для спавна (чем больше вес, тем чаще появляется)
SPAWN_WEIGHTS = {
    'scout': 30,
    'tank': 15,
    'sniper': 10,
    'kamikaze': 8,
    'swarmer': 20,
    'guardian': 5,
    'turret': 5
}