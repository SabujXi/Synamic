from synamic.core.synamic.router.url import ContentUrl
from synamic.core.contracts import DocumentType


class RouterService:
    def __init__(self, synamic):
        self.__synamic = synamic
        self.__is_loaded = False

    def load(self):
        self.__is_loaded = True

    def get_content(self, url_str: str):
        site_id, path_components, special_components = ContentUrl.parse_requested_url(self.__synamic, url_str)
        # print("Path comps: %s" % str(path_components))
        try:
            site = self.__synamic.sites.get_by_id(site_id)
        except KeyError:
            site = None

        if site is None:
            content = None
        else:
            # step 1: search for static/binary file in file system with the path components : TODO: do for static.
            # step 2 if 1 fails: search for non-static content and in this case the url is already cached.
            url_object = ContentUrl(site, path_components, DocumentType.NONE)
            content = self.get_content_by_url(site, url_object)
            if content is None:
                url_object = ContentUrl(site, path_components, DocumentType.HTML_DOCUMENT)
                content = self.get_content_by_url(site, url_object)
        return content

    def get_content_by_url(self, site, url_object):
        """Forgiving function that returns None"""
        if DocumentType.is_text(url_object.for_document_type):
            content_cpath = site.object_manager.get_text_cpath_by_curl(url_object)
            if content_cpath is not None:
                return site.object_manager.get_text_content(content_cpath)
            else:
                return None
        else:
            # TODO: fix bug: a.txt /a.txt/ and /a.txt work the same - /a.txt/ is most weird
            statics_dir = self.__synamic.default_configs.get('dirs')['statics.statics']
            contents_dir = self.__synamic.default_configs.get('dirs')['contents.contents']
            statics_cpath = site.object_manager.get_path_tree().create_file_cpath([statics_dir, url_object.to_file_system_path])
            contents_cpath = site.object_manager.get_path_tree().create_file_cpath([contents_dir, url_object.to_file_system_path])
            if statics_cpath.exists():
                return site.object_manager.get_binary_content(statics_cpath)
            elif contents_cpath.exists():
                return site.object_manager.get_binary_content(contents_cpath)
            else:
                return None

    @classmethod
    def make_url(cls, site, url_path_comps, for_document_type=None):
        return ContentUrl(site, url_path_comps, for_document_type=for_document_type)