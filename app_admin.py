"""This module implements frontend for the admin control panel of API"""
import json
import re
import datetime
from dateutil.relativedelta import relativedelta

from pywebio import start_server
from pywebio.session import set_env, run_js
from pywebio.input import input_group, input, NUMBER, PASSWORD
from pywebio.output import (put_error, use_scope, put_scope, remove,
                            put_buttons, put_tabs, toast, put_success,
                            put_image, put_grid, span, put_markdown, put_html,
                            put_column, put_table, popup)
import pywebio.pin

import pyecharts.options as opts
from pyecharts.charts import Line
from pyecharts.components import Table
from pyecharts.options import ComponentTitleOpts

from configs.admin_frontend_config import AdminFronendConfig
from admin_frontend_services.admin_request import AdminRequest


ADMIN_PRIVILEGE = ["owner", "admin"]
LIST_PRIVILEGE = ["user", "admin"]
ENDPOINT_LIST = ['chat_completions',
                 'completions', 
                 'embeddings', 
                 'fine_tunes']


admin_frontend_config = AdminFronendConfig()
admin_request = AdminRequest(admin_frontend_config)

def init():
    """Initialize SDK"""
    global admin_frontend_config
    admin_frontend_config = AdminFronendConfig()
    global admin_request
    admin_request = AdminRequest(admin_frontend_config)
    admin_request.is_db_init()


# @config(theme='dark')
def main():
    """Main function"""
    set_env(title="OpenAI API Control Panel")
    put_image(open('resources/admin_logo.png',
                   'rb').read(), width="50%", 
                   height="50%").style('display: block; margin: auto;')
    init()

    # if admin_request.is_init:
    #     login()
    # else:
    #     db_init()
    #     return

    login()
    remove('login')
    select_tools()

@use_scope('db_init')
def db_init():
    """Add user"""
    def convert_data(data):
        permissions = {
            "text_completion_models": False,
            "chat_completion_models": False,
            "embeddings": False,
            "fine_tune": False
        }
        for permission in data['permissions']:
            permissions[permission] = True
        data['permissions'] = permissions
        data.pop("repeat_password")
        return data

    def query_submition():
        data = {}
        data['user_id'] = pywebio.pin.pin['init_user_id']
        data['name'] = pywebio.pin.pin['init_name']
        data['password'] = pywebio.pin.pin['init_password']
        data['repeat_password'] = pywebio.pin.pin['init_repeat_password']
        data['request_limit'] = 0
        data['fine_tune_limit'] = 0
        data['privilege'] = "owner"
        data['permissions'] = []

        for key, value in data.items():
            if key not in ['permissions'] and (value is None or value == ''):
                toast("Fill required fields.")
                return

        if data['password'] != data['repeat_password']:
            toast("Password and Repeat Password must be the same.")
            return

        if not validate_password(data['password']):
            toast("Password must be at least 8 characters and include at " \
                  "least 1 uppercase letter, 1 lowercase letter, and one number")
            return

        user_data = convert_data(data)
        results = admin_request.db_init(user_data)
        content = json.loads(results.content)

        if results.status_code != 200 and results.status_code != 201:
            remove('message_init_user')
            with use_scope('message_init_user'):
                put_error(content['detail'])
        else:
            remove('message_init_user')
            with use_scope('message_init_user'):
                put_success("User successfully created. Your API key is:\n" + content['detail'] + \
                    "\n*WARNING* This key is not recoverable. " \
                    "Please write it down and keep it somewhere safe.")


    put_tabs([
        {'title':'Initialize', 'content':put_scope('init_user_form')}
    ])
    with use_scope("init_user_form"):
        pywebio.pin.put_input(label='User ID', name='init_user_id')
        pywebio.pin.put_input(label='Name', name='init_name')
        pywebio.pin.put_input(label='Password', name='init_password', type=PASSWORD)
        pywebio.pin.put_input(label='Repeat Password', name='init_repeat_password', type=PASSWORD)

        put_buttons([
            {'label':'Submit', 'value':'submit', 'color':'primary'},
            {'label':'Refresh', 'value':'back', 'color':'secondary'}
        ], onclick=[query_submition, logout_button]).style('text-align:left;')

