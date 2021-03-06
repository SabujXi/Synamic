"""
    author: "Md. Sabuj Sarker"
    copyright: "Copyright 2017-2018, The Synamic Project"
    credits: ["Md. Sabuj Sarker"]
    license: "MIT"
    maintainer: "Md. Sabuj Sarker"
    email: "md.sabuj.sarker@gmail.com"
    status: "Development"
"""

from markupsafe import Markup
from synamic.core.standalones.functions.md import render_content_markdown


class Html:
    def __init__(self, html_str):
        self.__html_str = html_str
        self.__markup_safe = Markup(html_str)
        self.__plain_text = None

    @property
    def as_plain_text(self):
        if self.__plain_text is None:
            self.__plain_text = self.__markup_safe.striptags()
        return self.__plain_text

    def get_summary(self, limit=None):
        if limit is not None:
            return self.as_plain_text[:limit]
        else:
            return self.as_plain_text

    @property
    def as_str(self):
        return self.__html_str

    @property
    def as_markup(self):
        """Returns markup object from markupsafe"""
        return self.__markup_safe

    def __str__(self):
        return self.__html_str

    def __repr__(self):
        return repr(self.__str__())


class Markdown:
    def __init__(self, site, md_str, value_pack=None, md_cpath=None, cfields=None):
        self.__site = site
        self.__md_str = md_str
        self.__value_pack = value_pack
        self.__md_cpath = md_cpath
        self.__cfields = cfields
        self.__html_obj = None
        self.__plain_text = None
        self.__rendered_text = None

    @property
    def rendered_markdown(self):
        if self.__rendered_text is None:
            self.__rendered_text = render_content_markdown(self.__site, self.__md_str, value_pack=self.__value_pack, md_cpath=self.__md_cpath, cfields=self.__cfields)
        return self.__rendered_text

    @property
    def as_html(self):
        rendered_txt = self.rendered_markdown
        if self.__html_obj is None:
            self.__html_obj = Html(rendered_txt)
        return self.__html_obj

    @property
    def as_markup(self):
        return self.as_html.as_markup

    @property
    def as_plain_text(self):
        return self.as_html.as_plain_text

    def get_summary(self, limit=None):
        if limit is not None:
            return self.as_plain_text[:limit]
        else:
            return self.as_plain_text

    @property
    def as_str(self):
        return self.__md_str

    def __str__(self):
        return self.__md_str

    def __repr__(self):
        return repr(self.__str__())
