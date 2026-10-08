# filters.py - decide whether a job matches your resume and rules
import re

YEARS = re.compile(r'(\d{1,2})\s*(?:\+|(?:-|–|to)\s*\d{1,2})?\s*(?:years|yrs|year)')


def has_word(word, text):
    pattern = r'(?<![a-z0-9])' + re.escape(word) + r'(?![a-z0-9])'
    return re.search(pattern, text) is not None


def passes(job, cfg):
    # returns (True, '') when the job should be considered, else (False, reason)
    title = job['title'].lower()
    place = job['location'].lower()
    text = (job['title'] + ' ' + job['description']).lower()

    if not any(k in title for k in cfg['title_include']):
        return False, 'title'
    if any(has_word(k, title) for k in cfg['title_exclude']):
        return False, 'seniority'

    is_remote = job['remote'] or 'remote' in place or 'remote' in title
    city_ok = any(c in place or c in title for c in cfg['onsite_cities'])
    region_ok = any(r in place or r in title for r in cfg['remote_regions'])
    bare_remote = is_remote and place.strip() in ('', 'remote')
    if not (city_ok or (is_remote and region_ok)
            or (bare_remote and cfg['allow_unspecified_remote'])):
        return False, 'location'

    hits = [s for s in cfg['skills'] if has_word(s, text)]
    if len(hits) < cfg['min_skill_hits']:
        return False, 'skills'

    years = [int(m.group(1)) for m in YEARS.finditer(text)]
    if years and min(years) > cfg['max_years_required']:
        return False, 'years'

    return True, ''
