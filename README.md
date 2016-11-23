# pysk

ncurses terminal app to display streaming data from a signalk server.

# Requirements

the [python-signalk-client][r-1] library is required but not available in
the Python Package Index. Install it first.

## Install

    python ./setup.py build
    sudo python ./setup.py install

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

[r-1]:https://github.com/ph1l/python-signalk-client

