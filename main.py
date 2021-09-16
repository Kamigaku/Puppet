import sys
import getopt
import importlib

from discordClient import puppet


def run_bot(api_key: str):
    bot = puppet.Puppet(api_key)
    bot.connectToServer()


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
