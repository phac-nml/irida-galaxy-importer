

# import cookielib
import json
import optparse
import os
# import urllib
# import urllib2
# import urlparse
import sys
# import optparse

from bioblend import galaxy
#from bioblend.galaxy.libraries import LibraryClient

# import galaxy.model # need to import model before sniff to resolve a circular import dependency
# from galaxy.datatypes import sniff
# from galaxy.datatypes.registry import Registry

def writeMessage(fileString,messageString):
        outf = open(fileString,'w')
        outf.write('\n'.join(messageString))
        outf.write('\n')
        outf.close

def irida_import( json_parameter_file, genomespace_site ):
   #  json_params = json.loads( open( json_parameter_file, 'r' ).read() )
   #  datasource_params = json_params.get( 'param_dict' )
   #  username = datasource_params.get( "gs-username", None )
   #
   #  metadata_parameter_file = open( json_params['job_config']['TOOL_PROVIDED_JOB_METADATA_FILE'], 'wb' )
   #
   #  #setup datatypes registry for sniffing
   #  datatypes_registry = Registry()
   #  datatypes_registry.load_datatypes( root_dir = json_params[ 'job_config' ][ 'GALAXY_ROOT_DIR' ], config = json_params[ 'job_config' ][ 'GALAXY_DATATYPES_CONF_FILE' ] )

    gi = galaxy.GalaxyInstance(url="http://localhost:8888/",key="09008eb345c9d5a166b0d8f301b1e72c")

    lib = galaxy.libraries.LibraryClient(gi)

    returnDict = lib.create_library("bob","this is the description for the library named bob")

    print(json.dumps(returnDict))
    print(os.getcwd())


    #gi.libraries.upload_file_from_server(returnDict['id'],'/home/jthiessen/lib_imp_dir/test/', folder_id=None, file_type='auto',
     #                                    dbkey='?', link_data_only='link_to_files', roles='')

    gi.libraries.upload_from_galaxy_filesystem(returnDict['id'],'/home/jthiessen/lib_imp_dir/test/test.fastq'
                                               ,link_data_only='link_to_files')


    sys.stdout.write("Hello Galaxy!\n")
    sys.stdout.write(json.dumps(json_parameter_file))


   # writeMessage('output.txt','Hello Galaxy!!');
           # metadata_parameter_file.write( "%s\n" % json.dumps( metadata_dict ) )
    #metadata_parameter_file.close()
    return True

if __name__ == '__main__':
    #Parse Command Line
    parser = optparse.OptionParser()
    parser.add_option( '-p', '--json_parameter_file', dest='json_parameter_file', action='store', type="string", default=None, help='json_parameter_file' )
    parser.add_option( '-s', '--irida_info', dest='irida_info', action='store', type="string", default=None, help='irida_info' )
    (options, args) = parser.parse_args()

    irida_import( options.json_parameter_file, options.irida_info )
