# Alien Invasion Defender

_A fast-paced Pygame “shmup” (shoot ’em up) featuring ten waves of varied enemies, culminating in a boss fight._

---

## Table of Contents

1. [Introduction](#introduction)  
2. [Features](#features)  
3. [Installation](#installation)  
4. [Running the Game](#running-the-game)  
5. [Controls](#controls)  
6. [Gameplay & Instructions](#gameplay--instructions)  
7. [License](#license)  

---

## Introduction

**Alien Invasion Defender** is a local‐only, wave‐based shooter built entirely in Python using [Pygame](https://www.pygame.org/). You pilot a spaceship defending Earth from ten increasingly difficult waves of alien invaders. Each wave introduces new enemy types and attack patterns—fast‐shooters, slow‐shooters, homing‐missile drones, kamikaze rushers, tanks & snipers, intermittent horizontal‐laser ships, and finally a multi‐pattern boss with its own reinforcements. The goal: survive all ten waves and defeat the final boss.

This project runs locally on your computer—no additional hosting or packaging required. Simply install the dependencies, run the main Python script, and enjoy!

---

## Features

- **Ten Unique Waves of Enemies**  
  1. **Wave 1:** 3 FastShooter drones (thin, rapid‐fire bullets).  
  2. **Wave 2:** 3 SlowShooter drones (big, slow bullets) + 1 Kamikaze rusher.  
  3. **Wave 3:** 4 HomingShooter drones (fire only homing missiles).  
  4. **Wave 4:** 2 Sniper/Tank pairs + 2 FastShooter drones. Tanks shield Snipers until destroyed.  
  5. **Wave 5:** 3 Kamikaze rushers + 2 SlowShooter drones + 1 SideLaserShip.  
  6. **Wave 6:** 5 Mixed shooters (fast/slow/homing) + 2 Sniper/Tank pairs + 1 SideLaserShip.  
  7. **Wave 7:** 4 HomingShooters + 3 Kamikaze rushers + 1 SideLaserShip.  
  8. **Wave 8:** 3 FastShooters + 3 SlowShooters + 3 HomingShooters + 1 SideLaserShip.  
  9. **Wave 9:** 5 HeavyEnemies (high HP, mixed fire) + 4 Kamikaze rushers + 2 Sniper/Tank pairs + 1 SideLaserShip.  
  10. **Wave 10 (Boss):** A powerful boss with multiple bullet patterns, vertical lasers, side‐ship spawns, and periodic Tank/Sniper spawns.

- **Multiple Bullet Types**  
  - Fast bullets (thin, high speed).  
  - Slow bullets (large, lower speed, drawn as circles, higher damage).  
  - Homing missiles (curve toward the player).  
  - Sniper bullets (extremely fast, targeted, higher damage).  
  - Horizontal lasers that block a row of the screen (also insta kill).  

- **Enemy Behaviors**  
  - **Dodging Logic:** Regular enemies (Fast/Slow/Homing drones) attempt to sidestep incoming player bullets.  
  - **Kamikaze Rushers:** Spawn at random edges (top, left, or right), lock on the player’s current position, and dash straight through. Any collision is an instant kill.  
  - **Tanks & Snipers:** Tanks have high HP and protect Snipers. Once a Tank is destroyed, its paired Sniper becomes vulnerable. Snipers fire targeted, high‐speed bullets every 3 seconds.  
  - **SideLaserShips:** Invulnerable horizontal‐laser carriers that fly in from left or right, dock at a fixed Y, flash a warning band, fire a horizontal laser across one band, then exit on the same side.  
  - **HeavyEnemies:** Slow, high HP drones that alternate between fast & slow fire.  
  - **Boss:** Spawns SideLaserShips from whichever side it is closer to, and periodically spawns Tank/Sniper pairs directly beneath it. Uses five distinct bullet patterns and vertical laser lanes.

- **Player Mechanics**  
  - Smooth WASD/Arrow‐key movement anywhere inside the window.  
  - Auto‐shooting every 150 ms.  
  - 5 lives, each represented by a heart icon. After getting hit, the player is invulnerable for 1 second (flashes red).  
  - Colliding with any enemy ship, bullet, kamikaze, or laser band deals damage or kills the player.

- **Pause & Quit**  
  - Press `P` to toggle pause/resume.  
  - Press `Esc` at any time to exit.

---

## Installation

1. **Clone or download this repository**  
   ```bash
   git clone git@github.com:Stanleyhoo1/Sci-Fi-Final-Project.git
   cd Sci-Fi-Final-Project
   ```

2. **Create & activate a Python virtual environment (recommended)**  
   ```bash
   # On macOS/Linux/WSL:
   python3 -m venv venv
   source venv/bin/activate

   # On Windows (PowerShell):
   python -m venv venv
   venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**  
   ```bash
   pip install pygame
   ```

---

## Running the Game

Once dependencies are installed, simply run the main Python file:

```bash
python spacedefender.py
```

---

## Controls

- **Move**: `W`, `A`, `S`, `D` or arrow keys  
- **Pause/Resume**: `P`  
- **Quit**: `Esc` (also closes the window)
- **Start**: `S`

There is no manual “shoot” key—your ship auto‐fires every 150 ms.

---

## Gameplay & Instructions

1. **Waves 1–9** progress sequentially. After you destroy all enemies (and kamikazes) in a wave and wait ~1.5 seconds, the next wave begins.  
2. **Enemy Types**:
   - **Default**: Base enemy is a ship that randomly fires either a fast, slow, or homing projectile.
  
     <img src="https://github.com/Stanleyhoo1/Sci-Fi-Final-Project/blob/main/assets/enemy_base.png" width="100" height="100">
   - **FastShooter**: Small drone that bounces in the top half of the screen. Fires only fast bullets.

     <img src="https://github.com/Stanleyhoo1/Sci-Fi-Final-Project/blob/main/assets/enemy_fast.png" width="100" height="100">
   - **SlowShooter**: Similar to FastShooter but slower movement, higher health, and fires large, slow bullets (drawn as circles).
  
     <img src="https://github.com/Stanleyhoo1/Sci-Fi-Final-Project/blob/main/assets/enemy_slow.png" width="100" height="100">
   - **HomingShooter**: Fires only homing missiles that curve toward you.
  
     <img src="https://github.com/Stanleyhoo1/Sci-Fi-Final-Project/blob/main/assets/enemy_homing.png" width="100" height="100">
   - **Kamikaze**: Spawns at a random edge (top, left, or right) and rushes your current position at high speed. If it touches you, you die instantly (explosion).
  
     <img src="https://github.com/Stanleyhoo1/Sci-Fi-Final-Project/blob/main/assets/kamakaze.png" width="100" height="100">
   - **Tank**: Tanks move slowly on top half, have high HP, and fire slow, large projectiles at you. Each Tank shields one Sniper perched slightly above. Once a Tank is destroyed, its paired Sniper (unprotected) can be shotSnipers fire high‐speed, targeted bullets every 3 seconds.
  
     <img src="https://github.com/Stanleyhoo1/Sci-Fi-Final-Project/blob/main/assets/enemy_tank.png" width="100" height="100">
   - **Sniper**: Snipers fire high‐speed, targeted bullets every 3 seconds.
     
     <img src="https://github.com/Stanleyhoo1/Sci-Fi-Final-Project/blob/main/assets/enemy_sniper.png" width="100" height="100">
   - **HeavyEnemy**: Moves slowly, high HP. Fires a mix of fast and slow bullets, attempts to dodge your shots.
  
     <img src="https://github.com/Stanleyhoo1/Sci-Fi-Final-Project/blob/main/assets/alien_heavy.png" width="100" height="100">
   - **SideLaserShip**: Invulnerable carrier that flies in from left or right, docks at a fixed X in the bottom half, flashes a horizontal warning band, then fires a horizontal laser across one band (killing you instantly if you stand in it), and immediately exits back offscreen.
  
     <img src="https://github.com/Stanleyhoo1/Sci-Fi-Final-Project/blob/main/assets/enemy_side.png" width="100" height="100">
   - **Boss (Wave 10)**: A large ship that enters from the top, wanders randomly horizontally, periodically emits vertical laser lanes (flash + active), and fires one of five bullet patterns in succession. Every ~5 s, the Boss spawns a Tank/Sniper (or lone Sniper) directly beneath itself to harass you. Additionally, every ~7 s, it spawns a SideLaserShip on the side it is closer to. The Boss has high HP (150) and five distinct bullet patterns:  
     1. Wide‐arc fast bullet spread (9 angled shots).  
     2. Triple slow‐bullet cluster straight down.  
     3. Homing missile volley (4 homing bullets).  
     4. Rapid spiral of 12 fast bullets around its center.  
     5. Zig‐zag pair pattern (two fast bullets at alternating small angles).
    
   <img src="https://github.com/Stanleyhoo1/Sci-Fi-Final-Project/blob/main/assets/boss.png" width="100" height="100">

4. **Player Mechanics**:  
   - You start with 5 lives. Each time you are hit, you lose lives and become invulnerable for 1 second (ship flashes red).  
   - Colliding with an enemy ship (non‐kamikaze) destroys that ship immediately and costs you one life (no explosion).  
   - Getting hit by a Kamikaze triggers an explosion animation and is effectively an immediate game‐over (player “dies”).  
   - If you survive all waves and the Boss is destroyed, you see “YOU WIN!” and can press `Esc` to quit.

5. **Tips & Tricks**:  
   - Stay on the bottom half to dodge most drones’ bullet patterns.  
   - For SideLaserShip waves, watch for the red warning band so you can move out of your current horizontal lane before it fires.  
   - Tanks protect Snipers—focus on Tanks first to expose Snipers.  
   - Homing missiles require constant lateral movement to avoid.  
   - During the Boss fight, keep an eye on both vertical laser lanes and periodic small enemy spawns. Prioritize picking off Tanks/Snipers quickly to reduce DPS against you.  
   - Use the bottom corners to dodge wide‐arc spreads and spirals.

---

## License

This project is released under the **MIT License**. Feel free to use, modify, and distribute as you wish, provided attribution is maintained. See the `LICENSE` file for full details.

---
