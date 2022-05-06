# supplychain-azure-function-dataset-download Function App


The **_supplychain-azure-function-dataset-download_** is a specialization for the Cosmo Tech Supply Chain solution of the the generic azure function app [_azure-function-scenario-download_](https://github.com/Cosmo-Tech/azure-function-scenario-download)

This Supply Chain specific version is based on the [Cosmotech Azure function Scenario Download](https://github.com/Cosmo-Tech/azure-function-scenario-download)

This azure function app aims to be integrated in the Cosmo Tech Supply Chain Web-app : [azure-supplychain-webapp](https://github.com/Cosmo-Tech/azure-supplychain-webapp) for Cosmo Tech internal use or [azure-supplychain-webapp-shared](https://github.com/Cosmo-Tech/azure-supplychain-webapp-shared) for external use


# Deploy 

## Pre-Requisites

1. Dedicated App registration with Cosmo API access permission configured and declare in ADT : app ID + secret needed<br>

2. App registration created for Cosmo webapp : only app ID needed

<br>

### Dedicated app registration to be created  :
- *_Organization.user_* permission on the Cosmo Tech Platform API   
- Client secret created
- _Azure Digital Twin Data Reader_ permission on the Azure Data Explorer instance 
<br><br>

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2FCosmo-Tech%2Fsupplychain-azure-function-dataset-download%2Fmain%2Fdeploy%2Fazuredeploy.json)

<br>

## Installation options

| Parameter | Note |
| ----------- | ----------- |
| Subscription | Choose same as related platform and webapp |
| Resource group | Choose same as related platform and webapp |
| Region | Choose same as related platform and webapp |
| Site Name | Function App Name	Choose a name for the function app |
| Storage Account Name | Storage account required for the function app |
| Location | Keep pre-populated value |
| Csm Api Host | Cosmo Tech Platform API host |
| Az Cli ID	| Client id of the dedicated app registration (see pre-requisites) |
| Az Cli Secret | Secret create of the dedicated app registration (see pre-requisites) |
| Csm Api Scope | Scope for accesing the Cosmo Tech Platform API |
| Package Address | URL of the Azure function package to be deployed  - IMPORTANT : pick the URL from the latest release, ex [release 2.1.10](https://github.com/Cosmo-Tech/supplychain-azure-function-dataset-download/releases/download/2.1.10/artifact.zip) |

<br>


## Configure CORS

- Check option Enable Access-Control-Allow-Credentials

- Allowed Origins : Cosmo Tech Supply Chain web-app URL

- Optional configuration dev usage : http://localhost:3000

<br>

# Integrate in the Cosmo Tech Supply Chain web-app



## Configure for the flowchart


```javascript
export const AZURE_FUNCTION_FLOWCHART_URL =
  'https://<azure function deployment url>/api/ScenarioDownload';
export const AZURE_FUNCTION_FLOWCHART_HEADERS = {
  'x-functions-key': '<default host keys>',
};
```

## Configure for the lever tables

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
