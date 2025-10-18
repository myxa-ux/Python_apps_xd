#dont work with (small screen/low qality)/не работает на маленьком экране/зинком разрешении экрана). нужно/need +1080       v1.1.5
import pygame
import math
import array
import sys
import time
import os
import json
from datetime import datetime
words=[]
language="RU"#"ENG"for english/"RU"для русского
if language=="RU":
    words=["Пианино", "Гитара", "Скрипка", "Синт-лид", "Бас", "Пэд", "Белл", "Плак","пробел","сохранить","отмена","пусто","выберите","загрузить","отмена","сохранено","сохранить как","конвертация","файл ненайден","ошибка","неверный формат","паттерн","загружено","стоп","играть","столбцов","ширина","высота","ы","шаг","инструмент","нот","сохранить","загрузить","очистить паттерн","очистить всё"]
elif language=="ENG":
    words=["Piano", "Guitar", "Violin", "Synth Lead", "Bass", "Pad", "Bell", "Pluck","space","save","cancel","empty","choice","download","cancel","saved","save as","convertation","file is not found","error","invalid format","pattern","loaded", "stop", "play", "columns", "width", "height","s","step","instruments","notes","save", "load", "clear pattern", "clear all"]
#15
SAVE_PATH = "/storage/emulated/0/mus" #место хранения
if not os.path.exists(SAVE_PATH):
    try:
        os.makedirs(SAVE_PATH)
    except:
        SAVE_PATH = "./saved_patterns"
        os.makedirs(SAVE_PATH, exist_ok=True)

#20
IN_CONTAINER = os.environ.get('CONTAINER', False) or os.path.exists('/.dockerenv')
if IN_CONTAINER:
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    os.environ['SDL_AUDIODRIVER'] = 'dummy'

#25
pygame.init()
WIDTH, HEIGHT = 1080,1080
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("LF Stu")

#30
BACKGROUND = (25, 25, 35)
GRID_COLOR = (60, 60, 80)
CELL_EMPTY = (40, 40, 55)
CELL_ACTIVE = (0, 200, 100)
CELL_HOVER = (70, 70, 90)
CURRENT_STEP = (255, 200, 0)
INSTRUMENT_PANEL = (45, 45, 60)
INSTRUMENT_SELECTED = (0, 150, 200)
TEXT_COLOR = (220, 220, 220)
WAVE_COLOR = (0, 255, 200)
DIALOG_BG = (40, 40, 60)
DIALOG_TEXT = (255, 255, 255)
PATTERN_ACTIVE = (100, 200, 100)
PATTERN_INACTIVE = (80, 80, 100)
BUTTON_COLOR = (70, 100, 150)
SCROLLBAR_COLOR = (80, 80, 100)
SCROLLBAR_HANDLE = (120, 120, 140)
ZOOM_BUTTON_COLOR = (90, 130, 180)

#50
INSTRUMENT_COLORS = [
    (0, 200, 100), (200, 100, 0), (150, 0, 200), (0, 150, 200),
    (200, 0, 100), (100, 200, 0), (200, 200, 0), (0, 100, 200)
]

#60
GRID_ROWS = 49
DEFAULT_COLS = 16
MIN_COLS, MAX_COLS = 8, 128
DEFAULT_CELL_WIDTH = 40
MIN_CELL_WIDTH, MAX_CELL_WIDTH = 20, 120
DEFAULT_CELL_HEIGHT = 20
MIN_CELL_HEIGHT, MAX_CELL_HEIGHT = 12, 60

#70
grid_cols = DEFAULT_COLS
cell_width = DEFAULT_CELL_WIDTH
cell_height = DEFAULT_CELL_HEIGHT
GRID_START_X, GRID_START_Y = 200, 100
INSTRUMENT_PANEL_WIDTH = 180
INSTRUMENT_BUTTON_HEIGHT = 50
PATTERN_PANEL_HEIGHT = 60
CONTROL_PANEL_HEIGHT = 90

SCROLLBAR_WIDTH = 25
ZOOM_PANEL_WIDTH = 50

#80
sample_rate = 44100
volume = 0.3
bpm = 120
step_duration = 60.0 / bpm / 4

scroll_x = 0
scroll_y = 0
max_scroll_x = 0
max_scroll_y = 0

dragging_horizontal = False
dragging_vertical = False
drag_offset_x = 0
drag_offset_y = 0

try:
    if not IN_CONTAINER:
        pygame.mixer.pre_init(sample_rate, -16, 2, 512)
        pygame.mixer.init()
    AUDIO_ENABLED = not IN_CONTAINER
except:
    AUDIO_ENABLED = False

#100
def create_notes():
    notes = []
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    base_freq = 65.41
    for octave in range(2, 7):
        for i, note_name in enumerate(note_names):
            if octave == 6 and i > 9:
                break
            freq = base_freq * (2 ** ((octave - 2) + i / 12))
            notes.append((f"{note_name}{octave}", freq))
    return notes

#150
NOTES = create_notes()
INSTRUMENTS = [words[0],words[1],words[2],words[3],words[4],words[5],words[6],words[7],]

#160
def generate_wave(freq, duration, sample_rate, wave_type, volume=1.0):
    n_samples = int(sample_rate * duration)
    samples = array.array('h', (0 for _ in range(n_samples)))
    max_amp = 2 ** 15 - 1
    for i in range(n_samples):
        t = i / sample_rate
        envelope = 1.0
        if wave_type == "piano":
            wave = (math.sin(2 * math.pi * freq * t) * 0.6 + 
                   math.sin(2 * math.pi * freq * 2 * t) * 0.2 +
                   math.sin(2 * math.pi * freq * 3 * t) * 0.1)
            envelope = 1.0 if t < 0.01 else (duration - t) / 0.3 if t > duration - 0.3 else 1.0
        elif wave_type == "guitar":
            wave = math.sin(2 * math.pi * freq * t) * 0.7 + math.sin(2 * math.pi * freq * 2 * t) * 0.3
            envelope = math.exp(-t * 2.5) * (1 + 0.02 * math.sin(2 * math.pi * 6 * t))
        elif wave_type == "bass":
            wave = 1 if math.sin(2 * math.pi * freq * t) > 0 else -1
            envelope = 1.0 - min(1.0, t / duration)
        else:
            wave = math.sin(2 * math.pi * freq * t)
            envelope = min(1.0, t * 2) * (1.0 - min(1.0, max(0, t - duration + 0.1) * 5))
        samples[i] = int(wave * envelope * max_amp * volume * 0.3)
    return samples

#170
SOUND_GENERATORS = [
    lambda f, d, sr, v=1.0: generate_wave(f, d, sr, "piano", v),
    lambda f, d, sr, v=1.0: generate_wave(f, d, sr, "guitar", v),
    lambda f, d, sr, v=1.0: generate_wave(f, d, sr, "piano", v),
    lambda f, d, sr, v=1.0: generate_wave(f, d, sr, "synth", v),
    lambda f, d, sr, v=1.0: generate_wave(f, d, sr, "bass", v),
    lambda f, d, sr, v=1.0: generate_wave(f, d, sr, "synth", v),
    lambda f, d, sr, v=1.0: generate_wave(f, d, sr, "piano", v),
    lambda f, d, sr, v=1.0: generate_wave(f, d, sr, "guitar", v)
]

