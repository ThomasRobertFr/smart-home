"""To be able to handle scenarios that can change over a time (eg. progressive dimming of lights,
activation of something after 10 min, etc.), we use a task queue so that the "content" of the
scenario can be handled outside of the API's web server, asynchronously. More precisely, this code
currently rely on Celery and RabbitMQ.

For this, a scenario will be able to launch sequences and create sequence groups.

A sequence is a succession of tasks run by the task queue one by one. Concrete tasks can be
separated by tasks that just wait for a defined period of time so that we can "schedule" them over
time. For example, to dim a light, we can lower the brightness by 1 every minute, i.e. lower the
brightness, wait a min, lower the brightness, etc.

Sequences can be be put in sequence groups. The goal is just to let the user know that a set set of
sequences are running for a named goal. For scenarios, the sequence group is the name of the
scenario. It also allows to cancel all the seqeunces in a group if needed.

The IDs of the Celery tasks that are running/queued are saved in a DB. The content of the DB can be
accessed through the API.
"""

import datetime
import logging
from time import sleep
from typing import List, Union

import pkg_resources
import requests
from celery import Celery, Task, chain
from celery.result import AsyncResult
from smarthome.misc.utils import TypedDict
from tinydb import Query, TinyDB

app = Celery('smarthome', broker='pyamqp://guest@localhost//')

DB = TinyDB(pkg_resources.resource_filename("smarthome", "data/sequences.json"))
SEQ_GROUPS_TABLE = DB.table("sequence_groups", cache_size=0)
SEQUENCES_TABLE = DB.table("sequences", cache_size=0)


class Sequence(TypedDict):
    """A concrete sequence of tasks that is running"""
    id: str
    group_id: Union[str, None]
    device_id: Union[str, None]
    device_idx: Union[int, None]
    tasks: List[str]


class SequenceToRun(TypedDict):
    """A concrete sequence of tasks that is running"""
    id: str
    device_id: Union[str, None]
    device_idx: Union[int, None]
    tasks: List[Task]


class SequenceGroup(TypedDict):
    """A wrapper to which one or multiple sequences can be linked"""
    id: str
    name: str
    date: str


class SequenceGroupEnriched(SequenceGroup):
    sequences: List[Sequence]


def get_unique_id(name: str) -> str:
    return name + "_" + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")


@app.task
def remove_sequence(id: str):
    group_id = None
    if sequence_exists(id):
        group_id = get_sequence(id)["group_id"]
    SEQUENCES_TABLE.remove(Query().id == id)
    # Remove the sequence_group if it was the last sequence in it
    if group_id is not None and not list_sequences(group_id=group_id):
        remove_sequence_group(group_id)


def sequence_exists(id: str) -> bool:
    return SEQUENCES_TABLE.contains(Query().id == id)


def get_sequence(id: str) -> Sequence:
    log = SEQUENCES_TABLE.get(Query().id == id)
    if log is None:
        raise ValueError("No sequence with this ID.")
    return log


def stop_sequence(id: str):
    if not sequence_exists(id):
        return
    sequence_log = get_sequence(id)
    for task_id in sequence_log["tasks"]:
        app.control.revoke(task_id, terminate=True, signal='SIGKILL')
    remove_sequence(id)


def list_sequences(group_id: str = None,
                   device_id: str = None,
                   device_idx: int = None) -> List[Sequence]:
    # Init a query that matches everything
    seq_query = Query()
    query = seq_query.id != "match_all_by_default"
    if group_id is not None:
        query = query & (seq_query.group_id == group_id)
    if device_id is not None:
        query = query & (seq_query.device_id == device_id)
    if device_idx is not None:
        query = query & (seq_query.device_idx == device_idx)

    return SEQUENCES_TABLE.search(query)


@app.task
def remove_sequence_group(id: str):
    SEQ_GROUPS_TABLE.remove(Query().id == id)


def sequence_group_exists(id: str) -> bool:
    if not SEQ_GROUPS_TABLE.contains(Query().id == id):
        return False
    elif not len(list_sequences(group_id=id)):
        remove_sequence_group(id)
        return False
    else:
        return True


def get_sequence_group(id: str) -> SequenceGroupEnriched:
    if not sequence_group_exists(id):
        raise ValueError("No sequence_group with this ID")
    seq: SequenceGroup = SEQ_GROUPS_TABLE.get(Query().id == id)
    seq: SequenceGroupEnriched
    seq["sequences"] = list_sequences(group_id=seq["id"])
    return seq


def list_sequence_groups() -> List[SequenceGroupEnriched]:
    return [
        get_sequence_group(seq["id"]) for seq in SEQ_GROUPS_TABLE.all()
        if sequence_group_exists(seq["id"])
    ]


def stop_sequence_group(group_id: str):
    for subsequence in list_sequences(group_id=group_id):
        stop_sequence(subsequence["id"])
    remove_sequence_group(group_id)


def run_sequence(id: str, group_id: Union[str, None], device_id: Union[str, None],
                 device_idx: Union[int, None], tasks: List[Task]) -> Sequence:
    """Launch a sequence of celery tasks. Register it in DB. If a sequence with the same ID already
    exist in DB, it will be stopped to be replaced by this one.
    """
    if sequence_exists(id):
        stop_sequence(id)
    seq: Sequence = {
        "id": id,
        "group_id": group_id,
        "device_id": device_id,
        "device_idx": device_idx,
        "tasks": []
    }
    sequence_obj = chain(*tasks, remove_sequence.si(id))
    res: AsyncResult = sequence_obj.delay()
    seq["tasks"] = res.as_list()
    SEQUENCES_TABLE.insert(seq)
    return seq


def run_sequence_group(name: str, sequences: List[SequenceToRun], use_name_as_id: bool = False) \
        -> SequenceGroupEnriched:
    """Run a group of sequences, register all in the DB. When the sequences are done they will
    remove themselves from DB. When all the sequences of the group are done, the sequence will be
    removed from DB.
    """
    if use_name_as_id:
        id = name
    else:
        id = get_unique_id(name)
    if sequence_group_exists(id):
        stop_sequence_group(id)

    sequences: List[Sequence] = [run_sequence(**sequence, group_id=id) for sequence in sequences]
    seq_group: SequenceGroup = {
        "id": id,
        "name": name,
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    SEQ_GROUPS_TABLE.insert(seq_group)

    seq_group: SequenceGroupEnriched
    seq_group["sequences"] = sequences
    return seq_group


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
