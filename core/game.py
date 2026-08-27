# core/game.py
import pygame
import sys
import math
from settings import *
from config_manager import ConfigManager
from entities.ship import Ship
from entities.enemy import Enemy
from entities.bullet import Bullet
from entities.powerups import PowerUpSystem
from systems.particles import ParticleSystem
from systems.waves import WaveSystem
from systems.minimap import Minimap
from world.chunk_starfield import ChunkStarField
from core.camera import Camera
from ui.menu import Menu
from utils import check_collision, distance_between, spawn_position