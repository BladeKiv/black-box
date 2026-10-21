"""Operational triage, never a replacement for ticket expectations."""
import json
import re


def normalize_message(message):
    message = re.sub(r'\b\d{4}-\d\d-\d\d(?:T[^\s]+)?', '<date>', str(message))
    message = re.sub(r'(?i)\b(?:id|traceid|token|tid|searchid)\s*[:=]\s*[^\s,;]+', '<id>', message)
    message = re.sub(r'\b[\da-fA-F]{8}(?:-[\da-fA-F]{4}){3}-[\da-fA-F]{12}\b', '<id>', message)
    message = re.sub(r'\b[A-Za-z0-9_+/=-]{24,}\b', '<token>', message)
    return re.sub(r'\s+', ' ', re.sub(r'\d+(?:\.\d+)?', '<n>', message)).strip().lower()


def classify_outcome(http_status=None, body_text='', transport_error=None, context=None):
    context = context or {}
    def result(reason, status='WARN', retry=False):
        return {'reason_code': reason, 'status': status, 'retryable': retry}
    if context.get('credentials_missing'):
        return result('AUTH_MISSING')
    if transport_error:
        error = str(transport_error).lower()
        if any(s in error for s in ('ssl', 'tls', 'certificate', 'sec_e_untrusted_root')):
            return result('TLS_ERROR')
        return result('TIMEOUT' if any(s in error for s in ('timeout', 'timed out')) else 'TRANSPORT_ERROR', retry=True)
    try:
        body = json.loads(body_text)
        valid_json = True
    except (ValueError, TypeError):
        body = None
        valid_json = False
    message = str(body.get('message', body.get('Message', ''))) if isinstance(body, dict) else ''
    if http_status in (401, 403):
        return result('AUTH_REJECTED')
    if http_status == 422 and 'price change' in str(body_text).lower():
        return result('PRICE_CHANGE', retry=True)
    if http_status == 408:
        return result('RETRY_REQUESTED' if 'retry' in str(body_text).lower() else 'TIMEOUT', retry=True)
    if context.get('async_complete') is False:
        return result('ASYNC_INCOMPLETE', retry=True)
    if not valid_json:
        return result('INVALID_JSON')
    field = context.get('inventory_field', 'results')  # Documented Search contract path.
    if context.get('comparable_count') == 0 or (field and isinstance(body, dict) and body.get(field) == []):
        return result('NO_DATA')
    if context.get('expectation_observed') is False:
        return result('CONTRACT_MISMATCH', 'FAIL')
    if message and message not in context.get('expected_messages', []):
        return result('UNEXPECTED_MESSAGE')
    if http_status is None or not 200 <= http_status < 300:
        return result('HTTP_ERROR')
    return result('OK', 'PASS') if context.get('expectation_observed') is True else result('UNEVALUATED')

