# MiniTetris-in-Python
#
# Install colorama: pip install colorama
# Launch: python tetris.py
#
# written by Andrea Giani

import os
import sys
import time
import threading
import random
from enum import Enum
import platform

# Importazioni specifiche per l'input e l'audio
if platform.system() == "Windows":
    import msvcrt
    import winsound
else:
    import tty
    import termios
    # Placeholder per winsound su non-Windows
    def winsound_beep_placeholder(frequency, duration):
        pass
    winsound = type('', (), {'Beep': winsound_beep_placeholder})()

# Colorama init
# (colorama required)
from colorama import Fore, Back, Style, init
init(autoreset=True)

# === ENUMERAZIONI ===
class CellStates(Enum):
    Empty = 0
    Dead = 1
    Alive = 2

class Movement(Enum):
    Left = 0
    Down = 1
    Right = 2
    RotLeft = 3
    RotRight = 4

# === CLASSI DI SUPPORTO ===
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        if not isinstance(other, Point):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

# === VARIABILI GLOBALI ===
SPEED_UP = 0.9
DELAY = 800.0 # Usiamo float per il delay per la divisione e moltiplicazione
HEIGHT = 20
WIDTH = 10

WORLD = [[CellStates.Empty for _ in range(HEIGHT)] for _ in range(WIDTH)]
RAND = random.Random()
GAME_TIMER = None
SCORE = 0

PIECES = [
    [0, 1, 1, 1, 2, 1, 3, 1],  # I
    [0, 0, 0, 1, 1, 1, 2, 1],  # J
    [0, 1, 1, 1, 2, 0, 2, 1],  # L
    [1, 0, 2, 0, 1, 1, 2, 1],  # O
    [0, 1, 1, 0, 1, 1, 2, 0],  # S
    [0, 1, 1, 0, 1, 1, 2, 1],  # T
    [0, 0, 1, 0, 1, 1, 2, 1]   # Z
]

PIECE_COLORS = [1, 2, 3, 4, 5, 6, 7]
CURRENT_PIECE_COLOR = 1
CURRENT_PIECE_TYPE_INDEX = -1 # Aggiunto per tracciare il tipo di pezzo per la rotazione 'O'

game_running = True # Flag per controllare il main game loop

# === FUNZIONI DEL GIOCO ===

def setup_console():
    sys.stdout.write("\x1b[?25l") # Nascondi cursore
    sys.stdout.flush()

    if platform.system() == "Windows":
        os.system("title Python MINITETRIS")
        # os.system(f"mode con: cols={WIDTH * 2 + 20} lines={HEIGHT + 3}") # Opzionale per dimensioni
    else:
        sys.stdout.write("\x1b]0;Python MINITETRIS\x07")
        sys.stdout.flush()

    os.system('cls' if os.name == 'nt' else 'clear')

def reset_console():
    sys.stdout.write(Style.RESET_ALL)
    sys.stdout.write("\x1b[?25h") # Mostra cursore
    sys.stdout.flush()
    os.system('cls' if os.name == 'nt' else 'clear')

def beep(frequency, duration):
    try:
        winsound.Beep(frequency, duration)
    except Exception:
        pass

def play_song():
    while True:
        try:
            beep(1320,150)
            beep(990,100)
            beep(1056,100)
            beep(1188,100)
            beep(1320,50)
            beep(1188,50)
            beep(1056,100)
            beep(990,100)
            beep(880,300)
            beep(880,100)
            beep(1056,100)
            beep(1320,300)
            beep(1188,100)
            beep(1056,100)
            beep(990,300)
            beep(1056,100)
            beep(1188,300)
            beep(1320,300)
            beep(1056,300)
            beep(880,300)
            beep(880,300)
            time.sleep(1)
        except Exception:
            break

def set_piece_color(color_index):
    effective_index = (color_index - 1) % 7 if color_index > 0 else 0
    if effective_index == 0: sys.stdout.write(Fore.CYAN)
    elif effective_index == 1: sys.stdout.write(Fore.BLUE)
    elif effective_index == 2: sys.stdout.write(Fore.YELLOW)
    elif effective_index == 3: sys.stdout.write(Fore.YELLOW)
    elif effective_index == 4: sys.stdout.write(Fore.GREEN)
    elif effective_index == 5: sys.stdout.write(Fore.MAGENTA)
    elif effective_index == 6: sys.stdout.write(Fore.RED)
    else: sys.stdout.write(Fore.WHITE)

