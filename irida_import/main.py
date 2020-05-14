#!/usr/bin/env python3
import argparse
import sys
import logging

from irida_import.config import Config

"""
From the command line, pass JSON files to IridaImport, and set up the logger
"""
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-p', '--json_parameter_file', dest='json_parameter_file',
        default='sample.dat',
        help='A JSON formatted parameter file from Galaxy.',
             metavar='json_parameter_file')
    parser.add_argument(
        '-l', '--log-file', dest='log', default='log_file',
        help="The file to which the tool will output the log.", metavar='log')
    parser.add_argument(
        '-t', '--token', dest='token',
        help='The tool can use a supplied access token instead of querying '
             + 'IRIDA.', metavar='token')
    parser.add_argument(
        '-c', '--config', dest='config', default=Config.DEFAULT_CONFIG_PATH,
        help='The tool requires a config file to run. '
             + 'By default this is config.ini in the main irida_import folder.')
    parser.add_argument(
        '-g', '--generate_xml', action='store_true', default=False, dest='generate_xml',
        help='The tool must generate a galaxy tool xml file before Galaxy can be started. '
             + 'Use this option to do so.')
    parser.add_argument(
        '-i', '--history-id', dest='hist_id', default=False,
        help='The tool requires a History ID.')

    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    log_format = "%(levelname)s: %(message)s"
    logging.basicConfig(filename=args.log,
                        format=log_format,
                        level=logging.ERROR,
                        filemode="w")
    try:
        config = Config(args.config)
    except FileNotFoundError:
        message = ('Error: Could not find config.ini in the irida_importer'
                   + ' directory!')
        logging.info(message)
        print(message)
        exit(1)

    logging.debug("Reading from passed file")

    if args.generate_xml:
        config.generate_xml()
        message = 'Successfully generated the XML file!'
        logging.info(message)
        print(message)
    else:
        # importing here prevents a user from needing all libs when only performing a config,
        # after the tool xml is generated galaxy will install all the required dependencies
        from irida_import.irida_import import IridaImport
        
        importer = IridaImport(config)
        # otherwise start looking at the input file
        try:
            file_to_open = args.json_parameter_file
            importer.import_to_galaxy(file_to_open, args.log, args.hist_id,
                                      token=args.token)
        except Exception:
            logging.exception('')
            importer.print_summary(failed=True)
            raise
