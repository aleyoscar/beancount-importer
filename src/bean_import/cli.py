import typer
from .bean_import import bean_import

app = typer.Typer()
app.command()(bean_import)

if __name__ == "__main__":
    app()
