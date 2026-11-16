# Tiny chess engine v1 - alpha-beta search with TT and PST
import json,os,sys,urllib.request,urllib.error
ENV=os.environ.get("MAKEFUN_ENV_URL","")
VAL={"p":1,"n":3,"b":3,"r":5,"q":9,"k":100}
PST={
"p":[[0,0,0,0,0,0,0,0],[50,50,50,50,50,50,50,50],[10,10,20,30,30,20,10,10],[5,5,10,25,25,10,5,5],[0,0,0,20,20,0,0,0],[5,-5,-10,0,0,-10,-5,5],[5,10,10,-20,-20,10,10,5],[0,0,0,0,0,0,0,0]],
"n":[[-50,-40,-30,-30,-30,-30,-40,-50],[-40,-20,0,0,0,0,-20,-40],[-30,0,10,15,15,10,0,-30],[-30,5,15,20,20,15,5,-30],[-30,0,15,20,20,15,0,-30],[-30,5,10,15,15,10,5,-30],[-40,-20,0,5,5,0,-20,-40],[-50,-40,-30,-30,-30,-30,-40,-50]],
"b":[[-20,-10,-10,-10,-10,-10,-10,-20],[-10,0,0,0,0,0,0,-10],[-10,0,10,10,10,10,0,-10],[-10,5,5,10,10,5,5,-10],[-10,0,10,10,10,10,0,-10],[-10,10,10,10,10,10,10,-10],[-10,5,0,0,0,0,5,-10],[-20,-10,-10,-10,-10,-10,-10,-20]],
"r":[[0,0,0,0,0,0,0,0],[5,10,10,10,10,10,10,5],[-5,0,0,0,0,0,0,-5],[-5,0,0,0,0,0,0,-5],[-5,0,0,0,0,0,0,-5],[-5,0,0,0,0,0,0,-5],[-5,0,0,0,0,0,0,-5],[0,0,0,5,5,0,0,0]],
"q":[[-20,-10,-10,-5,-5,-10,-10,-20],[-10,0,0,0,0,0,0,-10],[-10,0,5,5,5,5,0,-10],[-5,0,5,5,5,5,0,-5],[0,0,5,5,5,5,0,-5],[-10,5,5,5,5,5,0,-10],[-10,0,5,0,0,0,0,-10],[-20,-10,-10,-5,-5,-10,-10,-20]],
"k":[[-30,-40,-40,-50,-50,-40,-40,-30],[-30,-40,-40,-50,-50,-40,-40,-30],[-30,-40,-40,-50,-50,-40,-40,-30],[-30,-40,-40,-50,-50,-40,-40,-30],[-20,-30,-30,-40,-40,-30,-30,-20],[-10,-20,-20,-20,-20,-20,-20,-10],[20,20,0,0,0,0,20,20],[20,30,10,0,0,10,30,20]]
}
def pst(p,x,y,col):
    if p.islower():return PST[p][y][x]
    return PST[p.upper()][7-y][x]
