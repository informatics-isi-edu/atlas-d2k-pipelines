import os
import requests
from requests.auth import HTTPDigestAuth
import json
import codecs
import base64
import xml.etree.ElementTree as ET
from datetime import date


class UpdateError(Exception):
    """ Exception when fail to update a DOI.
    """
    pass

class SetMetadataError(UpdateError):
    """ Exception when fail to update metadata associated with a DOI.
    """    
    pass

class SetUrlError(UpdateError):
    """ Exception when fail to update URL endpoint associated with a DOI.
    """        
    pass

class DeleteMetadataError(UpdateError):
    """ Exception when fail to delete metadata associated with a DOI.
    """
    pass

class MethodNotAllowed(UpdateError):
    """ Exception when fail to delete metadata associated with a DOI.
    """
    pass

class NotFound(Exception):
    """ Exception when URL endpoint returns 404.
    """
    pass

class NoContent(Exception):
    """ Exception when DOI exists but there is no metadata registered.
    """
    pass

class UnprocessableEntity(Exception):
    """ Exception when metadata is an invalid XML or fails schema validation.
    """
    pass

class DoiNamespaceExhausted(Exception):
    """ Exception When random generation of DOI suffix fails after a number of trials.
    """
    pass

# ===========================================================================
# 
class DataCiteMDS(object):
    """ DataCiteMDS provides methods to interact with DataCite Metadata Store (MDS) APIs.
    A json file specifying the 'server', 'username', and 'password' is needed
    to instantiate the class instance. Datacite MDS API is found at 
    https://support.datacite.org/docs/mds-api-guide

    Note: DOIs can exist in three states: draft, registered, and finable. DOIs are in the draft state 
    when metadata have been registered, and will transition to the findable state when registering a URL. 
    Finable DOIs can transitioned to the registered state when metadata are removed from search index.
    Registered DOIs are registered with the global handle system, but they are not indexed in DataCite Search.
    Only findable DOIs are indexed in DataCite Search. 
    
    Attributes: 
      server -- DataCite server
      authens -- Authentication object 
      doi_prefix -- prefix associated with the authens object
    
    """ 
    server='https://mds.datacite.org'
    authens=None
    doi_prefix=None  # there is no longer test prefix '10.5072'    
    verbose = False
    
    def __init__(self, credential_file, verbose=False):

        with open(credential_file) as data_file:
            credentials=json.load(data_file)
            
        self.server=credentials['server']
        self.authens=(credentials['username'], credentials['password'])
        self.doi_prefix=credentials['prefix']
        self.verbose = verbose
    
            
    def log(self, mesg):
        if self.verbose:
            print(mesg)
    
    # get all dois. This seems to work only on production server.
    def get_all_dois(self):
        """
        List all DOIs suffx associated with the client account. This feature
        doesn't seem to work on test DOIs.

        """
        endpoint=self.server + '/doi'
        resp = requests.get(endpoint, auth=self.authens)
        self.log('get_all_dois: %d \n%s' % (resp.status_code, resp.text))
        
        if resp.status_code >= 200 and resp.status_code < 299:        
            return resp.text
        if resp.status_code == requests.codes.not_found:
            raise NotFound(endpoint)
        raise NotImplementedError("Unexpected status code: %d %s" % (resp.status_code, resp.text))
            
    # get doi url
    def get_doi_url(self, doi):
        """
        Retrieve a DOI url associated with a DOI. 

        :param doi: a full DOI (prefix/suffix)
        :return: the registered URL associated with the DOI
        """
        
        endpoint=self.server + '/doi/' + doi
        resp = requests.get(endpoint, auth=self.authens)
        self.log('get_doi_url %s: %d %s' % (doi, resp.status_code, resp.text))                
        
        if resp.status_code == 200:
            return resp.text
        if resp.status_code == 204:
            raise NoContent("%s has no metadata content" % (doi))            
        if resp.status_code == requests.codes.not_found:
            raise NotFound("NOT FOUND: %s" % (endpoint))
        raise NotImplementedError("Unexpected status code: %d %s" % (resp.status_code, resp.text))

    # get doi metadata
    def get_doi_metadata(self, doi):
        """
        Retrieve a DOI XML metadata associated with a DOI. 

        :param doi: a full DOI (prefix/suffix)
        :return: the registered XML metadata associated with the DOI
        """
        
        endpoint=self.server + '/metadata/' + doi
        resp = requests.get(endpoint, auth=self.authens)
        self.log('get_doi_metadata %s: %d %s' % (doi, resp.status_code, resp.text))                        

        if resp.status_code == 200:
            return resp.text
        if resp.status_code == 204:
            raise NoContent("%s has no metadata content" % (doi))
        if resp.status_code == requests.codes.not_found:
            raise NotFound("NOT FOUND: %s" % (endpoint))            
        if resp.status_code == 422:
            raise UnprocessableEntity("Metadata failed validation against the DataCite schema")
        raise NotImplementedError("Unexpected status code: %d %s" % (resp.status_code, resp.text))

    # generate an unused doi suffix through a random generator and return the full doi
    def get_unused_suffix(self):
        """
        Generate an unused suffix in the form of XXXX-XXXX based on a random number. The script will check 
        whether the DOI has been registered. If so, it will keep trying up to 100 
        times before giving up. 

        :return: an unused suffix
        """
        
        max_trials = 100
        for i in range(max_trials):
            str = base64.b32encode(bytearray(os.urandom(5))).decode("utf-8")
            print(str)
            suffix = ''.join([str[0:4], '-', str[4:]])
            doi=''.join([self.doi_prefix, '/', suffix])            
            #doi=self.doi_prefix + '/' + suffix
            try:
                self.get_doi_url(doi)
            except NotFound as e:
                return suffix
            except:
                self.log("WARNING: Problems while checking unused DOI prefix %s. Will skip this prefix." % self.doi_prefix)
        
        raise DoiNamespaceExhausted("Can't generate an unused DOI for prefix %s after %d attempts" % (self.doi_prefix, max_trials))

    # generate an unused doi suffix through a random generator and return the full doi
    def get_unused_doi(self):
        """
        Generate an unused DOI based on a random number. The script will check 
        whether the DOI has been registered. If so, it will keep trying up to 100 
        times before giving up. 

        :return: an unused DOI
        """
        return ''.join([self.doi_prefix, '/', self.get_unused_suffix()])
    
    
    # given a suffix, generate a full doi
    def compose_doi(self, suffix):
        """
        Generate an DOI based on the given suffix. 

        :return: a DOI e.g. prefix/suffix
        """
        doi= self.doi_prefix + '/' + suffix
        return doi
        
    # given a suffix, generate a full doi
    def get_full_doi_url(self, suffix):
        """
        Generate an full DOI based on the given suffix. 

        :return: a DOI URL e.g. https://doi.org/prefix/suffix
        """
        doi="https://doi.org/%s/%s" % (self.doi_prefix, suffix)
        return doi

    # create/update doi metadata 
    def register_doi(self, doi, metadata_file):
        """
        Register a DOI through a metadata file. See detail in set_doi_metadata. 

        :param doi: doi to be created/updated.
        :param metadata_file: XML metadata file containing a DOI information.
        :return: true if both metadata and url were set. Otherwise, throws UpdateDoiError.
        """
        return self.set_doi_metadata(metadata_file)

    # update doi url
    def set_doi_url(self, doi, doi_url):
        """
        Set a URL associated with a DOI

        :param doi: a DOI (prefix/suffix)
        :param doi_url: a URL associated with the DOI. 
        :return: true if the doi_url was successrully set/updated. Otherwise, throw SetDoiMetadataError.
                 Note that the doi URL can only be set after a DOI with metadata has been created.
        """
        endpoint=self.server + '/doi'

        # Form-based request (not in the API documentation)
        # resp = requests.post(endpoint, auth=self.authens, data={'doi':doi, 'url':doi_url});

        # Updated the request to follow the latest document (09/2019) 
        headers={'Content-Type':'text/plain;charset=UTF-8'}
        resp = requests.post(endpoint, auth=self.authens, headers=headers, data="doi= %(doi)s\nurl=%(url)s" % {'doi':doi, 'url':doi_url})
        
        self.log('set_doi_url (%s, %s): %d %s' % (doi, doi_url, resp.status_code, resp.text))

        if resp.status_code >= 200 and resp.status_code < 299:
            return True
        error_templ = 'Unable to set DOI URL (%s, %s): %d %s'
        # Though 412 is documented in the API spec, I saw 422 returned in this case.
        if resp.status_code == 400:
            error_templ += '. 400 Bad Request: request body must be exactly two lines: DOI and URL; wrong domain; wrong prefix'
        if resp.status_code == 412:
            error_templ += '. Precondition failed: metadata must be uploaded first'
        if resp.status_code == 422:
            error_templ += '. Bad DOI (422 This doi has already been taken)'            
        raise SetUrlError(error_templ % (doi, doi_url, resp.status_code, resp.text ))
        
    # update doi metadata
    def set_doi_metadata(self, metadata_file):
        """
        Create or update DOI XML metadata. The metatada file must contain a DOI element. 
        If the DOI hasn't been created, this opertion will create one with the provided metadata. 
        Otherwise, the metadata data associated with the existing DOI will be updated. 

        :param metadata_file: XML metadata file containing a DOI information.
        :return: true if the metadata was created/updated. Otherwise, returns false.
        """
        endpoint=self.server + '/metadata'
        headers={'Content-Type':'application/xml;charset=UTF-8'}
        f=codecs.open(metadata_file, 'r', encoding='utf-8')
        metadata=f.read()    
        resp = requests.post(endpoint, auth=self.authens, headers=headers, data=metadata.encode('utf-8'))
        f.close()
        self.log('set_doi_metadata: %s %s' %(str(resp.status_code), resp.text))

        if resp.status_code >= 200 and resp.status_code < 299:
            return True
        if resp.status_code == 422:
            raise UnprocessableEntity("Invalid XML")
        # 415: Wrong Content Type: Not including the correct content type in the header.
        # Don't need to handle this since the content type should be correct. Fold this into general error.
        raise SetMetadataError('Unable to set DOI metadata: %d %s' % (resp.status_code, resp.text) )
        
    # Deactivate DOI metadata. This put the DOI in a "registered" state. 
    # This marks a dataset as inactive (not searchable from Datacite). To activate, post a new metadata.     
    # Registered DOIs are registered with global handle system, but they are not indexed in DataCite Search.
    def delete_doi_metadata_index(self, doi):
        """
        Delete a DOI metadata from the search index. This operation will put the DOI in the "registered" state. 
        Registered DOIs are registered with global handle system, but they are not indexed in DataCite Search.

        Note: DOIs can exist in three states: draft, registered, and finable. DOIs are in the draft state 
        when metadata have been registered, and will transition to the findable state when registering a URL. 
        Finable DOIs can transitioned to the registered state when metadata are deleted. Draft DOIs can be deleted.

        :param doi: a DOI to be deleted
        :return: true if the DOI metadata was deleted. 
        """
        endpoint=self.server + '/metadata/' + doi
        resp = requests.delete(endpoint, auth=self.authens)
        self.log('delete_doi_metadata_index %s: %d %s' % (doi, resp.status_code, resp.text))
        
        if resp.status_code >= 200 and resp.status_code < 299:        
            return True
        else:
            raise DeleteMetadataError('Unable to delete DOI metadata %s: %d %s' % (doi, resp.status_code, resp.text) )

    # delete doi. Delete DOI only if the DOI in the draft state (no URL set). 
    def delete_doi(self, doi):
        """
        Delete a draft DOI from the registry. A DOI is in a draft state when it has no assigned URL. 

        Note: DOIs can exist in three states: draft, registered, and finable. DOIs are in the draft state 
        when metadata have been registered, and will transition to the findable state when registering a URL. 
        Finable DOIs can transitioned to the registered state when metadata are deleted. Draft DOIs can be deleted.

        :param doi: a DOI to be deleted
        :return: true if the DOI was deleted. 
        """
        endpoint=self.server + '/doi/' + doi
        resp = requests.delete(endpoint, auth=self.authens)
        self.log('delete_doi %s: %d %s' % (doi, resp.status_code, resp.text))
        
        if resp.status_code >= 200 and resp.status_code < 299:        
            return True
        if resp.status_code == 405:        
            return MethodNotAllowed('Unable to delete non-draft DOI (DOI with assigned URL)')
        else:
            raise DeleteMetadataError('Unable to delete DOI %s: %d %s' % (doi, resp.status_code, resp.text) )
        

