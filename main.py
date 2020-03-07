import logging
import os
import sys

from math import ceil

from sodapy import Socrata

logging.basicConfig(filename="./logs.log", level=logging.DEBUG)
logger = logging.getLogger(__name__)

DATA_URL = "data.cityofnewyork.us"
DATA_ID = "nc67-uf89"


def get_client(url: str, app_token: str) -> Socrata:
    return Socrata(url, app_token)


def parse_args() -> dict:
    opts = {}
    args = sys.argv[1:]

    for arg in args:
        try:
            argname, argval = arg.split('=')
        except ValueError:
            logger.warn("Failed to split {arg} along '=', "
                        "assuming to be a boolean.")
            argname = arg
            argval = True
        except Exception:
            continue

        if argname.startswith('--'):
            argname = argname[2:]

        opts[argname] = argval

    return opts


def validate_num_pages(opts: dict, page_size: int) -> int:
    try:
        return int(opts['num_pages'])
    except KeyError:
        logger.warn("No option called 'num_pages' found! "
                    "Attempting to calculate from COUNT of all rows")
    except Exception as e:
        logger.warn("Failed to process num_pages. Here is why: "
                    f"{e}. Attempting to calculate from COUNT of all rows")

    try:
        results = client.get(DATA_ID, select='COUNT(*)')
        total = int(results[0]['COUNT'])
        return ceil(total / page_size)
    except Exception as e:
        logger.warn(f"Failed to count total: {e} "
                    "Stopping script and raising exception")
        raise


if __name__ == '__main__':
    opts = parse_args()
    client = get_client(DATA_URL, os.environ['APP_TOKEN'])

    page_size = int(opts.get('page_size', 1000))
    num_pages = validate_num_pages(opts, page_size)

    i = 0
    logger.debug("Begin processing of data for "
                 f"page_size: {page_size} and num_pages: {num_pages}")
    while i < num_pages:
        resp = client.get(DATA_ID, limit=page_size, offset=i*page_size)
        logger.debug(f"Processed page {i+1}, limit={page_size} and "
                     f"offset={i*page_size}")

        i += 1
        write_to_file = 'output' in opts
        if write_to_file:
            with open(opts['output'], 'a+') as fh:
                for item in resp:
                    fh.write(f"{str(item)}\n")
        else:
            for item in resp:
                print(str(item))
