import secrets
import urllib
import pickle
import os.path
import os
import sys
import hashlib

from flask import Flask, request, render_template, session, redirect, url_for
import requests
from requests.exceptions import ConnectionError
from Crypto.Cipher import AES

from mailchimp_objects import List, get_lists_url
from member_table import MemberTable
from search_functions import search_filter
from sort import sort_member_tbl
from api_calls import mc_objs_api_call
from utility import make_root_request
from crypto import encrypt, decrypt, KEY

app = Flask(__name__)
secret_key = secrets.token_urlsafe(2019)
app.config['SECRET_KEY'] = secret_key

DEMO_MODE = False
if len(sys.argv) > 1:
    if sys.argv[1] == 'demo':
        DEMO_MODE = True


@app.route('/')
def root():
    session.permanent = True
    session['sort_field'] = 'email_address'
    session['map_mode'] = False
    session['unmapped'] = False

    route = '/lists' if 'api_key' in session else '/login'
    return redirect(route)


@app.route('/lists', methods=['GET'])
def lists():
    api_key = session.get('api_key')
    if not api_key:
        return redirect(url_for('.root'))

    is_online = True
    try:
        requests.get('https://us1.api.mailchimp.com/3.0/')
    except ConnectionError:
        is_online = False

    user_dir = session['api_key_hash']

    if not is_online and not os.path.isdir(user_dir):
        return render_template(
            "login.html",
            error_msg="No internet connection and no data stored offline for this API Key!")

    if not os.path.isdir(user_dir):
        os.mkdir(user_dir)

    pickle_file_name = f'{user_dir}/lists.bin'

    if (not is_online and os.path.isfile(pickle_file_name)) or DEMO_MODE:
        with open(pickle_file_name, 'rb') as file:
            list_of_list_objs = pickle.load(file)
    else:
        list_of_list_objs = mc_objs_api_call(
            List, get_lists_url(session['data_center']), decrypt(KEY, api_key))

        with open(pickle_file_name, 'wb') as file:
            pickle.dump(list_of_list_objs, file)

    for ls in list_of_list_objs:
        p = f"{user_dir}/{ls['id']}"
        if not os.path.isdir(p):
            os.mkdir(p)

    list_of_list_dicts = [ls.get_as_dict() for ls in list_of_list_objs]

    session['list_dict'] = {ls['name']: ls['id'] for ls in list_of_list_dicts}

    if DEMO_MODE:
        session['single_list'] = True
        list_name = list_of_list_dicts[0].get('name')
        return redirect(url_for('.search', list_name=list_name, page_num=1))

    key = decrypt(KEY, session['api_key']).encode()
    cipher = None
    if os.path.isfile(f'{user_dir}/nonce.bin'):
        with open(f'{user_dir}/nonce.bin', 'rb') as file:
            nonce = file.read()
        cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)

    for list_id in session['list_dict'].values():
        f = f'{user_dir}/{list_id}/member_table.bin'
        enc_f = f'{user_dir}/{list_id}/member_table_encrypted.bin'
        if os.path.isfile(enc_f) and cipher:

            with open(enc_f, 'rb') as file:
                data = file.read()
                data_back = cipher.decrypt(data)

            with open(f, 'wb') as file:
                file.write(data_back)

            os.remove(enc_f)

    session['single_list'] = False
    if len(list_of_list_dicts) == 1:
        session['single_list'] = True
        list_name = list_of_list_dicts[0].get('name')
        return redirect(url_for('.search', list_name=list_name, page_num=1))

    return render_template(
        'lists.html',
        list_of_list_dicts=list_of_list_dicts)


@app.route('/search/<list_name>/')
def search_redir(list_name):
    return redirect(url_for('.search', list_name=list_name, page_num=1))


