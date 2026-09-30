#!/usr/bin/env python3
"""moth.py — thin, honest client for the MOTH engines this experiment needs."""
import os, json, time, urllib.request, urllib.error
MK=os.environ.get("MOTH_API_KEY",""); BASE="https://api.mothquantum.com"
def _req(path, data=None, timeout=180, method=None):
    req=urllib.request.Request(BASE+path, data=json.dumps(data).encode() if data is not None else None,
        headers={"Authorization":f"Bearer {MK}","Content-Type":"application/json","User-Agent":"Mozilla/5.0"},
        method=method or ("POST" if data is not None else "GET"))
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            b=r.read(); return r.status,(json.loads(b) if b and b[:1] in b'{[' else {"raw":len(b)})
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read())
        except Exception: return e.code,{}
    except Exception as e: return 0,{"err":str(e)[:90]}

def run(engine, params, poll=180):
    st,d=_req(f"/api/v1/engines/{engine}/process",{"params":params})
    if st!=202: return st, d
    jid=d["job_id"]; t0=time.time()
    while time.time()-t0 < poll:
        s,j=_req(f"/api/v1/jobs/{jid}")
        if s==200:
            stt=j.get("status")
            if stt in ("succeeded","failed","error","cancelled"):
                return 200 if stt=="succeeded" else 1, j
        time.sleep(1.2)
    return 0,{"err":"timeout","job_id":jid}

if __name__=="__main__":
    import sys
    st,j=run("qrc-train-v2",{"sequence":[
        "claw","lacks","ternary","routing","claw","lacks","conservation",
        "canary","is","024a5554","across","five","substrates",
        "egg","stimulus","is","vestigial","pincher","ci","was","red"],
        "epochs":30,"num_qubits":5,"seed":1337,"shots":512,"mode":"order"})
    print("status:", st)
    print(json.dumps(j, indent=1)[:1500])
