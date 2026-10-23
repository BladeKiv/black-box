"""Shared conservative detection; diagnostics never contain matched values."""
import json
import re
import base64
import binascii
from bisect import bisect_right

SENSITIVE_KEY = re.compile(r'^(?:authorization|proxy.authorization|password|passwd|bookpass|booklogin|username|booking_username|booking_password|token|access_token|refresh_token|api[_-]?key|secret|cookie|set-cookie|session_cookie|first_?name|last_?name|given_?name|surname|birthdate|birthday|date_?of_?birth|passport_?(?:number|no)|document_?number)$', re.I)
PATTERNS = {
    'credential': re.compile(r'''(?i)["']?\b(?:password|passwd|bookpass|booklogin|booking_username|booking_password|token|access_token|refresh_token|api[_-]?key|secret|session_cookie)\b["']?\s*[:=]\s*["']([^"'\r\n]+)["']'''),
    'author' + 'ization': re.compile(r'(?i)\b(?:Basic|Bearer)\s+([A-Za-z0-9+/_.=-]+)'),
    'session_cookie': re.compile(r'''(?i)["']?(?:cookie|set-cookie)["']?\s*[:=]\s*["']([^"'\r\n]+)'''),
    'private_key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'known_token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}|sk-[A-Za-z0-9_-]{20,})\b'),
    'embedded_credential': re.compile(r'''(?i)(?<![\w.])(?:bookpass|booklogin|username|password|passwd|token|api[_-]?key|access_token|refresh_token)\s*(?:=(?!=)|:)\s*([^\s&"'<>;,}]+)'''),
    'auth_value': re.compile(r'''(?i)["']?\bauthorization["']?\s*[:=]\s*["']?([^\s"',}\r\n]+)'''),
    'passenger_data': re.compile(r'''(?i)["'](?:first_?name|last_?name|given_?name|surname|birthdate|birthday|date_?of_?birth|passport_?(?:number|no)|document_?number)["']\s*:\s*["']([^"']+)["']'''),
    'postman_value': re.compile(r'''(?i)"key"\s*:\s*"(?:authorization|password|bookpass|booklogin|booking_password|booking_username|token|api[_-]?key|access_token|refresh_token|secret|cookie)"(?:\s*,\s*"(?:type|enabled)"\s*:\s*(?:"[^"]*"|true|false))*\s*,\s*"value"\s*:\s*"([^"]+)"'''),
}

# Literal prefilters avoid expensive regex passes over gigabytes of unrelated QA data.
HINTS = {
    'credential': ('password', 'passwd', 'bookpass', 'booklogin', 'booking_username',
                   'token', 'access_token', 'refresh_token', 'api_key',
                   'api-key', 'apikey', 'secret', 'session_cookie'),
    'author' + 'ization': ('basic', 'bearer'),
    'session_cookie': ('cookie',),
    'private_key': ('private key',),
    'known_token': ('ghp_', 'gho_', 'ghu_', 'ghs_', 'ghr_', 'akia', 'sk-'),
    'embedded_credential': ('bookpass', 'booklogin', 'username', 'password', 'passwd',
                            'token', 'api_key', 'api-key', 'apikey'),
    'auth_value': ('authorization',),
    'passenger_data': ('firstname', 'first_name', 'lastname', 'last_name', 'givenname',
                       'given_name', 'surname', 'birthdate', 'birthday', 'dateofbirth',
                       'date_ofbirth', 'dateof_birth', 'date_of_birth', 'passportnumber',
                       'passport_number', 'passportno', 'passport_no', 'documentnumber', 'document_number'),
    'postman_value': ('"key"',),
}


def placeholder(value):
    value = value.strip()
    return (not value or value in ('[REDACTED]', '<redacted>', '***', 'null', 'None', 'INVALID_TEST_TOKEN')
            or value.startswith(('{{', '${', '<', 'os.environ', 'process.env')))


def credential_match(kind, match):
    if match.lastindex and placeholder(match.group(match.lastindex)):
        return False
    if kind == 'auth_value':
        value = match.group(1)
        if value.lower() in ('basic', 'bearer'):
            suffix = re.match(r'''[ \t]+([^\s"',]+)''', match.string[match.end():])
            if suffix and placeholder(suffix.group(1)):
                return False
        if re.match(r'^[A-Za-z_]\w*(?:\.\w+)*[\[(]', value):
            return False  # Computed source expression, not a header value.
        if value.lower() in ('basic', 'bearer') and re.match(r'''\s*['"]\s*\+\s*[A-Za-z_$]''', match.string[match.end():]):
            return False
    if kind == 'authorization' and match.group().lower().startswith('basic'):
        # A fare named Basic Economy is not an HTTP Basic credential.
        try:
            return b':' in base64.b64decode(match.group(1), validate=True)
        except (ValueError, binascii.Error):
            return False
    return True


def findings(text):
    result = set()
    lowered = text.lower()
    newlines = [m.start() for m in re.finditer('\n', text)]
    for kind, pattern in PATTERNS.items():
        if not any(hint in lowered for hint in HINTS[kind]):
            continue
        for match in pattern.finditer(text):
            if not credential_match(kind, match):
                continue
            result.add((bisect_right(newlines, match.start()) + 1, kind))
    return [{'line': line, 'type': kind} for line, kind in sorted(result)]


def redact(value):
    if isinstance(value, dict):
        variable = SENSITIVE_KEY.fullmatch(str(value.get('key', '')))
        return {k: '[REDACTED]' if SENSITIVE_KEY.fullmatch(str(k)) or (variable and k == 'value') else redact(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(v) for v in value]
    if isinstance(value, str):
        for pattern in PATTERNS.values():
            value = pattern.sub('[REDACTED]', value)
    return value


def ensure_safe(value):
    def walk(item):
        if isinstance(item, dict):
            if SENSITIVE_KEY.fullmatch(str(item.get('key', ''))) and 'value' in item and not placeholder(str(item['value'])):
                raise ValueError('Sensitive variable rejected; no value logged')
            for key, val in item.items():
                if SENSITIVE_KEY.fullmatch(str(key)) and not placeholder(str(val)):
                    raise ValueError('Sensitive field rejected; no value logged')
                walk(val)
        elif isinstance(item, (list, tuple)):
            for child in item:
                walk(child)
    walk(value)
    if findings(json.dumps(value, ensure_ascii=False)):
        raise ValueError('Credential or personal-data pattern rejected; no value logged')

