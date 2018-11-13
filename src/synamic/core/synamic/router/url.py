"""
    author: "Md. Sabuj Sarker"
    copyright: "Copyright 2017-2018, The Synamic Project"
    credits: ["Md. Sabuj Sarker"]
    license: "MIT"
    maintainer: "Md. Sabuj Sarker"
    email: "md.sabuj.sarker@gmail.com"
    status: "Development"
"""

import re
import urllib.parse
from typing import Union
from synamic.core.contracts import CDocType


class ContentUrl:
    @classmethod
    def __str_path_to_comps(cls, path_str):
        comps = []
        for url_comp in re.split(r'[\\/]+', path_str):
            comps.append(url_comp)
        return comps

    @classmethod
    def __sequence_to_comps(cls, path_sequence):
        comps = []
        for url_comp in path_sequence:
            assert isinstance(url_comp, str)
            comps.extend(
                cls.__str_path_to_comps(url_comp)
            )
        return comps

    @classmethod
    def path_to_components(cls, *url_path_comps: Union[str, list, tuple]) -> tuple:
        res_url_path_comps = []
        for _comps in url_path_comps:
            if isinstance(_comps, str):
                res_url_path_comps.extend(cls.__str_path_to_comps(_comps))
            elif isinstance(_comps, (list, tuple)):
                res_url_path_comps.extend(cls.__sequence_to_comps(_comps))
            else:
                raise Exception('Invalid argument for url component: %s' % str(url_path_comps))

        # ignore empty ones
        _ = []
        for idx, comp in enumerate(res_url_path_comps):
            if idx in (0, len(res_url_path_comps) - 1):  # sparing the first and last empty string only
                _.append(comp)
            else:
                if comp != '':
                    _.append(comp)
                # else ignore
        res_url_path_comps = _

        # ../../../ recalculation and empty string removing from middle
        _ = []
        for idx, comp in enumerate(res_url_path_comps):
            if comp == '.':
                # just ignore it
                continue
            elif comp == '..':
                #  delete the last comp and add current one (replace the last one)
                if idx == 0:
                    continue
                else:
                    if len(_) >= 1:
                        del _[-1]
            else:
                _.append(comp)
        res_url_path_comps = _

        # re-adding empty string for zero length comps
        if len(res_url_path_comps) == 0:
            res_url_path_comps.append('')

        # comps should begin with empty string ... we can only handle site root absolute url as there is no context for
        # relative url in this function.
        elif res_url_path_comps[0] != '':
            res_url_path_comps.insert(0, '')
            # TODO: unlike file system path, this last '' should be removed for len(comps) > 1
            # HTML (both gen & non-gen) cdoctype url that does not end with a file extension will have /index.html (take
            # from settings) as real file system url and for browser (client) representation it will end with /.
            # So, for html cdoctype'd urls that have a file extension (place checking so that it does not exceed
            # certain length + the last comp does not start with a dot '.' )
            #  will not end with / for client representation.

        # ['', ''] issue
        if list(res_url_path_comps) == ['', '']:  # eg ['', ''] == '/'.split('/')
            res_url_path_comps = ['']

        # validating
        for idx, url_comp in enumerate(res_url_path_comps):
            assert not re.match(r'^\s+$', url_comp), "A component of an url cannot be one or all whitespaces"

        return tuple(res_url_path_comps)

    def __init__(self, site, url_path_comps, for_cdoctype=CDocType.UNSPECIFIED):
        """
        append_slash is only for dynamic contents and only when the url_path_comps is being passed as sting (not: list, tuple, content path)
        So, we are not persisting that data
        
        'index.html' in lower case is special throughout the url system - see the codes for extracting more info.
        
        if we indicate ...
        """
        assert isinstance(for_cdoctype, CDocType), \
            f'cURL without a CDocType specified is not acceptable. When you are not going to use the url for final url '\
            f'generation (e.g. for query by url only) you should specify CDocType.UNSPECIFIED\n'\
            f'The type you provided was {type(for_cdoctype)} with the value {for_cdoctype}'
        # TODO: make appending slash system  settings based.
        if CDocType.is_html(for_cdoctype):
            self.__url_path_comps = self.path_to_components(
                url_path_comps, '/'
            )
        else:
            self.__url_path_comps = self.path_to_components(
                url_path_comps
            )

        self.__site = site
        self.__for_cdoctype = for_cdoctype
        # TODO: fix this
        # assert type(self.__for_cdoctype) is CDocType
        # assert CDocType.is_text(self.__for_cdoctype) or CDocType.is_binary(self.__for_cdoctype) or\
        #     self.__for_cdoctype == CDocType.DIRECTORY
        self.__path_str = None
        self.__path_components_w_site = None
        self.__url_str = None

    def clone(self, for_cdoctype=CDocType.UNSPECIFIED):
        """Besides copying, usable when trying different type of content in router. e.g. static content need path gen"""
        return self.__class__(self.__site, self.__url_path_comps, for_cdoctype=for_cdoctype)

    @property
    def for_site(self):
        return self.__site

    @property
    def for_cdoctype(self):
        return self.__for_cdoctype

    @staticmethod
    def __join_path_comps(comps):
        # comps must be a result of to_path_components/self.__url_path_comps
        if comps == ('',):
            path_str = '/'
        else:
            path_str = '/'.join(comps)
        return path_str

    def join(self, url_comps: Union[str, list, tuple], for_cdoctype=CDocType.UNSPECIFIED):
        this_comps = self.__url_path_comps
        other_comps = self.path_to_components(url_comps)

        this_end = this_comps[-1]
        other_start = other_comps[0]

        if this_end != '' and other_start != '':
            comps = this_comps[:-1] + (this_end + other_start,) + other_comps[1:]
        elif this_end == '' or other_start == '':
            if this_end == '' and other_start == '':
                res_comp = ''
            elif this_end == '':
                res_comp = other_start
            else:
                assert other_start == ''
                res_comp = this_end
            comps = this_comps[:-1] + (res_comp,) + other_comps[1:]
        else:
            comps = this_comps + other_comps
        if for_cdoctype is None:
            for_cdoctype = self.__for_cdoctype
        return self.__class__(self.__site, comps, for_cdoctype)

    @property
    def path_components(self):
        return self.__url_path_comps

    @property
    def path_components_w_site(self):
        if self.__path_components_w_site is None:
            host_base_path = self.__site.object_manager.get_site_settings()['host_base_path']
            self.__path_components_w_site = self.path_to_components(
                host_base_path, self.__site.id.components, self.__url_path_comps
            )
        return self.__path_components_w_site

    @property
    def path_as_str(self):
        assert self.__for_cdoctype is not CDocType.UNSPECIFIED
        if self.__path_str is None:
            comps = self.path_components
            if comps == ('', ):
                path_str = '/'
            else:
                path_str = '/'.join(comps)
            self.__path_str = path_str
        return self.__path_str

    @property
    def path_as_str_w_site(self):
        assert self.__for_cdoctype is not CDocType.UNSPECIFIED
        if self.__path_str is None:
            self.__path_str = self.__join_path_comps(self.path_components_w_site)
        return self.__path_str

    @property
    def path_as_str_encoded(self):
        assert self.__for_cdoctype is not CDocType.UNSPECIFIED
        return urllib.parse.quote_plus(self.path_as_str, safe='/:#', encoding='utf-8')

    @property
    def path_as_str_w_site_encoded(self):
        assert self.__for_cdoctype is not CDocType.UNSPECIFIED
        return urllib.parse.quote_plus(self.path_as_str_w_site, safe='/:#', encoding='utf-8')

    @property
    def url(self):
        """URL with host name, port, path"""
        assert self.__for_cdoctype is not CDocType.UNSPECIFIED
        if self.__url_str is None:
            ss = self.__site.object_manager.get_site_settings()
            host_scheme = ss['host_scheme']
            hostname = ss['hostname']
            port = str(ss['host_port'])
            if port:
                port_part = ':' + port
            else:
                port_part = ''
            _ = host_scheme + '://' + hostname + port_part + self.path_as_str_w_site
            self.__url_str = _
        return self.__url_str

    @property
    def url_encoded(self):
        assert self.__for_cdoctype is not CDocType.UNSPECIFIED
        return urllib.parse.quote_plus(self.url, safe='/:#', encoding='utf-8')

    @property
    def to_file_system_path(self):
        p = self.path_as_str
        if CDocType.is_html(self.__for_cdoctype):
            index_file_name = self.__site.object_manager.get_site_settings()['index_file_name']
            if p.endswith('/'):
                p += index_file_name
            else:
                p += '/' + index_file_name
        else:
            # validation
            # assert not p.endswith('/')
            pass
        return p

    @property
    def is_file(self):
        return CDocType.is_file(self.__for_cdoctype)

    @property
    def to_cpath(self):
        return self.__site.path_tree.create_cpath(
            self.to_file_system_path,
            is_file=self.is_file
        )

    def __str__(self):
        # same as self.path_as_str_w_site, but cannot use that property due to CDocType check issue.
        # keep this method synced with self.path_as_str_w_site
        path_str = self.__join_path_comps(self.path_components_w_site)
        return f'CURL: {path_str}'

    def __repr__(self):
        return repr(self.__str__())

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.path_components_w_site == other.path_components_w_site

    def __hash__(self):
        return hash(self.path_components_w_site)

    @classmethod
    def parse_requested_url(cls, synamic, url_str):
        # python urlparse // bug workaround
        url_str = re.sub(r'(?<!:)/+', '/', url_str)

        parsed_url = urllib.parse.urlparse(url_str)
        url_path = parsed_url.path
        # Unused for now: url_query = parsed_url.query
        # Unused for now: url_fragment = parsed_url.fragment
        path_segments = list(cls.path_to_components(url_path))
        assert path_segments[0] == ''  # logical validation of path to components
        path_segments = path_segments[1:]
        # del path_segments[0]
        # partition at special url comp
        site_ids_comps = sorted([site_id.components for site_id in synamic.sites.ids], key=len, reverse=True)
        url_partition_comp = synamic.default_data.get_syd('settings')['url_partition_comp']

        site_id_components, path_components, special_components = [], [], []
        #  extract out site id.
        for site_id_comps in site_ids_comps:
            if len(path_segments) < len(site_id_comps):
                continue
            if tuple(path_segments[:len(site_id_comps)]) == tuple(site_id_comps):
                site_id_components = path_segments[:len(site_id_comps)]
                path_segments = path_segments[len(site_id_comps):]
                break

        # extract out paginated part
        assert '/' not in url_partition_comp
        assert ' ' not in url_partition_comp
        for idx, segment in enumerate(path_segments):
            if segment == url_partition_comp:
                special_components.extend(
                    path_segments[idx+1:]
                )
                break
            else:
                path_components.append(segment)

        site_id = synamic.sites.make_id('/'.join(site_id_components))

        return site_id, path_components, special_components
