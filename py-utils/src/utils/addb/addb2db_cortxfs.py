#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

import argparse
import logging
import numpy
import time
from typing import List
import multiprocessing
from itertools import zip_longest
from collections import defaultdict
from tqdm import tqdm
from plumbum.cmd import wc
from math import ceil
import sys


from peewee import SqliteDatabase

DB      = SqliteDatabase(None)
BLOCK   = 16<<10
PROC_NR = 48
DBBATCH = 95
PID     = 0

def die(what: str):
    print(what, file=sys.stderr)
    sys.exit(1)

# ======================================================================

from peewee import Model

class BaseModel(Model):
    class Meta:
        """To initialize the DB."""
        database = DB

from peewee import IntegerField
from peewee import TextField

class entity_states(BaseModel):
    pid         = IntegerField()
    time        = IntegerField()
    tsdb_mod    = TextField()
    fn_tag      = TextField()
    entity_type = TextField()
    opid        = IntegerField()
    state_type  = TextField()

class entity_attributes(BaseModel):
    pid         = IntegerField()
    time        = IntegerField()
    tsdb_mod    = TextField()
    fn_tag      = TextField()
    entity_type = TextField()
    opid        = IntegerField()
    attr_name   = TextField()
    attr_val    = IntegerField()

class entity_maps(BaseModel):
    pid         = IntegerField()
    time        = IntegerField()
    tsdb_mod    = TextField()
    fn_tag      = TextField()
    entity_type = TextField()
    map_name    = IntegerField()
    src_opid    = IntegerField()
    dst_opid    = IntegerField()

db_create_delete_tables = [entity_states, entity_attributes, entity_maps]

def db_create_tables():
    with DB:
        DB.create_tables(db_create_delete_tables)

def db_drop_tables():
    with DB:
        DB.drop_tables(db_create_delete_tables)

def db_init(path):
    DB.init(path, pragmas={
        'journal_mode': 'memory',
        'cache_size': -1024*1024*256,
        'synchronous': 'off',
    })

def db_connect():
    DB.connect()

def db_close():
    DB.close()

# ======================================================================

class profiler:
    def __init__(self, what):
        """Profiler init."""
        self.what = what

    def __exit__(self, exp_type, exp_val, traceback):
        """Profiler exit."""
        delta = time.time() - self.start
        logging.info(f"{self.what}: {delta}s")
    def __enter__(self):
        """Profiler enter."""
        self.start = time.time()

# ======================================================================

class ADDB2PPNFS:
    @staticmethod
    def to_unix(motr_time):
        mt = list(motr_time)
        mt[10] = 'T'
        np_time = numpy.datetime64("".join(mt))
        return np_time.item()

    # [ '*',
    #   'Time < 2020-01-26-17:14:57.140967535 >',
    #   'tsdb_modules',
    #   'function tag',
    #   'PET_STATE',
    #   'opid',
    #   'perfc_entity_states',
    #   'Rest']
    def p_entity_states(row, labels, table):
        ret = {}
        # print ("states " + labels + table)
        ret['pid']  = 1
        ret['time'] = ADDB2PPNFS.to_unix(row[1])
        ret['tsdb_mod'] = row[2]
        ret['fn_tag'] = row[3]
        ret['entity_type'] = row[4]
        ret['opid'] = int(row[5], 16)
        ret['state_type'] = row[6]
        return((table, ret))

    # [ '*',
    #   'Time < 2020-01-26-17:14:57.140967535 >',
    #   'tsdb_modules',
    #   'function tag',
    #   'PET_ATTR',
    #   'opid',
    #   'perfc_entity_attrs',
    #   'Rest']
    def p_entity_attributes(row, labels, table):
        ret = {}
        # print ("attributes " + labels + " " + table + " " + row[8])
        ret['pid']  = 2
        ret['time'] = ADDB2PPNFS.to_unix(row[1])
        ret['tsdb_mod'] = row[2]
        ret['fn_tag'] = row[3]
        ret['entity_type'] = row[4]
        ret['opid'] = int(row[5], 16)
        ret['attr_name'] = row[6]
        ret['attr_val'] = int(row[8], 16)
        return((table, ret))

    # [ '*',
    #   'Time < 2020-01-26-17:14:57.140967535 >',
    #   'tsdb_modules',
    #   'function tag',
    #   'PET_STATE',
    #   'src opid',
    #   'dst opid',
    #   'Rest']
    def p_entity_maps(row, labels, table):
        ret = {}
        # print ("maps" + labels + " " + table + " " + row[5])
        ret['pid']  = 3
        ret['time'] = ADDB2PPNFS.to_unix(row[1])
        ret['tsdb_mod'] = row[2]
        ret['fn_tag'] = row[3]
        ret['entity_type'] = row[4]
        ret['map_name'] = int(row[5], 16)
        # ret['src_opid'] = int(row[6], 16)
        ret['src_opid'] = 0
        ret['dst_opid'] = int(row[8], 16)
        return((table, ret))

    def __init__(self):
        """App init."""
        self.parsers = {
            "state"         : (ADDB2PPNFS.p_entity_states,      "entity_states"),
            "attribute"     : (ADDB2PPNFS.p_entity_attributes,  "entity_attributes"),
            "map"           : (ADDB2PPNFS.p_entity_maps,        "entity_maps"),
        }

    def consume_record(self, rec):
        def _add_pid(_,ret):
            ret.update({"pid": PID})
            return ((_,ret))

        # row[0] and labels[1..] (mnl)
        mnl = rec.split("|")
        row= mnl[0].split()
        row=  [s.strip(',') for s in row]
        row=  [s.strip('?') for s in row]
        if row== []:
            return
        measurement_name = row[4]
        labels=measurement_name

        for pname, (parser, table) in self.parsers.items():
            if pname == labels:
                return _add_pid(*parser(row, labels, table))
        return None

