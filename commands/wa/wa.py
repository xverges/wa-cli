
from collections import namedtuple
from datetime import datetime, timezone
from fnmatch import fnmatch
import json
import os
from typing import Dict, List, Tuple

import click
import ibm_watson as watson
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

from ..helpers import cfg

VERSION = '2020-02-05'
SkillTuple = namedtuple('SkillTuple', ['id', 'name', 'updated_on'])


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

    def _list_skills(self, pattern: str = '',) -> List[SkillTuple]:
        response = self.service.list_workspaces(include_audit=True)
        _trace_rate_limits('list_workspaces', response)
        results = response.get_result()
        skills = []
        for workspace in results['workspaces']:
            if not pattern or fnmatch(workspace['name'], pattern):
                skills.append(SkillTuple(workspace['workspace_id'],
                                         workspace['name'],
                                         workspace['updated']))
        return skills

    def _delete_skill(self, skill_id: str) -> bool:
        response = self.service.delete_workspace(skill_id)
        _trace_rate_limits('delete_workspace', response)
        return response.get_status_code() == 200

    def _get_skill(self, skill_id: str) -> Dict:
        response = self.service.get_workspace(skill_id,
                                              export=True,
                                              sort='stable',
                                              include_audit=True)
        _trace_rate_limits('get_workspace', response)
        results = response.get_result()
        return results

    def _create_skill(self, skill_data: Dict) -> bool:
        response = self.service.create_workspace(**skill_data)
        _trace_rate_limits('create_workspace', response)
        return response.get_status_code() == 201

    def _update_skill(self, skill_data: Dict) -> bool:
        response = self.service.update_workspace(**skill_data)
        _trace_rate_limits('update_workspace', response)
        return response.get_status_code() == 200

    def _get_skill_file(self, skill: SkillTuple) -> Tuple[str, object]:
        "Saves a skill to a file, and returns (path, data)"

        skill_file = os.path.join(cfg.skills_folder(), f'{skill.id}-{skill.name}.json')
        skill_data = self._get_cached(skill_file, skill.updated_on)
        if skill_data:
            click.echo(f'Using cache for skill {skill.name}-{skill.id}')
        else:
            skill_data = self._get_skill(skill.id)
            with open(skill_file, 'w', encoding='utf-8') as json_file:
                json.dump(skill_data, json_file, ensure_ascii=False, indent=4)
        return (skill_file, skill_data)

    @staticmethod
    def _get_cached(full_path: str, modified: str) -> object:
        if os.path.isfile(full_path):
            with open(full_path, 'r') as json_file:
                cached = json.load(json_file)
                if cached['updated'] == modified:
                    return cached
        return None

    @staticmethod
    def list_skills(apikey: str, url: str, pattern: str) -> List[SkillTuple]:
        return wa(apikey, url)._list_skills(pattern)

    @staticmethod
    def delete_skill(apikey: str, url: str, skill_id: str) -> bool:
        return wa(apikey, url)._delete_skill(skill_id)

    @staticmethod
    def deploy_skill(apikey: str, url: str, skill_file: str, force: bool) -> bool:
        service = wa(apikey, url)
        skills = service._list_skills()
        with open(skill_file, 'r') as json_file:
            new_skill = json.load(json_file)
        name = new_skill['name']
        matching = [skill for skill in skills if skill.name == name]
        if len(matching) and not force:
            if not click.confirm(f'Do you want to overwrite the skill {matching[0].id}-{name} continue?',
                                 abort=True):
                return False
        new_skill.pop('created', None)
        new_skill.pop('status', None)
        new_skill.pop('updated', None)
        if len(matching):
            success = service._update_skill(new_skill)
        else:
            new_skill.pop('workspace_id', None)
            success = service._create_skill(new_skill)
        return success

    @staticmethod
    def delete_all_skills(apikey: str, url: str) -> bool:
        service = wa(apikey, url)
        skills = service._list_skills()
        success = True
        for skill in skills:
            click.echo(f'Deleting skill {skill.name}-{skill.id}...')
            service._delete_skill(skill.id)
        return success

    @staticmethod
    def clone_service_skills(rw_apikey: str, rw_url: str,
                             ro_apikey: str, ro_url: str,
                             force: bool) -> bool:
        src = wa(ro_apikey, ro_url)
        tgt = wa(rw_apikey, rw_url)
        skills = src._list_skills()
        success = True
        for skill in skills:
            if not force:
                if not click.confirm(f'Do you want to copy the skill {skill.id}-{skill.name} continue?'):
                    continue
            skill_file, skill_data = src._get_skill_file(skill)
            try:
                skill_data['description'] = f'{skill_data["description"]} - Cloned from {skill.id}-{skill.name}'
                tgt._create_skill(skill_data)
                click.echo(f'Cloned skill {skill.name}-{skill.id}')
            except watson.ApiException as xcpt:
                click.secho(f'Error cloning skill {skill.name}-{skill.id}: {xcpt.message}', fg='white', bg='red')
                success = False
        return success

    @staticmethod
    def download_service_skills(apikey: str, url: str,
                                force: bool) -> bool:
        service = wa(apikey, url)
        skills = service._list_skills()
        success = True
        for skill in skills:
            if not force:
                if not click.confirm(f'Do you want to download the skill {skill.id}-{skill.name} continue?'):
                    continue
            service._get_skill_file(skill)
            click.echo(f'Downloaded skill {skill.name}-{skill.id}')
        return success
