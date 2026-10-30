"""Validate examples and cross-file invariants of the lab's contracts."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import yaml
from jsonschema import Draft4Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
files = sorted((ROOT / 'api').glob('*-service.yaml'))
assert len(files) == 5
specs = {f.stem: yaml.safe_load(f.read_text()) for f in files}
operation_ids = set()
event_types = set()
counts = {'operations': 0, 'examples': 0, 'events': 0}
problem = specs['incident-service']['components']['schemas']['Problem']

def expand(value, doc):
    if isinstance(value, list):
        return [expand(x, doc) for x in value]
    if not isinstance(value, dict):
        return value
    if '$ref' in value:
        assert value['$ref'].startswith('#/'), value['$ref']
        target = doc
        for token in value['$ref'][2:].split('/'):
            target = target[token.replace('~1', '/').replace('~0', '~')]
        return expand(target, doc)
    return {k: expand(v, doc) for k, v in value.items()}

def validate_example(schema, example, doc):
    Draft4Validator(expand(schema, doc), format_checker=FormatChecker()).validate(example)
    counts['examples'] += 1

for service, doc in specs.items():
    assert doc['components']['schemas']['Problem'] == problem
    expand(doc, doc)  # All references resolve, including unreferenced event components.
    for name, schema in doc['components']['schemas'].items():
        Draft4Validator.check_schema(expand(schema, doc))
        if 'example' in schema:
            validate_example(schema, schema['example'], doc)
        if 'x-routing-key' in schema:
            event = schema['x-routing-key']
            assert event not in event_types
            event_types.add(event)
            assert schema['x-publisher'] == service
            assert set(schema['x-subscribers']) <= specs.keys()
            assert {'eventId', 'eventType', 'occurredAt', 'schemaVersion', 'correlationId', 'payload'} <= set(schema['required'])
            counts['events'] += 1
    for path, methods in doc['paths'].items():
        for method, op in methods.items():
            counts['operations'] += 1
            assert op['operationId'] not in operation_ids
            operation_ids.add(op['operationId'])
            assert ('internal' in op['tags']) == path.startswith('/internal/')
            parameters = op.get('parameters', [])
            if method != 'get':
                assert any(p['name'] == 'Idempotency-Key' and p['required'] for p in parameters)
            assert set(re.findall(r'{([^}]+)}', path)) == {p['name'] for p in parameters if p['in'] == 'path'}
            for p in parameters:
                validate_example(p['schema'], p['example'], doc)
            if 'requestBody' in op:
                media = op['requestBody']['content']['application/json']
                validate_example(media['schema'], media['example'], doc)
            assert {'400', '401', '403', '404', '409', '503'} <= op['responses'].keys()
            for code, response in op['responses'].items():
                if code == '204':
                    assert 'content' not in response
                for kind, media in response.get('content', {}).items():
                    validate_example(media['schema'], media['example'], doc)
                    if int(code) >= 400:
                        assert kind == 'application/problem+json'
                        assert media['example']['status'] == int(code)
                    if media['schema'].get('$ref', '').endswith('List'):
                        assert {'page', 'size'} <= {p['name'] for p in parameters}
for path in [ROOT/'README.md', *(ROOT/'docs').glob('*.md')]:
    for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
        if '://' in target or target.startswith('#'):
            continue
        assert (path.parent / target.split('#')[0]).exists(), (path, target)
for name in ['architecture', 'sequence-success', 'sequence-failure']:
    assert (ROOT/'docs'/f'{name}.png').read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    ET.parse(ROOT/'docs'/f'{name}.svg')
ET.parse(ROOT/'docs/architecture.drawio')
assert counts['events'] >= 2
print(f'OK: {len(files)} services, {counts["operations"]} operations, {counts["events"]} events, {counts["examples"]} examples; references, links, pagination, errors, idempotency and diagram formats checked.')
