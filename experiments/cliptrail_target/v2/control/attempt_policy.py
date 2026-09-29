"""v2 authorization/attempt checks. No inference or machine changes on import."""
import datetime
import json
import os
from pathlib import Path

from target_common import sha

AUTHORIZATION_ID = 'cliptrail-htp-v2-asus-x2e88100-one-attempt'
TIMEOUT_SECONDS = 600


def validate_authorization(authorization):
    if (authorization.get('authorization_id') != AUTHORIZATION_ID or
            authorization.get('explicit_extension_after_v1_cutoff') is not True or
            authorization.get('max_native_attempts') != 1 or
            authorization.get('attempt_wall_timeout_seconds') != TIMEOUT_SECONDS or
            authorization.get('automatic_retries') is not False):
        raise ValueError('Invalid v2 single-attempt authorization')


def claim_native_once(root, output, manifest, ticket_path, *, guard_base=None):
    """Require supervisor's ticket, then consume a second atomic native-start guard.

    guard_base is injectable only for host unit tests; the runner uses LOCALAPPDATA.
    The persistent marker also blocks accidental reruns from a second extraction.
    """
    validate_authorization(manifest['authorization'])
    ticket_path = Path(ticket_path).resolve()
    if ticket_path != output / 'attempt-ticket.json':
        raise ValueError('Ticket must be in this attempt output directory')
    ticket = json.loads(ticket_path.read_text(encoding='utf-8-sig'))
    base = Path(guard_base) if guard_base is not None else Path(os.environ['LOCALAPPDATA'])
    guard = base / 'ClipTrail' / AUTHORIZATION_ID
    issued = json.loads((guard / 'attempt.json').read_text(encoding='utf-8-sig'))
    if issued != ticket or ticket.get('authorization_id') != AUTHORIZATION_ID:
        raise ValueError('Ticket differs from persistent supervisor claim')
    if not ticket.get('token') or ticket.get('timeout_seconds') != TIMEOUT_SECONDS:
        raise ValueError('Invalid supervisor ticket or duration')
    if (Path(ticket['bundle_directory']).resolve() != root or
            Path(ticket['output_directory']).resolve() != output):
        raise ValueError('Supervisor ticket belongs to another extraction/run')
    if ticket.get('manifest_sha256') != sha(root / 'bundle-manifest.json'):
        raise ValueError('Supervisor ticket does not match this manifest')
    started = datetime.datetime.fromisoformat(ticket['started_utc'].replace('Z', '+00:00'))
    if started.tzinfo is None:
        raise ValueError('Ticket timestamp requires timezone')
    age = (datetime.datetime.now(datetime.timezone.utc) - started).total_seconds()
    if age < -5 or age >= TIMEOUT_SECONDS:
        raise ValueError('v2 attempt ticket is expired or in the future')
    record = {'authorization_id': AUTHORIZATION_ID, 'token': ticket['token'],
              'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'pid': os.getpid(), 'manifest_sha256': ticket['manifest_sha256']}
    with (guard / 'native-started.json').open('x', encoding='utf-8') as f:
        json.dump(record, f, indent=2)
        f.write('\n')
    # Never delete either guard, even if subsequent initialization fails.
    return record


def target_inventory(output, expected):
    paths = list(output.glob('inventory-*/inventory.json'))
    if len(paths) != 1:
        raise ValueError('Expected exactly one inventory from this attempt')
    data = json.loads(paths[0].read_text(encoding='utf-8-sig'))
    if (str(data.get('manufacturer', '')).strip().casefold() != expected['manufacturer'].casefold() or
            str(data.get('model', '')).strip().casefold() != expected['model'].casefold() or
            not any(expected['cpu_contains'].casefold() in str(p.get('Name', '')).casefold()
                    for p in data.get('processors', []))):
        raise ValueError('Inventory does not identify the authorized ASUS X2E88100 target')
    return {'file': str(paths[0].relative_to(output)), 'sha256': sha(paths[0]),
            'manufacturer': data['manufacturer'], 'model': data['model'],
            'processors': data['processors'], 'windows': data['windows'],
            'ram_bytes': data['ram_bytes'], 'power_scheme': data['power_scheme'],
            'inventory_errors': data.get('errors', [])}
