import inspect
import pprint
pp = pprint.PrettyPrinter(indent=4)

def logger_debug(obj):
    print("Debug at ",inspect.stack()[1][3])
    pp.pprint(obj)