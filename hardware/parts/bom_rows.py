"""Read canonical BOM rows shared by the gallery and standalone validator."""
import ast
import csv
import io
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def dimensions(value):
    if not value:return ''
    if isinstance(value,list):
        label=' × '.join(str(v) for v in value if v is not None)+' mm'
        if len(value)==3 and value[2] is None:label+='; height unspecified'
        return label
    return str(value)


def source_url(value):
    if not value:
        return ""
    if isinstance(value, dict):
        return value.get('url', '')
    if value.startswith('{'):
        return ast.literal_eval(value).get('url', '')
    return value if value.startswith('https://') else ''


def read_rows(config, root=ROOT):
    rows = []
    for source in config['sources']:
        path = root / source['path']
        raw = (json.loads(path.read_text())['items'] if path.suffix == '.json'
               else list(csv.DictReader(io.StringIO(path.read_text()))))
        for r in raw:
            fmt = source['format']
            if fmt == 'original':
                ref, qty, model = r['ref'], r['qty'], r['model_or_requirement']
                note = ' · '.join(filter(None, [r.get('item'), r.get('power_or_signal'), r.get('notes')]))
                package, condition = r.get('dimensions_mm', ''), r.get('variant', '')
            elif fmt == 'reference':
                ref, qty, model = r['ref'], r['qty'], r['model']
                note, condition = r.get('note', ''), 'Reference only; ' + r.get('phase', '')
                package = dimensions(r.get('body_mm', ''))
            elif fmt == 'assembly':
                ref, qty, model = r['Reference'], r['Quantity'], r['Manufacturer part / value']
                note, package, condition = r.get('Note', ''), r.get('Footprint', ''), 'Fitted to board'
            elif fmt == 'harness':
                ref, qty, model = r['Item'], r['Quantity'], r['Model/specification']
                note = ' · '.join(filter(None, [r.get('Purpose'), r.get('Notes')]))
                package, condition = '', 'Harness / external / service; read row notes'
            else:
                raise ValueError(f'Unknown BOM format: {fmt}')
            rows.append(dict(key=source['id'] + ':' + ref, source_id=source['id'], ref=ref,
                             qty=str(qty), model=model, note=note, package=package,
                             condition=condition, source=source_url(r.get('source', r.get('Source', '')))))
    return rows
