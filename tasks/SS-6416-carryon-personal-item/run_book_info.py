import os
"""One read-only PREPROD request per approved fixture; credentials stay in memory."""
import base64
import json
from pathlib import Path
import ssl
import sys
import urllib.error
import urllib.request
import urllib.parse
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from bb.security import redact
from bb.transport import NoRedirect


def capture(name):
    values = {'booklogin': os.environ.get('BOOKING_USERNAME'), 'bookpass': os.environ.get('BOOKING_PASSWORD')}
    assert values.get('booklogin') and values.get('bookpass'), 'Missing local PREPROD credentials'
    fixture_dir = Path(__file__).parent
    if name == 'SQ':
        payload = json.loads((ROOT / 'tasks/SS-6425-baggage-description/book-info-request.json').read_text())
        folder = ROOT / 'tasks/SS-6425-baggage-description/runs' / os.environ.get('QA_RUN_LABEL', '2026-10-21-checked-text')
    else:
        assert name in ('LX', 'AA', 'QF')
        payload = json.loads((fixture_dir / 'fixtures.json').read_text())[name]
        folder = fixture_dir / 'runs' / os.environ.get('QA_RUN_LABEL', '2026-10-21-preprod') / name
    folder.mkdir(parents=True, exist_ok=True)
    assert not (folder / 'response.json').exists(), 'Refuse unapproved repeat request'
    # Book/Info port is evidenced by the prior ticket collection; searchhost is Search-only.
    url = os.environ.get('AIRAPI_BOOK_INFO_URL', 'https://airapi51.kivops.info:8089/ndc/v1/book/info')
    target = urllib.parse.urlsplit(url)
    assert target.scheme == 'https' and target.hostname == 'airapi51.kivops.info'
    assert target.path == '/ndc/v1/book/info' and target.port in (None, 443, 8089)
    encoded_auth = base64.b64encode((values['booklogin'] + ':' + values['bookpass']).encode()).decode()
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method='POST',
                                 headers={'Authorization': 'Basic ' + encoded_auth, 'Content-Type': 'application/json'})
    context = ssl.create_default_context()
    # Standing direct user authorization 2026-10-21, HTTPS retained.
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=context))
    started = datetime.now(timezone.utc).isoformat()
    result = {'http_status': None, 'traceID': None, 'body': None, 'transport_error': None}
    try:
        try:
            response = opener.open(req, timeout=60)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            result['http_status'] = response.code
            result['traceID'] = response.headers.get('Traceid')
            body = json.loads(response.read())
            output = body.get('data', {}).get('response', {})
            segments = output.get('pnrInfo', {}).get('segments')
            # Persist only ticket fields; passenger names, tickets and provider payloads are excluded.
            result['body'] = {k: body[k] for k in ('status', 'name', 'code') if k in body}
            if segments is not None:
                fields = ('tripId', 'segmentId', 'segmentNumber', 'departureAirportCode',
                          'arrivalAirportCode', 'baggageAllowance', 'baggage', 'carryOnAllowance', 'carryOn')
                result['body']['data'] = {'response': {'pnrInfo': {'segments': [
                    {k: s[k] for k in fields if k in s} for s in segments]}}}
            elif body.get('message'):
                result['body']['message'] = redact(body['message'])
    except (OSError, ValueError) as exc:
        result['transport_error'] = str(exc)
    for filename, obj in [('request.json', payload), ('response.json', redact(result)),
                          ('meta.json', {'started_utc': started, 'ended_utc': datetime.now(timezone.utc).isoformat(),
                           'url': url, 'method': 'POST', 'requests': 1, 'retries': 0, 'tls_verification': False,
                           'tls_authority': 'Standing direct user instruction 2026-10-21'})]:
        (folder / filename).write_text(json.dumps(obj, indent=2), encoding='utf-8')
    print(json.dumps({'fixture': name, **result}))


if __name__ == '__main__':
    capture(sys.argv[1])
