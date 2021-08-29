import unicodedata

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

# RARITIES_EMOJI = [unicodedata.lookup('BLACK LARGE SQUARE'), unicodedata.lookup('WHITE LARGE SQUARE'),
#                   unicodedata.lookup('LARGE GREEN SQUARE'), unicodedata.lookup('LARGE BLUE SQUARE'),
#                   unicodedata.lookup('LARGE YELLOW SQUARE'), unicodedata.lookup('LARGE ORANGE SQUARE'),
#                   unicodedata.lookup('LARGE PURPLE SQUARE')]

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

RARITIES_LABELS = ["E", "D", "C", "B", "A", "S", "SS"]

LEFT_ARROW_EMOJI = unicodedata.lookup('Leftwards Black Arrow')
RIGHT_ARROW_EMOJI = unicodedata.lookup('Black Rightwards Arrow')

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
