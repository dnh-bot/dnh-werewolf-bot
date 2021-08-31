import inspect
import pprint
pp = pprint.PrettyPrinter(indent=4)

def logger_debug(obj):
    print(inspect.stack()[1][3])
    pp.pprint(obj)