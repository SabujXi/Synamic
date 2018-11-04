import re
from synamic.core.parsing_systems.curlybrace_parser import SydParser  #covert_one_value
from collections import OrderedDict, namedtuple
_operators_map = OrderedDict([
    ('contains', 'CONTAINS'),
    ('!contains', 'NOT_CONTAINS'),
    ('in', 'IN'),
    ('!in', 'NOT_IN'),
    ('==', 'EQ'),
    ('!=', 'NOT_EQ'),
    ('>=', 'GTE'),
    ('<=', 'LTE'),
    ('>', 'GT'),
    ('<', 'LT')
])


class Parser:
    __OPERATORS_MAP = _operators_map.copy()
    __LOGICAL_OPS = {'|', '&'}

    Section = namedtuple('Section', ('id', 'op', 'value', 'logic'))

    class Pattern:
        identifier = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*')
        ws = re.compile(r'\s+')
        before_and_or = re.compile(r'[^&|]*')

    def __init__(self, txt):
        self.__txt = txt
        self.__pos = 0
        self.__sections = []
        self.__current_section = []

    def reset_current_section(self):
        current_section = list(self.__current_section)
        if len(current_section) == 3:
            current_section.append(None)
        section = self.Section(*current_section)
        self.__sections.append(section)
        self.__current_section.clear()

    def on_error(self):
        err_before_txt = '_' * self.__pos
        err_after_txt = '^' * (len(self.__txt) - self.__pos - 1)
        err_txt = '\n' + self.__txt + '\n' + err_before_txt + err_after_txt

        raise Exception("Error at %s: %s" % (self.__pos, err_txt))

    def expect_id(self):
        match = self.Pattern.identifier.match(self.__txt, self.__pos)
        if not match:
            self.on_error()
        else:
            identifier = match.group()
            self.__pos = match.end()
            self.__current_section.append(identifier)
            return True
        return False

    def skip_ws(self):
        match = self.Pattern.ws.match(self.__txt, self.__pos)
        if match:
            self.__pos = match.end()

    def expect_ws(self):
        match = self.Pattern.ws.match(self.__txt, self.__pos)
        if match:
            self.skip_ws()
            return True
        else:
            self.on_error()
        return False

    def expect_operator(self):
        matched_op = None
        for op in self.__OPERATORS_MAP.keys():
            if self.__txt[self.__pos:].startswith(op):
                matched_op = op
                break
        if matched_op is None:
            self.on_error()
        else:
            self.__pos += len(matched_op)
            self.__current_section.append(matched_op)
            return True
        return False

    def expect_or_and_end(self):
        if self.__pos + 1 >= len(self.__txt):
            self.reset_current_section()
            return True
        elif self.__txt[self.__pos:].startswith(('&', '|')):
            value = self.__txt[self.__pos:self.__pos+1]
            # and_or = 'OR' if value == '|' else 'AND'
            self.__current_section.append(value)
            self.reset_current_section()
            self.__pos += 1
            return True
        else:
            self.on_error()
        return False

    def grab_value_until_and_or(self):
        match = self.Pattern.before_and_or.match(self.__txt, self.__pos)
        if match:
            value = match.group().strip()
            if value != '':
                self.__pos = match.end()
                self.__current_section.append(value)
                return True
            else:
                self.on_error()
        else:
            self.on_error()
        return False

    def parse(self):
        """
        title == something | type in go, yes & age > 6
        """
        # find identifier, operator
        # find value until you encounter and (&) or or (|)

        while self.__pos < len(self.__txt) - 1:
            # print(self.__sections)
            self.skip_ws()

            self.expect_id()
            self.expect_ws()

            self.expect_operator()
            self.expect_ws()

            self.grab_value_until_and_or()

            self.expect_or_and_end()
            self.skip_ws()
        sections = tuple(self.__sections)
        self.__pos = 0
        self.__sections.clear()
        # validation
        for idx, section in enumerate(sections):
            if idx == len(sections) - 1:
                assert section.logic is None
            else:
                assert section.logic is not None

        # convert values according to syd system.
        _ = []
        for section in sections:
            _.append(self.Section(
                section[0],
                section[1],
                SydParser.covert_one_value(section[2]),
                section[3])
            )
        sections = tuple(_)
        return sections


def test(query):
    tokens = Parser(query).parse()
    for token in tokens:
        print(token)


if __name__ == '__main__':
    test('  x > 1 | time > 12:24     AM | a > b & c in d | d in ~hh        & m contains tag 1, tag 2 & n !in go sfsdfsdf')
