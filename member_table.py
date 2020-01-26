from collections import OrderedDict
from field_types import get_display_repr
from mailchimp_objects import MergeField, Member, InterestCategory, Interest
from mailchimp_objects import (
    get_merge_fields_url, get_members_url, get_interest_categories_url,
    get_interests_url)
from utility import list_to_dict, get_country_dict
from api_calls import mc_objs_api_call


class MemberTable:
    '''
    A user's data (from lists of Mailchimp Objects) in a tabular format that
    can easily be displayed and searched.
    '''

    def __init__(self, data_center, api_key, list_id):
        self.data_center = data_center
        self.api_key = api_key
        self.list_id = list_id
        self.country_dict = get_country_dict()
        self._set_mc_objs()

    def _set_mc_objs(self):
        '''Download all the necessary Mailchimp Object lists.'''

        def _call(clss, url_fnc):
            return mc_objs_api_call(
                clss, url_fnc(self.data_center, self.list_id), self.api_key)

        self.member_list = _call(Member, get_members_url)
        self.merge_field_dict = list_to_dict(_call(
            MergeField, get_merge_fields_url), 'tag')
        self.interest_category_list = _call(
            InterestCategory, get_interest_categories_url)

        self.interest_dict = {}
        for category in self.interest_category_list:
            self.interest_dict[category['id']] = mc_objs_api_call(
                Interest,
                get_interests_url(
                    self.data_center, self.list_id, category['id']),
                self.api_key)

    def get_table_dict(self):
        '''
        Return the table as a list of dicts, where "fields" is a dict of
        fields and each field is represented as a string.
        '''

        self.interest_dict_dict = {}
        for k, dict_ in self.interest_dict.items():
            self.interest_dict_dict[k] = list_to_dict(dict_, 'id')

        table = []
        for member in self.member_list:
            fields = {}
            for field in ['email_address', 'status']:
                fields[field] = member[field]

            for category in self.interest_category_list:
                interest_dict = self.interest_dict_dict[category['id']]
                interest_strings = []
                for id_, member_has_interest in member['interests'].items():
                    if member_has_interest:
                        interest = interest_dict.get(id_)
                        if interest is not None:
                            interest_strings.append(interest['name'])
                fields[category['title']] = (', ').join(interest_strings)

            for tag, merge_field in self.merge_field_dict.items():
                merge_field_type = merge_field['type']
                field_value = member['merge_field_dict'][tag]
                fields[tag] = get_display_repr(
                    field_value, merge_field_type, self.country_dict)

            table.append({
                'fields': fields,
                'profile_link': self._make_edit_link(member['web_id']),
                'id': member['id']
                })

        return table

    def get_header_info(self):
        '''
        Return specific info about the columns, which is required for the
        search and sort functions and the tables appearance.
        '''

        headers = self._get_header_order()
        labels = self.get_header_labels_dict()
        is_hyperlink = self._get_header_attr('is_field_hyperlink')
        is_numeric = self._get_header_attr('is_field_numeric')

        header_dict = OrderedDict()
        for header in headers:
            header_dict[header] = {
                'label': labels[header],
                'is_hyperlink': is_hyperlink[header],
                'is_numeric': is_numeric[header]
            }

        return header_dict

    def _make_edit_link(self, web_id):
        root = f'https://{self.data_center}.admin.mailchimp.com'
        return f'{root}/lists/members/view?id={web_id}'

    def get_header_labels_dict(self):
        label_dict = {}

        label_dict['email_address'] = 'Email Address'
        label_dict['status'] = 'Status'

        for category in self.interest_category_list:
            category_title = category['title']
            label_dict[category_title] = category_title

        for tag, merge_field in self.merge_field_dict.items():
            label_dict[tag] = merge_field['name']

        return label_dict

    def _get_header_order(self):
        order_dict = self._get_header_order_dict()
        order_ls = [None for _ in range(len(order_dict.items()))]
        for tag, order in order_dict.items():
            order_ls[order - 1] = tag
        return order_ls

    def _get_header_order_dict(self):
        order_dict = {}
        order_dict['email_address'] = 1
        merge_field_orders = []

        for tag, merge_field in self.merge_field_dict.items():
            merge_field_order = merge_field['display_order']
            order_dict[tag] = merge_field_order
            merge_field_orders.append(merge_field_order)

        gaps_in_merge_fieds = self._get_gap_inds(
            merge_field_orders,
            self.interest_category_list)

        for i, category in enumerate(self.interest_category_list):
            category_order = gaps_in_merge_fieds[i]
            order_dict[category['title']] = category_order

        def max_or_else(ls, x):
            return max(ls) if ls else x

        max_gap_ind_in_merge_fields = max_or_else(gaps_in_merge_fieds, 0)
        max_merge_field_ind = max_or_else(merge_field_orders, 1)
        order_dict['status'] = 1 + max(
            max_merge_field_ind,
            max_gap_ind_in_merge_fields)
        return order_dict

    @staticmethod
    def _get_gap_inds(ls, ls_ref):
        ls.sort()
        ls.insert(0, 1)
        max_ind = max(ls)
        gaps = []
        for i in range(len(ls) - 1):
            gap = ls[i + 1] - ls[i]
            for j in range(gap - 1):
                gaps.append(ls[i] + j + 1)

        tail_len = max(len(ls_ref) - len(gaps), 0)
        for i in range(tail_len):
            gaps.append(max_ind + i + 1)

        return gaps

    def _get_header_attr(self, attr):
        d = {k: getattr(v, attr) for k, v
             in self.merge_field_dict.items()}
        d['email_address'] = False
        d['status'] = False
        for category in self.interest_category_list:
            d[category['title']] = False
        return d
