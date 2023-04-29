# hardhat event streams cli

import click

@click.group
@click.option('-d', '--debug', is_flag=True, help='debug mode')
@click.option('-b', '--bind-address', envvar='BIND_ADDRESS', help='bind address')
@click.option('-p', '--port', envvar='PORT', help='listen port')
@click.option('-g', '--gateway', envvar='GATEWAY_URL', help='gateway URL')
@click.pass_context
def cli(ctx, **kwargs)
    ctx.obj = {}
    ctx.obj.update(**kwargs)

@cli.command
@click.pass_context
def run(ctx):
    """run server"""
    pass

@cli.group
@click.pass_context
def db(ctx):
    """database commands"""
    pass

@db.command
@click.pass_context
def init(ctx):
    """create database"""
    pass

@db.command
@click.pass_context
def dump(ctx):
    """dump database to file"""
    pass

@db.command
@click.pass_context
def load(ctx):
    """load database from file"""
    pass

@db.command
@click.pass_context
def clear(ctx):
    """clear database"""
    pass


