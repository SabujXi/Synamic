from synamic.core.classes.static import StaticContent
from synamic.core.classes.path_tree import ContentPath2


def synamic_add_static_content(synamic, file_path):
    self = synamic
    assert type(file_path) is ContentPath2
    static_content = StaticContent(self, file_path)
    self.add_content(static_content)
    return static_content
