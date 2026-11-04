import json
from pathlib import Path
from bb.classify import classify_outcome
from bb.escalations import Escalations, handle_outcome
from bb.lessons import Store

root = Path(__file__).resolve().parent
capture = json.loads((root / 'configuration-discovery.json').read_text())
response = capture['response']
scope = {'ticket':'SS-6438', 'environment':'PREPROD', 'endpoint':'/algo/conf', 'allow_retry':False, 'allow_poll':False, 'allow_retest':False, 'approved_inputs':[]}
outcome = classify_outcome(response['http_status'], json.dumps(response['body']), response['transport_error'], {'inventory_field':None, 'expectation_observed':False})
escalations = Escalations()
print(handle_outcome(Store(), escalations, outcome, 'SS-6438-20261102-preparation', ['SS-6438','PREPROD'], 'configuration discovery connection refused at user corrected https host', scope, retries=1, steps=3))
escalations.ask(run='SS-6438-20261102-preparation', question='PREPROD refused the connection at https://airapi51.kivops.info:8080. Should I wait for that service to be restored, or is there an updated PREPROD HTTPS host?', reason_code='TRANSPORT_ERROR', matching_lesson_found=False, tags=['SS-6438','PREPROD'], pattern='original preprod port refused', scope_conditions={'ticket':'SS-6438','environment':'PREPROD','endpoint':'/algo/conf'})
# User answer changes the endpoint host and is recorded in ticket scope rather than lessons.
