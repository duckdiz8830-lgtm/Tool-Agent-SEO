# -*- coding: utf-8 -*-
import os, sys
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
import autopost as A
import requests

class Resp:
    def __init__(self, code, data=None): self.status_code=code; self._data=data or {}; self.text='mock'
    def json(self): return self._data
    def raise_for_status(self):
        if self.status_code >= 400: raise RuntimeError(self.status_code)

models=['gemini-5.0-flash','gemini-3.6-flash']
def fake_get(url,*a,**k):
    return Resp(200, {'models':[{'name':'models/'+m,'supportedGenerationMethods':['generateContent'],
                                 'inputTokenLimit':1000,'outputTokenLimit':1000} for m in models]})
requests.get=fake_get
os.environ['GOOGLE_API_KEY']='FAKE'

# Case 1: model đã nhớ chạy được -> đúng 1 probe, timeout 12, có lưu config.
os.environ['MODEL_GEMINI']='gemini-3.6-flash'
A._MODEL_404_TRONG_PHIEN.clear()
calls=[]; saved=[]
def post1(url,*a,**k):
    m=url.split('/models/')[1].split(':')[0]; calls.append((m,k.get('timeout')))
    return Resp(200)
requests.post=post1
A.C.luu_gemini=lambda key, model: saved.append((key,model))
out=A.do_model()
assert calls == [('gemini-3.6-flash',12)], calls
assert saved and saved[-1][1]=='gemini-3.6-flash', saved

# Case 2: 404 chỉ thử một lần trong session. Không cho mock save đổi env để
# lần 2 không được hưởng ưu tiên model, chỉ được hưởng cache 404.
os.environ['MODEL_GEMINI']=''
A._MODEL_404_TRONG_PHIEN.clear(); calls=[]
def post2(url,*a,**k):
    m=url.split('/models/')[1].split(':')[0]; calls.append(m)
    return Resp(404, {'error':{'message':'no longer available'}}) if m=='gemini-5.0-flash' else Resp(200)
requests.post=post2
A.C.luu_gemini=lambda key, model: None
A.do_model(); first=list(calls); calls.clear()
os.environ['MODEL_GEMINI']=''
A.do_model(); second=list(calls)
assert first == ['gemini-5.0-flash','gemini-3.6-flash'], first
assert second == ['gemini-3.6-flash'], second
print('PASS A2: remembered=1 probe timeout=12; 404 first=', first, '; second=', second)
