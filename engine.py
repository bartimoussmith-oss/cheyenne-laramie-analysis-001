import gzip, hashlib, itertools, json, re, subprocess, time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

READY = {'same-record-topic-overlap', 'shared-exact-identifier', 'duplicate-content', 'source-url-revisions'}

def hit(text, terms):
    for term in terms:
        m = re.search(r'(?<!\w)' + re.escape(term).replace(r'\ ', r'\s+') + r'(?!\w)', text, re.I)
        if m:
            return [m.start(), m.end()]
    return None

def issuer(url):
    host = urlsplit(url).hostname
    if host in {'www.cheyennecity.org', 'cheyennecity.org'}:
        return 'cheyenne-city'
    if host in {'www.laramiecountywy.gov', 'laramiecounty.legistar.com'}:
        return 'laramie-county'
    if host in {'www.cheyennebopu.org', 'cheyennebopu.org'}:
        return 'cheyenne-bopu'
    return host

def plans(config):
    return [{'id': a + '--' + b + '--' + r, 'left': a, 'right': b, 'recipe': r, 'implemented': r in READY} for a,b in itertools.combinations(config['subjects'],2) for r in config['recipes']]

def evaluate(plan, docs, metadata):
    left, right, method = plan['left'], plan['right'], plan['recipe']
    a = [d for d in docs if left in d['topics']]
    b = [d for d in docs if right in d['topics']]
    unique = {}
    def add(row):
        key=json.dumps([sorted(row['records']),row['join_key']],sort_keys=True)
        unique.setdefault(key,row)
        return len(unique)>=5
    if method == 'same-record-topic-overlap':
        for d in a:
            if right in d['topics'] and add({'records':[d['id']],'join_key':'same representation','meaning':'topic overlap only; no causal inference'}):
                break
    elif method == 'shared-exact-identifier':
        index=defaultdict(dict)
        for d in b:
            for key in d['references']:
                index[tuple(key)].setdefault(d['source_hash'],d)
        for x in a:
            for key in x['references']:
                for digest,y in index[tuple(key)].items():
                    if x['source_hash']!=digest:
                        if add({'records':[x['id'],y['id']],'join_key':key,'meaning':'literal year-qualified reference and issuer; entity not independently resolved'}):
                            return list(unique.values())
                        break
    elif method == 'duplicate-content':
        index={d['source_hash']:d for d in b}
        for x in a:
            digest=x['source_hash']
            urls=sorted(metadata[digest]['urls'])
            if digest in index and len(urls)>1:
                if add({'records':list(dict.fromkeys([x['id'],index[digest]['id']])),'join_key':digest,'urls':urls[:10],'meaning':'identical original bytes at multiple URLs; not independent corroboration'}):
                    break
    elif method == 'source-url-revisions':
        index=defaultdict(dict)
        for y in b:
            for url in metadata[y['source_hash']]['urls']:
                index[url].setdefault(y['source_hash'],y)
        for x in a:
            for url in metadata[x['source_hash']]['urls']:
                for digest,y in index[url].items():
                    if x['source_hash']!=digest:
                        if add({'records':[x['id'],y['id']],'join_key':url,'meaning':'different observed bytes at one URL; not proof of a legal amendment or its date'}):
                            return list(unique.values())
                        break
    return list(unique.values())

def load(source, config, cursor):
    metadata = {}
    for line in (source/'ledger.jsonl').read_text(encoding='utf-8').splitlines():
        row = json.loads(line)
        digest = row.get('sha256','')
        if row.get('disposition')=='captured' and re.fullmatch('[0-9a-f]{64}',digest) and urlsplit(row.get('url','')).scheme=='https':
            item = metadata.setdefault(digest,{'urls':set(),'observations':[]})
            item['urls'].add(row['url'])
            item['observations'].append(row.get('retrieved_at'))
    files = sorted((source/'text').glob('*.txt')) + sorted((source/'derived').glob('*/page-*.json'))
    docs, errors, size, visited = [], [], 0, 0
    for i in range(min(len(files),2000)):
        path = files[(cursor+i)%len(files)]
        visited += 1
        try:
            if path.is_symlink() or path.stat().st_size>2100000:
                continue
            if path.suffix=='.json':
                obj=json.loads(path.read_text(encoding='utf-8'))
                digest,text,page=obj['source_sha256'],obj['text'],obj['page']
            else:
                digest,text,page=path.stem,path.read_text(encoding='utf-8'),None
            if digest not in metadata:
                continue
            size += len(text.encode('utf-8'))
            if size>12000000:
                break
            url=sorted(metadata[digest]['urls'])[0]
            topics={k:span for k,terms in config['subjects'].items() if (span:=hit(text,terms)) is not None}
            refs=[]
            for m in re.finditer(r'\b(ordinance|resolution|contract|project)\s+(?:no[.:]?\s*)?((?:19|20)\d{2}[-/][A-Z0-9-]+)\b',text,re.I):
                refs.append([issuer(url),m.group(1).lower(),m.group(2).upper()])
            docs.append({'id':hashlib.sha256(str(path.relative_to(source)).encode()).hexdigest()[:24], 'source_hash':digest,'source_url':url,'path':path.relative_to(source).as_posix(),'page':page,'text':text,'topics':topics,'references':refs[:100]})
        except Exception as exc:
            if len(errors)<50:
                errors.append(str(exc)[:300])
    return docs,metadata,len(files),(cursor+visited)%max(1,len(files)),errors