@use_scope('login')
def login():
    """Login"""
    while True:
        login_data = input_group("Login",[
            input('Username', name='username', required=True),
            input('Password', name='password', required=True, type=PASSWORD)
        ])

        result = admin_request.get_token(login_data)
        content = json.loads(result.content)

        if result.status_code != 200:
            remove('message_error_login')
            with use_scope('message_error_login'):
                put_error(content['detail'])
        else:
            remove('message_error_login')
            return result

@use_scope('select_tools', clear=True)
def select_tools():
    """Select tools"""
    if admin_request.user_info['privilege'] in ADMIN_PRIVILEGE:
        put_tabs([
            dict(title='Select Tools', content=[
                put_buttons(buttons=[
                    dict(label="Add User", value="add_user"),
                    dict(label="Update User", value="update_user", color="warning"),
                    dict(label="User Statistics", value="stat_user", color="success"),
                    dict(label="Delete User", value="delete_user", color="danger"),
                    dict(label="Change Password", value="change_password", color="dark"),
                    dict(label="Logout", value="logout", color="secondary")
                    ], onclick=show_tools).style('text-align:center;')
            ])
        ])
    else:
        put_tabs([
            dict(title='Select Tools', content=[
                put_buttons(buttons=[
                    dict(label="User Statistics", value="stat_user", color="success"),
                    dict(label="Change Password", value="change_password", color="dark"),
                    dict(label="Logout", value="logout", color="secondary")
                    ], onclick=show_tools).style('text-align:center;')
            ])
        ])

@use_scope('show_tools')
def show_tools(input):
    """Show tools"""
    remove('select_tools')

    if input == 'add_user':
        add_user()

    if input == 'update_user':
        update_user()

    if input == 'stat_user':
        stat_user()

    if input == 'delete_user':
        delete_user()

    if input == 'change_password':
        change_password()

    if input == 'logout':
        logout_button()

@use_scope('add_user')
def add_user():
    """Add user"""
    def convert_data(data):
        permissions = {
            "text_completion_models": False,
            "chat_completion_models": False,
            "embeddings": False,
            "fine_tune": False
        }
        for permission in data['permissions']:
            permissions[permission] = True
        data['permissions'] = permissions
        data.pop("repeat_password")
        return data

    def query_submition():
        data = {}
        data['user_id'] = pywebio.pin.pin['add_user_id']
        data['name'] = pywebio.pin.pin['add_name']
        data['password'] = pywebio.pin.pin['add_password']
        data['repeat_password'] = pywebio.pin.pin['add_repeat_password']
        data['request_limit'] = pywebio.pin.pin['add_request_limit']
        data['fine_tune_limit'] = pywebio.pin.pin['add_fine_tune_limit']
        data['privilege'] = pywebio.pin.pin['add_privilege']
        data['permissions'] = pywebio.pin.pin['add_permissions']

        for key, value in data.items():
            if key not in ['permissions'] and (value is None or value == ''):
                toast("Fill required fields.")
                return

            if key in ['permissions'] and len(value) == 0:
                toast("At least one permission must be selected.")
                return

        if data['password'] != data['repeat_password']:
            toast("Password and Repeat Password must be the same.")
            return

        if not validate_password(data['password']):
            toast("Password must be at least 8 characters and include at " \
                  "least 1 uppercase letter, 1 lowercase letter, and one number")
            return

        user_data = convert_data(data)
        results = admin_request.add_user(user_data)
        content = json.loads(results.content)

        if results.status_code != 200 and results.status_code != 201:
            remove('message_add_user')
            with use_scope('message_add_user'):
                put_error(content['detail'])
        else:
            remove('message_add_user')
            with use_scope('message_add_user'):
                put_success("User successfully created. Your API key is:\n" + content['detail'] + \
                    "\n*WARNING* This key is not recoverable. " \
                    "Please write it down and keep it somewhere safe.")


    put_tabs([
        {'title':'Add User', 'content':put_scope('add_user_form')}
    ])
    with use_scope("add_user_form"):
        pywebio.pin.put_input(label='User ID', name='add_user_id')
        pywebio.pin.put_input(label='Name', name='add_name')
        pywebio.pin.put_input(label='Password', name='add_password', type=PASSWORD)
        pywebio.pin.put_input(label='Repeat Password', name='add_repeat_password', type=PASSWORD)
        pywebio.pin.put_input(label='Request Limit', name='add_request_limit', type=NUMBER)
        pywebio.pin.put_input(label='Fine-Tune Limit', name='add_fine_tune_limit', type=NUMBER)
        pywebio.pin.put_select(label='User Privilege', name='add_privilege',
                               options=LIST_PRIVILEGE)
        pywebio.pin.put_checkbox(label="Permissions", name='add_permissions', options=[
            dict(label="Text Completion Models", value="text_completion_models"),
            dict(label="Chat Completion Models", value="chat_completion_models"),
            dict(label="Embedding Models", value="embeddings"),
            dict(label="Finetune", value="fine_tune")
        ])

        put_buttons([
            {'label':'Submit', 'value':'submit', 'color':'primary'},
            {'label':'Back', 'value':'back', 'color':'secondary'}
        ], onclick=[query_submition, back_button]).style('text-align:left;')

