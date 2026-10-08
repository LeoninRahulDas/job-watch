# sources.py - fetch jobs from each source and normalise them to one format
import html
import re

import feedparser
import requests

TIMEOUT = 25
HEADERS = {'User-Agent': 'job-watch/1.0 (personal job alerts)'}


def clean(text):
    # turn HTML (possibly escaped) into plain text
    text = html.unescape(text or '')
    text = re.sub(r'<[^>]+>', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def make_job(source, job_id, title, company, location, url, description, remote=False):
    return {
        'id': f'{source}:{job_id}',
        'title': title or '',
        'company': company or '',
        'location': location or '',
        'url': url or '',
        'description': clean(description),
        'remote': bool(remote),
        'source': source,
    }


def get_json(url, params=None):
    r = requests.get(url, headers=HEADERS, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def greenhouse(name):
    data = get_json(f'https://boards-api.greenhouse.io/v1/boards/{name}/jobs', {'content': 'true'})
    return [
        make_job('greenhouse', j['id'], j['title'], name,
                 (j.get('location') or {}).get('name'), j['absolute_url'], j.get('content'))
        for j in data.get('jobs', [])
    ]


def lever(name):
    data = get_json(f'https://api.lever.co/v0/postings/{name}', {'mode': 'json'})
    jobs = []
    for j in data:
        place = (j.get('categories') or {}).get('location')
        jobs.append(make_job('lever', j['id'], j['text'], name, place, j['hostedUrl'],
                             j.get('descriptionPlain'), j.get('workplaceType') == 'remote'))
    return jobs


def ashby(name):
    data = get_json(f'https://api.ashbyhq.com/posting-api/job-board/{name}')
    return [
        make_job('ashby', j['id'], j['title'], name, j.get('location'), j.get('jobUrl'),
                 j.get('descriptionPlain') or j.get('descriptionHtml'), j.get('isRemote'))
        for j in data.get('jobs', [])
    ]


def adzuna(app_id, app_key, what, where):
    params = {'app_id': app_id, 'app_key': app_key, 'results_per_page': 50,
              'what': what, 'where': where, 'max_days_old': 2, 'sort_by': 'date'}
    data = get_json('https://api.adzuna.com/v1/api/jobs/in/search/1', params)
    return [
        make_job('adzuna', j['id'], j['title'], (j.get('company') or {}).get('display_name'),
                 (j.get('location') or {}).get('display_name'), j['redirect_url'], j.get('description'))
        for j in data.get('results', [])
    ]


def remotive():
    data = get_json('https://remotive.com/api/remote-jobs', {'category': 'devops'})
    return [
        make_job('remotive', j['id'], j['title'], j.get('company_name'),
                 j.get('candidate_required_location'), j['url'], j.get('description'), True)
        for j in data.get('jobs', [])
    ]


def weworkremotely():
    url = 'https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss'
    feed = feedparser.parse(url, request_headers=HEADERS)
    jobs = []
    for e in feed.entries:
        company, _, title = e.title.partition(': ')
        jobs.append(make_job('wwr', e.link, title or e.title, company, e.get('region', ''),
                             e.link, e.get('summary'), True))
    return jobs