# ===========================================================================

# 
# pretty print the xml content
'''
copy and paste from http://effbot.org/zone/element-lib.htm#prettyprint
it basically walks your tree and adds spaces and newlines so the tree is
printed in a nice way
'''
def indent(elem, level=0):
  i = "\n" + level*"  "
  if len(elem):
    if not elem.text or not elem.text.strip():
      elem.text = i + "  "
    if not elem.tail or not elem.tail.strip():
      elem.tail = i
    for elem in elem:
      indent(elem, level+1)
    if not elem.tail or not elem.tail.strip():
      elem.tail = i
  else:
    if level and (not elem.tail or not elem.tail.strip()):
      elem.tail = i


# ===========================================================================
# This class contains methods to manipulate datacite xml metadata tree needed to register a DOI.
#
class DataCiteXMLMetadata(object):
    """DataCiteXMLMetadata provides methods to manipulate XML metadata needed to register a DOI.

    Attributes:
       resource_tree --  the root of the XML metadata document tree.
    """ 
    resource_tree=None

    
    def __init__(self):
#        resource = ET.Element('resource')
#        resource.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
#        resource.set('xmlns', 'http://datacite.org/schema/kernel-4')
#        resource.set('xsi:schemaLocation', 'http://datacite.org/schema/kernel-4 http://schema.datacite.org/meta/kernel-4/metadata.xsd')
        self.resource_tree = self.create_resource_tree()

    # create an arbitrary root resource tree
    def create_resource_tree(self):
        """
        Create a new XML document tree. 

        :return: the root of the document tree
        """
        
        resource = ET.Element('resource')
        resource.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        resource.set('xmlns', 'http://datacite.org/schema/kernel-4')
        resource.set('xsi:schemaLocation', 'http://datacite.org/schema/kernel-4 http://schema.datacite.org/meta/kernel-4/metadata.xsd')
        return resource

    def add_identifier(self, parent, identifier):
        """
        Adding publication DOI to an existing xml resource.

        :param parent: a document node to attach the DOI to
        :param identifier: a full DOI (prefix/suffix)
        :return: the newly created node containing the DOI information
        """
        
        id = ET.SubElement(parent, 'identifier', {'identifierType':'DOI'})
        id.text = identifier
        return id

    def add_creator(self, parent, info):
        """
        Adding a publication author to an existing xml resource.

        :param parent: a document node to attach an author to
        :param titles: an author object which is a dictionary of 
                       'creatorName', 'givenName', 'familyName', 'orcid'.
        :return: the newly created node containing the author metadata
        """
        
        creator = ET.SubElement(parent, 'creator')
        keys = info.keys()
        #    print info
        if 'creatorName' in keys and info['creatorName'] is not None:
            creatorName = ET.SubElement(creator, 'creatorName')        
            creatorName.text = info['creatorName']
        if 'givenName' in keys and info['givenName'] is not None:
            givenName = ET.SubElement(creator, 'givenName')
            givenName.text = info['givenName']
        if 'familyName' in keys and info['familyName'] is not None:
            familyName = ET.SubElement(creator, 'familyName')
            familyName.text = info['familyName']
        if 'orcid' in keys and info['orcid'] is not None:
            nameIdentifier = ET.SubElement(creator, 'nameIdentifier', {'schemeURI':'http://orcid.org/','nameIdentifierScheme':'ORCID'})
            nameIdentifier.text = info['orcid']
        return creator

    def add_creators(self, parent, creators):
        """
        Adding publication authors to an existing xml resource.

        :param parent: a document node to attach the authors to
        :param titles: an array of author object
        :return: the newly created node containing the authors metadata
        """
        
        cs = ET.SubElement(parent, 'creators')
        for creator in creators:
            self.add_creator(cs, creator)
        return cs

    def add_titles(self, parent, titles):
        """
        Adding publication titles to an existing xml resource.

        :param parent: a document node to attach the titles to
        :param titles: an array of titles
        :return: the newly created node containing the titles metadata
        """
        
        ts = ET.SubElement(parent, 'titles')
        for title in titles:
            t = ET.SubElement(ts, 'title', {'xml:lang':'en'})
            t.text = title
        return ts

    def add_publisher(self, parent, publisher):
        """
        Adding publisher metatata to an existing xml resource.

        :param parent: a document node to attach the publisher information to
        :param publisher: a publisher name
        :return: the newly created node containing the publisher metadata
        """
        
        pub = ET.SubElement(parent, 'publisher')
        pub.text = publisher
        return pub

    def add_publication_year(self, parent, year=str(date.today().year)):
        """
        Adding publication year to an existing xml resource.

        :param parent: a document node to attach the publication year to
        :param year: a publication year text
        :return: the newly created node containing the publication year metadata
        """

        pub_year = ET.SubElement(parent, 'publicationYear')
        pub_year.text = year
        return pub_year    

    def add_alternative_identifier(self, parent, alt_id):
        """
        Adding alternative identifier to an existing xml resource.

        :param parent: a document node to attach alternative identifier to
        :param alt_id: an alternate identifier 
        :return: the newly created node containing the alternate id metadata
        """
        
        id = ET.SubElement(parent, 'alternativeIdentifier')
        id.text = alt_id

    def add_subjects(self, parent, subjects=['Dataset']):
        """
        Adding subjects to an existing xml resource.

        :param parent: a document node to attach subjects to
        :param subjects: an array of text, each representing a subject
        :return: the newly created node containing the subjects metadata
        """
        
        subs = ET.SubElement(parent, 'subjects')    
        for s in subjects:
            sub = ET.SubElement(subs, 'subject', {'xml:lang':'en'})
            sub.text = s
        return subs

    def add_language(self, parent, language="en"):
        """
        Adding a language metadata to an existing xml resource.

        :param parent: a document node to attach the language to
        :param language: a string representing the language
        :return: the newly created node containing the language metadata
        """
        
        lang = ET.SubElement(parent, 'language')
        lang.text = language
        return lang

    def add_resource_type(self, parent, type="Dataset"):
        """
        Adding a resource_type metadata to an existing xml resource.

        :param parent: a document node to attach the resource type to
        :param type: a string representing the resource type. Currently, the script only 
                     support 'Dataset'. Other type will be ignored.
        :return: the newly created node containing the resource type metadata
        """
        resourceTypeGeneralMapping = {
            "Dataset": "Dataset",
            "Video": "Audiovisual"
        }

        rtype = ET.SubElement(parent, 'resourceType')
        rtype_general = resourceTypeGeneralMapping.get(type)
        if rtype_general is not None:
            rtype.set('resourceTypeGeneral', rtype_general)
        rtype.text = type
            
        return rtype

    def add_version(self, parent, version="1.0"):
        """
        Adding a version metadata to an existing xml resource.

        :param parent: a document node to attach the version to
        :param version: a version string
        :return: the newly created node containing the version information
        """
        
        v = ET.SubElement(parent, 'version')
        v.text = version
        return v

    def add_descriptions(self, parent, descriptions):
        """
        Adding an array of descriptions an existing xml resource.

        :param parent: a document node to attach the descriptions to
        :param funders: an array of description texts
        :return: the newly created node containing the descriptions
        """
        
        descs = ET.SubElement(parent, 'descriptions')
        for description in descriptions:
            desc = ET.SubElement(descs, 'description', {'xml:lang':'en','descriptionType':'Abstract'})
            desc.text = description
        return descs

    def add_funding_reference(self, parent, info):
        """
        Adding a funding reference to an existing xml resource.

        :param parent: a document node to attach the funding reference to
        :param info: a funding object which is a dictionary of 
                     'funderName', 'funderIdentifier', 'funderIdentifierType', 'awardNumber',
                     'awardURI', and 'awardTitle'
        :return: the newly created node containing funding reference
        """
        
        funder = ET.SubElement(parent, 'fundingReference')
        keys = info.keys()
        #    print info
        if 'funderName' in keys and info['funderName'] is not None:
            name = ET.SubElement(funder, 'funderName')
            name.text = info['funderName']
        if 'funderIdentifier' in keys and info['funderIdentifier'] is not None:
            identifier = ET.SubElement(funder, 'funderIdentifier')
            identifer.text = info['funderIdentifier']
            if 'funderIdentifierType' in keys and info['funderIdentifierType'] is not None:
                identifier.set('funderIdentifierType', info['funderIdentifierType'])
        if 'awardNumber' in keys and info['awardNumber'] is not None:
            awardNumber = ET.SubElement(funder, 'awardNumber')
            awardNumber.text = info['awardNumber']
            if 'awardURI' in keys and info['awardURI'] is not None:
                awardNumber.set('awardURI', info['awardURI'])
        if 'awardTitle' in keys and info['awardTitle'] is not None:
            awardTitle = ET.SubElement(funder, 'awardTitle')
            awardTitle.text = info['awardTitle']        
        return funder

    def add_funding_references(self, parent, funders):
        """
        Adding an array of funding references to an existing xml resource.

        :param parent: a document node to attach the funding references to
        :param funders: an array of funding reference objects
        :return: the newly created node containing funding references
        """
        
        fs = ET.SubElement(parent, 'fundingReferences')
        for funder in funders:
            self.add_funding_reference(fs, funder)
        return fs

    def write_resource_tree(self, filename="/tmp/metadata.xml"):
        """
        Write the XML resource tree to a file. 

        :param filename: file path that the metadata will be written to
        """
        indent(self.resource_tree)
        tree = ET.ElementTree(self.resource_tree)
        tree.write(filename, xml_declaration=True, encoding='utf-8', method="xml")

    