@use_scope('change_password')
def change_password():
    """Change the password"""
    def query_submition():
        data = {}
        data['old_password'] = pywebio.pin.pin['change_password_old_password']
        data['password'] = pywebio.pin.pin['change_password_new_password']
        data['repeat_password'] = pywebio.pin.pin['change_password_repeat_new_password']

        if data['password'] != data['repeat_password']:
            toast("Password and Repeat Password must be the same.")
            return

        if not validate_password(data['password']):
            toast("Password must be at least 8 characters and include at " \
                  "least 1 uppercase letter, 1 lowercase letter, and one number")
            return

        data.pop('repeat_password')
        results = admin_request.change_password(data=data)
        content = json.loads(results.content)

        if results.status_code != 200 and results.status_code != 201:
            remove('message_change_password')
            with use_scope('message_change_password'):
                put_error(content['detail'])
        else:
            remove('message_change_password')
            with use_scope('message_change_password'):
                popup("Change Password", "User succesfully updated password.")
            back_button()
    put_tabs([
        {'title':'Change Password', 'content':put_scope('change_password_form')}
    ])
    with use_scope("change_password_form"):
        pywebio.pin.put_input(label='Current Password',
                              name='change_password_old_password',
                              type=PASSWORD)
        pywebio.pin.put_input(label='New Password',
                              name='change_password_new_password',
                              type=PASSWORD)
        pywebio.pin.put_input(label='Repeat New Password',
                              name='change_password_repeat_new_password',
                              type=PASSWORD)

        put_buttons([
            {'label':'Submit', 'value':'submit', 'color':'primary'},
            {'label':'Back', 'value':'back', 'color':'secondary'}
        ], onclick=[query_submition, back_button]).style('text-align:left;')

