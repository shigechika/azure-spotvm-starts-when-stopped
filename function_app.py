import logging
import azure.functions as func
import os
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.resource import ResourceManagementClient

app = func.FunctionApp()

@app.schedule(schedule="0 * * * * *", arg_name="myTimer", run_on_startup=True,
              use_monitor=False) 
def timer_trigger(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')

    logging.info('timer_trigger function start.')

    # Acquire a credential object.
    CREDENTIAL = DefaultAzureCredential()

    # Retrieve subscription ID from environment variable.
    SUBSCRIPTION_ID = os.environ["AZURE_SUBSCRIPTION_ID"]
    if SUBSCRIPTION_ID is None:
        logging.error("SUBSCRIPTION_ID is None")
        exit(1)
    RESOURCE_GROUP_NAME = os.environ["RESOURCE_GROUP_NAME"]
    VM_NAME = os.environ["VM_NAME"]

    # Obtain the management object for virtual machines
    compute_client = ComputeManagementClient(
        credential=CREDENTIAL, subscription_id=SUBSCRIPTION_ID
    )

    vm_result = compute_client.virtual_machines.instance_view(
        resource_group_name=RESOURCE_GROUP_NAME,
        vm_name=VM_NAME,
    )
    display_status = vm_result.serialize()["statuses"][1]["displayStatus"]

    logging.info(
        f"VM_NAME={VM_NAME}, RESOURCE_GROUP_NAME={RESOURCE_GROUP_NAME}, displayStatus={display_status}"
    )

    if display_status != "VM running":
        # 'VM running' or 'VM deallocated'
        vm_result = compute_client.virtual_machines.begin_start(
            resource_group_name=RESOURCE_GROUP_NAME,
            vm_name=VM_NAME,
        )
        # 'InProgress' or 'Succeeded'
        logging.info(f"begin_start={vm_result.status()}")

    logging.info('timer_trigger function finish.')
