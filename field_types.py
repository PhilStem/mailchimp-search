FIELD_TYPE_DICT = {
    'text': lambda x: x,
    'number': lambda x: str(x),
    'phone': lambda x: x,
    'birthday': lambda x: x,
    'url': lambda x: to_url(x),
    'date': lambda x: x,
    'dropdown': lambda x: x,
    'radio': lambda x: x,
    'imageurl': lambda x: x,
    'zip': lambda x: x
}


def get_display_repr(data, field_type, country_dict):
    if field_type == 'address':
        return to_address(data, country_dict)
    else:
        if field_type in FIELD_TYPE_DICT:
            return FIELD_TYPE_DICT[field_type](data)
        else:
            try:
                return str(data)
            except TypeError:
                return ''


def to_url(data):
    if (not (data.startswith('http://') or data.startswith('https://'))
            and data):
        data = f'https://{data}'
    return data


def to_address(addr_dict, country_dict):
    def get_as_string(field, addr_dict):
        if field == 'country' and addr_dict[field] in country_dict:
            return country_dict[addr_dict[field]]
        else:
            return addr_dict[field]

    if addr_dict:
        fields = ['addr1', 'addr2', 'zip', 'city', 'state', 'country']
        return (" ".join([get_as_string(
            field, addr_dict) for field in fields if addr_dict[field]]))

    else:
        return ''
