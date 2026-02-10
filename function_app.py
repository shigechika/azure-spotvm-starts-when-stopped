import logging
import os

import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient

app = func.FunctionApp()

credential = DefaultAzureCredential()


def _get_display_status(vm_instance_view) -> str:
    """PowerState を持つ status から displayStatus を取得する。"""
    for status in vm_instance_view.statuses:
        if status.code and status.code.startswith("PowerState/"):
            return status.display_status
    return "Unknown"


@app.schedule(schedule="0 * * * * *", arg_name="myTimer", run_on_startup=True,
              use_monitor=False)
def timer_trigger(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')

    logging.info('timer_trigger function start.')

    subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
    resource_group_name = os.environ.get("RESOURCE_GROUP_NAME")
    vm_name = os.environ.get("VM_NAME")

    if not subscription_id or not resource_group_name or not vm_name:
        logging.error(
            "Required environment variables are missing: "
            "AZURE_SUBSCRIPTION_ID=%s, RESOURCE_GROUP_NAME=%s, VM_NAME=%s",
            subscription_id, resource_group_name, vm_name,
        )
        return

    compute_client = ComputeManagementClient(
        credential=credential, subscription_id=subscription_id
    )

    try:
        vm_result = compute_client.virtual_machines.instance_view(
            resource_group_name=resource_group_name,
            vm_name=vm_name,
        )
        display_status = _get_display_status(vm_result)

        logging.info(
            "VM_NAME=%s, RESOURCE_GROUP_NAME=%s, displayStatus=%s",
            vm_name, resource_group_name, display_status,
        )

        if display_status != "VM running":
            poller = compute_client.virtual_machines.begin_start(
                resource_group_name=resource_group_name,
                vm_name=vm_name,
            )
            logging.info("begin_start=%s", poller.status())
    except Exception:
        logging.exception("Failed to check or start VM %s", vm_name)

    logging.info('timer_trigger function finish.')
