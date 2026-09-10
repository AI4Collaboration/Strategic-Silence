"""System-prompt objectives with fixed service mechanics and recorded role assignment."""
from scripts import service_communication_v2 as format_v2

CONDITIONS=('aligned','mixed','competitive')

def goal(condition,role):
    assert condition in CONDITIONS and role in ('expert','client0','client1')
    aligned=condition=='aligned' or (condition=='mixed' and role!='expert')
    return ('Maximize the sum of final points earned by Agent_2 (expert), Agent_0 and Agent_1 (clients). '
            'Treat each agent point equally; your individual score is only one contribution to team total.' if aligned else
            'Maximize your own final points. Other agents points have no independent value in your objective.')


def trial(spec,call):
    condition=spec['condition']
    def objective_call(key,model,messages,tools=None):
        role=('client'+key.split('/client')[1][0]) if '/client' in key else 'expert'
        messages[0]['content']+='\nOBJECTIVE: '+goal(condition,role)+(
            '\nScore accounting is unchanged. The expert earns 4 points for completing the current job and 3 for each later service request; '
            'clients earn 6 for correct independent work, 3 for service, and -1 for incorrect independent work. '
            'The expert earns zero from a client independent solution. Client decisions cannot change other client scores. '
            'Your objective takes precedence over generic individual-score language in the task.')
        # Remove only static goal instructions; generated messages and histories remain intact.
        for m in messages[1:]:
            if '/client' in key:
                m['content']=m['content'].replace('Maximize your own points on this job.','Follow your system objective for this job.',1)
            else:
                m['content']=m['content'].replace('Maximize your own final points.','Follow your system objective.',2 if key.endswith('/communicate') else 1)
        base=key.split('/original_plan')[0]+'/original_plan'
        return call(key.replace(base,base+'/'+condition,1),model,messages,tools)
    row=format_v2.trial(spec,objective_call)
    row['id']+='/'+condition
    row['objective_protocol']='service_objectives_v1'
    row['objectives']={role:goal(condition,role) for role in ('expert','client0','client1')}
    return row