@app.route('/search/<list_name>/<int:page_num>', methods=['GET', 'POST'])
def search(list_name, page_num):

    list_dict = session.get('list_dict')
    api_key = session.get('api_key')

    if list_dict is None or api_key is None:
        return redirect(url_for('.root'))

    user_dir = session['api_key_hash']
    list_id = list_dict.get(list_name)
    pickle_file_name = f'{user_dir}/{list_id}/member_table.bin'

    if os.path.isfile(pickle_file_name):
        with open(pickle_file_name, "rb") as file:
            pickle_obj = pickle.load(file)
    else:
        tbl = MemberTable(
            session['data_center'], decrypt(KEY, api_key), list_id)

        pickle_obj = (tbl.get_table_dict(), tbl.get_header_info())

        with open(pickle_file_name, "wb") as file:
            pickle.dump(pickle_obj, file)

    (table_dict, header_info) = pickle_obj

    data = request.args

    quoted_search_string = data.get('search_string')
    if quoted_search_string is not None:
        search_string = urllib.parse.unquote(quoted_search_string)
    else:
        search_string = ''

    if 'unmapped' in data:
        session['unmapped'] = data['unmapped'] == 'True'

    alert_string = ''
    error_string = ''

    if session['unmapped']:
        alert_string += '''Some cities are not specified or could not
        be found on the map. City and/or country may be misspelled or
        mismatched. '''

    tbl_dict_map, alert, error = search_filter(
        search_string,
        table_dict,
        header_info)

    alert_string += alert
    error_string += error
    tbl_dict = tbl_dict_map

    if 'marker' in data:
        tbl_dict, alert, error = search_filter(
            data['marker'],
            tbl_dict,
            header_info)

        alert_string += alert
        error_string += error

    if 'sort_field' in data:
        session['sort_field'] = data['sort_field']

    header_vis_file = f'{user_dir}/{list_id}/header_vis.bin'
    if not os.path.isfile(header_vis_file):
        header_vis = {}
    else:
        with open(header_vis_file, 'rb') as file:
            header_vis = pickle.load(file)

    for i in header_info:
        if i not in header_vis:
            header_vis[i] = True

    header_order_dict = {i: True for i in header_info}
    for k in header_vis:
        if k not in header_order_dict:
            header_vis.pop(k)

    if request.method == 'POST':
        for k in header_vis:
            header_vis[k] = False
        for k in request.form:
            header_vis[k] = True
        header_vis['email_address'] = True

    with open(header_vis_file, 'wb') as file:
        pickle.dump(header_vis, file)

    tbl_dict = sort_member_tbl(tbl_dict, header_info, session['sort_field'])

    if 'map_mode' in data:
        session['map_mode'] = data['map_mode'] == 'True'

    n_row_disp = 50 if session['map_mode'] else 100

    return render_template(
        'search.html',
        n_rows_disp=n_row_disp,
        res=tbl_dict,
        n_entries=len(tbl_dict),
        header_info=header_info,
        header_vis=header_vis,
        search_string=search_string,
        search_string_enc=urllib.parse.quote(search_string),
        list_name=list_name,
        single_list=session['single_list'],
        page_num=page_num,
        error_string=error_string,
        alert_string=alert_string,
        sort_col=session['sort_field'])


@app.route('/delete_cache/<list_name>/<int:page_num>')
def delete_cache(list_name, page_num):
    if DEMO_MODE:
        return redirect('/')
    try:
        resp = make_root_request(
            decrypt(KEY, session['api_key']), session['data_center'])
        if resp.status_code < 400:
            list_id = session["list_dict"][list_name]
            user_dir = session['api_key_hash']
            table_file_name = f"{user_dir}/{list_id}/member_table.bin"
            lists_file_name = f"{user_dir}/lists.bin"
            for file_name in [table_file_name, lists_file_name]:
                if os.path.isfile(file_name):
                    os.remove(file_name)
        else:
            print('could not connect to mailchimp API')
            error_msg = 'Could not connect to mailchimp API!'
            return render_template(
                '/no_connection.html',
                list_name=list_name,
                page_num=page_num,
                error_msg=error_msg)

    except ConnectionError:
        error_msg = 'No internet connection!'
        return render_template(
            '/no_connection.html',
            list_name=list_name,
            page_num=page_num,
            error_msg=error_msg)

    return redirect(url_for(".lists", list_name=list_name, page_num=page_num))


@app.route('/logout', methods=['GET'])
def logout():
    if DEMO_MODE:
        session.clear()
        return redirect("/")

    if all([x in session for x in ['list_dict', 'api_key', 'api_key_hash']]):
        list_dict = session['list_dict']
        user_dir = session['api_key_hash']
        key = decrypt(KEY, session['api_key']).encode()

        cipher = AES.new(key, AES.MODE_EAX)
        nonce = cipher.nonce
        with open(f'{user_dir}/nonce.bin', 'wb') as file:
            file.write(nonce)

        for list_id in list_dict.values():
            f = f'{user_dir}/{list_id}/member_table.bin'
            enc_f = f'{user_dir}/{list_id}/member_table_encrypted.bin'
            if os.path.isfile(f):
                with open(f, 'rb') as file:
                    data = file.read()
                    enc_data, _ = cipher.encrypt_and_digest(data)

                with open(enc_f, 'wb') as file:
                    file.write(enc_data)

                os.remove(f)

    session.clear()
    return redirect("/")


@app.route('/login', methods=["GET", "POST"])
def login():
    if DEMO_MODE:
        session['api_key'] = '1234'
        session['data_center'] = '1234'
        session['api_key_hash'] = '0dummy_data'
        return redirect(url_for(".lists"))

    if 'api_key' in request.args:
        api_key_full = request.args.get("api_key")
        if not api_key_full:
            return render_template("login.html", error_msg="Enter an api key!")
        if ("-" not in api_key_full or 'us' not in api_key_full.split("-")[1]
                or len(api_key_full.split('-')[0]) != 32):
            return render_template(
                "login.html",
                error_msg='''Enter a valid API key! A valid API key looks like
                this: 123456789abcdefedcba987654321012-us10''')

        try:
            resp = make_root_request(
                api_key_full, api_key_full.split("-")[1])
            if resp.status_code >= 400:
                return render_template(
                    "login.html", error_msg="Could not validate API key!")
        except ConnectionError:
            pass

        api_key, data_center = request.args.get('api_key').split('-')
        session['api_key'] = encrypt(KEY, api_key)
        session['data_center'] = data_center
        h = hashlib.sha1()
        h.update(api_key.encode())
        session['api_key_hash'] = h.hexdigest()

        return redirect(url_for(".lists"))

    return render_template("login.html")


if __name__ == '__main__':
    app.run(debug=True, host='localhost')
