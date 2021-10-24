import unicodedata

from discord import Colour
from discord_slash import ButtonStyle
from discord_slash.utils.manage_components import create_button, create_select_option, create_select

COIN_NAME = "biteCoin"

LETTER_EMOJIS = [
    unicodedata.lookup(f'REGIONAL INDICATOR SYMBOL LETTER {chr(letter)}')
    for letter in range(ord('A'), ord('Z') + 1)
]

NUMBER_EMOJIS = [unicodedata.lookup("KEYCAP DIGIT ZERO"), unicodedata.lookup("KEYCAP DIGIT ONE"),
                 unicodedata.lookup("KEYCAP DIGIT TWO"), unicodedata.lookup("KEYCAP DIGIT THREE"),
                 unicodedata.lookup("KEYCAP DIGIT FOUR"), unicodedata.lookup("KEYCAP DIGIT FIVE"),
                 unicodedata.lookup("KEYCAP DIGIT SIX"), unicodedata.lookup("KEYCAP DIGIT SEVEN"),
                 unicodedata.lookup("KEYCAP DIGIT EIGHT"), unicodedata.lookup("KEYCAP DIGIT NINE"),
                 "\U0001F51F"]

ASTERISK_EMOJI = unicodedata.lookup("KEYCAP ASTERISK")

RARITIES_EMOJI = ["\U00002B1B", "\U00002B1C",
                  "\U0001F7E9", "\U0001F7E6",
                  "\U0001F7E8", "\U0001F7E7",
                  "\U0001F7EA"]

SELL_EMOJI = "\U0001F4B0"
REPORT_EMOJI = "\U0001F4E2"
LIBRARY_EMOJI = "\U0001F4D1"
WARNING_EMOJI = "\U000026A0"
CHECK_EMOJI = "\U00002705"
DETAILS_EMOJI = "\U0001F50D"
RED_CROSS_EMOJI = "\U0000274C"
ROTATE_EMOJI = "\U0001F504"
LOCK_EMOJI = "\U0001F512"
HEART_EMOJI = "\U00002764"

RARITIES_LABELS = ["E", "D", "C", "B", "A", "S", "SS"]
RARITIES_COLORS = [Colour(0x9B9B9B), Colour(0xFFFFFF), Colour(0x69e15e), Colour(0x4ccfff), Colour(0xf0b71c),
                   Colour(0xf08033), Colour(0x8f39ce)]
RARITIES_HEXA = ["9B9B9B", "FFFFFF", "69e15e", "4ccfff", "f0b71c", "f08033", "8f39ce"]
RARITIES_URL = "https://www.colorhexa.com/{}.png"

LEFT_ARROW_EMOJI = "\U00002b05\U0000fe0f"
RIGHT_ARROW_EMOJI = "\U000027a1\U0000fe0f"

PUPPET_IDS = {"CARD_COGS_BUY": 1,
              "MUSEUM_COGS_CATEGORIES": 2,
              "MUSEUM_COGS_TYPES": 3,
              "MUSEUM_COGS_AFFILIATION_LETTERS": 4,
              "MUSEUM_COGS_AFFILIATIONS": 5,
              "MUSEUM_COGS_RARITIES": 6,
              "MUSEUM_COGS_CHARACTERS": 7,
              "REPORT_COGS_DETAIL": 8,
              "CARD_COGS_LIST": 9,
              "TRADE_COGS_LIST": 10,
              "TRADE_COGS_RECAP": 11,
              "TRADE_COGS_OFFER": 12}

REACTION_ADD = "REACTION_ADD"
REACTION_REMOVE = "REACTION_REMOVE"

# BUTTONS
SELL_BUTTON = create_button(style=ButtonStyle.green, label="Sell", custom_id="sell_card", emoji=SELL_EMOJI)
REPORT_BUTTON = create_button(style=ButtonStyle.red, label="Report", custom_id="report_card", emoji=REPORT_EMOJI)
LOCK_BUTTON = create_button(style=ButtonStyle.blue, label="Lock", custom_id="lock_card", emoji=LOCK_EMOJI)
FAVORITE_BUTTON = create_button(style=ButtonStyle.blue, label="Favorite", custom_id="favorite_card", emoji=HEART_EMOJI)
VALIDATE_BUTTON = create_button(style=ButtonStyle.green, label="Validate", custom_id="validate", emoji=CHECK_EMOJI)
CANCEL_BUTTON = create_button(style=ButtonStyle.red, label="Cancel", custom_id="cancel", emoji=RED_CROSS_EMOJI)
CHANGE_OWNER_BUTTON = create_button(style=ButtonStyle.blue, label="Change owner", custom_id="change_owner",
                                    emoji=ROTATE_EMOJI)

# SELECTS
RARITY_SELECT = create_select(options=[create_select_option(f"{RARITIES_LABELS[index]}",
                                                            value=f"{index}",
                                                            emoji=f"{RARITIES_EMOJI[index]}")
                                       for index in range(1, 7)],
                              placeholder="Select the rarity you want to apply",
                              custom_id="rarity_select",
                              max_values=6)