@use_scope('update_user')
def update_user():
    """update user"""
    def convert_data(data):
        permissions = {
            "text_completion_models": False,
            "chat_completion_models": False,
            "embeddings": False,
            "fine_tune": False
        }
        for permission in data['permissions']:
            permissions[permission] = True
        data['permissions'] = permissions
        return data

    def query_submition():
        data = {}
        data['user_id'] = pywebio.pin.pin['update_user_id']
        data['name'] = pywebio.pin.pin['update_name']
        data['request_limit'] = pywebio.pin.pin['update_request_limit']
        data['fine_tune_limit'] = pywebio.pin.pin['update_fine_tune_limit']
        data['permissions'] = pywebio.pin.pin['update_permissions']

        for key, value in data.items():
            if key in ['user_id'] and (value is None or value == ''):
                toast("Fill required fields.")
                return

            if key in ['permissions'] and len(value) == 0:
                toast("At least one permission must be selected.")
                return

        user_data = convert_data(data)
        results = admin_request.update_user(user_data)
        content = json.loads(results.content)

        if results.status_code != 200 and results.status_code != 201:
            remove('message_update_user')
            with use_scope('message_update_user'):
                put_error(content['detail'])
        else:
            remove('message_update_user')
            with use_scope('message_update_user'):
                put_success("User successfully updated.")

    @use_scope('update_user_search')
    def user_search():
        def user_search_submission():
            user_id = pywebio.pin.pin['update_user_search']

            if user_id is None or user_id == '':
                toast("No existing user.")
                return

            results = admin_request.get_user(user_id=user_id)
            content = json.loads(results.content)

            if results.status_code != 200 and results.status_code != 201:
                remove('message_search_user')
                with use_scope('message_search_user'):
                    put_error(content['detail'])
            else:
                remove('update_user_search')
                remove('message_search_user')
                update_searched_user(content)

        all_users = get_all_user()
        put_tabs([
            {'title':'Update User', 'content': [
                pywebio.pin.put_select(label='User ID', name='update_user_search',
                                       options=all_users),
                put_buttons([
                    {'label':'Submit', 'value':'submit', 'color':'primary'},
                    {'label':'Back', 'value':'back', 'color':'secondary'}],
                    onclick=[user_search_submission, back_button]).style('text-align:left;')
            ]}])

    @use_scope("update_searched_user")
    def update_searched_user(content):
        put_tabs([
            {'title':'Update User', 'content':put_scope('update_user_form')}
        ])
        with use_scope("update_user_form"):
            pywebio.pin.put_input(label='User ID', name='update_user_id',
                                  value=content['user_id'], readonly=True)
            pywebio.pin.put_input(label='Name', name='update_name',
                                  value=content['name'])
            pywebio.pin.put_input(label='Request Limit', name='update_request_limit',
                                  type=NUMBER, value=content['request_limit'])
            pywebio.pin.put_input(label='Fine-Tune Limit', name='update_fine_tune_limit',
                                  type=NUMBER, value=content['fine_tune_limit'])
            pywebio.pin.put_checkbox(label="Permissions", name='update_permissions', options=[
                dict(label="Text Completion Models", value="text_completion_models"),
                dict(label="Chat Completion Models", value="chat_completion_models"),
                dict(label="Embedding Models", value="embeddings"),
                dict(label="Finetune", value="fine_tune")
            ], value=[key for key, value in content['permissions'].items() if value])

            put_buttons([
                {'label':'Submit', 'value':'submit', 'color':'primary'},
                {'label':'Back', 'value':'back', 'color':'secondary'}
            ], onclick=[query_submition, back_button]).style('text-align:left;')

    user_search()


