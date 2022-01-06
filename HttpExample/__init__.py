import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.digitaltwins.core import DigitalTwinsClient

import json

from Supplychain.Generic.folder_io import FolderReader
from Supplychain.Generic.memory_folder_io import MemoryFolderIO
from Supplychain.Validate.validate_dict import DictValidator
from Supplychain.Generic.excel_folder_reader import ExcelReader
from Supplychain.Transform.from_table_to_dict import FromTableToDictConverter
from Supplychain.Transform.complete_dict import DictCompleter
from Supplychain.Generic.timer import Timer

import cosmotech_api
from cosmotech_api.api.dataset_api import DatasetApi
from cosmotech_api.api.workspace_api import WorkspaceApi
from cosmotech_api.api.scenario_api import ScenarioApi

import tempfile

from typing import Union
import os

credentials = DefaultAzureCredential()


def add_configuration(function):
    def wrapper(*args, **kwargs):
        scope = "http://dev.api.cosmotech.com/.default"
        token = credentials.get_token(scope)

        configuration = cosmotech_api.Configuration(
            host="https://dev.api.cosmotech.com",
            discard_unknown_keys=True,
            access_token=token.token
        )
        return function(configuration=configuration, *args, **kwargs)

    return wrapper


@add_configuration
def get_scenario_data(scenario_id: str, workspace_id: str, organization_id: str, configuration):
    with cosmotech_api.ApiClient(configuration) as api_client:
        api_instance = ScenarioApi(api_client)
        scenario_data = api_instance.find_scenario_by_id(organization_id=organization_id,
                                                         workspace_id=workspace_id,
                                                         scenario_id=scenario_id)
    return scenario_data


@add_configuration
def get_dataset_from_api(dataset_id: str, workspace_id: str, organization_id: str, configuration) -> Union[
    FolderReader, None]:
    tmp_dataset_dir = tempfile.mkdtemp()
    with cosmotech_api.ApiClient(configuration) as api_client:
        api_instance = DatasetApi(api_client)

        dataset = api_instance.find_dataset_by_id(organization_id=organization_id,
                                                  dataset_id=dataset_id)

        api_ws = WorkspaceApi(api_client)

        file_name = dataset['connector']['parameters_values']['AZURE_STORAGE_CONTAINER_BLOB_PREFIX'].replace(
            '%WORKSPACE_FILE%/', '')

        dl_file = api_ws.download_workspace_file(organization_id=organization_id,
                                                 workspace_id=workspace_id,
                                                 file_name=file_name)

        with open(os.path.join(tmp_dataset_dir, "dataset.xlsx"), "wb") as temp_excel_file:
            temp_excel_file.write(dl_file.read())

    r = ExcelReader(input_folder=tmp_dataset_dir)
    content = MemoryFolderIO()

    with FromTableToDictConverter(reader=r, writer=content) as td:
        td.convert_all()

    print("Dataset downloaded from API")

    return content


def get_dataset_from_adt(adt_adress: str) -> FolderReader:
    client = DigitalTwinsClient(adt_adress, credentials)
    query_expression = 'SELECT * FROM digitaltwins'
    query_result = client.query_twins(query_expression)
    json_content = dict()
    for twin in query_result:
        entity_type = twin.get('$metadata').get('$model').split(':')[-1].split(';')[0]
        t_content = {k: v for k, v in twin.items()}
        t_content['id'] = t_content['$dtId']
        for k in twin.keys():
            if k[0] == '$':
                del t_content[k]
        json_content.setdefault(entity_type, [])
        json_content[entity_type].append(t_content)
        relationships = client.list_relationships(twin['$dtId'])
        for relation in relationships:
            tr = {
                "$relationshipId": "id",
                "$sourceId": "source",
                "$targetId": "target"
            }
            r_content = {k: v for k, v in relation.items()}
            for k, v in tr.items():
                r_content[v] = r_content[k]
            for k in relation.keys():
                if k[0] == '$':
                    del r_content[k]
            json_content.setdefault(relation['$relationshipName'], [])
            json_content[relation['$relationshipName']].append(r_content)
    content = MemoryFolderIO()
    content.files = json_content

    print("Dataset downloaded from ADT")

    return content


@add_configuration
def get_adt_address_from_dataset(dataset_id: str, organization_id: str, configuration) -> str:
    with cosmotech_api.ApiClient(configuration) as api_client:
        api_instance = DatasetApi(api_client)

        dataset = api_instance.find_dataset_by_id(organization_id=organization_id,
                                                  dataset_id=dataset_id)
        adt_address = dataset['connector']['parameters_values']['AZURE_DIGITAL_TWINS_URL']
    return adt_address


def main(req: func.HttpRequest) -> func.HttpResponse:
    with Timer('[Control]') as t:
        scenario_id = req.params.get('scenario-id')
        organization_id = req.params.get('organization-id')
        workspace_id = req.params.get('workspace-id')

        if scenario_id is None or organization_id is None or workspace_id is None:
            return func.HttpResponse(body='Query is missing configuration', status_code=400)

        scenario_data = get_scenario_data(scenario_id=scenario_id,
                                          organization_id=organization_id,
                                          workspace_id=workspace_id)
        t.split("Got scenario data")
        adt_address = get_adt_address_from_dataset(dataset_id=scenario_data['dataset_list'][0],
                                                   organization_id=organization_id)

        t.split("Got adt address")
        mass_lever_id = None
        for parameter in scenario_data['parameters_values']:
            if parameter['parameter_id'] == 'mass_lever_excel_file':
                mass_lever_id = parameter['value']

        t.split("Checked for mass action lever")
        if mass_lever_id is None or int(req.params.get('force_adt', 0)):
            content = get_dataset_from_adt(adt_address)
        else:
            content = get_dataset_from_api(dataset_id=mass_lever_id,
                                           organization_id=organization_id,
                                           workspace_id=workspace_id)
        t.split("Downloaded dataset")

        if content is not None:
            content.files.setdefault('Configuration', [])

            completed_data = MemoryFolderIO()

            with DictCompleter(reader=content, writer=completed_data) as dc:
                dc.complete()

            t.split("Completed dataset")
            with DictValidator(completed_data) as d_val:
                if d_val.validate():
                    t.split("Validated dataset")
                    return func.HttpResponse(body=json.dumps(content.files))
                else:
                    return func.HttpResponse('Error while validating the dataset')
        else:
            return func.HttpResponse('No dataset was found')
