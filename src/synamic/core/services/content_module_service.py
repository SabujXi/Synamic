import io
import re
import mimetypes
from synamic.core.classes.pagination import PaginationStream
from synamic.core.contracts import BaseContentModuleContract, ContentContract
from synamic.core.contracts.document import MarkedDocumentContract
from synamic.core.functions.decorators import not_loaded, loaded
from synamic.core.functions.frontmatter import parse_front_matter
from synamic.core.functions.yaml_processor import load_yaml
from synamic.core.classes.frontmatter import Frontmatter
from synamic.core.classes.url import ContentUrl
from markupsafe import Markup
from synamic.core.functions.normalizers import normalize_key
from synamic.core.functions.md import render_markdown
from synamic.core.classes.mapping import FinalizableDict
from synamic.core.new_parsers.document_parser import DocumentParser

_invalid_url = re.compile(r'^[a-zA-Z0-9]://', re.IGNORECASE)


class MarkedContentImplementation(MarkedDocumentContract):
    def __init__(self, config, path_object, file_content: str):
        self.__config = config
        self.__path = path_object
        self.__content_type = ContentContract.types.DYNAMIC
        self.__file_content = file_content

        self.__body = None
        self.__fields = None

        self.__url = None

        # loading body and field
        doc = DocumentParser(self.__file_content).parse()

        res_map = self.__config.model_service.get_converted('text', doc.root_field, doc.body)
        print("Resp Map : %s" % res_map)
        self.__body = res_map['__body__']
        # del res_map['__body__']
        self.__fields = res_map
        print("Resp Map2: %s" % res_map)

    # temporary for fixing sitemap
    @property
    def config(self):
        return self.__config

    @property
    def path_object(self):
        return self.__path

    @property
    def content_id(self):
        return self.fields.get('id', None)

    def get_stream(self):
        template_name = self.fields.get('template', None)
        res = self.__config.templates.render(template_name, content=self.get_content_wrapper())
        f = io.BytesIO(res.encode('utf-8'))
        return f

    @property
    def content_type(self):
        return self.__content_type

    @property
    def mime_type(self):
        mime_type = 'octet/stream'
        path = self.url_object.real_path
        type, enc = mimetypes.guess_type(path)
        if type:
            mime_type = type
        return mime_type

    @property
    def body(self):
        return self.__body

    @property
    def fields(self):
        return self.__fields

    @property
    def url_object(self):
        if self.__url is None:
            print("Fields: %s" % self.fields)
            self.__url = ContentUrl(self.__config, self.fields['permalink'])
        return self.__url

    @property
    def absolute_url(self):
        return self.url_object.full_url

    def get_content_wrapper(self):
        # TODO: should place in contract!
        # So, with cotract it can be used in paginator too
        return ContentWrapper(self)

    def __str__(self):
        return self.path_object.relative_path

    def __repr__(self):
        return str(self)


class ContentWrapper:
    __slots__ = ('__content',)

    def __init__(self, content):
        self.__content = content

    def __getattr__(self, item):
        return getattr(self.__content, item)

    @property
    def id(self):
        return self.__content.content_id

    @property
    def url_path(self):
        return self.__content.url_object.path


class MarkedContentService(BaseContentModuleContract):
    __slots__ = ('__config', '__is_loaded', '__contents_by_id', '__dynamic_contents', '__auxiliary_contents')

    def __init__(self, _cfg):
        self.__config = _cfg
        self.__is_loaded = False
        self.__service_home_path = None

    @property
    def service_home_path(self):
        if self.__service_home_path is None:
            self.__service_home_path = self.__config.path_tree.create_path(('content', ))
        return self.__service_home_path

    @property
    def name(self):
        return 'content'

    @property
    def config(self):
        return self.__config

    @property
    def is_loaded(self):
        return self.__is_loaded

    @not_loaded
    def load(self):
        paths = self.__config.path_tree.list_file_paths(*self.service_home_path.relative_path_components)
        print(paths)

        for file_path in paths:
            if file_path.extension.lower() in {'md', 'markdown'}:
                with file_path.open("r", encoding="utf-8") as f:
                    text = f.read()
                    content_obj = MarkedContentImplementation(self.__config, file_path, text)

                    content_id = content_obj.fields.get('id', None)
                    # if content_id in self.__dynamic_contents:
                    #     if content_obj.content_id is not None:
                    #         raise Exception("Duplicate `{module_name}` content id. It is `{content_id}`".format(module_name=self.name, content_id=content_obj.id))
                    self.__config.add_document(content_obj)
            else:
                self.__config.add_static_content(file_path, self)
        self.__is_loaded = True