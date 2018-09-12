from __future__ import print_function

import argparse
from functools import wraps
import sys

import rossum
from rossum.extraction import MissingApiKeyException


def parse_args():
    parser = argparse.ArgumentParser(description='Rossum CLI.')
    subparsers = parser.add_subparsers(dest='command')
    parser_extract = subparsers.add_parser('extract')

    parser_extract.add_argument('document_path', metavar='DOCUMENT_PATH', help='Document path (PDF/PNG)')
    parser_extract.add_argument('-o', '--output', required=False,
                                help='Path of output JSON (defaults to DOCUMENT_PATH + .json)')
    parser_extract.add_argument('-l', '--locale', help='Locale (eg. en_US)')

    return parser


def exit_on_missing_api_key(exit_code=-1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except MissingApiKeyException as e:
                print(e)
                sys.exit(exit_code)
        return wrapper
    return decorator


@exit_on_missing_api_key(exit_code=-1)
def main():
    arg_parser = parse_args()
    args = arg_parser.parse_args()

    if args.command == 'extract':
        print('Extracting document:', args.document_path)
        output_path = args.output if args.output is not None else args.document_path + '.json'
        extracted = rossum.extract(args.document_path, output_path, locale=args.locale)
        rossum.extraction.print_summary(extracted)
        print('Extracted to:', output_path)
    else:
        arg_parser.print_help()
