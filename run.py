from smarthome import server
import sys

if len(sys.argv) > 1 and sys.argv[1] == "--debug":
    server.run_debug()
else:
    server.run()
