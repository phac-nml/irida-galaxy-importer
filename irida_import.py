import optparse
import logging
from bioblend import galaxy


def write_message(fileString, messageString):
    outf = open(fileString, 'w')
    outf.write('\n'.join(messageString))
    outf.write('\n')
    outf.close


def irida_import(json_parameter_file, irida_info):

    gi = galaxy.GalaxyInstance(url="http://localhost:8888/",
                               key="09008eb345c9d5a166b0d8f301b1e72c")

    lib = galaxy.libraries.LibraryClient(gi)

    returnDict = lib.create_library("bob",
                                    "description for the library named bob")

    gi.libraries.upload_from_galaxy_filesystem(
        returnDict['id'],
        '/home/jthiessen/lib_imp_dir/test/test.fastq',
        link_data_only='link_to_files')

    return True

if __name__ == '__main__':
    logging.basicConfig(filename="irida_import.log", level=logging.DEBUG,
                        filemode="w")

    logging.info("Parsing the Command Line")
    parser = optparse.OptionParser()
    parser.add_option(
        '-p', '--json_parameter_file', dest='json_parameter_file',
        action='store', type="string", default=None,
        help='json_parameter_file')

    parser.add_option(
        '-s', '--irida_info', dest='irida_info',
        action='store', type="string", default=None,
        help='irida_info')

    (options, args) = parser.parse_args()

    irida_import(options.json_parameter_file, options.irida_info)