def draw():
    sys.stdout.write("\x1b[H") # Posiziona cursore in 0,0
    sys.stdout.flush()

    sys.stdout.write(Fore.WHITE + "╔" + "═" * (WIDTH * 2) + "╗\n")
    for y in range(HEIGHT):
        sys.stdout.write("║")
        for x in range(WIDTH):
            if WORLD[x][y] == CellStates.Empty:
                sys.stdout.write(Fore.LIGHTBLACK_EX + "░░")
            else:
                color_to_use = CURRENT_PIECE_COLOR if WORLD[x][y] == CellStates.Alive else ((x + y) % 7 + 1)
                set_piece_color(color_to_use)
                sys.stdout.write("██")
        sys.stdout.write(Fore.WHITE + "║\n")

    sys.stdout.write(Fore.WHITE + "╚" + "═" * (WIDTH * 2) + "╝\n")

    sys.stdout.write(f"\x1b[{2 + 1};{WIDTH * 2 + 5 + 1}H")
    sys.stdout.write(Fore.WHITE + "Python MINITETRIS")
    sys.stdout.write(f"\x1b[{4 + 1};{WIDTH * 2 + 5 + 1}H")
    sys.stdout.write(f"Score: {SCORE}")
    sys.stdout.write(f"\x1b[{6 + 1};{WIDTH * 2 + 5 + 1}H")
    sys.stdout.write("Checks:")
    sys.stdout.write(f"\x1b[{7 + 1};{WIDTH * 2 + 5 + 1}H")
    sys.stdout.write("A - Left")
    sys.stdout.write(f"\x1b[{8 + 1};{WIDTH * 2 + 5 + 1}H")
    sys.stdout.write("D - Right")
    sys.stdout.write(f"\x1b[{9 + 1};{WIDTH * 2 + 5 + 1}H")
    sys.stdout.write("S - Below")
    sys.stdout.write(f"\x1b[{10 + 1};{WIDTH * 2 + 5 + 1}H")
    sys.stdout.write("Q/E - Wheel")
    sys.stdout.write(f"\x1b[{11 + 1};{WIDTH * 2 + 5 + 1}H")
    sys.stdout.write("ESC - Done")
    sys.stdout.flush()

def get_current_piece_positions():
    current_piece_positions = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if WORLD[x][y] == CellStates.Alive:
                current_piece_positions.append(Point(x, y))
    return current_piece_positions

def move_piece(movement):
    global WORLD, WIDTH, HEIGHT, CURRENT_PIECE_TYPE_INDEX

    current_positions = get_current_piece_positions()
    if not current_positions: # Nessun pezzo vivo, non muovere
        return False

    new_positions = []
    delta_x, delta_y = 0, 0

    if movement == Movement.Left: delta_x = -1
    elif movement == Movement.Right: delta_x = 1
    elif movement == Movement.Down: delta_y = 1

    if movement == Movement.RotLeft or movement == Movement.RotRight:
        if CURRENT_PIECE_TYPE_INDEX == 3: # Pezzo 'O'
            return True

        pivot = current_positions[1] # Assumiamo il secondo blocco come pivot
        
        for p in current_positions:
            translated_x = p.x - pivot.x
            translated_y = p.y - pivot.y

            if movement == Movement.RotLeft:
                rotated_x, rotated_y = -translated_y, translated_x
            else: # Movement.RotRight
                rotated_x, rotated_y = translated_y, -translated_x
            
            new_x = rotated_x + pivot.x
            new_y = rotated_y + pivot.y
            new_positions.append(Point(new_x, new_y))
    else:
        for p in current_positions:
            new_positions.append(Point(p.x + delta_x, p.y + delta_y))

    # Collision Check
    for p in new_positions:
        if not (0 <= p.x < WIDTH and 0 <= p.y < HEIGHT):
            return False
        # Controlla collisione con celle 'Dead', ma non con le nostre celle 'Alive'
        # Per farlo correttamente, le celle 'Alive' attuali devono essere considerate 'Empty' durante il check.
        # Una buona pratica sarebbe "pulire" temporaneamente le celle 'Alive' prima del controllo
        # e poi ripristinarle se il movimento non è valido.
        # Per semplicità, replichiamo la logica Python assumendo che non si sovrapponga a se stesso.
        if WORLD[p.x][p.y] == CellStates.Dead:
             # Controlla se il punto è una delle posizioni attuali del pezzo "Alive"
             is_current_alive_cell = False
             for current_p in current_positions:
                 if p.x == current_p.x and p.y == current_p.y:
                     is_current_alive_cell = True
                     break
             if not is_current_alive_cell:
                 return False # Collisione con un blocco morto non nostro

    # Se il movimento è valido, aggiorna il WORLD
    for p in current_positions:
        WORLD[p.x][p.y] = CellStates.Empty
        
    for p in new_positions:
        WORLD[p.x][p.y] = CellStates.Alive
        
    draw()
    return True

