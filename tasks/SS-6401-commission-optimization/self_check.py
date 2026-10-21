import copy
from analyze import compare, duration

r={'key':'opaque+=','gds':'S','pcc':'TEST','cons':'TEST','currency':'USD','trips':[{'segments':[{'flightNumber':'1','fareCode':'Y','bookingClass':'Y'}]}], 'priceElement':{'oBaseFare':{'ADT':100}},'prices':{'comm':10,'totalPrice':90},'passengers':{'ADT':{'cnt':1,'comm':10}},'keys':{'commission_info':{'processed':True,'fareCalculation':{'ADT':[{'code':'Y','owner':'AA','amount':100,'commissions':{'TEST':{'upfront':{'rule':1,'subRule':2,'amount':10,'percent':[10]}}}}]}}}}
a={'results':[r]}; b=copy.deepcopy(a); b['results'][0]['key']='anotherOpaque=='
c=compare(a,b); assert c['matched']==c['equal']==c['rule_equal']==1
b['results'][0]['keys']['commission_info']['fareCalculation']['ADT'][0]['commissions']['TEST']['upfront']['rule']=3
c=compare(a,b); assert c['matched']==1 and len(c['rule_differences'])==1 and len(c['differences'])==1
b=copy.deepcopy(a); b['results'][0]['prices']['comm']=11
c=compare(a,b); assert len(c['differences'])==1 and c['rule_equal']==1
b=copy.deepcopy(a); b['results'][0]['priceElement']['oBaseFare']['ADT']=101
assert compare(a,b)['matched']==0
b=copy.deepcopy(a); b['results'][0]['prices']['commBreakdown']=None
assert len(compare(a,b)['differences'])==1
assert abs(duration('390.539252ms')-.390539252)<1e-12
assert duration('1m2.5s')==62.5
a=copy.deepcopy(a); b=copy.deepcopy(a)
for d,rule,subrule in [(a,6189,45694),(b,6082,44388)]:
 d['results'][0]['keys']['commission_info']['fareCalculation']['ADT'][0]['commissions']['TEST']['upfront'].update(rule=rule,subRule=subrule)
c=compare(a,b);assert c['equal']==c['rule_equal']==1 and not c['differences']
b['results'][0]['keys']['commission_info']['fareCalculation']['ADT'][0]['commissions']['TEST']['upfront']['amount']=11
assert len(compare(a,b)['differences'])==1
from analyze import pair_equal,match_records
x={'contract':'Lowest','subRule':35156,'amount':40};y={'contract':'Lowest','subRule':35157,'amount':40}
assert pair_equal(x,y)
assert not pair_equal(x,{**y,'amount':41})
assert pair_equal(x,{**y,'subRule':35048})
assert not pair_equal({**x,'contract':'Average'},{**y,'contract':'Average'})
assert len(match_records([{**x,'subRule':35156},{**x,'subRule':35157}],[{**x,'subRule':35157},{**x,'subRule':35155}],lambda r:r)[0])==2
assert pair_equal({'passengers':{'ADT':{'comm':40,'oComm':{'amount':160}}}},{'passengers':{'ADT':{'comm':40,'oComm':{'amount':40}}}})
assert not pair_equal({'passengers':{'ADT':{'comm':40,'oComm':{'amount':160}}}},{'passengers':{'ADT':{'comm':41,'oComm':{'amount':40}}}})
from analyze import usd_breakdown_equal
entry=lambda n:{'amount':n,'fullAmount':n,'currency':'USD','deduct':True}
assert usd_breakdown_equal({'backend':[entry(15)]},{'upfront':[entry(14.5)]})
assert usd_breakdown_equal({'backend':[entry(15)]},{'upfront':[entry(14)]})
assert not usd_breakdown_equal({'backend':[entry(15)]},{'upfront':[entry(13.99)]})
assert not usd_breakdown_equal({'backend':[{**entry(15),'currency':'CAD'}]},{'upfront':[{**entry(14.5),'currency':'CAD'}]})
assert not usd_breakdown_equal({'segmentFees':[entry(15)]},{'segmentFees':[entry(14.5)]})
assert not usd_breakdown_equal({'backend':[{'currency':'USD'}]},{'upfront':[{'currency':'USD'}]})
print('Comparator self-check: 22 checks passed, including inclusive USD 1 breakdown tolerance and scope guards')