class B:
    def __init__(s,fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"):
        s.fen=fen;L=fen.split();s.B={}
        for y,row in enumerate(L[0].split("/")):
            x=0
            for c in row:
                if c.isdigit():x+=int(c)
                else:s.B[f"{chr(97+x)}{8-y}"]=c;x+=1
        s.turn=L[1];s.W=s.bishop_pair()
    def b_pair(s):
        bn=bw=0
        for _,p in s.B.items():
            if p=="b":bn+=1
            elif p=="B":bw+=1
        return bn,bw
    def bishop_pair(s):
        n=s.b_pair()
        return (1 if n[0] else 0)+(1 if n[1] else 0)
    def gen_moves(s):
        ms=[]
        for sq,p in list(s.B.items()):
            x,y=sq[0],int(sq[1])
            lc=p.lower();col=p.isupper()
            if lc=="p":
                dir=-1 if col else 1;start=6 if col else 1
                f=sq[0]
                # forward
                ny=y+dir
                if 0<=ny<8:
                    ns=f+str(ny)
                    if ns not in s.B:
                        ms.append((sq,ns))
                        if y==start:
                            n2=y+2*dir;s2=f+str(n2)
                            if 0<=n2<8 and s2 not in s.B:ms.append((sq,s2))
                # captures
                for dx in [-1,1]:
                    nx,ny=x+dx,y+dir
                    if 0<=nx<8 and 0<=ny<8:
                        ns=f"{chr(97+nx)}{ny}"
                        if ns in s.B and s.B[ns].isupper()!=col:ms.append((sq,ns))
            elif lc=="n":
                for dx,dy in[(1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)]:
                    nx,ny=x+dx,y+dy
                    if 0<=nx<8 and 0<=ny<8:
                        ns=f"{chr(97+nx)}{ny}"
                        if ns not in s.B or s.B[ns].isupper()!=col:ms.append((sq,ns))
            elif lc in"brq":
                dirs=[]
                if lc in"bq":dirs+=[(1,1),(-1,1),(1,-1),(-1,-1)]
                if lc in"rq":dirs+=[(0,1),(0,-1),(1,0),(-1,0)]
                for dx,dy in dirs:
                    nx,ny=x+dx,y+dy
                    while 0<=nx<8 and 0<=ny<8:
                        ns=f"{chr(97+nx)}{ny}"
                        if ns not in s.B:ms.append((sq,ns))
                        elif s.B[ns].isupper()!=col:ms.append((sq,ns));break
                        else:break
                        nx+=dx;ny+=dy
            elif lc=="k":
                for dx in[-1,0,1]:
                    for dy in[-1,0,1]:
                        if dx or dy:
                            nx,ny=x+dx,y+dy
                            if 0<=nx<8 and 0<=ny<8:
                                ns=f"{chr(97+nx)}{ny}"
                                if ns not in s.B or s.B[ns].isupper()!=col:ms.append((sq,ns))
        return ms
    def eval(s):
        sc=0
        for sq,p in s.B.items():
            x,y=sq[0],int(sq[1])
            if p.isupper():sc+=VAL[p.lower()]+pst(p,x,y,1)
            else:sc-=(VAL[p.lower()]+pst(p,x,y,0))
        sc+=s.W*(0.5 if p.isupper() else -0.5)
        return sc if s.turn=="w" else -sc
    def apply(s,mv):
        f,t=mv;B2=B(fen=s.fen)
        p=B2.B.pop(f);B2.B[t]=p;B2.turn="b" if s.turn=="w" else "w"
        if p=="P" and t[1]=="8":B2.B[t]="Q"
        if p=="p" and t[1]=="1":B2.B[t]="q"
        B2.fen=f"{'/'.join(''.join(B2.B.get(f'{c}{r}',"" )or str(sum(f'{c}{r}' not in B2.B for r in range(8)))for c in'abcdefgh')for r in range(8,0,-1)).replace('8/',' ').replace('7/','1 ')}/ {B2.turn} - - 0 1".split()[0]
        return B2
    def legal(s):
        ms=[]
        for m in s.gen_moves():
            nxt=s.apply(m)
            king="K"if s.turn=="w"else"k"
            found=False
            for sq,p in nxt.B.items():
                if p==king:found=True;break
            if not found:continue
            ms.append(m)
        return ms
def post(path,body):
    req=urllib.request.Request(ENV+path,data=json.dumps(body).encode(),headers={"content-type":"application/json"})
    try:
        with urllib.request.urlopen(req) as r:return json.load(r)
    except urllib.error.HTTPError as e:sys.exit(str(e))
TT={}
def alphabeta(b,d,a,beta,mx):
    key=b.fen+(("max"if mx else "min"),d)
    if key in TT:return TT[key]
    if d==0:return b.eval()
    ms=b.legal()
    if not ms:return 0
    ms.sort(key=lambda m:-abs(VAL.get(b.B.get(m[1],""),0)))
    val=-1e9 if mx else 1e9
    for m in ms:
        nb=b.apply(m);v=-alphabeta(nb,d-1,-beta,-a,not mx)
        if v>val:val=v
        if v>a:a=v
        if a>=beta:break
    TT[key]=val
    return val
def choose(b):
    ms=b.legal()
    if not ms:return None
    best=None;bestv=-1e9
    for m in ms:
        nb=b.apply(m);v=-alphabeta(nb,3,-1e9,1e9,False)
        if v>bestv:bestv=v;best=m
    return best
while True:
    g=post("/game",{})
    if g["status"]=="done":break
    while g["status"]=="your_move":
        fen=g["fen"];turn=g["colour"]
        b=B(fen)
        mv=choose(b)
        if not mv:g["status"]="over";break
        g=post("/move",{"game":g["game"],"move":mv})
    print(f"game {g['game']}: {g['outcome']} by {g['reason']}",file=sys.stderr)
print(f"done: {g.get('wins')} won, {g.get('draws')} drawn, {g.get('losses')} lost",file=sys.stderr)
