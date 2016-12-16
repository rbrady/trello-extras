#!/usr/bin/env python
import click
import jinja2
import os
from pprint import pprint
import requests
import six
import sys

from trello import trelloclient

import pdb

try:
    import configparser
except ImportError:
    import ConfigParser as configparser


# overriding the conf file and using a template for report rendering
# trello-board-report --board_name my-retro-board --template my-retro-jinja.html
#                     --config ~/.trello.conf

# using values passed in for board access and a template for report rendering
# trello-board-report --board_name my-retro-board --template my-retro-jinja.html
#                     --api_key 23432423hj32g43 --access_token 89238432842394

# assuming ~/.trello-report-utils.conf exists and returns report in text format
# trello-board-report --board_name my-retro-board

# trello-board-report --board_name my-retro-board --template my-retro-jinja.html
#                     --ignore-lists Checkin,Close

def create_context_title(name):
    return '_'.join(name.lower().split(' '))


def get_config_info(config_file_path):
    if not config_file_path:
        config_file_path = '~/.trello-extras.conf'
    config_path = os.environ.get('TRELLO_EXTRAS_CONFIG',
                                 os.path.expanduser(config_file_path))
    config = configparser.SafeConfigParser()
    if not config.read(config_path):
        click.echo('Failed to parse config file {}.'.format(config_path))
        sys.exit(1)
    if not config.has_section('trello'):
        click.echo('Config file does not contain section [trello].')
        sys.exit(1)
    trello_data = dict(config.items('trello'))
    required_settings = ['api_key', 'access_token']
    for setting in required_settings:
        if setting not in trello_data:
            click.echo(
                'Config file requires a setting for {setting}'
                ' in section [trello].'.format(setting)
            )
            sys.exit(1)
    return trello_data


@click.command()
@click.option('--access_token', default=None, type=str)
@click.option('--api_key', default=None, type=str)
@click.option('--config', default=None, type=str)
@click.option('--board_name', '-b', default=None, type=str)
@click.option('--output', '-o', default=None, type=str)
@click.option('--template', '-t', default=None, type=str)
def board_report(access_token, api_key, config, board_name, output, template):
    # check for access_token and api_key
    # if the access_token and api_key are not provided, try to use the config.
    if access_token is None or api_key is None:
        # if the config value is None, the method will try the default path.
        config_data = get_config_info(config)
        access_token = config_data['access_token']
        api_key = config_data['api_key']

    # if no trello auth data found, print message and exit
    if access_token is None or api_key is None:
        click.echo("No authentication data was provided for Trello")

    if not board_name:
        click.echo("You must provide a board_name.")
        sys.exit(1)

    if not output:
        output = "{}.txt".format(board_name)

    trello_api = trelloclient.TrelloClient(api_key=api_key, token=access_token)

    # check for board existence
    board = [b for b in trello_api.list_boards() if b.name == board_name][0]
    # if no board, print error and exit
    if not board:
        click.echo("Trello board not found!")
        sys.exit(1)

    # create board context
    context = {'board': board}

    # if template is included, render the template and return
    if template:
        with open(template,'r') as template_file:
            template_data = template_file.read()
            try:
                # Render the j2 template
                raw_template = jinja2.Environment().from_string(template_data)
                r_template = raw_template.render(**context)
                with open(output, 'w') as output_file:
                    output_file.write(r_template)
            except jinja2.exceptions.TemplateError as ex:
                error_msg = ("Error rendering template %s : %s"
                             % (template, six.text_type(ex)))
                raise Exception(error_msg)
    else:
        click.echo(board_name.title())
        click.echo(pprint(context))
    pass


if __name__ == '__main__':
    board_report()
