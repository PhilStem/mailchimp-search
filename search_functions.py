from levenshtein import distance


def search_filter(search_string, table_dict, header_info):
    '''
    How the search function works is described in templates/help_modal.html
    '''

    if not table_dict:
        return [], '', ''

    _error_string = []
    _alert_string = []
    table_dict_dict = {
        member_dict['id']: member_dict for member_dict in table_dict}

    if '<=' in search_string or '>=' in search_string:
        _error_string.append('<= and >= are not allowed.')

    header_labels_dict = {k: v['label'] for k, v in header_info.items()}
    inv_header_labels_dict = {
        v.lower(): k for k, v in header_labels_dict.items()}

    search_string = convert_between(search_string, '"', ',', ';')
    search_tokens = search_string.split(',')
    search_tokens = [
        convert_between(token, '"', ';', ',') for token in search_tokens]

    search_tokens_free = []
    search_tokens_restr_pairs = []
    search_tokens_ineq_pairs = []
    t1 = t2 = ''

    token_fields_restr = []
    token_fields_ineq = []

    for token in search_tokens:
        if '=' in token:
            token_field, token_vals_string = token.split('=', 1)
            tag = inv_header_labels_dict.get(token_field.strip().lower())
            search_tokens_restr_pairs.append([tag, token_vals_string])
            token_fields_restr.append(token_field)

        elif ('<' in token) or ('>' in token):
            operator = '<' if '<' in token else '>'
            token_field, token_vals_string = token.split(operator, 1)
            tag = inv_header_labels_dict.get(token_field.strip().lower())
            search_tokens_ineq_pairs.append([tag, token_vals_string])
            token_fields_ineq.append(token_field)

        elif '*' in token:
            token_parts = token[1:].strip().lower().split(" ")
            if len(token_parts) != 2:
                return [], '', 'The * must be followed by a first name, then a space and then a last name.'
            t1, t2 = token_parts

        else:
            search_tokens_free.append(token.strip())

    name_in_fields = all([
        x in header_labels_dict for x in ['FNAME', 'LNAME']])
    if t1 and not name_in_fields:
        _error_string.append(
            'Did not find fields for first and/or last name.')

    def field_exists_check(search_tokens, fields):
        for j, ((tag, _), token_field) in enumerate(zip(
                search_tokens, fields)):
            if tag is None:
                lev_dict = {k: distance(
                    token_field.strip().lower(),
                    v.lower()) for k, v in header_labels_dict.items()}
                min_dist = min(lev_dict.values())
                for k, d in lev_dict.items():
                    if d == min_dist:
                        if min_dist <= 3:
                            search_tokens[j][0] = k
                            _alert_string.append(
                                f'Corrected "{token_field.strip()}" to '
                                f'"{header_labels_dict[k]}".')
                        else:
                            _error_string.append(
                                f'"{token_field.strip()}" is not a field. '
                                f'It might be misspelled.')
                            break

    field_exists_check(search_tokens_restr_pairs, token_fields_restr)
    field_exists_check(search_tokens_ineq_pairs, token_fields_ineq)

    matching_member_ids = []
    for member_id, member_dict in table_dict_dict.items():
        member_fields = member_dict['fields']
        is_match = True

        for tag, token_vals_string in search_tokens_restr_pairs:
            if tag is not None:
                field_val = member_fields[tag]
                values_not_in_field = [
                    not _compare_fnc(
                        v.strip().lower(), field_val.lower())
                    for v in token_vals_string.split('/')]
                if all(values_not_in_field):
                    is_match = False
            else:
                is_match = False

        for tag, token_vals_string in search_tokens_ineq_pairs:
            if tag is not None:
                field_val = member_fields[tag]
                is_match = _compare_fnc_2(
                    field_val,
                    token_vals_string.strip(),
                    operator)
            else:
                is_match = False

        if is_match:
            if search_tokens_free:
                is_match = False
            for field in member_fields.values():
                for free_token in search_tokens_free:
                    if _compare_fnc(free_token.lower(), field.lower()):
                        is_match = True
                        break
                if is_match:
                    break

        if t1:
            is_match = False
        if t1 and (
                t1 == member_fields['FNAME'].lower()
                and t2 == member_fields['LNAME'].lower()):
            is_match = True

        if is_match:
            matching_member_ids.append(member_id)

    new_tbl = {}
    for member_id in matching_member_ids:
        new_tbl[member_id] = table_dict_dict[member_id]

    new_tbl = list(new_tbl.values())
    if not new_tbl:
        _alert_string.append('No entries found.')

    return new_tbl, (' ').join(_alert_string), (' ').join(_error_string)


def _compare_fnc(x, y):
    if '"' in x:
        return x.replace('"', '') == y
    else:
        return x in y


def _compare_fnc_2(x, y, operator):
    try:
        x = float(x)
        y = float(y)
        if operator == '<':
            return x < y
        else:
            return x > y
    except ValueError:
        return False


def convert_between(string, between_char, old_char, new_char):
    new_string = ''
    is_between = False
    for char in string:
        if char == between_char:
            is_between = not is_between
        if is_between and char == old_char:
            new_string += new_char
        else:
            new_string += char

    return new_string
