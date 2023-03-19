"""
Entrypoint for CLI.
"""
import click
import logging
import atexit

from mastodon_bot.commands import init, post, listen

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@click.group(chain=True)
@click.option("--debugging",is_flag=True, default=False, help="output debug information")
@click.pass_context
def cli(ctx, debugging):
    click.echo('Debug mode is %s' % ('on' if debugging else 'off'))
    ctx.ensure_object(dict)

    if debugging:
        # Change the logging level to debug
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("")
    else:
        # Use the default logging level (info)
        logging.getLogger().setLevel(logging.INFO)
    

    logging.debug("cli()")

    #ctx.obj['debugging'] = debugging

def exit_handler():
    logging.debug("exit_handler")

cli.add_command(init)
cli.add_command(post)
cli.add_command(listen)

atexit.register(exit_handler)

if __name__ == '__main__':
    cli()