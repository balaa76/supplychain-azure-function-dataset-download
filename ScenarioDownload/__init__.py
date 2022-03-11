from CosmoTech_Acceleration_Library.Accelerators.scenario_download.azure_function_main import generate_main

from Supplychain.Generic.memory_folder_io import MemoryFolderIO
from Supplychain.Transform.from_table_to_dict import FromTableToDictConverter
from Supplychain.Generic.cosmo_api_parameters import CosmoAPIParameters
from Supplychain.Transform.patch_dict_with_parameters import DictPatcher
from Supplychain.Generic.csv_folder_writer import CSVWriter

import tempfile
import os
import json


def apply_update(content: dict, scenario_data: dict) -> dict:
    dataset_content = content
    # Apply you transformation here
    for dataset_id, dataset in content['datasets'].items():
        if dataset['type'] == 'adt':
            dataset_content = dataset['content']
            continue
        if dataset['name'] == 'mass_lever_excel_file':
            mass_action_lever_content = dataset['content']
            _r = MemoryFolderIO()
            _r.files = mass_action_lever_content
            _w = MemoryFolderIO()
            with FromTableToDictConverter(reader=_r, writer=_w) as td:
                td.convert_all()
            dataset_content = _w.files
            break

    tmp_parameter_dir = tempfile.mkdtemp()
    tmp_parameter_file = os.path.join(tmp_parameter_dir, "parameters.json")

    tmp_dataset_dir = tempfile.mkdtemp()

    parameters = []

    for parameter_name, value in content['parameters'].items():
        def add_file_parameter(compared_parameter_name: str):
            if parameter_name == compared_parameter_name:
                param_dir = os.path.join(tmp_parameter_dir, compared_parameter_name)
                os.mkdir(param_dir)
                _writer = CSVWriter(output_folder=param_dir)
                param_content = content['datasets'][value]['content']['content']
                _writer.write_from_list(param_content, 'content')
                parameters.append({
                    "parameterId": parameter_name,
                    "value": parameter_name,
                    "varType": "%DATASETID%"
                })

        add_file_parameter("demand_plan")
        add_file_parameter("transport_duration")
        add_file_parameter("production_resource_opening_time")
        if value in content['datasets']:
            continue
        parameters.append({
            "parameterId": parameter_name,
            "value": value,
            "varType": str(type(value))
        })
    with open(tmp_parameter_file, "w") as _file:
        json.dump(parameters, _file)

    _p = CosmoAPIParameters(parameter_folder=tmp_parameter_dir,
                            dataset_folder=tmp_dataset_dir)

    reader = MemoryFolderIO()
    reader.files = dataset_content
    writer = MemoryFolderIO()

    handler = DictPatcher(reader=reader,
                          writer=writer,
                          parameters=_p)

    configuration = handler.memory.files['Configuration'][0]
    if scenario_data['run_template_id'] == "Lever":
        configuration['EnforceProductionPlan'] = True
    elif scenario_data['run_template_id'] == "MILPOptimization":
        _p.update_parameters([
            {
                'parameterId': 'stock_policy',
                'value': 'None',
                'varType': 'enum',
            },
            {
                'parameterId': 'stock_dispatch_policy',
                'value': 'None',
                'varType': 'enum',
            },
            {
                'parameterId': 'production_policy',
                'value': 'None',
                'varType': 'enum',
            },
        ])
        configuration['EnforceProductionPlan'] = False
        handler.handle_optimization_parameter()
    elif scenario_data['run_template_id'] == "UncertaintyAnalysis":
        configuration['EnforceProductionPlan'] = True
        configuration['ActivateUncertainties'] = True
        handler.handle_uncertainties_settings()

    _tmp_params = dict(_p.get_all_parameters())
    check = True
    for name in ['start_date', 'end_date', 'simulation_granularity']:
        if name not in _tmp_params:
            check = False
            break
    if check:
        handler.handle_simple_simulation()
    handler.handle_model_behavior()
    handler.handle_flow_management_policies()

    return writer.files


main = generate_main(apply_update=apply_update)
