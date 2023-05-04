# hardhat event streams cli
import sys

import click
import uvicorn

from . import settings


class Context:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


@click.group
@click.option("-d", "--debug", is_flag=True, envvar="DEBUG", show_envvar=True, help="debug mode")
@click.option("-l", "--log-level", envvar="LOG_LEVEL", show_envvar=True, help="log level")
@click.option("-b", "--bind-address", envvar="BIND_ADDRESS", show_envvar=True, help="bind address")
@click.option("-p", "--port", type=int, envvar="PORT", show_envvar=True, help="listen port")
@click.option("-w", "--workers", type=int, envvar="WORKERS", show_envvar=True, help="server worker instances")
@click.option("-k", "--api-key", envvar="API_KEY", show_envvar=True, help="api key")
@click.option("-g", "--gateway-url", envvar="GATEWAY_URL", show_envvar=True, help="gateway URL")
@click.pass_context
def cli(ctx, debug, log_level, bind_address, port, api_key, workers, gateway_url):
    ctx.obj = Context(
        debug=debug or settings.DEBUG,
        log_level=log_level or settings.LOG_LEVEL,
        bind_address=bind_address or settings.BIND_ADDRESS,
        port=port or settings.PORT,
        api_key=api_key or settings.API_KEY,
        gateway_url=gateway_url or settings.GATEWAY_URL,
        workers=workers or settings.WORKERS,
    )


@cli.command
@click.pass_obj
def run(ctx):
    """run server"""
    sys.exit(
        uvicorn.run(
            "hardhat_event_streams.app:app",
            host=ctx.bind_address,
            port=ctx.port,
            log_level=ctx.log_level.lower(),
            workers=ctx.workers,
            reload=False,
        )
    )


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


if __name__ == "__main__":
    sys.exit(cli())
