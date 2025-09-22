import requests

# Set your credentials and IDs
AUTH_URL = 'https://auth.anaplan.com/token/authenticate'
CLOUDWORKS_RUN_URL = 'https://api.cloudworks.anaplan.com/1/0/integrationFlows/{integration_flow_id}/run'
USERNAME = 'your_anaplan_account_email'
PASSWORD = 'your_anaplan_password'
INTEGRATION_FLOW_ID = 'your_integration_flow_id'

# Step 1: Authenticate and get the token
auth_headers = {'Content-Type': 'application/json'}
auth_data = {'username': USERNAME, 'password': PASSWORD}
auth_response = requests.post(AUTH_URL, json=auth_data, headers=auth_headers)
auth_response.raise_for_status()
token = auth_response.json()['tokenInfo']['tokenValue']

# Step 2: Trigger the integration flow
integration_headers = {
    'Content-Type': 'application/json',
    'Authorization': f'AnaplanAuthToken {token}'
}
run_response = requests.post(
    CLOUDWORKS_RUN_URL.format(integration_flow_id=INTEGRATION_FLOW_ID),
    headers=integration_headers
)
run_response.raise_for_status()
print("Integration Flow Triggered. Status:", run_response.status_code, run_response.text)
