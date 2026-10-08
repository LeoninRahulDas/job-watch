# main.py - collect, filter, score, alert, remember
import datetime as dt
import json
import os
import sys

import yaml

import filters
import notify
import scorer
import sources

SEEN_FILE = 'seen.json'


def load_yaml(path):
    with open(path, encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def load_seen():
    try:
        with open(SEEN_FILE, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_seen(seen):
    cutoff = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=60)).isoformat()
    seen = {k: v for k, v in seen.items() if v >= cutoff}   # forget jobs older than 60 days
    with open(SEEN_FILE, 'w', encoding='utf-8') as f:
        json.dump(seen, f, indent=0, sort_keys=True)


def collect(companies, run_slow):
    jobs = []

    def safe(label, fn, *args):
        try:
            jobs.extend(fn(*args))
        except Exception as e:      # one broken source must not stop the others
            print(f'[warn] {label} failed: {e}')

    for name in companies.get('greenhouse') or []:
        safe('greenhouse ' + name, sources.greenhouse, name)
    for name in companies.get('lever') or []:
        safe('lever ' + name, sources.lever, name)
    for name in companies.get('ashby') or []:
        safe('ashby ' + name, sources.ashby, name)

    app_id, app_key = os.getenv('ADZUNA_APP_ID'), os.getenv('ADZUNA_APP_KEY')
    if app_id and app_key:
        for what, where in [('devops engineer', 'bangalore'),
                            ('aws devops engineer', 'bangalore'),
                            ('remote devops engineer', 'india')]:
            safe('adzuna ' + what, sources.adzuna, app_id, app_key, what, where)

    if run_slow:    # these sites ask for infrequent requests, so fetch them every few hours only
        safe('remotive', sources.remotive)
        safe('weworkremotely', sources.weworkremotely)
    return jobs


def format_message(job, result):
    lines = [job['title'] + ' - ' + job['company'],
             (job['location'] or 'location not stated') + '  [' + job['source'] + ']']
    if result:
        lines.append('Fit: ' + str(result['score']) + '/100 - ' + result['reason'])
        lines.append('Missing: ' + (', '.join(result['missing']) or 'nothing obvious'))
    lines.append(job['url'])
    return '\n'.join(lines)


def main():
    bootstrap = '--bootstrap' in sys.argv      # record current jobs without alerting
    cfg = load_yaml('keywords.yaml')
    companies = load_yaml('companies.yaml')
    with open('resume.txt', encoding='utf-8') as f:
        resume = f.read()

    now = dt.datetime.now(dt.timezone.utc)
    run_slow = bool(os.getenv('FORCE_SLOW')) or (now.hour % 6 == 0 and now.minute < 30)
    use_ai = cfg.get('use_ai_scoring') and os.getenv('GEMINI_API_KEY')

    seen = load_seen()
    jobs = collect(companies, run_slow)
    new = [j for j in jobs if j['id'] not in seen]
    print(f'fetched {len(jobs)} jobs, {len(new)} new')

    sent = 0
    for job in new:
        if job['id'] in seen:       # the same job can arrive twice in one run
            continue
        if not bootstrap:
            ok, _why = filters.passes(job, cfg)
            if ok:
                result = scorer.score(job, resume) if use_ai else None
                if result is None or result['score'] >= cfg['min_score']:
                    if not notify.send(format_message(job, result)):
                        continue        # failed to send: try again on the next run
                    sent += 1
        seen[job['id']] = now.isoformat()
        if sent >= cfg.get('max_alerts_per_run', 15):
            break

    save_seen(seen)
    print(f'alerts sent: {sent}')


if __name__ == '__main__':
    main()