def write_json(path, data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
    started=time.monotonic()
    config=json.loads(Path('engine-config.json').read_text())
    state=json.loads(Path('engine-state.json').read_text()) if Path('engine-state.json').exists() else {'plan_cursor':0,'record_cursor':0}
    source=Path('source')
    rev=subprocess.run(['git','-C',str(source),'rev-parse','HEAD'],check=True,capture_output=True,text=True).stdout.strip()
    docs,metadata,available,next_record,errors=load(source,config,state['record_cursor'])
    all_plans=plans(config)
    eligible=[p for p in all_plans if p['implemented']]
    out=Path('public')
    out.mkdir(exist_ok=True)
    with gzip.open(out/'research-plans.jsonl.gz','wt',encoding='utf-8') as f:
        for p in all_plans:
            f.write(json.dumps(p)+'\n')
    by_id={d['id']:d for d in docs}
    candidates,evidence,receipts,verified=[],{},[],{}
    checked=0
    for i in range(min(512,len(eligible))):
        if time.monotonic()-started>420 or len(candidates)>=200:
            break
        plan=eligible[(state['plan_cursor']+i)%len(eligible)]
        checked+=1
        rows=evaluate(plan,docs,metadata)
        receipts.append({'plan':plan['id'],'candidate_count_before_release_checks':len(rows),'status':'candidates' if rows else 'no_match_in_current_window'})
        for row in rows:
            if len(candidates)>=200:
                break
            permitted=True
            for rid in row['records']:
                d=by_id[rid]
                digest=d['source_hash']
                if digest not in verified:
                    original=source/'objects'/digest[:2]/digest
                    verified[digest]=original.exists() and not original.is_symlink() and hashlib.sha256(original.read_bytes()).hexdigest()==digest
                if not verified[digest]:
                    permitted=False
            if not permitted:
                continue
            for rid in row['records']:
                d=by_id[rid]
                prefix='https://github.com/bartimoussmith-oss/cheyenne-laramie-archive/blob/'+rev+'/'
                evidence[rid]={**d,'representation_text_sha256':hashlib.sha256(d['text'].encode('utf-8')).hexdigest(),'representation_permalink':prefix+d['path'],'original_hash_verified':True,'extraction_accuracy_verified':False}
            candidates.append({'plan_id':plan['id'],'classification':'unreviewed_candidate_not_a_finding','source_revision':rev,**row})
    with open(out/'evidence.jsonl','w',encoding='utf-8') as f:
        for item in evidence.values():
            f.write(json.dumps(item,ensure_ascii=False)+'\n')
    with open(out/'candidates.jsonl','w',encoding='utf-8') as f:
        for item in candidates:
            f.write(json.dumps(item,ensure_ascii=False)+'\n')
    write_json(out/'run-status.json',{'generated_at':datetime.now(timezone.utc).isoformat(),'source_revision':rev,'generated_research_plans':len(all_plans),'eligible_plan_variants':len(eligible),'implemented_recipe_algorithms':len(READY),'plans_checked_this_run':checked,'available_representation_files':available,'window_records_loaded':len(docs),'candidate_rows':len(candidates),'released_evidence_records':len(evidence),'errors_first_50':errors,'reviewed_findings':0,'full_historical_coverage':False,'receipts':receipts})
    (out/'index.md').write_text('# Civic cross-domain research candidates\n\nThese are bounded, unreviewed leads, not allegations or verified findings. Read run-status.json, candidates.jsonl and the self-contained evidence.jsonl. The catalog contains planned recipes, not 10,080 implemented algorithms. Independent source corroboration, dates, units, geometry and legal conclusions are not inferred.\n',encoding='utf-8')
    if sum(p.stat().st_size for p in out.iterdir() if p.is_file())>25000000:
        raise RuntimeError('Publication budget exceeded; outputs must not be committed')
    write_json(Path('engine-state.json'),{'plan_cursor':(state['plan_cursor']+checked)%len(eligible),'record_cursor':next_record,'source_revision':rev})

if __name__=='__main__':
    main()
