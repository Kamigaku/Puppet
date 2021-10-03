import unicodedata

from discord import Colour

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
