import os
import sys
import errno
import shutil
import pymysql
import pandas as pd
import warnings
from pathlib import Path

def getinfo(sample_id):
    try :
        connection = pymysql.connect(host="192.168.9.100", user="gxd_pipeline", password="gw!2341234", database="gxd")
    except Exception as e:
        sys.exit({e})

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        db_tbl = pd.read_sql(subname_query(sample_id), connection)

    return db_tbl

def subname_query(sample_id):
    query = f"""
    SELECT concat(tesh.equip_side, tesh.fc_id) AS sub_name, tol.timepoint, gp.PATIENT_NO, gp.PRJ_TYPE, cctm.CLINICAL_TRIAL_NAME
    FROM gxd.tb_expr_seq_header tesh
    INNER JOIN gxd.gc_qc_sample gqs
    ON tesh.run_id = gqs.run_id
    INNER JOIN gxd.gc_project gp
    ON gqs.SAMPLE_ID = gp.SAMPLE_ID
    INNER JOIN gxd.tb_order_line tol
    ON tol.sample_ID = gp.SAMPLE_ID 
    INNER JOIN gxd.gc_history_log ghl
    ON gqs.SAMPLE_ID = ghl.SAMPLE_ID
    AND ghl.idx = (SELECT MAX(idx) FROM gc_history_log WHERE SAMPLE_ID = gqs.SAMPLE_ID)
    LEFT OUTER JOIN gxd.tb_order_header toh
    ON tol.order_header_id = toh.order_header_id
    LEFT OUTER JOIN cm_pi_company_clinical_trial_map cpcctm
    ON toh.pi_comp =  cpcctm.PI_COMP_ID
    LEFT OUTER JOIN gxd.cm_clinical_trial_mst cctm
    ON cpcctm.CLINICAL_TRIAL_ID = cctm.CLINICAL_TRIAL_ID
    WHERE ghl.SAMPLE_ID = '{sample_id}' AND ghl.ANAL_STATUS = '102'
    """
    return query

def search_info(sample_id, directory) :

    tbl = getinfo(sample_id)
    if tbl.shape[0] == 0 :
        return None, None, None, None, None
    subname = tbl.sub_name[0]
    patient = tbl.PATIENT_NO[0]
    anal_type = "eWES" if tbl.PRJ_TYPE[0] == 'EWES' else tbl.PRJ_TYPE[0]
    title = tbl.CLINICAL_TRIAL_NAME[0]

    if tbl.timepoint[0] == 'REGIST':
        timepoint = 'Registration'
    elif tbl.timepoint[0] == 'SURGERY':
        timepoint = 'Surgery'
    elif tbl.timepoint[0] == 'RECUR':
        timepoint = 'Recurrence'
    elif tbl.timepoint[0] == 'PROGRE':
        timepoint = 'Progression'
    elif tbl.timepoint[0] == 'AFTER':
        timepoint = 'Completionoftx'
    elif tbl.timepoint[0] == 'ETC':
        timepoint = 'Other'
    else :
        timepoint = None

    fcDirs = [fcDir for fcDir in Path(os.path.join(directory, anal_type)).iterdir() if fcDir.name.endswith(subname)]
    fcDirs.sort()
    if not os.path.isdir(os.path.join(directory, anal_type, fcDirs[-1], sample_id, 'Summary')) :
        anal_dir = None
    else :
        anal_dir = fcDirs[-1]
    return anal_dir, anal_type, timepoint, patient, title

def create_link(linkDir, FILES):

    os.makedirs(linkDir, exist_ok=True)

    for raw_path in FILES :
        link_path = os.path.join(linkDir, os.path.basename(raw_path))

        if not os.path.isfile(raw_path) :
            return True

        if os.path.isfile(link_path) :
            os.remove(link_path)

        try:
            os.symlink(raw_path, link_path)
        except OSError as e:
            if e.errno == errno.EEXIST:
                os.remove(link_path)
                os.symlink(target, link_name)
            elif e.errno == errno.ENOENT :
                os.makedirs(linkDir, exist_ok=True)
                os.symlink(raw_path, link_path)
            else:
                return True

    return False

def remove_upstream(dir_path, hold_dir='/data1/work/send_to_ITMS'):
    dir_path = os.path.abspath(dir_path)
    shutil.rmtree(dir_path)
    
    while True :
        dir_path = Path(dir_path).parent
        files_dir = [ f for f in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, f))]
        if len(files_dir) > 0 :
            break
        elif dir_path == hold_dir :
            break
        else :
            shutil.rmtree(dir_path)

def prompt_choice(prompt, choices):
    while True:
        ans = input(prompt).strip().lower()
        if ans in choices:
            return ans

def rmdup_list(lst):
    seen = set()
    return [x for x in lst if not (x in seen or seen.add(x))]

def init(msg="") :
    print(msg)
    sys.exit(1)

