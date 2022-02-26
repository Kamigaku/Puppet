import unicodedata

COIN_NAME = "biteCoin"

COGS_PATH = "cogs"

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
BELL_EMOJI = "\U0001F514"
GIFT_EMOJI = "\U0001F381"
PACKAGE_EMOJI = "\U0001F4E6"
UNLOCK_EMOJI = "\U0001F513"
BROKEN_HEART_EMOJI = "\U0001F494"

RARITIES_LABELS = ["E", "D", "C", "B", "A", "S", "SS"]
RARITIES_COLORS = [0x9B9B9B, 0xFFFFFF, 0x69e15e, 0x4ccfff, 0xf0b71c,
                   0xf08033, 0x8f39ce]
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
#SELL_BUTTON = Button(style=ButtonStyle.green, label="Sell", custom_id="sell_card", emoji=SELL_EMOJI)
#REPORT_BUTTON = Button(style=ButtonStyle.red, label="Report", custom_id="report_card", emoji=REPORT_EMOJI)
#LOCK_BUTTON = Button(style=ButtonStyle.blurple, label="Lock", custom_id="lock_card", emoji=LOCK_EMOJI)
#FAVORITE_BUTTON = Button(style=ButtonStyle.blurple, label="Favorite", custom_id="favorite_card", emoji=HEART_EMOJI)
#VALIDATE_BUTTON = Button(style=ButtonStyle.green, label="Validate", custom_id="validate", emoji=CHECK_EMOJI)
#CANCEL_BUTTON = Button(style=ButtonStyle.red, label="Cancel", custom_id="cancel", emoji=RED_CROSS_EMOJI)
# CHANGE_OWNER_BUTTON = Button(style=ButtonStyle.blurple, label="Change owner", custom_id="change_owner",
#                              emoji=ROTATE_EMOJI)
# PARTICIPATE_BUTTON = Button(style=ButtonStyle.green, label="Participate", custom_id="participate",
#                             emoji=CHECK_EMOJI)

# SELECTS
# RARITY_SELECT = Select(options=[SelectOption(label=f"{RARITIES_LABELS[index]}",
#                                              value=f"{index}",
#                                              emoji=f"{RARITIES_EMOJI[index]}")
#                                 for index in range(1, 7)],
#                        placeholder="Select the rarity you want to apply",
#                        custom_id="rarity_select",
#                        max_values=6)
