import click
import sys
from urllib.request import urlopen

from staking_deposit.cli.existing_mnemonic import existing_mnemonic
from staking_deposit.cli.exit_transaction_keystore import exit_transaction_keystore
from staking_deposit.cli.exit_transaction_mnemonic import exit_transaction_mnemonic
from staking_deposit.cli.generate_bls_to_execution_change import generate_bls_to_execution_change
from staking_deposit.cli.new_mnemonic import new_mnemonic
from staking_deposit.utils.click import (
    captive_prompt_callback,
    choice_prompt_func,
    jit_option,
)
from staking_deposit.utils import config
from staking_deposit.utils.constants import INTL_LANG_OPTIONS
from staking_deposit.utils.intl import (
    get_first_options,
    fuzzy_reverse_dict_lookup,
    load_text,
)


def check_python_version() -> None:
    '''
    Checks that the python version running is sufficient and exits if not.
    '''
    if sys.version_info < (3, 7):
        click.pause(load_text(['err_python_version']))
        sys.exit()


def check_connectivity() -> None:
    '''
    Checks if there is an internet connection and warns the user if so.
    '''
    try:
        urlopen('https://www.google.com/', timeout=2)
        click.pause(load_text(['connectivity_warning']))
    except:  # noqa: E722
        return None


@click.group()
@click.pass_context
@jit_option(
    '--language',
    callback=captive_prompt_callback(
        lambda language: fuzzy_reverse_dict_lookup(language, INTL_LANG_OPTIONS),
        choice_prompt_func(lambda: 'Please choose your language', get_first_options(INTL_LANG_OPTIONS)),
        default='English',
    ),
    default='English',
    help='The language you wish to use the CLI in.',
    prompt=choice_prompt_func(lambda: 'Please choose your language', get_first_options(INTL_LANG_OPTIONS))(),
    type=str,
)
@click.option(
    '--non_interactive',
    default=False,
    is_flag=True,
    help='Disables interactive prompts. Warning: with this flag, there will be no confirmation step(s) to verify the input value(s). Please use it carefully.',  # noqa: E501
    hidden=False,
)
@click.option(
    '--ignore_connectivity',
    default=False,
    is_flag=True,
    help='Disables internet connectivity check.',
    hidden=False,
)
def cli(ctx: click.Context, language: str, non_interactive: bool, ignore_connectivity: bool) -> None:
    if not ignore_connectivity:
        check_connectivity()
    config.language = language
    config.non_interactive = non_interactive  # Remove interactive commands


cli.add_command(existing_mnemonic)
cli.add_command(new_mnemonic)
cli.add_command(generate_bls_to_execution_change)
cli.add_command(exit_transaction_keystore)
cli.add_command(exit_transaction_mnemonic)


def run() -> None:
    check_python_version()
    cli()


if __name__ == '__main__':
    run()
