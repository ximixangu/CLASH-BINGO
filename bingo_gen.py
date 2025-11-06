CELL_TYPE_WEIGHTS = {
    'last_hit': 10,
    'duplicate': 10,
    'misc': 10,
    'triplet': 20,
    'win_condition': 5,
    'arena': 3,
    'elixir': 3,
}

TRIPLET_RANDOM_RATE = 0.3
WIN_CONDITION_RANDOM_RATE = 0.3
MODIFIERS_RANDOM_RATE = 1

from PIL import Image
from pathlib import Path
import random
import streamlit as st
from PIL import Image
import io

from data import TRIPLETS_LIST, WIN_CONDITIONS, DUPLICATES, EXCLUDED_CARDS

triplet_list = TRIPLETS_LIST.copy()
win_conditions = WIN_CONDITIONS.copy()
duplicates_list = DUPLICATES.copy()
last_img = None

CARDS_PATH = Path("assets/cards")
ASSETS_PATH = Path("assets")
MODIFIERS_PATH = ASSETS_PATH / "modifiers"
MISC_PATH = ASSETS_PATH / "misc"
ELIXIR_PATH = ASSETS_PATH / "elixir"

for path in [CARDS_PATH, ASSETS_PATH, MODIFIERS_PATH, MISC_PATH]:
    path.mkdir(parents=True, exist_ok=True)

files_misc = [f.name for f in MISC_PATH.glob("*.png")]
files_elixir = [f.name for f in ELIXIR_PATH.glob("*.png")]
last_hits = [f.name for f in CARDS_PATH.glob("*.png") if f.name not in EXCLUDED_CARDS]
arena_files = [f.name for f in (ASSETS_PATH / "arenas").glob("*.png")]

TRIPLET_POSITIONS = [(10, 70), (55, 0), (100, 70)]


def weighted_choice(choices):
    total = sum(choices.values())
    r = random.uniform(0, total)
    upto = 0
    for choice, weight in choices.items():
        if upto + weight >= r:
            return choice
        upto += weight
    return None


def load_and_paste(base_img, img_path, size, pos):
    if img_path.exists():
        img = Image.open(img_path)
        img.thumbnail(size)
        base_img.paste(img, pos, img)
    return base_img


def get_random_card(cards_path, exclude=None):
    all_cards = [f.name for f in cards_path.glob("*.png")]
    if exclude:
        all_cards = [c for c in all_cards if c not in exclude]
    return random.choice(all_cards) if all_cards else None


def create_cell_content(cell_type):
    global last_img
    img = Image.new('RGBA', (190, 190), (0, 0, 0, 0))

    all_cards = [f.name for f in CARDS_PATH.glob("*.png")]

    if cell_type == 'triplet':
        global triplet_list
        if triplet_list and random.random() > TRIPLET_RANDOM_RATE:
            triplet = random.choice(triplet_list)
            triplet_list.remove(triplet)
        else:
            triplet = random.sample(all_cards, min(3, len(all_cards)))

        for card_name, pos in zip(triplet, TRIPLET_POSITIONS):
            load_and_paste(img, CARDS_PATH / card_name, (120, 120), pos)

    elif cell_type == 'win_condition':
        global win_conditions
        card = None
        if win_conditions and random.random() > WIN_CONDITION_RANDOM_RATE:
            card = random.choice(win_conditions)
            win_conditions.remove(card)
        else:
            card = get_random_card(CARDS_PATH, exclude=EXCLUDED_CARDS)

        if card:
            load_and_paste(img, CARDS_PATH / card, (180, 180), (8, 0))
        load_and_paste(img, ASSETS_PATH / "aux/crown.png", (75, 75), (109, 124))

    elif cell_type == 'last_hit':
        global last_hits
        card = None
        card = random.choice(last_hits)
        try:
            last_hits.remove(card)
        except ValueError:
            pass

        if card:
            load_and_paste(img, CARDS_PATH / card, (180, 180), (8, 0))
        load_and_paste(img, ASSETS_PATH / "aux/tower.png", (75, 75), (114, 115))

    elif cell_type == 'duplicate':
        global duplicates_list
        if duplicates_list:
            duplicate = random.choice(duplicates_list)
            duplicates_list.remove(duplicate)
            card, count = duplicate

            load_and_paste(img, CARDS_PATH / card, (180, 180), (8, 0))
            load_and_paste(img, ASSETS_PATH / f"aux/{count}", (100, 100), (90, 125))

    elif cell_type == 'misc':
        if files_misc:
            img_name = random.choice(files_misc)
            img = Image.open(MISC_PATH / img_name)
            files_misc.remove(img_name)
            img.thumbnail((190, 190))
            last_img = img_name

    elif cell_type == 'elixir':
        if files_elixir:
            img_name = random.choice(files_elixir)
            img = Image.open(ELIXIR_PATH / img_name)
            files_elixir.remove(img_name)
            img.thumbnail((190, 190))
        else:
            img = create_cell_content('misc')

    elif cell_type == 'arena':
        img = Image.new('RGBA', (190, 190), (255, 255, 255, 0))
        global arena_files
        if arena_files and len(arena_files) > 1:

            img_name1 = random.choice(arena_files)
            arena_files.remove(img_name1)
            img_name2 = random.choice(arena_files)

            img1 = Image.open(ASSETS_PATH / "arenas" / img_name1)
            img2 = Image.open(ASSETS_PATH / "arenas" / img_name2)

            half_width = img1.width // 2  # 250
            height = img1.height          # 500

            left_half = img1.crop((0, 0, half_width, height))
            right_half = img2.crop((half_width, 0, img2.width, height))

            combined = Image.new('RGBA', (img1.width, height), (0, 0, 0, 0))
            combined.paste(left_half, (0, 0))
            combined.paste(right_half, (half_width, 0))

            combined.thumbnail((190, 190))
            img.paste(combined, (0, 0), combined)
        else:
            img = create_cell_content('misc')

    return img


