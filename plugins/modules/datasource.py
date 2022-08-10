#!/usr/bin/python

DOCUMENTATION = '''
---
module: datasource
author:
  - Ishan Jain (@ishanjainn)
version_added: "0.0.1"
short_description: Manage Data sources in Grafana
description:
  - Create, Update and delete Data sources using Ansible.
options:
  datasource:
    description:
      - JSON source code for the Data source
    type: dict
    required: true
  stack_slug:
    description:
      - Name of the Grafana Cloud stack to which the notification policies will be added
    type: str
    required: true
  cloud_api_key:
    description:
      - CLoud API Key to authenticate with Grafana Cloud.
    type: str
    required : true
  state:
    description:
      - State for the Grafana CLoud stack.
    choices: [ present, absent ]
    default: present
    type: str
'''

EXAMPLES = '''
- name: Create/Update Data sources
  datasource:
    datasource: "{{ lookup('file', 'datasource.json') }}"
    stack_slug: "{{ stack_slug }}"
    cloud_api_key: "{{ grafana_cloud_api_key }}"
    state: present

- name: Delete Data sources
  datasource:
    datasource: "{{ lookup('file', 'datasource.json') }}"
    stack_slug: "{{ stack_slug }}"
    cloud_api_key: "{{ grafana_cloud_api_key }}"
    state: absent
'''

RETURN = r'''
output:
  description: Dict object containing Data source information
  returned: On success
  type: dict
  contains:
    datasource:
      description: The response body content for the data source configuration.
      returned: state is present and on success
      type: dict
    id:
      description: The ID assigned to the data source
      returned: on success
      type: int
    name:
      description: The name of the data source defined in the JSON source code
      returned: state is present and on success
      type: str
    message:
      description: The message returned after the operation on the Data source
      returned: on success
      type: str
'''

from ansible.module_utils.basic import AnsibleModule
import requests


def present_datasource(module):
    api_url = 'https://' + module.params['stack_slug'] + '.grafana.net/api/datasources'

    result = requests.post(api_url, json=module.params['datasource'], headers={"Authorization": 'Bearer ' + module.params['cloud_api_key']})

    if result.status_code == 200:
        return False, True, result.json()
    elif result.status_code == 409:
        get_id_url = requests.get('https://' + module.params['stack_slug'] + '.grafana.net/api/datasources/id/' + module.params['datasource']['name'],
                                  headers={"Authorization": 'Bearer ' + module.params['cloud_api_key']})

        api_url = 'https://' + module.params['stack_slug'] + '.grafana.net/api/datasources/' + str(get_id_url.json()['id'])

        result = requests.put(api_url, json=module.params['datasource'], headers={"Authorization": 'Bearer ' + module.params['cloud_api_key']})

        if result.status_code == 200:
            return False, True, result.json()
        else:
            return True, False, {"status": result.status_code, 'response': result.json()['message']}

    else:
        return True, False, {"status": result.status_code, 'response': result.json()['message']}


def absent_datasource(module):
    api_url = 'https://' + module.params['stack_slug'] + '.grafana.net/api/datasources/' + module.params['datasource']['name']

    result = requests.delete(api_url, headers={"Authorization": 'Bearer ' + module.params['cloud_api_key']})

    if result.status_code == 200:
        return False, True, result.json()
    else:
        return True, False, {"status": result.status_code, 'response': result.json()['message']}


def main():
    module_args = dict(
        datasource=dict(type='dict', required=True),
        stack_slug=dict(type='str', required=True),
        cloud_api_key=dict(type='str', required=True),
        state=dict(type='str', required=False, default='present', choices=['present', 'absent'])
    )

    choice_map = {
        "present": present_datasource,
        "absent": absent_datasource,
    }

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    is_error, has_changed, result = choice_map.get(
        module.params['state'])(module)

    if not is_error:
        module.exit_json(changed=has_changed, output=result)
    else:
        module.fail_json(msg=result)


if __name__ == '__main__':
    main()