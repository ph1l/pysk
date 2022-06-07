# pysk

ncurses terminal app to display streaming data from a [Signal-K][1] Server

## local install for development

    pip install -e .

## Usage

If your server implementation has mDNS Service discovery, just run:

    $ pysk

You can also pass the server and port on the command line:

    $ pysk <server:port>

Use arrow keys to navigate and `q`, `ESC` or `CTRL-c` to exit

## Debugging

Enable a debug log:

    $ pysk --log-level=DEBUG --log-file=/tmp/pysk.debug.log [<server:port>]

## References

[1]: http://signalk.org
[r-1]: https://github.com/ph1l/python-signalk-client