def spawn_piece():
    global CURRENT_PIECE_COLOR, WORLD, PIECES, RAND, WIDTH, HEIGHT, game_running, CURRENT_PIECE_TYPE_INDEX

    rand_piece_index = RAND.randint(0, 6)
    CURRENT_PIECE_TYPE_INDEX = rand_piece_index
    CURRENT_PIECE_COLOR = PIECE_COLORS[rand_piece_index]
    
    exit_game = False
    
    for i in range(0, 8, 2):
        x = PIECES[rand_piece_index][i] + WIDTH // 2 - 2
        y = PIECES[rand_piece_index][i + 1]

        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            if WORLD[x][y] != CellStates.Empty:
                exit_game = True
                break
            else:
                WORLD[x][y] = CellStates.Alive
        else:
            exit_game = True
            break

    draw()

    if exit_game:
        reset_console()
        print("Game Over! Final Score: " + str(SCORE))
        time.sleep(2)
        game_running = False

def kill_all():
    global WORLD
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if WORLD[x][y] == CellStates.Alive:
                WORLD[x][y] = CellStates.Dead

def visual_line_effect(line_index):
    sys.stdout.write(f"\x1b[{line_index + 1 + 1};{0 + 1}H")
    for i in range(4):
        for x in range(WIDTH):
            if i % 2 == 0:
                set_piece_color((x + line_index) % 7 + 1)
            else:
                sys.stdout.write(Back.BLACK + Fore.BLACK)
            sys.stdout.write("██")
        sys.stdout.flush()
        time.sleep(0.05)

def remove_lines():
    global WORLD, SCORE, DELAY, SPEED_UP

    lines_removed_in_this_round = 0

    for y in range(HEIGHT - 1, -1, -1):
        is_full_line = True
        for x in range(WIDTH):
            if WORLD[x][y] == CellStates.Empty:
                is_full_line = False
                break

        if is_full_line:
            lines_removed_in_this_round += 1
            visual_line_effect(y)

            for yy in range(y, 0, -1):
                for xx in range(WIDTH):
                    WORLD[xx][yy] = WORLD[xx][yy - 1]
            
            for xx in range(WIDTH):
                WORLD[xx][0] = CellStates.Empty
            
            y += 1 # Riconsidera la stessa riga nel loop esterno

    if lines_removed_in_this_round > 0:
        SCORE += lines_removed_in_this_round * 100
        DELAY *= SPEED_UP
        if DELAY < 50:
            DELAY = 50
        draw()

def tick():
    global GAME_TIMER, DELAY, game_running

    if not game_running:
        if GAME_TIMER:
            GAME_TIMER.cancel()
        return

    piece_moved = move_piece(Movement.Down)

    if not piece_moved:
        kill_all()
        remove_lines()
        spawn_piece()

    if game_running:
        GAME_TIMER = threading.Timer(DELAY / 1000.0, tick)
        GAME_TIMER.start()

def input_handler(key_char):
    global game_running, GAME_TIMER, DELAY

    if key_char == 'q':
        move_piece(Movement.RotLeft)
    elif key_char == 'e':
        move_piece(Movement.RotRight)
    elif key_char == 'a':
        move_piece(Movement.Left)
    elif key_char == 's':
        if GAME_TIMER:
            GAME_TIMER.cancel()
        move_piece(Movement.Down) # Forziamo il movimento
        GAME_TIMER = threading.Timer(DELAY / 1000.0, tick) # E riavviamo il timer
        GAME_TIMER.start()
    elif key_char == 'd':
        move_piece(Movement.Right)
    elif key_char == '\x1b': # ESC
        reset_console()
        game_running = False

def initialize_game():
    global WORLD, GAME_TIMER, DELAY
    for y in range(HEIGHT):
        for x in range(WIDTH):
            WORLD[x][y] = CellStates.Empty

    spawn_piece()
    draw()

    GAME_TIMER = threading.Timer(DELAY / 1000.0, tick)
    GAME_TIMER.start()

def run_game_loop():
    global game_running
    music_thread = threading.Thread(target=play_song)
    music_thread.daemon = True
    music_thread.start()

    old_settings = None
    if platform.system() != "Windows":
        old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin)

    try:
        while game_running:
            if platform.system() == "Windows":
                if msvcrt.kbhit():
                    key = msvcrt.getch().decode('utf-8').lower()
                    if key == '\x03': # Ctrl+C
                        game_running = False
                        break
                    input_handler(key)
            else:
                import select
                if select.select([sys.stdin], [], [], 0)[0]:
                    key = sys.stdin.read(1)
                    if key == '\x03' or key == '\x1b': # Ctrl+C or ESC
                        game_running = False
                        break
                    input_handler(key)
            time.sleep(0.01)
    finally:
        if platform.system() != "Windows" and old_settings:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

# === PUNTO DI INGRESSO PRINCIPALE ===
if __name__ == "__main__":
    setup_console()
    try:
        initialize_game()
        run_game_loop()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        reset_console()
        print("Game closed.")
        # Assicurati che il timer venga cancellato alla fine
        if GAME_TIMER and GAME_TIMER.is_alive():
            GAME_TIMER.cancel()