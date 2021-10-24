import getopt
import importlib
import sys

from discordClient import PuppetBot


def run_bot(api_key: str, prefix: str, debug: bool, sync_commands: bool):
    bot = PuppetBot(commands_prefix=f"{prefix}",
                    debug_mode=debug,
                    sync_commands=sync_commands)
    bot.default_initialisation()
    bot.run(api_key)


def make_migration(migration_file: str):
    importlib.import_module(migration_file, package="migrations")
    print("Migration over!")


if __name__ == '__main__':

    options, args = getopt.getopt(sys.argv[1:], 'm:a:p:ds',
                                  ['migrate=',
                                   'api_key=',
                                   'prefix=',
                                   'debug',
                                   'sync'])
    api_key = None
    commands_clear = False
    prefix = None
    debug = False
    sync_commands = False
    for opt, arg in options:
        if opt in ('-m', '--migrate'):
            make_migration(arg)
        elif opt in ('-a', '--api_key'):
            api_key = arg
        elif opt in ('-p', '--prefix'):
            prefix = arg
        elif opt in ('-d', '--debug'):
            debug = True
        elif opt in ('-s', '--sync'):
            sync_commands = True

    if api_key is not None:
        run_bot(api_key, prefix, debug, sync_commands)
