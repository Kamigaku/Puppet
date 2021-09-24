import sys
import getopt
import importlib

from discordClient import Puppet


def run_bot(api_key: str):
    bot = Puppet(api_key)
    bot.connect_to_server()


def make_migration(migration_file: str):
    importlib.import_module(migration_file, package="migrations")
    print("Migration over!")


if __name__ == '__main__':

    options, args = getopt.getopt(sys.argv[1:], 'm:a:', ['migrate=',
                                                         'api_key='])
    for opt, arg in options:
        if opt in ('-m', '--migrate'):
            make_migration(arg)
        elif opt in ('-a', '--api_key'):
            run_bot(arg)
