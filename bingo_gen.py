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
from text_gen import multiple_text_image
import io

from data import TRIPLETS_LIST, WIN_CONDITIONS, DUPLICATES
from data import TEXT_DESCRIPTION, MISC_DESCRIPTION, MODIFIERS_DESCRIPTION
from data import INCOMPATIBLE_MODIFIERS, EXCLUDED_CARDS

triplet_list = TRIPLETS_LIST.copy()
win_conditions = WIN_CONDITIONS.copy()
duplicates_list = DUPLICATES.copy()
text_list = TEXT_DESCRIPTION.copy()
misc_text_list = MISC_DESCRIPTION.copy()
modifiers_text_list = MODIFIERS_DESCRIPTION.copy()
incompatible_modifiers = INCOMPATIBLE_MODIFIERS.copy()
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
        last_img = card

    elif cell_type == 'last_hit':
        global last_hits
        card = None
        card = random.choice(last_hits)
        last_img = card
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
            last_img = card

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
    mod = False

    bingo = Image.open(ASSETS_PATH / "empty_card.png")
    bingo = bingo.resize((1000, 1000))
    bingo_text = bingo.copy()

    modifiers = [f.name for f in MODIFIERS_PATH.glob("*.png")]

    for i in range(5):
        for j in range(5):
            x = 7 + j * 199
            y = 7 + i * 199

            cell_type = weighted_choice(cell_weights)
            img = create_cell_content(cell_type)

            if cell_type == 'misc':
                text = misc_text_list.get(last_img, "")
            else:
                text = text_list.get(cell_type, "")

            img.thumbnail((190, 190))

            bingo.paste(img, (x, y), img)
            bingo_text.paste(img, (x, y), img)

            if random.random() < modifiers_rate and modifiers:
                excluded = set(incompatible_modifiers.get(cell_type, []))
                if last_img:
                    excluded.update(incompatible_modifiers.get(last_img, []))
                valid_modifiers = [m for m in modifiers if m not in excluded]
                
                modifier_name = random.choice(valid_modifiers)
                mod_img = Image.open(MODIFIERS_PATH / modifier_name)
                mod_img.thumbnail((90, 90))
                bingo.paste(mod_img, (x + 105, y + 2), mod_img)
                bingo_text.paste(mod_img, (x + 105, y + 2), mod_img)
                mod = True

            parr = [text]
            if mod == True:
                parr.append(modifiers_text_list.get(modifier_name, ""))

            text_img = multiple_text_image(
                parrafos= parr,
                colores = ['white', 'magenta'],
                tam_fuente=15,
                max_line_length=20,
            )
            text_img.thumbnail((190, 190))
            bingo_text.paste(text_img, (x, y), text_img)

            mod = False
            last_img = None

    bingo = bingo.resize((1320, 1320))
    # bingo_text.show()

    return bingo, bingo_text

if __name__ == "__main__":
    st.set_page_config(
        page_title="Clash Royale Bingo",
        initial_sidebar_state="collapsed",
    )    

    st.markdown("""
    <style>
    .responsive-title {
    font-weight: bold;
    font-size: 40px;
    }
    .responsive-subtitle {
    color: gray;
    font-size: 14px;
    }

    @media (max-width: 600px) {
    .responsive-title {
        font-size: 34px !important;
    }
    .responsive-subtitle {
        font-size: 14px !important;
    }
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        '<span class="responsive-title">Clash Royale Bingo </span> '
        '<span class="responsive-subtitle">by @pinxevi</span>',
        unsafe_allow_html=True
    )

    if "bingos" not in st.session_state:
        st.session_state.bingos = [None, None]
    if "bingo_index" not in st.session_state:
        st.session_state.bingo_index = 0

    st.sidebar.header("Settings")

    with st.sidebar.expander("Parameters", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            modifiers_rate = st.slider("Modifier rate", 0.01, 1.0, 0.3)
            triplet_rate = st.slider("Triplet weight", 0.01, 5.0, 1.0)
            arena_rate = st.slider("Arena weight", 0.01, 5.0, 0.1)
            win_conditions_rate = st.slider("Wincon weight", 0.01, 5.0, 1.0)
        with col2:
            last_hits_rate = st.slider("Last hit weight", 0.01, 5.0, 1.0)
            duplicate_rate = st.slider("Dupes weight", 0.01, 5.0, 1.0)
            misc_rate = st.slider("Misc. weight", 0.01, 5.0, 1.0)
            elixir_rate = st.slider("Elixir weight", 0.01, 5.0, 0.1)
        

    col1, col2, right = st.columns([1, 1, 2])

    with col1:
        if st.button("Generate Bingo Card"):
            st.session_state.bingos = generate_bingo_card(
                modifiers_rate=modifiers_rate,
                cell_weights={
                    'last_hit': last_hits_rate,
                    'win_condition': win_conditions_rate,
                    'misc': misc_rate,
                    'triplet': triplet_rate,
                    'duplicate': duplicate_rate,
                    'arena': arena_rate,
                    'elixir': elixir_rate,
                }
            )
            st.session_state.bingo_index = 0  # Mostrar siempre el primero por defecto

    with col2:
        if st.button("Toggle Info"):
            st.session_state.bingo_index = 1 - st.session_state.bingo_index


    if st.session_state.bingos[st.session_state.bingo_index]:
        buf = io.BytesIO()
        st.session_state.bingos[st.session_state.bingo_index].save(buf, format="PNG")
        buf.seek(0)
        if st.session_state.bingo_index == 0:
            st.image(buf, caption="Bingo Card", use_column_width=True)
        else:
            st.image(buf, caption="Card Descriptions", use_column_width=True)

    st.write("" \
    "The objective is to complete any row or column.\n\n" \
    "Winning each match is required to check off any cell.\n\n" \
    "'Toggle Description' button lets you see each cell's objective, as well as modifiers (if any).\n\n" \
    "You can adjust the likelihood of each cell type by changing the weights under 'Parameters' in the sidebar.")