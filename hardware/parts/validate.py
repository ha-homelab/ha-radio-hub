#!/usr/bin/env python3
"""Validate full, exact BOM coverage and honest image/purchase-link metadata."""
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import json


def require(condition, message):
    if not condition:
        raise ValueError(message)


def web_url(value):
    url=urlparse(value)
    require(url.scheme=='https' and bool(url.netloc) and not url.username and not url.password,
            f'Unsafe/non-HTTPS URL: {value}')


def validate(config, data, root=None):
    from build import ROOT, HERE, read_rows
    root=root or ROOT
    sources=config['sources']
    require(len({s['id'] for s in sources})==len(sources),'Duplicate source id')
    expected=read_rows(config,root)
    require(len({r['key'] for r in expected})==len(expected),'Duplicate canonical row key')
    actual=[r for card in data['cards'] for r in card['rows'] if r['source_id']!='accessory']
    require(Counter(r['key'] for r in actual)==Counter(r['key'] for r in expected),'Missing/duplicate/unexpected BOM coverage')
    require({r['key']:r for r in expected}=={r['key']:r for r in actual},'BOM row values differ from canonical source')
    require(len({c['id'] for c in data['cards']})==len(data['cards']),'Duplicate card id')
    known={s['id'] for s in sources}|{'accessory'}
    for card in data['cards']:
        require(card['rows'],'Empty card')
        require(all(r['source_id'] in known for r in card['rows']),'Unknown source id')
        require(all(r['model']==card['model'] and r['package']==card['package'] for r in card['rows']), 'Wrong component grouping')
        image=card['image']
        require(image['kind'] in {'manufacturer_photo','manufacturer_render','dimensioned_diagram','original_illustration'},'Unlabeled image type')
        require(bool(image['caption']) and bool(image['credit']),'Missing image provenance')
        if image['kind'].startswith('manufacturer_'):
            web_url(image['url']);web_url(image['source'])
            require(image in [dict(i) for i in config['images']], 'Manufacturer image not in reviewed source manifest')
        else:
            require(not urlparse(image['url']).scheme,'Local illustration expected')
            target=(HERE/image['url']).resolve()
            require(target.is_relative_to(root),'Local image escapes repo')
            # Original illustration files are created after validation by build.py.
            if image['kind']=='dimensioned_diagram':require(target.is_file(),'Missing physical contact diagram')
        for row in card['rows']:
            if row['source']:web_url(row['source'])
        ali=card['ali']
        if ali['kind']=='project_source':
            require(not urlparse(ali['url']).scheme,'Expected local project source')
            require((HERE/ali['url']).resolve().is_relative_to(root) and (HERE/ali['url']).is_file(),'Missing project source')
            continue
        web_url(ali['url'])
        require(ali['kind']=='search_unverified','Purchase claim requires a new explicit review; search only in this catalog')
        url=urlparse(ali['url'])
        require(url.netloc=='www.aliexpress.com' and url.path=='/wholesale' and bool(parse_qs(url.query).get('SearchText')), 'Invalid AliExpress search link')
        require('search' in ali['label'].lower() and 'unverified' in ali['label'].lower(),'Unclear AliExpress link label')
    return True


if __name__=='__main__':
    here=Path(__file__).resolve().parent
    validate(json.loads((here/'catalog.json').read_text()),json.loads((here/'inventory.json').read_text()))
    print('BOM coverage, image provenance and search-link labels: PASS')
