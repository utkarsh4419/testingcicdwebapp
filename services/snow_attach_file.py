import requests
from config.settings import *
from config.keyvault import get_CONFIG
from utils.helpers import return_error

def get_snow_token():

    CONFIG = get_CONFIG()
    url = "https://genpactdevelop.service-now.com/oauth_token.do"

    payload = {
        "grant_type": "client_credentials",
        "client_id": CONFIG['snow_id'],
        "client_secret": CONFIG['snow_secret']
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(url, data=payload, headers=headers)
    response.raise_for_status()

    return response.json()["access_token"]


def get_change_task_sys_id(token, change_task_number):
    url = f"https://genpactdevelop.service-now.com/api/now/v2/table/change_task"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    params = {
        "sysparm_query": f"number={change_task_number}",
        "sysparm_fields": "sys_id",
        "sysparm_limit": 1
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    result = response.json()["result"]
    if not result:
        raise Exception("Change task not found")

    return result[0]["sys_id"]

def get_existing_attachment(token, change_task_sys_id,file_name):
    url = f"https://genpactdevelop.service-now.com/api/now/table/sys_attachment"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    params = {
        "sysparm_query": (
            f"table_name=change_task^"
            f"table_sys_id={change_task_sys_id}^"
            f"file_name={file_name}"

        ),
        "sysparm_fields": "sys_id,file_name"
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    #result = response.json().get("result", [])
    return response.json().get("result", [])


def delete_attachment(token, attachment_sys_id):
    url = f"https://genpactdevelop.service-now.com/api/now/table/sys_attachment/{attachment_sys_id}"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.delete(url, headers=headers)
    response.raise_for_status()

    return True

def delete_attachments(token, attachments):
    for attachment in attachments:
        attachment_sys_id = attachment["sys_id"]
        delete_attachment(token, attachment_sys_id)

def attach_file_to_change_task(token, change_task_sys_id, json_data):
    url = f"https://genpactdevelop.service-now.com/api/now/attachment/file?table_name=change_task&table_sys_id={change_task_sys_id}&file_name=Data.txt"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/zip"
    }

    payload = f"{json_data}"
   

    response = requests.post(url, headers=headers,  data=payload)
    response.raise_for_status()

    return response.json()

def replace_attachment(token, change_task_sys_id, frontend_json):
    file_name = "Data.txt"

    # Step 1: find ALL duplicates
    attachments = get_existing_attachment(
        token,
        change_task_sys_id,
        file_name
    )

    # Step 2: delete ALL if any
    if attachments:
        delete_attachments(token, attachments)

    # Step 3: attach fresh file
    return attach_file_to_change_task(
        token,
        change_task_sys_id,
        frontend_json
    )

