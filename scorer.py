# scorer.py - ask Gemini how well a job fits your resume (optional, free tier)
import json
import os
import re
import time

import requests

MODEL = 'gemini-3.5-flash-lite'
URL = 'https://generativelanguage.googleapis.com/v1beta/models/' + MODEL + ':generateContent'
PAUSE_SECONDS = 4      # keeps you under the free per-minute limit


def score(job, resume):
    # returns {'score': int, 'reason': str, 'missing': [str]} or None if scoring failed
    key = os.getenv('GEMINI_API_KEY')
    if not key:
        return None
    prompt = (
        'You screen job postings for a DevOps engineer with about 2 years of experience. '
        'Judge only from the resume and the job below. Be strict and honest: the score is '
        'the chance this person gets an interview. Reply with ONLY a JSON object with the keys '
        'score (0 to 100), reason (one short sentence) and missing (a list of required skills '
        'the resume does not show).\n\n'
        'RESUME:\n' + resume + '\n\n'
        'JOB:\nTitle: ' + job['title'] + '\nCompany: ' + job['company'] +
        '\nLocation: ' + job['location'] + '\nDescription:\n' + job['description'][:6000]
    )
    time.sleep(PAUSE_SECONDS)
    try:
        r = requests.post(
            URL,
            headers={'x-goog-api-key': key, 'Content-Type': 'application/json'},
            json={
                'contents': [{'parts': [{'text': prompt}]}],
                'generationConfig': {'responseMimeType': 'application/json', 'maxOutputTokens': 400},
            },
            timeout=60,
        )
        r.raise_for_status()
        raw = r.json()['candidates'][0]['content']['parts'][0]['text']
        data = json.loads(re.search(r'\{.*\}', raw, re.S).group(0))
        return {'score': int(data['score']), 'reason': str(data.get('reason', '')),
                'missing': list(data.get('missing', []))}
    except Exception as e:
        print(f'[warn] scoring failed: {e}')
        return None