# =============================================================================
'''
Create datacite metadata file in a specified filename based on the dataset dictionary. 
This function assumes a certain structure of the dataset. Here is an example of the expected structure.
dataset1 = {
    'creators' : [{'creatorName':'Andrew McMahon', 'givenName':'Andrew', 'familyName':'McMahon'}],
    'titles' : ['Whole-mount 3D views of the human nephrogenic niche and kidneys'],
    'descriptions': ['A collection of human embryonic and fetal 3D views of whole kidneys and nephrogenic niches. CS19-Week11.'],
    'publisher' : ISRD_PROJECTS['GUDMAP']['projectReference'],
    'publicationYear' : str(date.today().year),
    'subjects' : ['Dataset', 'Biology', 'Kidney', 'Immunofluorescence videos'],
    'language' : 'en',
    'resourceType' : 'Dataset',
    'version' : '1',
    'fundingReferences' : [ ISRD_PROJECTS['GUDMAP'] ],
    'rid' : 'R-1234',
    'url' : 'https://www-gudmap3.gudmap.org/chaise/record/#2/Common:Collection/RID=R-1234'
}
'''
def create_datacite_metadata(doi, filename, dataset):
    dcm = DataCiteXMLMetadata()
    root = dcm.resource_tree
    dcm.add_identifier(root, doi)

    keys = dataset.keys()

    # TODO: check mandatory fields and throw an error if missing
    if (dataset.get('creators') is None or dataset.get('titles') is None):
        print('creators, titles are mandatory')
        return None
        
    if 'creators' in keys:
        dcm.add_creators(root, dataset['creators'])
    
    if 'titles' in keys:
        dcm.add_titles(root, dataset['titles'])
    
    if 'descriptions' in keys:        
        dcm.add_descriptions(root, dataset['descriptions'])
    
    if 'publisher' in keys:                
        dcm.add_publisher(root, dataset['publisher'])
    
    if 'publicationYear' in keys:                
        dcm.add_publication_year(root, dataset['publicationYear'])
    else:
        dcm.add_publication_year(root, str(date.today().year))
    
    if 'subjects' in keys:                
        dcm.add_subjects(root, dataset['subjects'])
    
    if 'language' in keys:                
        dcm.add_language(root, dataset['language'])
    else:
        dcm.add_language(root, 'en')
    
    if 'resourceType' in keys:                
        dcm.add_resource_type(root, dataset['resourceType'])
    else:
        dcm.add_resource_type(root, 'Dataset')
    
    if 'version' in keys:                        
        dcm.add_version(root, dataset['version'])
    else:
        dcm.add_version(root, '1')
    
    if 'fundingReferences' in keys:
        dcm.add_funding_references(root, dataset['fundingReferences'])

    # write metadata tree to a file
    dcm.write_resource_tree(filename)

    return root


