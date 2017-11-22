import json
import pydocumentdb.documents as documents
import pydocumentdb.document_client as document_client
import pydocumentdb.errors as errors
import datetime

class IDisposable:
    """ A context manager to automatically close an object with a close method
    in a with statement. """

    def __init__(self, obj):
        self.obj = obj

    def __enter__(self):
        return self.obj # bound to target

    def __exit__(self, exception_type, exception_val, trace):
        # extra cleanup in here
        self = None

class AzureRepository(object):

    def __init__(self):
        self.config = self.read_config()
        self.client = document_client.DocumentClient(self.config['ENDPOINT'], {'masterKey': self.config['MASTERKEY']})
        self.db_link = 'dbs/' + self.config['DOCUMENTDB_DATABASE']


    @staticmethod
    def read_config():
        with open('/home/datadrive/azure_secrets/tennisai2.config') as f:
            config = json.load(f)
        return config

    def get_document_collection_link(self, document_id):
        return self.db_link + '/colls/' + document_id

    def find_collection(self, client, id):
        print('1. Query for Collection')

        collections = list(client.QueryCollections(
            self.db_link,
            {
                "query": "SELECT * FROM r WHERE r.id=@id",
                "parameters": [{ "name":"@id", "value": id }]
            }
        ))

        if len(collections) > 0:
            print('Collection with id \'{0}\' was found'.format(id))
            return collections
        else:
            print('No collection with id \'{0}\' was found'. format(id))
            return []

    def write_to_collection(self, collection_id, json_document):
        id = json_document['id']
        print('Writing document to Azure')
        current_hash = self.client.QueryDocuments(self.get_document_collection_link(collection_id), 'SELECT t.hash  FROM tournaments t where t.id = ' + id)
        if current_hash != json_document['hash']:
            json_document['update_date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.client.UpsertDocument(self.get_document_collection_link(collection_id), json_document)

