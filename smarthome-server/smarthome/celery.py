"""To be able to handle scenarios that can change over a time (eg. progressive dimming of lights,
activation of something after 10 min, etc.), we use a task queue so that the "content" of the
scenario can be handled outside of the API's web server, asynchronously.

We want to be able to run a long scenarios outside the web server, but all to list all the running
scenarios and interrupt a running one.

We use Celery and RabbitMQ to run the scenarios. In particular, we use the chain feature along with
a task that just waits between two concrete tasks. Maybe there's a better way to do this with
Celery, I'm new to this.

The IDs of the tasks that are running/queued for a scenario are saved in a DB, so that we can cancel
them. The content of the DB can be accessed through the API.

TODO better handle both chains and sequences, show both in API, allow to stop both.
TODO propose to handle unique names of chains and sequences. If you create a new chain / sequence
 with same unique name as an existing one, stop the existing one and replace it.
"""

import datetime
import logging
from time import sleep
from typing import List

import pkg_resources
import requests
from celery import Celery, Task, chain
from celery.result import AsyncResult
from smarthome.misc.utils import TypedDict
from tinydb import Query, TinyDB

app = Celery('smarthome', broker='pyamqp://guest@localhost//')

DB = TinyDB(pkg_resources.resource_filename("smarthome", "data/tasks.json"))
SEQUENCES_TABLE = DB.table("sequences")
CHAINS_TABLE = DB.table("chains")


class ChainLog(TypedDict):
    id: str
    tasks: List[str]


class SequenceLog(TypedDict):
    id: str
    name: str
    date: str
    chains: List[str]


def get_sequence_id(name: str) -> str:
    """Generate a sequence ID."""
    return name + "_" + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")


def get_chain(id: str) -> ChainLog:
    """Get a chain from the DB"""
    log = CHAINS_TABLE.get(Query().id == id)
    if log is None:
        raise ValueError("No chain with this ID.")
    return log


@app.task
def remove_chain(id: str):
    """Remove a chain from DB"""
    CHAINS_TABLE.remove(Query().id == id)


@app.task
def remove_sequence(id: str):
    """Remove a sequence from DB"""
    SEQUENCES_TABLE.remove(Query().id == id)


def is_sequence_running(sequence: SequenceLog):
    if all(CHAINS_TABLE.get(Query().id == chain_id) is None for chain_id in sequence["chains"]):
        remove_sequence(sequence["id"])
        return False
    else:
        return True


def get_sequence(id: str) -> SequenceLog:
    """Get a chain from the DB"""
    seq: SequenceLog = SEQUENCES_TABLE.get(Query().id == id)
    if seq is None or not is_sequence_running(seq):
        raise ValueError("No chain with this ID.")
    return seq


def list_sequences() -> List[SequenceLog]:
    """List all chains in the DB."""
    return [seq for seq in SEQUENCES_TABLE.all() if is_sequence_running(seq)]


def stop_sequence(id: str):
    """interrupt a running sequence"""
    sequence_doc = get_sequence(id)
    for chain_id in sequence_doc["chains"]:
        chain_log = get_chain(chain_id)
        for task_id in chain_log["tasks"]:
            app.control.revoke(task_id, terminate=True, signal='SIGKILL')
        remove_chain(chain_id)
    remove_sequence(id)


def register_sequence(name: str, chains: List[List[str]], id: str = None) -> SequenceLog:
    """Register a chain in the chains DB"""
    if id is None:
        id = get_sequence_id(name)

    seq_log: SequenceLog = {
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "id": id,
        "name": name,
        "chains": []
    }
    for i, chain_tasks in enumerate(chains):
        chain_log: ChainLog = {"id": f"{id}_{i}", "tasks": chain_tasks}
        CHAINS_TABLE.insert(chain_log)
        seq_log["chains"].append(chain_log["id"])
    SEQUENCES_TABLE.insert(seq_log)
    return seq_log


def run_sequence(name: str, list_of_chains: List[List[Task]]) -> SequenceLog:
    """Run a chain of tasks and register it in the DB of chains that are running. When the task is
    done, it will remove itself from the DB.
    """
    id = get_sequence_id(name)

    chains = []
    for chain_tasks in list_of_chains:
        chain_obj = chain(*chain_tasks, remove_chain.si(id))
        res: AsyncResult = chain_obj.delay()
        tasks_ids = res.as_list()
        chains.append(tasks_ids)

    return register_sequence(name, chains, id)


@app.task
def call_domoticz(url: str, catch_error: bool = False):
    try:
        logging.info(f"Calling {url}")
        req = requests.get(url)
        req.raise_for_status()
        if req.json().get("status") != "OK":
            raise RuntimeError(f"Domoticz did not return status=OK, got {req.json()}")
        return True
    except Exception as e:
        if catch_error:
            logging.error(f"Failed during domoticz call to {url}: {e}")
            return False
        else:
            raise RuntimeError(f"Failed during domoticz call to {url}: {e}") from e


@app.task
def wait(wait_sec: float):
    sleep(wait_sec)