for field in ['totalPrice','totalTax']:
 x={'currency':'USD','prices':{field:100,'comm':10}}
 assert pair_equal(x,{'currency':'USD','prices':{field:101,'comm':10}})
 assert not pair_equal(x,{'currency':'USD','prices':{field:101.01,'comm':10}})
 assert not pair_equal(x,{'currency':'USD','prices':{'comm':10}})
 assert not pair_equal({'currency':'CAD','prices':{field:100}},{'currency':'CAD','prices':{field:100.01}})
 assert not pair_equal({'prices':{field:100}},{'prices':{field:100.01}})
 assert pair_equal({'tickets':[x]},{'tickets':[{'currency':'USD','prices':{field:100.5,'comm':10}}]})
assert not pair_equal({'currency':'USD','prices':{'comm':10}},{'currency':'USD','prices':{'comm':10.01}})
print('USD total price/tax: 13 scope and boundary checks passed')

assert pair_equal({'currency':'USD','prices':{'totalPrice':None}},{'currency':'USD','prices':{'totalPrice':None}})
assert not pair_equal({'currency':'USD','prices':{'totalPrice':False}},{'currency':'USD','prices':{'totalPrice':0}})

# User-reviewed PROD exceptions are directional: left is PROD, right is PREPROD.
ref=lambda trip,seg:{'tripId':trip,'segmentId':seg}
assert pair_equal({'segments':[ref(1,1),ref(2,1),ref(2,1)]},{'segments':[ref(1,1),ref(2,1)]})
assert pair_equal({'segments':[ref(1,1),ref(1,1)]},{'segments':[ref(1,1)]})
assert not pair_equal({'segments':[ref(2,1)]},{'segments':[ref(2,1),ref(2,1)]})
fee=lambda n:{'segmentFees':{'amount':n,'fullAmount':n,'currency':'USD','rule':4933}}
assert pair_equal(fee(35),fee(15))
assert not pair_equal(fee(15),fee(35))
assert not pair_equal(fee(35),{'segmentFees':{**fee(15)['segmentFees'],'rule':9}})
assert pair_equal({'comm':0},{'comm':0,'commBreakdown':{'upfront':[entry(14.5)]}})
assert pair_equal({'commBreakdown':{'segmentFees':[entry(35)]}},{'commBreakdown':{'segmentFees':[entry(15)],'upfront':[entry(14.5)]}})
assert not pair_equal({'commBreakdown':{'upfront':[entry(14.5)]}}, {})
x={'rule':4989,'subRule':34186,'combKey':'AMOTHER','amount':41.65,'percent':[5]}
y={'rule':4926,'subRule':33655,'combKey':'AMNONJV','amount':41.65,'percent':[5]}
assert pair_equal(x,y)
assert not pair_equal(x,{**y,'amount':42})
asset=lambda n,c='USD':{'priceElement':{'Assets':{'Commission':{'ValuePerPax':{'ADT':{'amount':n,'currency':c}}}}}}
assert pair_equal(asset(167.56),asset(168.56))
assert not pair_equal(asset(167.56),asset(168.57))
assert not pair_equal(asset(167.56,'CAD'),asset(167.57,'CAD'))
print('Reviewed PROD exception checks passed')

def f90_fare(rule,subrule,key,tour,amount=100,od=('SFO','MUC')):
 return {'departure':od[0],'arrival':od[1],'commissions':{'VZC':{'upfront':{'rule':rule,'subRule':subrule,'combKey':key,'tourCode':tour,'amount':amount,'fullAmount':amount,'currency':'CAD','percent':[10]}}}}
x=f90_fare(5561,37750,'TC7AIB','TC7A');y=f90_fare(4065,28486,'AJBUPY','AJBUPY')
assert pair_equal(x,y)
assert not pair_equal(x,f90_fare(4065,28486,'AJBUPY','AJBUPY',101))
assert not pair_equal(f90_fare(5561,37750,'TC7AIB','TC7A',od=('JFK','MUC')),f90_fare(4065,28486,'AJBUPY','AJBUPY',od=('JFK','MUC')))
assert pair_equal(f90_fare(4065,28486,'AJBUPY','AJBUPY',od=('MUC','SFO')),f90_fare(5556,37713,'TC7AOB','TC7A',od=('MUC','SFO')))
print('F-90 approved equal-amount OD-scoped rule-choice checks passed')
