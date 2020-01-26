class MailchimpObject():
    FIELD_NAME = ''
    ATTRS_TO_SET = []

    def __init__(self, requested_dict):
        self.attr_dict = {
            attr: requested_dict[attr] for attr in self.ATTRS_TO_SET
        }

    def __getitem__(self, key):
        return self.attr_dict[key]

    def __repr__(self):
        attrs = [f'{attr!r}: {self[attr]!r}' for attr in self.ATTRS_TO_SET]
        return type(self).__name__ + '({' + (', ').join(attrs) + '})'

    def get_as_dict(self):
        return {attr: self.attr_dict.get(attr) for attr in self.ATTRS_TO_SET}


class List(MailchimpObject):
    FIELD_NAME = 'lists'
    ATTRS_TO_SET = ['id', 'name', 'date_created']

    def __getitem__(self, key):
        attr = super().__getitem__(key)
        if key == 'date_created':
            attr = attr[:10]
        return attr


class Member(MailchimpObject):
    FIELD_NAME = 'members'
    ATTRS_TO_SET = ['id', 'email_address', 'web_id', 'status']

    def __init__(self, member_dict):
        super(Member, self).__init__(member_dict)
        self.attr_dict['merge_field_dict'] = member_dict['merge_fields']
        self.attr_dict['interests'] = member_dict['interests']


class MergeField(MailchimpObject):
    FIELD_NAME = 'merge_fields'
    ATTRS_TO_SET = ['tag', 'name', 'type', 'display_order']

    @property
    def is_field_hyperlink(self):
        return self.attr_dict.get('type') == 'url'

    @property
    def is_field_numeric(self):
        return self.attr_dict.get('type') == 'number'


class InterestCategory(MailchimpObject):
    FIELD_NAME = 'categories'
    ATTRS_TO_SET = ['id', 'title', 'display_order', 'type']


class Interest(MailchimpObject):
    FIELD_NAME = 'interests'
    ATTRS_TO_SET = ['category_id', 'list_id', 'id', 'name', 'display_order']


def get_root_url(data_center):
    return f'https://{data_center}.api.mailchimp.com/3.0'


def get_lists_url(data_center):
    return f'{get_root_url(data_center)}/lists'


def get_members_url(data_center, list_id):
    return f'{get_root_url(data_center)}/lists/{list_id}/members'


def get_merge_fields_url(data_center, list_id):
    return f'{get_root_url(data_center)}/lists/{list_id}/merge-fields'


def get_interest_categories_url(data_center, list_id):
    return f'{get_root_url(data_center)}/lists/{list_id}/interest-categories'


def get_interests_url(data_center, list_id, interest_category_id):
    return (
        f'{get_root_url(data_center)}/lists/{list_id}/interest-categories/'
        f'{interest_category_id}/interests')
