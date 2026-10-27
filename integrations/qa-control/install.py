"""Install the reviewed backend adapter; preserves unrelated dashboard code."""
import argparse
from pathlib import Path
import shutil


def install(dashboard):
    source = Path(__file__).resolve().parent
    target = dashboard / 'backend/services/codexRunner.js'
    text = target.read_text(encoding='utf-8')
    if "from './hybridService.js'" not in text:
        edits = [
            ("import {Codex} from '@openai/codex-sdk';", "import {Codex} from '@openai/codex-sdk';\nimport {hybridScope,plannerPrompt,runHybridService} from './hybridService.js';"),
            ("return async({task,settings,onEvent,signal})=>{", "return async({task,settings,onEvent,signal})=>{\n  const hybrid=hybridScope(task,settings);"),
            ("const codex=new Codex", "if(hybrid){env.AIRAPI_SEARCH_AUTHORIZATION='';env.AIRAPI_VARIABLES_JSON='{}';env.KIBANA_USERNAME='';env.KIBANA_PASSWORD='';}\n  const codex=new Codex"),
            ("networkAccessEnabled:true", "networkAccessEnabled:!hybrid"),
            ("const prompt=`AirAPI", "const prompt=hybrid?plannerPrompt(task,settings,hybrid):`AirAPI"),
            ("if(!completed)throw Error('Codex stream ended without turn.completed; verify CLI login and executable configuration');", "if(!completed)throw Error('Codex stream ended without turn.completed; verify CLI login and executable configuration');\n  if(hybrid)await runHybridService({task,settings,onEvent,signal,scope:hybrid});"),
        ]
        for before, after in edits:
            if text.count(before) != 1:
                raise ValueError('Dashboard runner changed; review adapter before installation')
            text = text.replace(before, after, 1)
        target.write_text(text, encoding='utf-8', newline='\n')
    shutil.copy2(source / 'hybridService.js', dashboard / 'backend/services/hybridService.js')
    test = (source / 'hybridService.test.js').read_text(encoding='utf-8').replace("from './hybridService.js'", "from '../services/hybridService.js'")
    (dashboard / 'backend/test/hybridService.test.js').write_text(test, encoding='utf-8', newline='\n')
    readme = dashboard / 'README.md'
    documentation = readme.read_text(encoding='utf-8')
    if '## Hybrid execution service' not in documentation:
        addition = '''## Hybrid execution service

SS-6412 now uses Codex for preparation and a separate local Black-Box service
for controlled Search execution and points_diff evaluation. Start the service
with `python -B -m bb.service` from Black-Box before running this supported
ticket. Select the STAGE1 profile matching its registered scope. The planner
receives no Search credentials and has network disabled. Results flow through
the existing evidence validation and approval gates. Other tickets keep their
existing agent workflow. See `Black-Box/docs/hybrid-qa-service.md` for scope,
startup and limitations. No live test is submitted merely by starting either app.

'''
        documentation = documentation.replace('## Current workflow\n', addition + '## Current workflow\n', 1)
        readme.write_text(documentation, encoding='utf-8', newline='\n')
    print('Installed hybrid service backend adapter and tests. No settings, credentials or database changed.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dashboard', type=Path)
    install(parser.parse_args().dashboard.resolve())
