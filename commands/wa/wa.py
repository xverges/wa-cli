
from collections import namedtuple
from datetime import datetime, timezone
from fnmatch import fnmatch
import json
import os
import pathlib
from typing import Dict, List

import click
import ibm_watson as watson
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator


VERSION = '2020-02-05'
SkillId = namedtuple('SkillId', ['id', 'name'])

skills_folder = os.path.join(os.getcwd(), 'output-skills')


def Service(apikey: str, url: str) -> watson.AssistantV1:
    authenticator = IAMAuthenticator(apikey)
    service = watson.AssistantV1(version=VERSION, authenticator=authenticator)
    service.set_service_url(url)
    return service


def _trace_rate_limits(action: str, response: watson.DetailedResponse):
    headers = response.get_headers()
    header_names = ['X-RateLimit-Reset', 'X-RateLimit-Remaining', 'X-RateLimit-Limit']
    ratelimit = {k: headers[k] for k in header_names}
    ratelimit['X-RateLimit-Reset'] = datetime.fromtimestamp(int(ratelimit['X-RateLimit-Reset']),
                                                            timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    click.secho(f'  {action} - {ratelimit}', fg='green', err=True)


class wa(object):

    def __init__(self, apikey: str, url: str):
        self.service = Service(apikey, url)

    def _list_skills(self, pattern: str = '') -> List[SkillId]:
        response = self.service.list_workspaces()
        _trace_rate_limits('list_workspaces', response)
        results = response.get_result()
        skills = []
        for workspace in results['workspaces']:
            if not pattern or fnmatch(workspace['name'], pattern):
                skills.append(SkillId(workspace['workspace_id'], workspace['name']))
        return skills

    def _delete_skill(self, skill_id: str) -> bool:
        response = self.service.delete_workspace(skill_id)
        _trace_rate_limits('delete_workspace', response)
        return response.get_status_code() == 200

    def _get_skill(self, skill_id: str) -> Dict:
        response = self.service.get_workspace(skill_id, export=True, sort='stable')
        _trace_rate_limits('get_workspace', response)
        results = response.get_result()
        return results

    def _create_skill(self, skill_data: Dict) -> bool:
        response = self.service.create_workspace(**skill_data)
        _trace_rate_limits('create_workspace', response)
        return response.get_status_code() == 201

    @staticmethod
    def list_skills(apikey: str, url: str, pattern: str) -> List[SkillId]:
        return wa(apikey, url)._list_skills(pattern)

    @staticmethod
    def delete_skill(apikey: str, url: str, skill_id: str) -> bool:
        return wa(apikey, url)._delete_skill(skill_id)

    @staticmethod
    def delete_all_skills(apikey: str, url: str) -> bool:
        service = wa(apikey, url)
        skills = service._list_skills()
        success = True
        for (id, name) in skills:
            click.echo(f'Deleting skill {name}-{id}...')
            service._delete_skill(id)
        return success

    @staticmethod
    def clone_service(rw_apikey: str, rw_url: str,
                      ro_apikey: str, ro_url: str,
                      force: bool) -> bool:
        pathlib.Path(skills_folder).mkdir(parents=True, exist_ok=True)
        src = wa(ro_apikey, ro_url)
        tgt = wa(rw_apikey, rw_url)
        skills = src._list_skills()
        success = True
        for (id, name) in skills:
            if not force:
                if not click.confirm(f'Do you want to copy the skill {id}-{name} continue?'):
                    continue
            skill_data = src._get_skill(id)
            skills_file = os.path.join(skills_folder, f'{id}-{name}.json')
            with open(skills_file, 'w', encoding='utf-8') as json_file:
                json.dump(skill_data, json_file, ensure_ascii=False, indent=4)
            try:
                skill_data['description'] = f'{skill_data["description"]} - Cloned from {id}-{name}'
                tgt._create_skill(skill_data)
                click.echo(f'Cloned skill {name}-{id}')
            except watson.ApiException as xcpt:
                click.secho(f'Error cloning skill {name}-{id}: {xcpt.message}', fg='white', bg='red')
                success = False
        return success
