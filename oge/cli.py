import sys

from .paths import resolve_cli_map
from .ui import OccupancyEditor


def main(arguments=None):
    arguments = sys.argv[1:] if arguments is None else list(arguments)
    if len(arguments) > 1:
        print("usage: occupancy-grid-editor [MAP.yaml]", file=sys.stderr)
        return 2

    map_path = None
    if arguments:
        try:
            map_path = resolve_cli_map(arguments[0])
        except (OSError, ValueError) as error:
            print(error, file=sys.stderr)
            return 2

    app = OccupancyEditor()
    if map_path and not app.open_path(map_path):
        app.destroy()
        return 1
    app.mainloop()
    return 0
