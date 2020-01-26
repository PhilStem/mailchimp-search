import requests
from mailchimp_objects import MailchimpObject


def mc_objs_api_call(clss, url, api_key, count=1000):
    '''
    Download an array of a user's Mailchimp objects (e.g. Members, Lists,
    Interest Categories) via the Mailchimp API.
    '''

    if not issubclass(clss, MailchimpObject):
        raise TypeError("Class has to be Mailchimp Object.")

    auth = ("anystring", api_key)
    obj_ls = []
    offset = 0

    # Mailchimp limits the count of objects to retrieve to 1000,
    # so downloading them has to be done in a loop.
    while True:
        arged_url = url + f'?offset={offset}&count={count}'
        resp = requests.get(arged_url, auth=auth)
        data = resp.json()
        list_of_json_objs = data.get(clss.FIELD_NAME)

        if not list_of_json_objs:
            return []

        obj_ls_section = [clss(obj) for obj in list_of_json_objs]
        obj_ls += obj_ls_section
        offset += count

        if len(obj_ls_section) < count:
            break

    return obj_ls
