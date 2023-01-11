"""
Entrypoint for CLI.
"""
import click, atexit

from src.commands import init, post, listen

@click.group(chain=True)
@click.option("--debugging/--no-debugging", default=False, help="output debug information")
@click.pass_context
def cli(ctx, debugging):
    click.echo('Debug mode is %s' % ('on' if debugging else 'off'))
    ctx.ensure_object(dict)
    ctx.obj['debugging'] = debugging

def exit_handler():
    click.echo("exit_handler")

cli.add_command(init)
cli.add_command(post)
cli.add_command(listen)

atexit.register(exit_handler)

if __name__ == '__main__':
    cli()