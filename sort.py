import re


def sort_member_tbl(tbl, header_info, field):
    '''
    Sort the entries of a table according to one column either alphabetically
    or numerically.
    '''

    def string_sort_fnc(ind_entry_tuple):
        entry = ind_entry_tuple[1]['fields'][field].lower()

        # If the string starts with a special characters, remove those
        while entry:
            if re.match(r'[\W_]', entry) is not None:
                entry = entry[1:]
            else:
                break

        return (entry == '', entry)

    def number_sort_fnc(ind_entry_tuple):
        entry = ind_entry_tuple[1]['fields'][field]
        return (False, float(entry)) if entry else (True, 0)

    if field in header_info and header_info[field]['is_numeric']:
        sort_fnc = number_sort_fnc
    else:
        sort_fnc = string_sort_fnc
    return [tbl[ind] for ind, entry in sorted(enumerate(tbl), key=sort_fnc)]
