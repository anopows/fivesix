"""Export aggregate counters without initializing object storage."""
import argparse
import os
from pathlib import Path
import shutil
import time
from . import kpi
from .db import Database
from .limits import EXPORT_QUEUE_LIMIT
from .quotas import STORED_BYTES_SQL
from .config import Settings
from .r2_guard import R2Guard,CostLimit

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('path'); args=parser.parse_args()
    root=Path(os.environ.get('CHOREO_STATE_DIR','/var/lib/choreo'))
    db=Database(root/'room.sqlite3'); now=time.time()
    with db.connect() as con:
        gauges={'sessions_active':con.execute('SELECT count(*) FROM sessions WHERE expires>?',(now,)).fetchone()[0]}
        for status, n in con.execute("SELECT status,count(*) FROM projects WHERE expires>? AND status NOT IN ('deleted','expired') GROUP BY status",(now,)):
            if status in ('creating','uploading','completing','queued','processing','ready','failed'):
                gauges['projects.'+status]=n
        version=con.execute('PRAGMA user_version').fetchone()[0]
        cfg=Settings()
        if version>=1:
            gauges['stored_bytes']=con.execute(STORED_BYTES_SQL).fetchone()[0]
            gauges['users_total']=con.execute('SELECT count(*) FROM users').fetchone()[0]
            gauges['users_active_status']=con.execute("SELECT count(*) FROM users WHERE status='active'").fetchone()[0]
            gauges['users_google']=con.execute("SELECT count(*) FROM users WHERE google_sub IS NOT NULL AND google_sub!=''").fetchone()[0]
            gauges['users_active_7d']=con.execute('SELECT count(*) FROM users WHERE last_login>=?',(now-7*86400,)).fetchone()[0]
            gauges['users_active_30d']=con.execute('SELECT count(*) FROM users WHERE last_login>=?',(now-30*86400,)).fetchone()[0]
            gauges['users_new_7d']=con.execute('SELECT count(*) FROM users WHERE created>=?',(now-7*86400,)).fetchone()[0]
            gauges['users_new_30d']=con.execute('SELECT count(*) FROM users WHERE created>=?',(now-30*86400,)).fetchone()[0]
            gauges['users_with_videos']=con.execute("SELECT count(DISTINCT owner) FROM projects WHERE status='ready' AND expires>? AND owner IN (SELECT id FROM users)",(now,)).fetchone()[0]
            gauges['users_signed_in_now']=con.execute('SELECT count(DISTINCT user_id) FROM sessions WHERE expires>?',(now,)).fetchone()[0]
            gauges['users_cap']=cfg.signup_cap
            gauges['open_reports']=con.execute("SELECT count(*) FROM reports WHERE status='open'").fetchone()[0]
        else:
            gauges['stored_bytes']=con.execute("SELECT coalesce(sum(bytes),0) FROM projects WHERE status='ready' AND expires>?",(now,)).fetchone()[0]
        gauges['storage_cap_bytes']=cfg.storage_cap_bytes
        try: gauges['guard_stopped']=int(bool(R2Guard(root/'r2-guard.sqlite3').status()['stopped']))
        except CostLimit:gauges['guard_stopped']=1
        gauges['queue_limit']=EXPORT_QUEUE_LIMIT
        gauges['projects_ready']=con.execute("SELECT count(*) FROM projects WHERE status='ready' AND expires>?",(now,)).fetchone()[0]
        gauges['queue']=con.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','processing')").fetchone()[0]
        oldest=con.execute("SELECT min(created) FROM jobs WHERE status='queued'").fetchone()[0]
        gauges['oldest_queued_age_s']=max(0,int(now-oldest)) if oldest is not None else None
        gauges['disk_free_bytes']=shutil.disk_usage(root).free
        payload=kpi.export(con,'fivesix',gauges)
    kpi.write_json(args.path,payload)

if __name__=='__main__': main()
