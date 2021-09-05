# import importlib
# from pathlib import Path
#
# init_file = Path(__file__)
# model_dir = Path(init_file).parent
#
# for model_file in model_dir.iterdir():
#     model = model_file.stem
#
#     if model_file.is_dir() or model.startswith('_'):
#         continue
#
#     module_name = f'discordClient.model.{model}'
#     print(module_name)
#     importlib.import_module(module_name)

from .meta_model import *
from .affiliation import Affiliation
from .booster import Booster
from .character import Character
from .economy import Economy
from .jointure_tables import *
from .moderator import Moderator
from .report import Report
from .trade import Trade