@use_scope("stat_user")
def stat_user():
    """Stat user"""

    @use_scope("stat_user")
    def on_change(value):
        user_id = pywebio.pin.pin['stat_user_id']
        date = pywebio.pin.pin['stat_date']
        endpoint = pywebio.pin.pin['stat_endpoint']

        day_from, day_to = generate_day_from_to(date)
        slice = get_slice(day_from=day_from, day_to=day_to)

        user_info = json.loads(admin_request.get_user(user_id).content)
        user_records = admin_request.get_record(user_id, endpoint=endpoint,
                                                day_from=day_from, day_to=day_to,
                                                slice=slice)
        user_records = json.loads(user_records.content)

        with use_scope('stat_user_information', clear=True):
            headers = list(user_info.keys())
            user_info['permissions'] = [
                str(key) for key, value in user_info['permissions'].items() if value]
            row = [[str(e) for e in list(user_info.values())]]
            put_table(row, headers).style('text-align:center;')

        with use_scope('stat_charts', clear=True):
            x_data, x_data_str = generate_x_data_days(day_from, day_to,
                                                      slice=slice)
            y_data = generate_y_data(user_records, x_data, slice=slice)
            plot = plot_chart(x_data_str, y_data, "Requests Chart", endpoint + " requests")
            plot.width = "100%"
            put_html(plot.render_notebook()).style('text-align:center;')

        with use_scope('stat_aggregation', clear=True):
            table = generate_table([[str(sum(y_data))]], ['Total number of Requests'], None, None)
            put_html(table.render_notebook()).style('text-align:center;')

    put_grid([
        [span(put_markdown('## Select User'), col=2), None, put_markdown('## Select date')],
        [span(put_scope('stat_user_select'), col=2), None, put_scope('stat_date_select')],
        [span(put_markdown('## User information'), col=3)],
        [span(put_scope('stat_user_information'), col=4)],
        [span(put_markdown('## Charts'), col=2, row=1), None, put_markdown('## Aggregate ')],
        [span(put_column([put_scope('stat_endpoint_select'),
                          put_scope('stat_charts')],size="15%"), col=2, row=1),
                          None, put_scope('stat_aggregation')]
    ], cell_widths='33% 30% 3% 33%')

    with use_scope('stat_user_select'):
        if admin_request.user_info['privilege'] in ADMIN_PRIVILEGE:
            all_user = get_all_user()
            pywebio.pin.put_select(name='stat_user_id', help_text='User ID',
                                   options=all_user)
            pywebio.pin.pin_on_change('stat_user_id', onchange=on_change, clear=True)
        else:
            pywebio.pin.put_input(name='stat_user_id', help_text='User ID',
                                  value=[admin_request.user_info['user_id']],
                                  readonly=True)
            pywebio.pin.pin_on_change('stat_user_id', onchange=on_change, clear=True)

    with use_scope('stat_date_select'):
        date_options = ['1 hour', '24 hours', '3 days', ('1 week', '1 week', True),
                        '1 month', '3 months', '6 months']
        pywebio.pin.put_select(name='stat_date', help_text='Date Range',
                               options=date_options)
        pywebio.pin.pin_on_change('stat_date', onchange=on_change, clear=True)

    with use_scope('stat_endpoint_select'):
        pywebio.pin.put_select(name='stat_endpoint', help_text='Endpoint',
                               options=ENDPOINT_LIST)
        pywebio.pin.pin_on_change('stat_endpoint', onchange=on_change, clear=True,
                                  init_run=True)

    put_markdown("<br>")
    # if admin_request.user_info['privilege'] in ADMIN_PRIVILEGE:
    put_buttons([{'label':'Back', 'value':'back', 'color':'secondary'}],
                onclick=[back_button]).style('text-align:center;')
    # else:
    #     put_buttons([{'label':'Logout', 'value':'back', 'color':'secondary'}],
    #                 onclick=[logout_button]).style('text-align:center;')


@use_scope('delete_user')
def delete_user():
    """Delete user"""
    def user_search_submission():
        user_id = pywebio.pin.pin['delete_user_search']

        results = admin_request.delete_user(user_id=user_id)
        content = json.loads(results.content)

        if results.status_code != 200 and results.status_code != 201:
            remove('message_delete_user')
            with use_scope('message_delete_user'):
                put_error(content['detail'])
        else:
            remove('message_delete_user')
            with use_scope('message_delete_user'):
                put_success("User deleted successfully.")

    put_tabs([
        {'title':'Update User', 'content': [
            pywebio.pin.put_input(label='User ID', name='delete_user_search'),
            put_buttons([
                {'label':'Submit', 'value':'submit', 'color':'primary'},
                {'label':'Back', 'value':'back', 'color':'secondary'}],
                onclick=[user_search_submission, back_button]).style('text-align:left;')
        ]}])

def remove_scopes():
    """Remove scopes"""
    remove('select_tools')
    remove('show_tools')

    remove('add_user')
    remove('message_add_user')

    remove('update_user')
    remove('message_update_user')

    remove('update_user_search')
    remove('message_search_user')
    remove('update_searched_user')

    remove('delete_user')
    remove('message_delete_user')

    remove('change_password')
    remove('message_change_password')

    remove('stat_user')
    remove('stat_user_select')
    remove('stat_date_select')
    remove('stat_user_information')
    remove('stat_endpoint_select')
    remove('stat_charts')
    remove('stat_aggregation')


def back_button():
    """Back button"""
    remove_scopes()
    select_tools()

def logout_button():
    """Logout button"""
    run_js('window.location.reload()')

def get_all_user():
    """Get all users"""
    all_users = admin_request.get_all_user()

    return json.loads(all_users.content)

def plot_chart(x_data, y_data, title, bar_name):
    """Plot Bar charts"""
    plot = (
        Line()
        .add_xaxis(xaxis_data=x_data)
        .add_yaxis(
            series_name=bar_name, y_axis=y_data, label_opts=opts.LabelOpts(is_show=False)
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title),
            xaxis_opts=opts.AxisOpts(splitline_opts=opts.SplitLineOpts(is_show=False)),
            yaxis_opts=opts.AxisOpts(
                axistick_opts=opts.AxisTickOpts(is_show=True),
                splitline_opts=opts.SplitLineOpts(is_show=False),
            ),
        )
    )

    return plot