#180
class TouchDialog:
    @staticmethod
    def input_dialog(prompt, default=""):
        font = pygame.font.SysFont(None, 32)
        input_font = pygame.font.SysFont(None, 36)
        input_text = default
        active = True
        keyboard_layout = ["1234567890", "qwertyuiop", "asdfghjkl", "zxcvbnm"]
        key_size = 50
        key_spacing = 5
        keyboard_width = len(keyboard_layout[0]) * (key_size + key_spacing)
        keyboard_start_x = WIDTH // 2 - keyboard_width // 2
        keyboard_start_y = HEIGHT // 2 + 50
        enter_rect = pygame.Rect(WIDTH//2 - 100, keyboard_start_y + 200, 200, 50)
        cancel_rect = pygame.Rect(WIDTH//2 - 100, keyboard_start_y + 260, 200, 50)
        backspace_rect = pygame.Rect(WIDTH//2 + 180, HEIGHT//2 - 10, 100, 40)
        
        while active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = event.pos
                    if enter_rect.collidepoint(pos):
                        active = False
                    elif cancel_rect.collidepoint(pos):
                        return None
                    elif backspace_rect.collidepoint(pos) and input_text:
                        input_text = input_text[:-1]
                    else:
                        for row_idx, row in enumerate(keyboard_layout):
                            for col_idx, char in enumerate(row):
                                key_rect = pygame.Rect(
                                    keyboard_start_x + col_idx * (key_size + key_spacing),
                                    keyboard_start_y + row_idx * (key_size + key_spacing),
                                    key_size, key_size
                                )
                                if key_rect.collidepoint(pos) and len(input_text) < 20:
                                    input_text += char
                        space_rect = pygame.Rect(keyboard_start_x, keyboard_start_y + 4 * (key_size + key_spacing), 
                                               keyboard_width, key_size)
                        if space_rect.collidepoint(pos) and len(input_text) < 20:
                            input_text += " "
            
            screen.fill(BACKGROUND)
            dialog_rect = pygame.Rect(WIDTH//2-250, HEIGHT//2-100, 500, 400)
            pygame.draw.rect(screen, DIALOG_BG, dialog_rect, border_radius=10)
            pygame.draw.rect(screen, GRID_COLOR, dialog_rect, 2, border_radius=10)
            
            prompt_surf = font.render(prompt, True, DIALOG_TEXT)
            screen.blit(prompt_surf, (WIDTH//2 - prompt_surf.get_width()//2, HEIGHT//2-80))
            
            input_rect = pygame.Rect(WIDTH//2-230, HEIGHT//2-40, 460, 50)
            pygame.draw.rect(screen, (60, 60, 80), input_rect, border_radius=5)
            pygame.draw.rect(screen, GRID_COLOR, input_rect, 2, border_radius=5)
            
            text_surf = input_font.render(input_text, True, DIALOG_TEXT)
            screen.blit(text_surf, (input_rect.x + 10, input_rect.y + 10))
            
            for row_idx, row in enumerate(keyboard_layout):
                for col_idx, char in enumerate(row):
                    key_rect = pygame.Rect(
                        keyboard_start_x + col_idx * (key_size + key_spacing),
                        keyboard_start_y + row_idx * (key_size + key_spacing),
                        key_size, key_size
                    )
                    pygame.draw.rect(screen, BUTTON_COLOR, key_rect, border_radius=5)
                    pygame.draw.rect(screen, GRID_COLOR, key_rect, 2, border_radius=5)
                    char_surf = font.render(char.upper(), True, TEXT_COLOR)
                    screen.blit(char_surf, (key_rect.centerx - char_surf.get_width()//2, key_rect.centery - char_surf.get_height()//2))
            
            space_rect = pygame.Rect(keyboard_start_x, keyboard_start_y + 4 * (key_size + key_spacing), 
                                   keyboard_width, key_size)
            pygame.draw.rect(screen, BUTTON_COLOR, space_rect, border_radius=5)
            pygame.draw.rect(screen, GRID_COLOR, space_rect, 2, border_radius=5)
            space_surf = font.render(words[8], True, TEXT_COLOR)
            screen.blit(space_surf, (space_rect.centerx - space_surf.get_width()//2, space_rect.centery - space_surf.get_height()//2))
            
            pygame.draw.rect(screen, (200, 100, 100), backspace_rect, border_radius=5)
            pygame.draw.rect(screen, GRID_COLOR, backspace_rect, 2, border_radius=5)
            backspace_surf = font.render("←", True, TEXT_COLOR)
            screen.blit(backspace_surf, (backspace_rect.centerx - backspace_surf.get_width()//2, backspace_rect.centery - backspace_surf.get_height()//2))
            
            pygame.draw.rect(screen, (100, 200, 100), enter_rect, border_radius=5)
            pygame.draw.rect(screen, GRID_COLOR, enter_rect, 2, border_radius=5)
            enter_surf = font.render(words[9], True, TEXT_COLOR)
            screen.blit(enter_surf, (enter_rect.centerx - enter_surf.get_width()//2, enter_rect.centery - enter_surf.get_height()//2))
            
            pygame.draw.rect(screen, (200, 100, 100), cancel_rect, border_radius=5)
            pygame.draw.rect(screen, GRID_COLOR, cancel_rect, 2, border_radius=5)
            cancel_surf = font.render(words[10], True, TEXT_COLOR)
            screen.blit(cancel_surf, (cancel_rect.centerx - cancel_surf.get_width()//2, cancel_rect.centery - cancel_surf.get_height()//2))
            
            pygame.display.flip()
        
        return input_text if input_text else default

#190
    @staticmethod
    def file_list_dialog():
        files = [f for f in os.listdir(SAVE_PATH) if f.endswith('.json')]
        if not files:
            TouchDialog.message_dialog(words[11],)
            return None
        
        font = pygame.font.SysFont(None, 28)
        selected = 0
        items_per_page = 6
        load_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 180, 200, 50)
        cancel_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 240, 200, 50)
        up_rect = pygame.Rect(WIDTH//2 + 240, HEIGHT//2 - 140, 40, 40)
        down_rect = pygame.Rect(WIDTH//2 + 240, HEIGHT//2 - 90, 40, 40)
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = event.pos
                    if load_rect.collidepoint(pos):
                        return files[selected]
                    elif cancel_rect.collidepoint(pos):
                        return None
                    elif up_rect.collidepoint(pos):
                        selected = max(0, selected - 1)
                    elif down_rect.collidepoint(pos):
                        selected = min(len(files)-1, selected + 1)
                    else:
                        list_rect = pygame.Rect(WIDTH//2-230, HEIGHT//2-150, 460, 300)
                        if list_rect.collidepoint(pos):
                            rel_y = pos[1] - list_rect.y
                            item_index = rel_y // 50
                            if 0 <= item_index < min(len(files), items_per_page):
                                selected = item_index
            
            screen.fill(BACKGROUND)
            dialog_rect = pygame.Rect(WIDTH//2-250, HEIGHT//2-200, 500, 500)
            pygame.draw.rect(screen, DIALOG_BG, dialog_rect, border_radius=10)
            pygame.draw.rect(screen, GRID_COLOR, dialog_rect, 2, border_radius=10)
            
            title = font.render(words[12], True, DIALOG_TEXT)
            screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2-180))
            
            list_rect = pygame.Rect(WIDTH//2-230, HEIGHT//2-150, 460, 300)
            pygame.draw.rect(screen, (30, 30, 45), list_rect, border_radius=5)
            
            start_idx = max(0, min(selected, len(files) - items_per_page))
            for i in range(min(len(files) - start_idx, items_per_page)):
                idx = start_idx + i
                color = INSTRUMENT_SELECTED if idx == selected else DIALOG_TEXT
                item_rect = pygame.Rect(list_rect.x + 5, list_rect.y + 5 + i*50, list_rect.width - 10, 45)
                pygame.draw.rect(screen, (50, 50, 70) if idx == selected else (40, 40, 55), item_rect, border_radius=5)
                file_surf = font.render(f"{idx+1}. {files[idx]}", True, color)
                screen.blit(file_surf, (item_rect.x + 10, item_rect.y + 15))
            
            pygame.draw.rect(screen, BUTTON_COLOR, up_rect, border_radius=5)
            pygame.draw.rect(screen, GRID_COLOR, up_rect, 2, border_radius=5)
            up_surf = font.render("↑", True, TEXT_COLOR)
            screen.blit(up_surf, (up_rect.centerx - up_surf.get_width()//2, up_rect.centery - up_surf.get_height()//2))
            
            pygame.draw.rect(screen, BUTTON_COLOR, down_rect, border_radius=5)
            pygame.draw.rect(screen, GRID_COLOR, down_rect, 2, border_radius=5)
            down_surf = font.render("↓", True, TEXT_COLOR)
            screen.blit(down_surf, (down_rect.centerx - down_surf.get_width()//2, down_rect.centery - down_surf.get_height()//2))
            
            pygame.draw.rect(screen, (100, 200, 100), load_rect, border_radius=5)
            pygame.draw.rect(screen, GRID_COLOR, load_rect, 2, border_radius=5)
            load_surf = font.render(words[12], True, TEXT_COLOR)
            screen.blit(load_surf, (load_rect.centerx - load_surf.get_width()//2, load_rect.centery - load_surf.get_height()//2))
            
            pygame.draw.rect(screen, (200, 100, 100), cancel_rect, border_radius=5)
            pygame.draw.rect(screen, GRID_COLOR, cancel_rect, 2, border_radius=5)
            cancel_surf = font.render(words[13], True, TEXT_COLOR)
            screen.blit(cancel_surf, (cancel_rect.centerx - cancel_surf.get_width()//2, cancel_rect.centery - cancel_surf.get_height()//2))
            
            pygame.display.flip()

#200
    @staticmethod
    def message_dialog(message):
        font = pygame.font.SysFont(None, 32)
        ok_rect = pygame.Rect(WIDTH//2 - 50, HEIGHT//2 + 30, 100, 40)
        waiting = True
        
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and ok_rect.collidepoint(event.pos):
                    waiting = False
            
            screen.fill(BACKGROUND)
            dialog_rect = pygame.Rect(WIDTH//2-250, HEIGHT//2-50, 500, 120)
            pygame.draw.rect(screen, DIALOG_BG, dialog_rect, border_radius=10)
            pygame.draw.rect(screen, GRID_COLOR, dialog_rect, 2, border_radius=10)
            
            msg_surf = font.render(message, True, DIALOG_TEXT)
            screen.blit(msg_surf, (WIDTH//2 - msg_surf.get_width()//2, HEIGHT//2-30))
            
            pygame.draw.rect(screen, (100, 200, 100), ok_rect, border_radius=5)
            pygame.draw.rect(screen, GRID_COLOR, ok_rect, 2, border_radius=5)
            ok_surf = font.render("OK", True, TEXT_COLOR)
            screen.blit(ok_surf, (ok_rect.centerx - ok_surf.get_width()//2, ok_rect.centery - ok_surf.get_height()//2))
            
            pygame.display.flip()

#210
class Pattern:
    def __init__(self, name, rows=GRID_ROWS, cols=DEFAULT_COLS):
        self.name = name
        self.rows = rows
        self.cols = cols
        self.layers = {i: set() for i in range(len(INSTRUMENTS))}
    
    def toggle_note(self, instrument_id, row, col):
        if (row, col) in self.layers[instrument_id]:
            self.layers[instrument_id].remove((row, col))
            return False
        else:
            self.layers[instrument_id].add((row, col))
            return True
    
    def has_note(self, instrument_id, row, col):
        return (row, col) in self.layers[instrument_id]
    
    def clear_layer(self, instrument_id):
        self.layers[instrument_id] = set()
    
    def clear_all(self):
        for i in range(len(INSTRUMENTS)):
            self.layers[i] = set()
    
    def get_active_notes_count(self):
        return {i: len(self.layers[i]) for i in range(len(INSTRUMENTS))}
    
    def resize_cols(self, new_cols):
        if new_cols < 1:
            return
        for i in range(len(INSTRUMENTS)):
            self.layers[i] = {(r, c) for r, c in self.layers[i] if c < new_cols}
        self.cols = new_cols

#220
def save_pattern(sequencer, filename):
    if not filename.endswith('.json'):
        filename += '.json'
    
    filepath = os.path.join(SAVE_PATH, filename)
    if os.path.exists(filepath):
        timestamp = datetime.now().strftime("_%Y%m%d_%H%M%S")
        base_name = filename.replace('.json', '')
        filename = f"{base_name}{timestamp}.json"
        filepath = os.path.join(SAVE_PATH, filename)
    
    data = {
        "version": "compact_v3",
        "created": datetime.now().isoformat(),
        "bpm": bpm,
        "current_instrument": sequencer.current_instrument,
        "current_pattern_index": sequencer.current_pattern_index,
        "grid_settings": {
            "rows": GRID_ROWS,
            "cell_width": cell_width,
            "cell_height": cell_height,
            "grid_cols": grid_cols
        },
        "patterns": []
    }
    
    for pattern in sequencer.patterns:
        pattern_data = {
            "name": pattern.name,
            "cols": pattern.cols,
            "notes": {}
        }
        
        for i in range(len(INSTRUMENTS)):
            if pattern.layers[i]:
                notes_list = [f"{row},{col}" for row, col in pattern.layers[i]]
                pattern_data["notes"][str(i)] = notes_list
        
        data["patterns"].append(pattern_data)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        TouchDialog.message_dialog(f"{words[13]}: {filename}")
        return True
    except Exception as e:
        TouchDialog.message_dialog(f"words[19]: {str(e)}")
        return False

#230
def load_pattern(sequencer, filename):
    global grid_cols, cell_width, cell_height
    
    if not filename.endswith('.json'):
        filename += '.json'
    
    filepath = os.path.join(SAVE_PATH, filename)
    if not os.path.exists(filepath):
        TouchDialog.message_dialog(words[18])
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        version = data.get("version", "unknown")
        
        if version == "compact_v3":
            if "grid_settings" in data:
                grid_cols = data["grid_settings"].get("grid_cols", DEFAULT_COLS)
                cell_width = data["grid_settings"].get("cell_width", DEFAULT_CELL_WIDTH)
                cell_height = data["grid_settings"].get("cell_height", DEFAULT_CELL_HEIGHT)
            
            sequencer.patterns = []
            
            for pattern_data in data["patterns"]:
                pattern = Pattern(pattern_data["name"], GRID_ROWS, pattern_data.get("cols", DEFAULT_COLS))
                
                if "notes" in pattern_data:
                    for inst_str, notes_list in pattern_data["notes"].items():
                        instrument_id = int(inst_str)
                        for note_str in notes_list:
                            try:
                                row_str, col_str = note_str.split(",")
                                row, col = int(row_str), int(col_str)
                                if 0 <= row < GRID_ROWS and 0 <= col < pattern.cols:
                                    pattern.layers[instrument_id].add((row, col))
                            except:
                                continue
                
                sequencer.patterns.append(pattern)
            
            sequencer.current_pattern_index = data.get("current_pattern_index", 0)
            sequencer.current_instrument = data.get("current_instrument", 0)
            
        elif version in ["multipattern_v2", "multilayer_v1"]:
            TouchDialog.message_dialog(words[17])
            
            if version == "multipattern_v2":
                patterns_data = data["patterns"]
            else:
                patterns_data = [{
                    "name": "Импортированный", 
                    "rows": GRID_ROWS, 
                    "cols": DEFAULT_COLS, 
                    "layers": data["layers"]
                }]
            
            sequencer.patterns = []
            for pattern_data in patterns_data:
                pattern = Pattern(pattern_data["name"], GRID_ROWS, pattern_data.get("cols", DEFAULT_COLS))
                
                if "layers" in pattern_data:
                    for inst_str, layer_data in pattern_data["layers"].items():
                        instrument_id = int(inst_str)
                        for row in range(min(len(layer_data), GRID_ROWS)):
                            for col in range(min(len(layer_data[row]), pattern.cols)):
                                if layer_data[row][col]:
                                    pattern.layers[instrument_id].add((row, col))
                
                sequencer.patterns.append(pattern)
            
            sequencer.current_pattern_index = data.get("current_pattern_index", 0)
            sequencer.current_instrument = data.get("current_instrument", 0)
        
        else:
            TouchDialog.message_dialog(words[20])
            return False
        
        sequencer.current_step = 0
        TouchDialog.message_dialog(f"{words[22]}: {filename}")
        return True
        
    except Exception as e:
        TouchDialog.message_dialog(f"{words[19]}: {str(e)}")
        return False

#240
class MultiPatternSequencer:
    def __init__(self):
        self.patterns = [Pattern(f"{words[21]} 1")]
        self.current_pattern_index = 0
        self.is_playing = False
        self.current_step = 0
        self.last_step_time = 0
        self.current_instrument = 0
        self.current_wave_samples = []
        self.hovered_cell = None
        self.current_filename = ""
    
    @property
    def current_pattern(self):
        return self.patterns[self.current_pattern_index]
    
    def add_pattern(self):
        new_index = len(self.patterns)
        self.patterns.append(Pattern(f"{words[21]} {new_index + 1}", GRID_ROWS, grid_cols))
        return new_index
    
    def delete_pattern(self, index):
        if len(self.patterns) > 1 and 0 <= index < len(self.patterns):
            self.patterns.pop(index)
            if self.current_pattern_index >= len(self.patterns):
                self.current_pattern_index = len(self.patterns) - 1
            return True
        return False
    
    def switch_pattern(self, index):
        if 0 <= index < len(self.patterns):
            self.current_pattern_index = index
            if self.current_step >= self.current_pattern.cols:
                self.current_step = 0
            return True
        return False
    
    def toggle_cell(self, row, col):
        pattern = self.current_pattern
        if 0 <= row < pattern.rows and 0 <= col < pattern.cols:
            if pattern.toggle_note(self.current_instrument, row, col):
                self.play_note_direct(row, self.current_instrument)
    
    def play_step(self):
        if not self.is_playing:
            return
        
        current_time = time.time()
        if current_time - self.last_step_time >= step_duration:
            pattern = self.current_pattern
            
            if self.current_step >= pattern.cols:
                self.current_step = 0
            
            for instrument_id in range(len(INSTRUMENTS)):
                for row in range(pattern.rows):
                    if pattern.has_note(instrument_id, row, self.current_step):
                        self.play_note_direct(row, instrument_id)
            
            self.generate_current_wave()
            
            self.current_step += 1
            if self.current_step >= pattern.cols:
                self.current_step = 0
                next_pattern = (self.current_pattern_index + 1) % len(self.patterns)
                self.switch_pattern(next_pattern)
            
            self.last_step_time = current_time
    
    def play_note_direct(self, note_row, instrument_id):
        note_row = int(note_row)
        freq = NOTES[note_row][1]
        samples = SOUND_GENERATORS[instrument_id](freq, step_duration * 2, sample_rate, volume)
        
        if AUDIO_ENABLED:
            try:
                sound = pygame.mixer.Sound(buffer=samples)
                sound.play()
            except:
                pass
    
    def generate_current_wave(self):
        pattern = self.current_pattern
        total_samples = int(sample_rate * step_duration)
        mixed_samples = array.array('h', (0 for _ in range(total_samples)))
        
        for instrument_id in range(len(INSTRUMENTS)):
            for row in range(pattern.rows):
                if pattern.has_note(instrument_id, row, self.current_step):
                    freq = NOTES[row][1]
                    note_samples = SOUND_GENERATORS[instrument_id](freq, step_duration, sample_rate, volume * 0.2)
                    for i in range(min(len(mixed_samples), len(note_samples))):
                        mixed_samples[i] = max(-32767, min(32767, mixed_samples[i] + note_samples[i]))
        
        self.current_wave_samples = mixed_samples
    
    def start_stop(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.last_step_time = time.time()
        elif AUDIO_ENABLED:
            try:
                pygame.mixer.stop()
            except:
                pass
    
    def set_instrument(self, instrument_index):
        if 0 <= instrument_index < len(INSTRUMENTS):
            self.current_instrument = instrument_index
    
    def clear_all_patterns(self):
        for pattern in self.patterns:
            pattern.clear_all()
        self.current_filename = ""
        if AUDIO_ENABLED:
            try:
                pygame.mixer.stop()
            except:
                pass
    
    def clear_current_pattern(self):
        self.current_pattern.clear_all()
        if AUDIO_ENABLED:
            try:
                pygame.mixer.stop()
            except:
                pass
    
    def get_active_notes_count(self):
        return self.current_pattern.get_active_notes_count()

#250
sequencer = MultiPatternSequencer()

#260
def draw_control_panel(screen):
    panel_rect = pygame.Rect(GRID_START_X, 10, WIDTH - GRID_START_X - 10 - SCROLLBAR_WIDTH - ZOOM_PANEL_WIDTH, CONTROL_PANEL_HEIGHT)
    pygame.draw.rect(screen, INSTRUMENT_PANEL, panel_rect, border_radius=8)
    pygame.draw.rect(screen, GRID_COLOR, panel_rect, 2, border_radius=8)
    
    font = pygame.font.SysFont(None, 24)
    small_font = pygame.font.SysFont(None, 20)
    
    play_stop_rect = pygame.Rect(panel_rect.x + 20, panel_rect.y + 15, 120, 50)
    color = (0, 200, 100) if sequencer.is_playing else (200, 100, 0)
    pygame.draw.rect(screen, color, play_stop_rect, border_radius=5)
    pygame.draw.rect(screen, GRID_COLOR, play_stop_rect, 2, border_radius=5)
    
    status_text = words[23] if sequencer.is_playing else words[24]
    text_surf = font.render(status_text, True, TEXT_COLOR)
    screen.blit(text_surf, (play_stop_rect.centerx - text_surf.get_width()//2, play_stop_rect.centery - text_surf.get_height()//2))
    
    prev_pattern_rect = pygame.Rect(play_stop_rect.right + 20, panel_rect.y + 15, 50, 50)
    next_pattern_rect = pygame.Rect(prev_pattern_rect.right + 10, panel_rect.y + 15, 50, 50)
    
    pygame.draw.rect(screen, BUTTON_COLOR, prev_pattern_rect, border_radius=5)
    pygame.draw.rect(screen, GRID_COLOR, prev_pattern_rect, 2, border_radius=5)
    prev_surf = font.render("<", True, TEXT_COLOR)
    screen.blit(prev_surf, (prev_pattern_rect.centerx - prev_surf.get_width()//2, prev_pattern_rect.centery - prev_surf.get_height()//2))
    
    pygame.draw.rect(screen, BUTTON_COLOR, next_pattern_rect, border_radius=5)
    pygame.draw.rect(screen, GRID_COLOR, next_pattern_rect, 2, border_radius=5)
    next_surf = font.render(">", True, TEXT_COLOR)
    screen.blit(next_surf, (next_pattern_rect.centerx - next_surf.get_width()//2, next_pattern_rect.centery - next_surf.get_height()//2))
    
    cols_dec_rect = pygame.Rect(next_pattern_rect.right + 30, panel_rect.y + 15, 40, 40)
    cols_inc_rect = pygame.Rect(cols_dec_rect.right + 10, panel_rect.y + 15, 40, 40)
    cols_label_rect = pygame.Rect(cols_inc_rect.right + 10, panel_rect.y + 15, 80, 40)
    
    pygame.draw.rect(screen, BUTTON_COLOR, cols_dec_rect, border_radius=5)
    pygame.draw.rect(screen, GRID_COLOR, cols_dec_rect, 2, border_radius=5)
    cols_dec_surf = font.render("-", True, TEXT_COLOR)
    screen.blit(cols_dec_surf, (cols_dec_rect.centerx - cols_dec_surf.get_width()//2, cols_dec_rect.centery - cols_dec_surf.get_height()//2))
    
    pygame.draw.rect(screen, BUTTON_COLOR, cols_inc_rect, border_radius=5)
    pygame.draw.rect(screen, GRID_COLOR, cols_inc_rect, 2, border_radius=5)
    cols_inc_surf = font.render("+", True, TEXT_COLOR)
    screen.blit(cols_inc_surf, (cols_inc_rect.centerx - cols_inc_surf.get_width()//2, cols_inc_rect.centery - cols_inc_surf.get_height()//2))
    
    pygame.draw.rect(screen, (60, 60, 80), cols_label_rect, border_radius=5)
    pygame.draw.rect(screen, GRID_COLOR, cols_label_rect, 2, border_radius=5)
    cols_text = f"{words[25]}: {grid_cols}"
    cols_surf = small_font.render(cols_text, True, TEXT_COLOR)
    screen.blit(cols_surf, (cols_label_rect.centerx - cols_surf.get_width()//2, cols_label_rect.centery - cols_surf.get_height()//2))
    
    cell_width_dec_rect = pygame.Rect(cols_label_rect.right + 20, panel_rect.y + 15, 40, 40)
    cell_width_inc_rect = pygame.Rect(cell_width_dec_rect.right + 10, panel_rect.y + 15, 40, 40)
    cell_width_label_rect = pygame.Rect(cell_width_inc_rect.right + 10, panel_rect.y + 15, 100, 40)
    
    pygame.draw.rect(screen, BUTTON_COLOR, cell_width_dec_rect, border_radius=5)
    pygame.draw.rect(screen, GRID_COLOR, cell_width_dec_rect, 2, border_radius=5)
    cell_width_dec_surf = font.render("-", True, TEXT_COLOR)
    screen.blit(cell_width_dec_surf, (cell_width_dec_rect.centerx - cell_width_dec_surf.get_width()//2, cell_width_dec_rect.centery - cell_width_dec_surf.get_height()//2))
    
    pygame.draw.rect(screen, BUTTON_COLOR, cell_width_inc_rect, border_radius=5)
    pygame.draw.rect(screen, GRID_COLOR, cell_width_inc_rect, 2, border_radius=5)
    cell_width_inc_surf = font.render("+", True, TEXT_COLOR)
    screen.blit(cell_width_inc_surf, (cell_width_inc_rect.centerx - cell_width_inc_surf.get_width()//2, cell_width_inc_rect.centery - cell_width_inc_surf.get_height()//2))
    
    pygame.draw.rect(screen, (60, 60, 80), cell_width_label_rect, border_radius=5)
    pygame.draw.rect(screen, GRID_COLOR, cell_width_label_rect, 2, border_radius=5)
    cell_width_text = f"{words[26]}: {cell_width}px"
    cell_width_surf = small_font.render(cell_width_text, True, TEXT_COLOR)
    screen.blit(cell_width_surf, (cell_width_label_rect.centerx - cell_width_surf.get_width()//2, cell_width_label_rect.centery - cell_width_surf.get_height()//2))
    
    cell_height_dec_rect = pygame.Rect(cell_width_label_rect.right + 20, panel_rect.y + 15, 40, 40)
    cell_height_inc_rect = pygame.Rect(cell_height_dec_rect.right + 10, panel_rect.y + 15, 40, 40)
    cell_height_label_rect = pygame.Rect(cell_height_inc_rect.right + 10, panel_rect.y + 15, 100, 40)
    
    pygame.draw.rect(screen, BUTTON_COLOR, cell_height_dec_rect, border_radius=5)
    pygame.draw.rect(screen, GRID_COLOR, cell_height_dec_rect, 2, border_radius=5)
    cell_height_dec_surf = font.render("-", True, TEXT_COLOR)
    screen.blit(cell_height_dec_surf, (cell_height_dec_rect.centerx - cell_height_dec_surf.get_width()//2, cell_height_dec_rect.centery - cell_height_dec_surf.get_height()//2))
    
    pygame.draw.rect(screen, BUTTON_COLOR, cell_height_inc_rect, border_radius=5)
    pygame.draw.rect(screen, GRID_COLOR, cell_height_inc_rect, 2, border_radius=5)
    cell_height_inc_surf = font.render("+", True, TEXT_COLOR)
    screen.blit(cell_height_inc_surf, (cell_height_inc_rect.centerx - cell_height_inc_surf.get_width()//2, cell_height_inc_rect.centery - cell_height_inc_surf.get_height()//2))
    
    pygame.draw.rect(screen, (60, 60, 80), cell_height_label_rect, border_radius=5)
    pygame.draw.rect(screen, GRID_COLOR, cell_height_label_rect, 2, border_radius=5)
    cell_height_text = f"{words[27]}: {cell_height}px"
    cell_height_surf = small_font.render(cell_height_text, True, TEXT_COLOR)
    screen.blit(cell_height_surf, (cell_height_label_rect.centerx - cell_height_surf.get_width()//2, cell_height_label_rect.centery - cell_height_surf.get_height()//2))
    
    pattern = sequencer.current_pattern
    pattern_text = f"{pattern.name} ({sequencer.current_pattern_index + 1}/{len(sequencer.patterns)})"
    pattern_surf = small_font.render(pattern_text, True, TEXT_COLOR)
    screen.blit(pattern_surf, (panel_rect.x + 20, panel_rect.y + 70))
    
    info_text = f"{words[29]}: {sequencer.current_step + 1}/{pattern.cols} | BPM: {bpm}"
    info_surf = small_font.render(info_text, True, TEXT_COLOR)
    screen.blit(info_surf, (panel_rect.x + 250, panel_rect.y + 70))
    
    instrument_text = f"{words[30]}: {INSTRUMENTS[sequencer.current_instrument]}"
    instrument_surf = small_font.render(instrument_text, True, TEXT_COLOR)
    screen.blit(instrument_surf, (panel_rect.x + 450, panel_rect.y + 70))
    
    return (play_stop_rect, prev_pattern_rect, next_pattern_rect, 
            cols_dec_rect, cols_inc_rect, cell_width_dec_rect, cell_width_inc_rect,
            cell_height_dec_rect, cell_height_inc_rect)

#270
def draw_pattern_panel(screen):
    panel_rect = pygame.Rect(10, HEIGHT - PATTERN_PANEL_HEIGHT - (-10) - SCROLLBAR_WIDTH, WIDTH - 20 - SCROLLBAR_WIDTH - ZOOM_PANEL_WIDTH, PATTERN_PANEL_HEIGHT)
    pygame.draw.rect(screen, INSTRUMENT_PANEL, panel_rect, border_radius=8)
    pygame.draw.rect(screen, GRID_COLOR, panel_rect, 2, border_radius=8)
    
    font = pygame.font.SysFont(None, 24)
    title = font.render(f"{words[21]}{words[28]}", True, TEXT_COLOR)
    screen.blit(title, (panel_rect.x + 10, panel_rect.y + 10))
    
    pattern_width = 100
    pattern_spacing = 10
    start_x = 150
    
    pattern_rects = []
    for i, pattern in enumerate(sequencer.patterns):
        pattern_rect = pygame.Rect(start_x + i * (pattern_width + pattern_spacing), 
                                 panel_rect.y + 10, pattern_width, 40)
        pattern_rects.append(pattern_rect)
        
        color = PATTERN_ACTIVE if i == sequencer.current_pattern_index else PATTERN_INACTIVE
        pygame.draw.rect(screen, color, pattern_rect, border_radius=5)
        pygame.draw.rect(screen, GRID_COLOR, pattern_rect, 2, border_radius=5)
        
        pattern_font = pygame.font.SysFont(None, 20)
        name_text = pattern_font.render(pattern.name, True, TEXT_COLOR)
        screen.blit(name_text, (pattern_rect.x + 5, pattern_rect.y + 5))
        
        active_count = sum(len(pattern.layers[inst]) for inst in range(len(INSTRUMENTS)))
        count_text = pattern_font.render(f"{active_count} {words[31]}", True, (150, 150, 150))
        screen.blit(count_text, (pattern_rect.x + 5, pattern_rect.y + 22))
    
    add_rect = pygame.Rect(50, 
                          panel_rect.y -90, 40, 40)
    pygame.draw.rect(screen, (50, 150, 50), add_rect, border_radius=5) #тут
    pygame.draw.rect(screen, GRID_COLOR, add_rect, 2, border_radius=5)
    
    add_font = pygame.font.SysFont(None, 30)
    add_text = add_font.render("+", True, TEXT_COLOR)
    screen.blit(add_text, (50+15, add_rect.y + 8))
    
    del_rect = None
    if len(sequencer.patterns) > 1:
        del_rect = pygame.Rect(add_rect.x + 50, panel_rect.y -90, 40, 40)
        pygame.draw.rect(screen, (150, 50, 50), del_rect, border_radius=5)
        pygame.draw.rect(screen, GRID_COLOR, del_rect, 2, border_radius=5)
        
        del_font = pygame.font.SysFont(None, 30)
        del_text = del_font.render("-", True, TEXT_COLOR)
        screen.blit(del_text, (del_rect.x + 15, del_rect.y +10))
    
    return pattern_rects, add_rect, del_rect

#280
def draw_instrument_panel(screen):
    panel_height = HEIGHT - PATTERN_PANEL_HEIGHT - CONTROL_PANEL_HEIGHT - 40 - SCROLLBAR_WIDTH
    pygame.draw.rect(screen, INSTRUMENT_PANEL, (10, CONTROL_PANEL_HEIGHT + 20, INSTRUMENT_PANEL_WIDTH, panel_height))
    pygame.draw.rect(screen, GRID_COLOR, (10, CONTROL_PANEL_HEIGHT + 20, INSTRUMENT_PANEL_WIDTH, panel_height), 2)
    
    font = pygame.font.SysFont(None, 24)
    screen.blit(font.render(words[30], True, TEXT_COLOR), (20, CONTROL_PANEL_HEIGHT + 30))
    
    note_counts = sequencer.get_active_notes_count()
    
    instrument_rects = []
    for i, instrument in enumerate(INSTRUMENTS):
        y = CONTROL_PANEL_HEIGHT + 70 + i * (INSTRUMENT_BUTTON_HEIGHT + 5)
        instrument_rect = pygame.Rect(20, y, INSTRUMENT_PANEL_WIDTH - 20, INSTRUMENT_BUTTON_HEIGHT)
        instrument_rects.append(instrument_rect)
        
        color = INSTRUMENT_SELECTED if i == sequencer.current_instrument else INSTRUMENT_PANEL
        
        pygame.draw.rect(screen, color, instrument_rect, border_radius=5)
        pygame.draw.rect(screen, GRID_COLOR, instrument_rect, 2, border_radius=5)
        
        pygame.draw.rect(screen, INSTRUMENT_COLORS[i], (25, y + 5, 10, INSTRUMENT_BUTTON_HEIGHT - 10), border_radius=2)
        screen.blit(font.render(instrument, True, TEXT_COLOR), (40, y + 10))
        screen.blit(pygame.font.SysFont(None, 18).render(f"({note_counts[i]})", True, (150, 150, 150)), (40, y + 28))
    
    file_y = CONTROL_PANEL_HEIGHT + 70 + len(INSTRUMENTS) * (INSTRUMENT_BUTTON_HEIGHT + 5) + 20
    
    save_rect = pygame.Rect(20, file_y, INSTRUMENT_PANEL_WIDTH - 20, 35)
    load_rect = pygame.Rect(20, file_y + 45, INSTRUMENT_PANEL_WIDTH - 20, 35)
    clear_pattern_rect = pygame.Rect(20, file_y + 90, INSTRUMENT_PANEL_WIDTH - 20, 30)
    clear_all_rect = pygame.Rect(20, file_y + 130, INSTRUMENT_PANEL_WIDTH - 20, 30)
    
    buttons = [
        (save_rect, (50, 150, 200), words[32]),
        (load_rect, (150, 100, 200), words[33]),
        (clear_pattern_rect, (200, 100, 50), words[34]),
        (clear_all_rect, (200, 50, 50), words[35])
    ]
    
    for rect, color, text in buttons:
        pygame.draw.rect(screen, color, rect, border_radius=5)
        btn_font = pygame.font.SysFont(None, 18 if rect.height == 30 else 20)
        text_surf = btn_font.render(text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)
    
    return instrument_rects, save_rect, load_rect, clear_pattern_rect, clear_all_rect

#290
def draw_grid(screen):
    pattern = sequencer.current_pattern
    black_notes_indices = [1, 3, 6, 8, 10]
    
    # Вычисляем видимую область с учетом прокрутки
    visible_width = WIDTH - GRID_START_X - SCROLLBAR_WIDTH - ZOOM_PANEL_WIDTH
    visible_height = HEIGHT - GRID_START_Y - PATTERN_PANEL_HEIGHT - SCROLLBAR_WIDTH - 20
    
    # Ограничиваем прокрутку
    global scroll_x, scroll_y, max_scroll_x, max_scroll_y
    max_scroll_x = max(0, pattern.cols * (cell_width + 1) - visible_width)
    max_scroll_y = max(0, pattern.rows * (cell_height + 1) - visible_height)
    scroll_x = max(0, min(scroll_x, max_scroll_x))
    scroll_y = max(0, min(scroll_y, max_scroll_y))
    
    # Создаем поверхность для сетки
    grid_surface = pygame.Surface((pattern.cols * (cell_width + 1), pattern.rows * (cell_height + 1)))
    grid_surface.fill(BACKGROUND)
    
    # Рисуем сетку на поверхности
    for row in range(pattern.rows):
        is_black_note = (row % 12) in black_notes_indices
        base_color = (30, 30, 40) if is_black_note else CELL_EMPTY
        
        for col in range(pattern.cols):
            x = col * (cell_width + 1)
            y = row * (cell_height + 1)
            
            active_instruments = [i for i in range(len(INSTRUMENTS)) if pattern.has_note(i, row, col)]
            
            if active_instruments:
                main_instrument = active_instruments[0]
                color = INSTRUMENT_COLORS[main_instrument]
                if sequencer.current_instrument in active_instruments:
                    color = INSTRUMENT_COLORS[sequencer.current_instrument]
            elif sequencer.current_step == col and sequencer.is_playing:
                color = CURRENT_STEP
            else:
                color = base_color
            
            pygame.draw.rect(grid_surface, color, (x, y, cell_width, cell_height), border_radius=2)
            pygame.draw.rect(grid_surface, GRID_COLOR, (x, y, cell_width, cell_height), 1, border_radius=2)
            if len(active_instruments) > 1:
                for i, instrument_id in enumerate(active_instruments[:4]):
                    if instrument_id == (sequencer.current_instrument if sequencer.current_instrument in active_instruments else main_instrument):
                        continue
                        
                    size = 4
                    ind_x = x + 2 + (i % 2) * (size + 1)
                    ind_y = y + 2 + (i // 2) * (size + 1)
                    indicator_color = INSTRUMENT_COLORS[instrument_id]
                    pygame.draw.rect(grid_surface, indicator_color, (ind_x, ind_y, size, size))
    for octave_line in [12, 24, 36]:
        line_y = octave_line * (cell_height + 1)
        line_end_x = pattern.cols * (cell_width + 1)
        pygame.draw.line(grid_surface, (100, 100, 120), (0, line_y), (line_end_x, line_y), 2)
    font = pygame.font.SysFont(None, 16)
    for row in range(pattern.rows):
        y = row * (cell_height + 1) + cell_height // 2
        note_name = NOTES[row][0]
        color = TEXT_COLOR if '#' not in note_name else (180, 180, 180)
        note_surf = font.render(note_name, True, color)
        grid_surface.blit(note_surf, (5, y - 8))
    screen.blit(grid_surface, (GRID_START_X, GRID_START_Y), 
                (scroll_x, scroll_y, visible_width, visible_height))
    small_font = pygame.font.SysFont(None, 18)
    for col in range(pattern.cols):
        x = GRID_START_X + col * (cell_width + 1) + cell_width // 2 - scroll_x
        if x >= GRID_START_X and x <= GRID_START_X + visible_width:
            text = small_font.render(str(col + 1), True, TEXT_COLOR)
            screen.blit(text, text.get_rect(center=(x, GRID_START_Y - 15)))
#300
def draw_scrollbars(screen):
    visible_width = WIDTH - GRID_START_X - SCROLLBAR_WIDTH - ZOOM_PANEL_WIDTH
    visible_height = HEIGHT - GRID_START_Y - PATTERN_PANEL_HEIGHT - SCROLLBAR_WIDTH - 20
    
    pattern = sequencer.current_pattern
    
    h_scroll_rect = pygame.Rect(GRID_START_X, HEIGHT - SCROLLBAR_WIDTH - PATTERN_PANEL_HEIGHT - 10, 
                               visible_width, SCROLLBAR_WIDTH)
    pygame.draw.rect(screen, SCROLLBAR_COLOR, h_scroll_rect)
    
    h_handle_rect = None
    if max_scroll_x > 0:
        h_handle_width = max(50, (h_scroll_rect.width * visible_width) / 
                            (pattern.cols * (cell_width + 1)))
        h_handle_x = GRID_START_X + (scroll_x / max_scroll_x) * (h_scroll_rect.width - h_handle_width)
        h_handle_rect = pygame.Rect(h_handle_x, HEIGHT - SCROLLBAR_WIDTH - PATTERN_PANEL_HEIGHT - 10, 
                                   h_handle_width, SCROLLBAR_WIDTH)
        pygame.draw.rect(screen, SCROLLBAR_HANDLE, h_handle_rect, border_radius=5)
    v_scroll_rect = pygame.Rect(WIDTH - SCROLLBAR_WIDTH - ZOOM_PANEL_WIDTH, GRID_START_Y, 
                               SCROLLBAR_WIDTH, visible_height)
    pygame.draw.rect(screen, SCROLLBAR_COLOR, v_scroll_rect)
    
    v_handle_rect = None
    if max_scroll_y > 0:
        v_handle_height = max(50, (v_scroll_rect.height * visible_height) / 
                             (pattern.rows * (cell_height + 1)))
        v_handle_y = GRID_START_Y + (scroll_y / max_scroll_y) * (v_scroll_rect.height - v_handle_height)
        v_handle_rect = pygame.Rect(WIDTH - SCROLLBAR_WIDTH - ZOOM_PANEL_WIDTH, v_handle_y, 
                                   SCROLLBAR_WIDTH, v_handle_height)
        pygame.draw.rect(screen, SCROLLBAR_HANDLE, v_handle_rect, border_radius=5)
    
    return h_scroll_rect, v_scroll_rect, h_handle_rect, v_handle_rect

#310
def draw_zoom_panel(screen):
    zoom_panel_rect = pygame.Rect(WIDTH - ZOOM_PANEL_WIDTH, GRID_START_Y, ZOOM_PANEL_WIDTH, 
                                 HEIGHT - GRID_START_Y - PATTERN_PANEL_HEIGHT - SCROLLBAR_WIDTH - 20)
    pygame.draw.rect(screen, INSTRUMENT_PANEL, zoom_panel_rect)
    pygame.draw.rect(screen, GRID_COLOR, zoom_panel_rect, 2)
    
    zoom_in_rect = pygame.Rect(WIDTH - ZOOM_PANEL_WIDTH + 5, GRID_START_Y + 20, ZOOM_PANEL_WIDTH - 10, 40)
    zoom_out_rect = pygame.Rect(WIDTH - ZOOM_PANEL_WIDTH + 5, GRID_START_Y + 70, ZOOM_PANEL_WIDTH - 10, 40)
    
    pygame.draw.rect(screen, ZOOM_BUTTON_COLOR, zoom_in_rect, border_radius=5)
    pygame.draw.rect(screen, GRID_COLOR, zoom_in_rect, 2, border_radius=5)
    
    pygame.draw.rect(screen, ZOOM_BUTTON_COLOR, zoom_out_rect, border_radius=5)
    pygame.draw.rect(screen, GRID_COLOR, zoom_out_rect, 2, border_radius=5)
    
    font = pygame.font.SysFont(None, 30)
    zoom_in_text = font.render("+", True, TEXT_COLOR)
    zoom_out_text = font.render("-", True, TEXT_COLOR)
    
    screen.blit(zoom_in_text, (zoom_in_rect.centerx - zoom_in_text.get_width()//2, 
                              zoom_in_rect.centery - zoom_in_text.get_height()//2))
    screen.blit(zoom_out_text, (zoom_out_rect.centerx - zoom_out_text.get_width()//2, 
                               zoom_out_rect.centery - zoom_out_text.get_height()//2))
    
    #масштаб
    zoom_text = pygame.font.SysFont(None, 16).render(f"{cell_width}px", True, TEXT_COLOR)
    screen.blit(zoom_text, (WIDTH - ZOOM_PANEL_WIDTH + 10, GRID_START_Y + 120))
    
    return zoom_in_rect, zoom_out_rect

#320
def draw_wave_visualization(screen):
    if not sequencer.current_wave_samples:
        return
    
    wave_y = HEIGHT - (-80) - SCROLLBAR_WIDTH
    wave_h = 60
    wave_w = WIDTH - GRID_START_X - SCROLLBAR_WIDTH - ZOOM_PANEL_WIDTH - 40
    wave_x = GRID_START_X
    
    pygame.draw.rect(screen, (30, 30, 45), (wave_x, wave_y, wave_w, wave_h))
    pygame.draw.rect(screen, GRID_COLOR, (wave_x, wave_y, wave_w, wave_h), 2)
    
    center_y = wave_y + wave_h // 2
    pygame.draw.line(screen, (60, 60, 80), (wave_x, center_y), (wave_x + wave_w, center_y), 1)
    
    if len(sequencer.current_wave_samples) > 1:
        points = []
        step = max(1, len(sequencer.current_wave_samples) // wave_w)
        for i in range(0, min(len(sequencer.current_wave_samples), wave_w * step), step):
            x = wave_x + (i // step)
            y = center_y - (sequencer.current_wave_samples[i] / 32768) * (wave_h // 2 - 5)
            points.append((x, y))
        if points:
            pygame.draw.lines(screen, WAVE_COLOR, False, points, 2)

#330
def handle_click(pos):
    global cell_width, grid_cols, cell_height, scroll_x, scroll_y, dragging_horizontal, dragging_vertical, drag_offset_x, drag_offset_y
    
    x, y = pos
    
    pattern = sequencer.current_pattern
    visible_width = WIDTH - GRID_START_X - SCROLLBAR_WIDTH - ZOOM_PANEL_WIDTH
    visible_height = HEIGHT - GRID_START_Y - PATTERN_PANEL_HEIGHT - SCROLLBAR_WIDTH - 20
    
    max_scroll_x = max(0, pattern.cols * (cell_width + 1) - visible_width)
    max_scroll_y = max(0, pattern.rows * (cell_height + 1) - visible_height)
    scroll_x = max(0, min(scroll_x, max_scroll_x))
    scroll_y = max(0, min(scroll_y, max_scroll_y))
    
    h_scroll_rect, v_scroll_rect, h_handle_rect, v_handle_rect = draw_scrollbars(screen)
    
    if h_handle_rect and h_handle_rect.collidepoint(pos):
        dragging_horizontal = True
        drag_offset_x = x - h_handle_rect.x
        return
    
    if v_handle_rect and v_handle_rect.collidepoint(pos):
        dragging_vertical = True
        drag_offset_y = y - v_handle_rect.y
        return
    
    if h_scroll_rect.collidepoint(pos) and max_scroll_x > 0:
        rel_x = x - h_scroll_rect.x
        scroll_x = (rel_x / h_scroll_rect.width) * max_scroll_x
        dragging_horizontal = True
        drag_offset_x = 0
        return
    
    if v_scroll_rect.collidepoint(pos) and max_scroll_y > 0:
        rel_y = y - v_scroll_rect.y
        scroll_y = (rel_y / v_scroll_rect.height) * max_scroll_y
        dragging_vertical = True
        drag_offset_y = 0
        return
    zoom_in_rect, zoom_out_rect = draw_zoom_panel(screen)
    
    if zoom_in_rect.collidepoint(pos) and cell_width < MAX_CELL_WIDTH:
        cell_width += 2  
        return
    
    if zoom_out_rect.collidepoint(pos) and cell_width > MIN_CELL_WIDTH:
        cell_width -= 2  
        return
        
    controls = draw_control_panel(screen)
    (play_stop_rect, prev_pattern_rect, next_pattern_rect, 
     cols_dec_rect, cols_inc_rect, cell_width_dec_rect, cell_width_inc_rect,
     cell_height_dec_rect, cell_height_inc_rect) = controls
    
    if play_stop_rect.collidepoint(pos):
        sequencer.start_stop()
        return
    elif prev_pattern_rect.collidepoint(pos):
        prev_pattern = (sequencer.current_pattern_index - 1) % len(sequencer.patterns)
        sequencer.switch_pattern(prev_pattern)
        return
    elif next_pattern_rect.collidepoint(pos):
        next_pattern = (sequencer.current_pattern_index + 1) % len(sequencer.patterns)
        sequencer.switch_pattern(next_pattern)
        return
    elif cols_dec_rect.collidepoint(pos) and grid_cols > MIN_COLS:
        grid_cols -= 1
        for pattern in sequencer.patterns:
            pattern.resize_cols(grid_cols)
        return
    elif cols_inc_rect.collidepoint(pos) and grid_cols < MAX_COLS:
        grid_cols += 1
        for pattern in sequencer.patterns:
            pattern.resize_cols(grid_cols)
        return
    elif cell_width_dec_rect.collidepoint(pos) and cell_width > MIN_CELL_WIDTH:
        cell_width -= 2 
        return
    elif cell_width_inc_rect.collidepoint(pos) and cell_width < MAX_CELL_WIDTH:
        cell_width += 2
        return
    elif cell_height_dec_rect.collidepoint(pos) and cell_height > MIN_CELL_HEIGHT:
        cell_height -= 2  
        return
    elif cell_height_inc_rect.collidepoint(pos) and cell_height < MAX_CELL_HEIGHT:
        cell_height += 2  
        return
    
    pattern_rects, add_rect, del_rect = draw_pattern_panel(screen)
    
    if add_rect.collidepoint(pos):
        new_index = sequencer.add_pattern()
        sequencer.switch_pattern(new_index)
        return
    elif del_rect and del_rect.collidepoint(pos):
        if sequencer.delete_pattern(sequencer.current_pattern_index):
            TouchDialog.message_dialog("Паттерн удален")
        return
    
    for i, pattern_rect in enumerate(pattern_rects):
        if pattern_rect.collidepoint(pos):
            sequencer.switch_pattern(i)
            return
    
    instrument_rects, save_rect, load_rect, clear_pattern_rect, clear_all_rect = draw_instrument_panel(screen)
    
    for i, instrument_rect in enumerate(instrument_rects):
        if instrument_rect.collidepoint(pos):
            sequencer.set_instrument(i)
            return
    
    if save_rect.collidepoint(pos):
        filename = TouchDialog.input_dialog(f"{words[16]}:", "mp")
        if filename and save_pattern(sequencer, filename):
            sequencer.current_filename = filename if filename.endswith('.json') else filename + '.json'
        return
    elif load_rect.collidepoint(pos):
        filename = TouchDialog.file_list_dialog()
        if filename and load_pattern(sequencer, filename):
            sequencer.current_filename = filename
        return
    elif clear_pattern_rect.collidepoint(pos):
        sequencer.clear_current_pattern()
        return
    elif clear_all_rect.collidepoint(pos):
        sequencer.clear_all_patterns()
        return
    if (GRID_START_X <= x <= GRID_START_X + visible_width and
        GRID_START_Y <= y <= GRID_START_Y + visible_height):
        col = int((x - GRID_START_X + scroll_x) // (cell_width + 1))
        row = int((y - GRID_START_Y + scroll_y) // (cell_height + 1))
        
        if 0 <= col < pattern.cols and 0 <= row < pattern.rows:
            sequencer.toggle_cell(row, col)

#340
def handle_mouse_motion(pos):
    global scroll_x, scroll_y, dragging_horizontal, dragging_vertical
    
    x, y = pos
    sequencer.hovered_cell = None
    
    #границы
    pattern = sequencer.current_pattern
    visible_width = WIDTH - GRID_START_X - SCROLLBAR_WIDTH - ZOOM_PANEL_WIDTH
    visible_height = HEIGHT - GRID_START_Y - PATTERN_PANEL_HEIGHT - SCROLLBAR_WIDTH - 20
    max_scroll_x = max(0, pattern.cols * (cell_width + 1) - visible_width)
    max_scroll_y = max(0, pattern.rows * (cell_height + 1) - visible_height)
    scroll_x = max(0, min(scroll_x, max_scroll_x))
    scroll_y = max(0, min(scroll_y, max_scroll_y))
    if dragging_horizontal:
        h_scroll_rect, _, _, _ = draw_scrollbars(screen)
        rel_x = x - h_scroll_rect.x
        scroll_x = max(0, min(max_scroll_x, (rel_x / h_scroll_rect.width) * max_scroll_x))
    
    if dragging_vertical:
        _, v_scroll_rect, _, _ = draw_scrollbars(screen)
        rel_y = y - v_scroll_rect.y
        scroll_y = max(0, min(max_scroll_y, (rel_y / v_scroll_rect.height) * max_scroll_y))
    
    if (GRID_START_X <= x <= GRID_START_X + visible_width and
        GRID_START_Y <= y <= GRID_START_Y + visible_height):
        col = int((x - GRID_START_X + scroll_x) // (cell_width + 1))
        row = int((y - GRID_START_Y + scroll_y) // (cell_height + 1))
        
        if 0 <= col < pattern.cols and 0 <= row < pattern.rows:
            sequencer.hovered_cell = (row, col)

#1260
def main():
    global dragging_horizontal, dragging_vertical
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    handle_click(event.pos)
                elif event.button == 4: 
                    global scroll_y
                    scroll_y = max(0, scroll_y - 50)
                elif event.button == 5:
                    scroll_y = min(max_scroll_y, scroll_y + 50)
            elif event.type == pygame.MOUSEMOTION:
                handle_mouse_motion(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    dragging_horizontal = False
                    dragging_vertical = False
        
        try:
            sequencer.play_step()
        except Exception as e:
            print(f"Ошибка: {e}")
            sequencer.current_step = 0
        
        screen.fill(BACKGROUND)
        
        draw_grid(screen)
        draw_control_panel(screen)
        draw_instrument_panel(screen)
        draw_pattern_panel(screen)
        draw_scrollbars(screen)
        draw_zoom_panel(screen)
        draw_wave_visualization(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

#1300
if __name__ == "__main__":
    main()