# -----------------------------------------------------------------

def print_all_dois(datacite_credential):
    dc=DataCiteMDS(datacite_credential, True)
    print("%s " % (dc.get_all_dois()))


def create_new_doi(datacite_credential, dataset):
    dc=DataCiteMDS(datacite_credential, True)

    # generate a random unused_doi
    #new_doi = dc.get_unused_doi()

    # Use RID for DOI
    new_doi = dc.compose_doi(dataset['rid'])

    file_location='/tmp/metadata.xml'
    dc.log('Creating new doi: %s ' % new_doi)
    
    create_datacite_metadata(new_doi, file_location, dataset)
    dc.set_doi_metadata(file_location)
    dc.set_doi_url(new_doi, dataset['url'])    
    # dc.delete_doi_metadata_index(new_doi)
    # dc.get_doi_metadata(file_location)    

    
def print_doi(datacite_credential, doi_suffix):
    """ Given a doi_suffix such as RID, print doi metadata and URL from DataCite registry.
    """
    dc=DataCiteMDS(datacite_credential, True)
    doi = dc.get_full_doi_url(doi_suffix)
    try:
        dc.get_doi_metadata(doi)                
        dc.get_doi_url(doi)
    except Exception as e:
        print("ERROR: Can't print DOI suffix %s due to %s" % (doi_suffix, e))

    