def generate_table(rows, headers, title: str=None, subtitle: str=None):
    """Generate table."""
    table = Table()

    table.add(headers, rows)
    if title and subtitle:
        table.set_global_opts(
            title_opts=ComponentTitleOpts(title=title, subtitle=subtitle)
        )

    return table

def generate_day_from_to(range):
    """Generate day-from and day-to"""
    if range == '1 hour':
        return 1.0/24.0, 0.0
    elif range == '24 hours':
        return 1.0, 0.0
    elif range == '3 days':
        return 3.0, 0.0
    elif range == '1 week':
        return 7.0, 0.0
    elif range == '1 month':
        return 30.0, 0.0
    elif range == '3 months':
        return 90.0, 0.0
    elif range == '6 months':
        return 180.0, 0.0
    elif range == '1 year':
        return 365.0, 0.0


def generate_x_data_days(day_from, day_to, slice: str='hour'):
    """Generate X dates"""
    date_from = datetime.datetime.now() - datetime.timedelta(days=day_from)
    date_to = datetime.datetime.now() - datetime.timedelta(days=day_to)

    return generate_x_data(date_from=date_from, date_to=date_to, slice=slice)

def generate_x_data(date_from, date_to, slice: str='hour'):
    """Generate X dates"""
    delta = date_to - date_from
    reldelta = relativedelta(date_to, date_from)

    total_seconds = delta.total_seconds()
    total_minutes = int(total_seconds // 60)
    total_hours = int(total_seconds // 3600)
    total_days = int(total_seconds // (24 * 3600))
    total_months = reldelta.months

    if slice == "minute":
        x = [date_from + relativedelta(minutes=x) for x in range(total_minutes + 1)]
        x_str = [e.strftime("%Y-%m-%d %H:%M") for e in x]
    elif slice == "hour":
        x = [date_from + relativedelta(hours=x) for x in range(total_hours + 1)]
        x_str = [e.strftime("%Y-%m-%d %H") for e in x]
    elif slice == "day":
        x = [date_from + relativedelta(days=x) for x in range(total_days + 1)]
        x_str = [e.strftime("%Y-%m-%d") for e in x]
    elif slice == "month":
        x = [date_from + relativedelta(months=x) for x in range(total_months + 2)]
        x_str = [e.strftime("%Y-%m") for e in x]

    return x, x_str


def generate_y_data(records, x_data: list, slice: str="hour"):
    """Generate Y data"""
    y_data = [0] * len(x_data)
    if len(records) == 0:
        return y_data

    if slice == "minute":
        x_data_list = [{'year': e.year, 'month': e.month, 'day': e.day,
                        'hour': e.hour, 'minute': e.minute} for e in x_data]
    elif slice == "hour":
        x_data_list = [{'year': e.year, 'month': e.month, 'day': e.day,
                        'hour': e.hour} for e in x_data]
    elif slice == "day":
        x_data_list = [{'year': e.year, 'month': e.month,
                        'day': e.day} for e in x_data]
    elif slice == "month":
        x_data_list = [{'year': e.year, 'month': e.month} for e in x_data]
    else:
        return y_data

    for record in records:
        date = record['_id']['date']
        index = x_data_list.index(date) if date in x_data_list else -1
        if index != -1:
            y_data[index] = record['sum_request']

    return y_data

def get_slice(day_from, day_to):
    """Get slice"""
    diff =  day_from - day_to

    if diff <= 2.0/24.0:
        return "minute"
    elif diff <= 1.0:
        return "hour"
    elif diff <= 30.0:
        return "day"
    elif diff <= 365.0:
        return "month"

def validate_password(password: str):
    """Validate input password: must be at least 8 characters. 
    must contain lower case, upper case, and bumbers. 
    must not contain meta characters such as space.

    """
    if len(password) < 8:
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if re.search(r"\s" , password):
        return False

    return True

if __name__ == '__main__':
    start_server(main, port=admin_frontend_config.port,
                 cdn=admin_frontend_config.cdn)
