# location_trie.py -
# a singleton class for a trie that contains the names of physical locations like schools, towns, and cities

import re
from spellchecker import SpellChecker
from names_dataset import NameDataset

spell_checker = SpellChecker()

name_dataset = NameDataset()

class TrieNode(object):
    """
    A node in our trie that contains the connections to its children nodes.
    Since we are storing the names of places (which can contain spaces) this forms a 27-ary tree rather than 26-ary.
    """
    def __init__(self):
        self.children = {}
        self.is_solution = False


trie_root = TrieNode()


def add_to_trie(string):
    curr_node = trie_root

    for char in string:

        if char not in curr_node.children.keys():
            new_node = TrieNode()
            curr_node.children[char] = new_node
        curr_node = curr_node.children[char]

    curr_node.is_solution = True


def is_in_trie(curr_node, string, wrong_characters=1, extra_characters=1, missing_characters=1):
    if not string:
        return curr_node.is_solution

    curr_char = string[0]

    # If the next character is correct, just move along the trie as needed
    if curr_char in curr_node.children.keys():
        next_node = curr_node.children[curr_char]
        return is_in_trie(next_node, string[1:], wrong_characters, extra_characters, missing_characters)
    else:

        # We can allow a query to be off by one letter, like in "Henlo"
        # In that case, we search for a replacement character that creates a solution
        if wrong_characters:
            for char in curr_node.children.keys():
                next_node = curr_node.children[char]
                solution_with_wrong_character = is_in_trie(next_node, string[1:], wrong_characters-1, extra_characters, missing_characters)
                if solution_with_wrong_character:
                    return True

        # We can potentially allow for extra characters, like "Helllo"
        # In that case, just search for a solution without this character
        if extra_characters:
            solution_with_extra_character = is_in_trie(curr_node, string[1:], wrong_characters, extra_characters-1, missing_characters)
            if solution_with_extra_character:
                return True

        # We can also allow for missing characters, like "Helo"
        # In that case, search the children for a solution with the current rest of the string
        if missing_characters:
            for char in curr_node.children.keys():
                next_node = curr_node.children[char]
                solution_with_missing_character = is_in_trie(next_node, string, wrong_characters, extra_characters, missing_characters-1)
                if solution_with_missing_character:
                    return True

        return False


def contains_trie_contents(string):
    """
    Given a segment of text, determines if the segment of text contains something in the trie
    :return: True if the text contains something that was added to the trie
    """
    # Does not allow for typos in the text segment
    indices_of_words = [0] + [m.start()+1 for m in re.finditer(" ", string)]

    for i in indices_of_words:
        has_contents_at_this_i = _starts_with_trie_contents(string[i:], trie_root)
        if has_contents_at_this_i:
            print(string[i:])
            return True

    return False


def _starts_with_trie_contents(string, curr_node):
    if curr_node.is_solution:
        return True
    elif not string:
        return curr_node.is_solution
    else:
        first_char = string[0]
        if first_char in curr_node.children.keys():
            return _starts_with_trie_contents(string[1:], curr_node.children[first_char])
        else:
            return False


def add_from_school_listing():
    school_file = open("E:\\school_listing.csv", "r", encoding="utf-8", errors="ignore")
    lines = school_file.readlines()
    data_lines = lines[2:]

    elem_re = re.compile(r"\bELEM\b")
    ele_re = re.compile(r"\bELE\b")
    kinderg_re = re.compile(r"\bKINDERG\b")
    alt_re = re.compile(r"\bALT\b")
    tech_re = re.compile(r"\bTECH\b")
    ctr_re = re.compile(r"\bCTR\b")
    co_re = re.compile(r"\bCO\b")
    det_re = re.compile(r"\bDET\b")
    n_re = re.compile(r"\bN\b")
    s_re = re.compile(r"\bS\b")
    reg_re = re.compile(r"\bREG\b")
    sr_re = re.compile(r"\bSR\b")
    h_re = re.compile(r"\bH\b")
    m_re = re.compile(r"\bM\b")
    e_re = re.compile(r"\bE\b")

    for data_line in data_lines:
        re.purge()
        data_points = data_line.split(",")
        school_name = data_points[7].strip()

        # Remove any suffix to the school name, like in MCNEEL SCH - VACCA CAMPUS
        last_hyphen_i = school_name.rfind(" - ")
        if last_hyphen_i != -1:
            school_name = school_name[:last_hyphen_i].strip()

        # Remove any ending "SCH", like in ALA AVENUE MIDDLE SCH
        if school_name.endswith("SCH"):
            school_name = school_name[:-3].strip()
        elif school_name.endswith("SCHOOL"):
            school_name = school_name[:-6].strip()
        elif school_name.endswith("SC"):
            school_name = school_name[:-2].strip()
        elif school_name.endswith("S"):
            school_name = school_name[:-1].strip()

        # Expand any abbreviated words, like "ELEM" and "ALT"
        school_name = elem_re.sub("ELEMENTARY", school_name)

        school_name = ele_re.sub("ELEMENTARY", school_name)

        school_name = kinderg_re.sub("KINDERGARTEN", school_name)

        school_name = alt_re.sub("ALTERNATIVE", school_name)

        school_name = tech_re.sub("TECHNICAL", school_name)

        school_name = ctr_re.sub("CENTER", school_name)

        school_name = co_re.sub("COUNTY", school_name)

        school_name = det_re.sub("DETENTION", school_name)

        school_name = n_re.sub("NORTH", school_name)
        school_name = s_re.sub("SOUTH", school_name)

        school_name = reg_re.sub("REGIONAL", school_name)

        school_name = sr_re.sub("SENIOR", school_name)

        school_name = h_re.sub("HIGH", school_name)
        school_name = m_re.sub("MIDDLE", school_name)
        school_name = e_re.sub("ELEMENTARY", school_name)

        # Only add the school if the name is not an English word or a first name.
        if len(spell_checker.unknown([school_name])) and not name_dataset.search_first_name(school_name):
            add_to_trie(school_name)


def add_from_us_cities():
    fp = open("E:\\uscities.csv")
    data_lines = fp.readlines()[1:]
    for line in data_lines:
        data = line.split(",")
        city = data[0]
        state_abbr = data[2]
        state = data[3]

        city = city.replace("\"", "")
        state_abbr = state_abbr.replace("\"", "")
        state = state.replace("\"", "")


        add_to_trie(city.upper() + " " + state_abbr.upper())
        add_to_trie(city.upper() + ", " + state_abbr.upper())
        add_to_trie(city.upper() + " " + state.upper())

        if len(spell_checker.unknown([city.upper()])) and not name_dataset.search_first_name(city.upper()):
            add_to_trie(city.upper())


if __name__ == "__main__":
    add_from_us_cities()
    add_from_school_listing()

    has_trie_contents = contains_trie_contents("DONT GO TO CLEVELAND TOMORROW")
    print(has_trie_contents)
