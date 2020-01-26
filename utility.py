import json
import requests


def make_root_request(api_key, data_center):
    '''
    Make a root request to the Mailchimp API, e.g. to see if a user is
    authenticated.
    '''

    url = f'https://{data_center}.api.mailchimp.com/3.0/'
    auth = ('anystring', api_key)
    req = requests.get(url, auth=auth)
    return req


def list_to_dict(list_of_objs, attr):
    '''
    Convert a list of objects to a dict where the key is some attribute of
    those objects.
    '''

    return {obj[attr]: obj for obj in list_of_objs}


def get_country_dict():
    '''Convert countries abbreviations to their full name.'''

    with open('country_abbrev_list.json') as file:
        country_dict = json.load(file)
    return country_dict