def delete_doi(datacite_credential, doi_suffix):
    """ Given a doi_suffix such as RID, delete doi from DataCite registry.
    """
    dc=DataCiteMDS(datacite_credential, True)
    #dc.delete_doi_metadata_index(dc.compose_doi(doi_suffix))
    dc.delete_doi(dc.compose_doi(doi_suffix))    


def test():
    # -- test
    ISRD_PROJECTS={
        'GUDMAP' : {
            'publisher':'GUDMAP (www.gudmap.org)',
            'funderName':'National Institute of Health (NIH)',
            'awardNumber':'5U24DK110814',
            'awardTitle':'USC GUDMAP Coordinating Center'
        }
    }
    
    ds = {
        'creators' : [{'creatorName':'Andrew McMahon', 'givenName':'Andrew', 'familyName':'McMahon'}],
        'titles' : ['Whole-mount 3D views of the human nephrogenic niche and kidneys'],
        'descriptions': ['A collection of human embryonic and fetal 3D views of whole kidneys and nephrogenic niches. CS19-Week11.'],
        'publisher' : ISRD_PROJECTS['GUDMAP']['publisher'],
        'publicationYear' : str(date.today().year),
        'subjects' : ['Dataset', 'Biology', 'Kidney', 'Immunofluorescence videos'],
        'language' : 'en',
        'resourceType' : 'Dataset',
        'version' : '1',
        'fundingReferences' : [ ISRD_PROJECTS['GUDMAP'] ],
        'rid' : 'R-1234-0',
        'url' : 'https://www.gudmap.org/chaise/record/#2/Common:Collection/RID=R-1234-0'
    }

    credential = 'test-kidney.json'

    # generate a random unused_doi
    dc = DataCiteMDS(credential, False)    
    #doi_suffix = dc.get_unused_suffix()
    doi_suffix = 'R-2345-7'
    
    ds['rid'] = doi_suffix
    ds['url'] = 'https://www.gudmap.org/chaise/record/#2/Common:Collection/RID=%s' % (doi_suffix)
    
    create_new_doi(credential, ds)
    delete_doi(credential, doi_suffix)
    # dc.delete_doi_metadata_index(dc.compose_doi(doi_suffix))    
    print_doi(credential, doi_suffix)
    print_all_dois(credential)
    
    
#test()

