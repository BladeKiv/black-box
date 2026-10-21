"""HTTPS-only single request. No retries, redirects or persistence."""
import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from .classify import classify_outcome
from .security import redact


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request(url, *, method='GET', headers=None, data=None, timeout=30,
            verify_tls=True, tls_bypass_authorized=False, credentials_required=False,
            context=None, allowed_endpoint=None):
    """allowed_endpoint is an explicit exact (method, path) for read-only POSTs.

    The hosting agent supplies current authorization; lessons cannot supply it.
    """
    headers = headers or {}
    parsed = urllib.parse.urlsplit(url)
    result = {'http_status': None, 'body': None, 'transport_error': None}
    def blocked(reason):
        return {**result, 'reason_code': reason, 'status': 'WARN', 'retryable': False}
    if credentials_required and not any(k.lower() == 'authorization' and v for k, v in headers.items()):
        return blocked('AUTH_MISSING')
    if parsed.scheme != 'https' or parsed.username or parsed.password:
        return blocked('TRANSPORT_ERROR')
    if not verify_tls and not tls_bypass_authorized:
        return blocked('SCOPE_BLOCKED')
    path = parsed.path.lower().rstrip('/')
    if any(s in path for s in ('/book/', '/ticket/')) and path not in ('/ndc/v1/book/info', '/ndc/v1/ticket/void/check'):
        return blocked('SCOPE_BLOCKED')
    if method.upper() != 'GET' and allowed_endpoint != (method.upper(), parsed.path):
        return blocked('SCOPE_BLOCKED')
    ssl_context = ssl.create_default_context()
    if not verify_tls:
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
    opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=ssl_context))
    raw = ''
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
        with opener.open(req, timeout=timeout) as response:
            result['http_status'] = response.status
            raw = response.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as exc:
        result['http_status'] = exc.code
        raw = exc.read().decode('utf-8', errors='replace')
    except (OSError, ValueError) as exc:
        result['transport_error'] = str(exc)
    try:
        result['body'] = json.loads(raw)
    except ValueError:
        result['body'] = {'raw': raw}
    result.update(classify_outcome(result['http_status'], raw, result['transport_error'], context))
    return redact(result)