APP = ADDB2PPNFS()
def fd_consume_record(rec):
    return APP.consume_record(rec) if rec else None

def fd_consume_data(file, pool):
    def grouper(n, iterable, padvalue=None):
        return zip_longest(*[iter(iterable)]*n,
                           fillvalue=padvalue)
    results=[]
    _wc = int(wc["-l", file]().split()[0])
    _wc = ceil(_wc/BLOCK)*BLOCK

    with tqdm(total=_wc, desc=f"Read file: {file}") as t:
        with open(file) as fd:
            for chunk in grouper(BLOCK, fd):
                results.extend(pool.map(fd_consume_record, chunk))
                t.update(BLOCK)

    return results

from peewee import chunked

def db_consume_data(files: List[str]):
    rows   = []
    tables = defaultdict(list)

    db_connect()
    db_drop_tables()
    db_create_tables()

    with profiler(f"Read files: {files}"):
        for f in files:
            def pool_init(pid):
                global PID; PID=pid
            # Ugly reinitialisation of the pool due to PID value propagation
            pool = multiprocessing.Pool(PROC_NR, pool_init, (len(f),))
            rows.extend(filter(None, fd_consume_data(f, pool)))
        for k,v in rows:
            tables[k].append(v)

    with tqdm(total=len(rows), desc="Insert records") as t:
        with profiler("Write to db"):
             for k in tables.keys():
                 with profiler(f"    {k}/{len(tables[k])}"):
                     with DB.atomic():
                         for batch in chunked(tables[k], DBBATCH):
                             globals()[k].insert_many(batch).execute()
                             t.update(len(batch))

    db_close()

def db_setup_loggers():
    format_c='%(asctime)s %(name)s %(levelname)s %(message)s'
    level=logging.INFO
    level_sh=logging.WARN
    logging.basicConfig(filename='logfile.txt',
                        filemode='w',
                        level=level,
                        format=format_c)

    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter(format_c))
    sh.setLevel(level_sh)
    log = logging.getLogger()
    log.addHandler(sh)

def db_parse_args():
    parser = argparse.ArgumentParser(description="""
addb2db_nfs.py: creates sql database containing performance samples from cortxfs
    """)
    parser.add_argument('--dumps', nargs='+', type=str, required=False,
                        default=["dump.txt", "dump_s.txt"],
                        help="""
A bunch of addb2dump.txts can be passed here for processing:
python3 addb2db_nfs.py --dumps dump1.txt dump2.txt ...
""")
    parser.add_argument('--db', type=str, required=False,
                        default="nfscortxfs.db",
                        help="Output database file")
    parser.add_argument('--procs', type=int, required=False,
                        default=PROC_NR,
                        help="Number of processes to parse dump files")
    parser.add_argument('--block', type=int, required=False,
                        default=BLOCK,
                        help="Block of data from dump files processed at once")
    parser.add_argument('--batch', type=int, required=False,
                        default=DBBATCH,
                        help="Number of samples commited at once")

    return parser.parse_args()

if __name__ == '__main__':
    args=db_parse_args()
    BLOCK=args.block
    PROC_NR=args.procs
    DBBATCH=args.batch
    db_init(args.db)
    db_setup_loggers()
    db_consume_data(args.dumps)
