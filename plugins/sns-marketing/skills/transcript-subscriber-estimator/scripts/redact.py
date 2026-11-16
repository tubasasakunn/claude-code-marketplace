#!/usr/bin/env python3
"""Mask source identity, self-reported reach and production claims. Dictionary stays private."""
import argparse,json,re
from pathlib import Path

def redact(text, terms):
    counts={}
    def replace(label,pattern):
        nonlocal text
        text,n=re.subn(pattern,'[伏字]',text,flags=re.I)
        if n:counts[label]=n
    replace('url',r'https?://[^\s<>]+')
    replace('handle',r'(?<![\w])@[A-Za-z0-9_.-]+')
    # Entire identifying claim, not merely its digits, to avoid leaking the milestone.
    replace('wrapped_reach',r'(?:登録者(?:数)?|フォロワー|再生回数|再生数|総再生)[^\d０-９]{0,35}[\d０-９][\d０-９,.，]*\s*(?:億|万|千|[kKmM])?\s*(?:人|回)?')
    replace('reach_or_history',r'[^\n。！？!?]*(?:登録者(?:数)?|フォロワー|再生回数|再生数|総再生|チャンネル開設|周年|投稿本数)[^\n。！？!?]*[。！？!?]?')
    replace('production_claim',r'[^\n。！？!?]*(?:AI(?:で|が|により)(?:生成|制作|作成)|NotebookLMで|生成AIによる)[^\n。！？!?]*[。！？!?]?')
    for i,term in enumerate(sorted(set(terms),key=len,reverse=True)):
        if term:replace('term_'+str(i),r'\s*'.join(re.escape(c) for c in term))
    text=re.sub(r'(?:\[伏字\][ \t]*){2,}','[伏字]',text)
    return text,counts

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--terms',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--audit',type=Path,required=True);a=p.parse_args()
    if a.output.exists() or a.audit.exists():p.error('Refusing to overwrite existing output or audit')
    text,counts=redact(a.input.read_text(),json.loads(a.terms.read_text()))
    a.output.write_text(text);a.audit.write_text(json.dumps({'counts':counts,'manual_review_required':True},ensure_ascii=False,indent=2)+'\n')
