import sys
import getopt
import importlib

from discordClient import Puppet


def run_bot(api_key: str, prefix: str):
    bot = Puppet(api_key, prefix)
    bot.connect_to_server()


def make_migration(migration_file: str):
    importlib.import_module(migration_file, package="migrations")
    print("Migration over!")


if __name__ == '__main__':

    options, args = getopt.getopt(sys.argv[1:], 'm:a:p:', ['migrate=',
                                                           'api_key=',
                                                           'prefix='])
    api_key = None
    commands_clear = False
    prefix = None
    for opt, arg in options:
        if opt in ('-m', '--migrate'):
            make_migration(arg)
        elif opt in ('-a', '--api_key'):
            api_key = arg
        elif opt in ('-p', '--prefix'):
            prefix = arg

    if api_key is not None:
        run_bot(api_key, prefix)