def generate_bingo_card(
        modifiers_rate=MODIFIERS_RANDOM_RATE,
        cell_weights=CELL_TYPE_WEIGHTS
):
    global last_img
    bingo = Image.open(ASSETS_PATH / "empty_card.png")
    bingo = bingo.resize((1000, 1000))

    modifiers = [f.name for f in MODIFIERS_PATH.glob("*.png")]

    incompatible_modifiers = {
        'elixir': ['elixir_5.png', 'elixir_3.png'],
        'Rocket_King_Tower.png': ['TowerActivation.png'],
        'KingTower.png': ['TowerActivation.png', 'RedCrown.png', '3Crowns.png'],
        'Spells.png': ['Time.png'],
        'Perfection.png': ['RedCrown.png'],
        'Buildings.png': ['Time.png', 'elixir_5.png'],
        'arena': ['elixir_3.png', 'elixir_5.png'],
        'Random.png': ['elixir_5.png', 'elixir_3.png'],
    }

    for i in range(5):
        for j in range(5):
            x = 7 + j * 199
            y = 7 + i * 199

            cell_type = weighted_choice(cell_weights)
            img = create_cell_content(cell_type)

            img.thumbnail((190, 190))
            bingo.paste(img, (x, y), img)

            if random.random() < modifiers_rate and modifiers:
                excluded = set(incompatible_modifiers.get(cell_type, []))
                if last_img:
                    excluded.update(incompatible_modifiers.get(last_img, []))
                valid_modifiers = [m for m in modifiers if m not in excluded]
                
                modifier_name = random.choice(valid_modifiers)
                mod_img = Image.open(MODIFIERS_PATH / modifier_name)
                mod_img.thumbnail((90, 90))
                bingo.paste(mod_img, (x + 105, y + 2), mod_img)
            
            last_img = None

    bingo = bingo.resize((1320, 1320))
    bg = Image.open(ASSETS_PATH / "preset.png")
    bg.paste(bingo, (60, 820), bingo)
    bg.show()
    return bingo

def generate_bingo_grid(
    modifiers_rate=MODIFIERS_RANDOM_RATE,
    cell_weights=CELL_TYPE_WEIGHTS
):
    cell_images = []
    cell_explanations = []
    modifiers = [f.name for f in MODIFIERS_PATH.glob("*.png")]
    for i in range(5):
        row_imgs = []
        row_expls = []
        for j in range(5):
            cell_type = weighted_choice(cell_weights)
            img = create_cell_content(cell_type)
            desc = get_cell_description(cell_type)  # Debes implementar esta función
            img.thumbnail((190, 190))
            row_imgs.append(img.copy())
            row_expls.append(desc)
        cell_images.append(row_imgs)
        cell_explanations.append(row_expls)
    return cell_images, cell_explanations

def get_cell_description(cell_type):
    descriptions = {
        'triplet': "Juega tres cartas distintas en una partida.",
        'win_condition': "Gana una partida usando esta condición.",
        'last_hit': "La última carta jugada debe ser esta.",
        'duplicate': "Juega dos veces la misma carta.",
        'misc': "Realiza el reto especial de esta casilla.",
        'elixir': "Gasta la cantidad de elixir indicada.",
        'arena': "Juega en estas dos arenas distintas.",
    }
    return descriptions.get(cell_type, "Realiza el objetivo especial.")

    
if __name__ == "__main__":
    st.title("Bingo Clash Royale Interactivo")

    if 'bingo_grid' not in st.session_state:
        st.session_state.bingo_grid = None

    def img_to_bytes(img):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf.read()
    
    if st.button("Generar tablero interactivo"):
        imgs, explanations = generate_bingo_grid()
        # Convierte imágenes PIL a bytes
        st.session_state.bingo_grid = [
            [img_to_bytes(img) for img in row] for row in imgs
        ]
        st.session_state.bingo_expl = explanations

    if st.session_state.bingo_grid:
        st.markdown("Haz clic/tap en una casilla para ver qué debes hacer:")
        for i in range(5):
            cols = st.columns(5)
            for j in range(5):
                with cols[j]:
                    key = f"cell_{i}_{j}"
                    if st.button("", key=key):
                        st.session_state['last_exp'] = st.session_state.bingo_expl[i][j]
                    st.image(st.session_state.bingo_grid[i][j], use_column_width=True)

        if 'last_exp' in st.session_state:
            st.info(st.session_state['last_exp'])