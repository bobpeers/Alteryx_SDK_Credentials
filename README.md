# Alteryx_SDK_Credentials
Alteryx tool to retrieve saved credentials from Windows Credentials Manager. This avoids the issue of having hard coded usernames and password in workflows for use in APIs for example.

## Installation
Download the yxi file and double click to install in Alteyrx. The tool will be installed in the __Developer__ category.

![alt text](https://github.com/bobpeers/Alteryx_SDK_Credentials/blob/master/images/Credentials_toolbar.png "Alteryx Developer Category")

## Requirements

This tool uses the standard Python libraries so no dependencies will be installed.

## Usage
This tool has no inputs. Place tool on the canvas and configure the tools with the name of the saved credential to retrieve.

## Outputs
Sucessful operations will be output to the O-Output. The output is in two columns, saved username and password.

## Usage
This workflow demonstrates the tool in use and the output data. The name of the saevd credential is enter and the workflow returns the username and password associated with the key.

![alt text](https://github.com/bobpeers/Alteryx_SDK_Credentials/blob/master/images/Credentials_workflow.png "Credentials Workflow")

Credentials must be save din the __Generic Credentials__ section of Windows Credentials Manager as shown below.

![alt text](https://github.com/bobpeers/Alteryx_SDK_Credentials/blob/master/images/Credential_Manager.png "Windows Credential Manager")
