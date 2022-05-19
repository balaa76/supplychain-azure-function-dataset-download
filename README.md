# supplychain-azure-function-dataset-download Function App


The **_supplychain-azure-function-dataset-download_** is a specialization for the Cosmo Tech Supply Chain solution of the the generic azure function app [_azure-function-scenario-download_](https://github.com/Cosmo-Tech/azure-function-scenario-download)

This Supply Chain specific version is based on the [Cosmotech Azure function Scenario Download](https://github.com/Cosmo-Tech/azure-function-scenario-download)

This azure function app aims to be integrated in the Cosmo Tech Supply Chain Web-app : [azure-supplychain-webapp](https://github.com/Cosmo-Tech/azure-supplychain-webapp) for Cosmo Tech internal use or [azure-supplychain-webapp-shared](https://github.com/Cosmo-Tech/azure-supplychain-webapp-shared) for external use

# Build

## How to build a deployable file

Running the following commands in a terminal will create a file `Artifact.zip` which can then be used for deployment 

```bash
pip install --target .python_packages/lib/site-packages/ -r requirements.txt
zip -r artifact.zip . -x ".git/*" ".github/*" ".gitignore"
```

# Deploy 

## Pre-Requisites

- Dedicated App registration created (see details below)

<br>

### Dedicated app registration :
1. Create a new app registration
2. Add a API permission to the Cosmo Tech Platform API, choose the permission type *_Application_* (not *_Delegated_*) and select the permission *_Organization.user_*
3. Create a client secret
4. In the related Azure Digital Twins resources, assign the role _Azure Digital Twin Data Reader_  to app registration 
<br><br>

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2FCosmo-Tech%2Fsupplychain-azure-function-dataset-download%2Fmain%2Fdeploy%2Fazuredeploy.json)

<br>

## Installation options

| Parameter            | Note                                                                                                                                                                                                                                       |
|----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Subscription         | Choose same as the related platform and webapp                                                                                                                                                                                             |
| Resource group       | Choose same as the related platform and webapp                                                                                                                                                                                             |
| Region               | Choose same as related platform and webapp                                                                                                                                                                                                 |
| Site Name            | Choose a name for the function app or leave the default value for auto-generated name                                                                                                                                                      |
| Storage Account Name | Choose a name for the storage account required for the function app or leave the default value for auto-generated name                                                                                                                     |
| Location             | Location for the resources to be created (Function App, App Service plan and Storage Account)                                                                                                                                              |
| Csm Api Host         | Cosmo Tech Platform API host                                                                                                                                                                                                               |
| Csm Api Scope        | Scope for accessing the Cosmo Tech Platform API (must end with /.default)                                                                                                                                                                  |
| Az Cli ID	           | Client ID of the dedicated app registration (see pre-requisites)                                                                                                                                                                           |
| Az Cli Secret        | Client Secret create of the dedicated app registration (see pre-requisites)                                                                                                                                                                |
| Package Address      | URL of the Azure function package to be deployed  - IMPORTANT : pick the URL from the latest release, ex [release 2.1.10](https://github.com/Cosmo-Tech/supplychain-azure-function-dataset-download/releases/download/2.1.10/artifact.zip) |

<br>


## Configure CORS

### Request Credentials
Check option _*Enable Access-Control-Allow-Credentials*_

### Allowed Origins :
- Add the URL of the Cosmo Tech Supply Chain Web-App
- For dev usage (optional) add http://localhost:3000

<br>


# Secure the Azure Function

The azure function includes a first level of securizartion with the host key.<br>
This keys being included in the web application, we need a second layer of securization by limiting the azure function calls to the users being authorized to the Cosmo Tech API :

## Add identity provider

- Go to Authentication
- Add identity provider
- Select "Microsoft"
- In "App registration type", select "Pick an existing app registration in this directory"
<br>

- Restrict access : "Require authentication"
- Unauthenticated requests : HTTP 401
- Token store : leave checked
<br>
## Configure audience
- In the created identity provider, click on "Edit"
- Allowed token audiences : "https://_*cosmo platform*_.api.cosmotech.com" 
Note : you may need to specify the core platform app registration id instead of the API 

# Integrate in the Cosmo Tech Supply Chain web-app


## Configure for the flowchart

### in file "src/config/AppInstance.js"

```javascript
export const AZURE_FUNCTION_FLOWCHART_URL =
  'https://<azure function deployment url>/api/ScenarioDownload';
export const AZURE_FUNCTION_FLOWCHART_HEADERS = {
  'x-functions-key': '<default host keys>',
};
```

## Configure for the lever tables

### in file "src/config/ScenarioParameters.js", for each lever table

Example with the demand plan table

```javascript
  demand_plan: {
    connectorId: 'c-ll43p5nll5xqx',
    defaultFileTypeFilter: '.csv',
    subType: 'AZURETABLE',
    azureFunction: 'https://<azure function deployment url>/api/DemandsPlan',
    azureFunctionHeaders: { 'x-functions-key': '<default host keys>' },
  }
```
