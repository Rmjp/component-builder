import sys
k=Exception
y=super
c=print
q=False
hH=True
hn=int
hd=ValueError
hJ=None
hp=str
hW=len
a={"R0":0,"R1":1,"R2":2,"R3":3,"R4":4,"R5":5,"R6":6,"R7":7,"R8":8,"R9":9,"R10":10,"R11":11,"R12":12,"R13":13,"R14":14,"R15":15,"SP":0,"LCL":1,"ARG":2,"THIS":3,"THAT":4,"SCREEN":16384,"KBD":24576}
i={'0':'0101010','1':'0111111','-1':'0111010','D':'0001100','A':'0110000','!D':'0001101','!A':'0110001','-D':'0001111','-A':'0110011','D+1':'0011111','A+1':'0110111','D-1':'0001110','A-1':'0110010','D+A':'0000010','D-A':'0010011','A-D':'0000111','D&A':'0000000','D|A':'0010101','M':'1110000','!M':'1110001','-M':'1110011','M+1':'1110111','M-1':'1110010','D+M':'1000010','D-M':'1010011','M-D':'1000111','D&M':'1000000','D|M':'1010101'}
M={'':'000','M':'001','D':'010','MD':'011','A':'100','AM':'101','AD':'110','AMD':'111'}
A={'':'000','JGT':'001','JEQ':'010','JGE':'011','JLT':'100','JNE':'101','JLE':'110','JMP':'111'}
b=1
R=2
S=0
class AssemblerError(k):
 def __init__(w,t):
  w.message=t
  y().__init__(t)
 def __str__(w):
  return w.message
def h():
 for f in a:
  c(f'{sym:>15} {symtab[sym]:6}')
def H(symbol):
 if symbol=='':
  return q
 if symbol[0].isdigit():
  return q
 for c in symbol:
  if(not c.isalnum())and(c not in '_.$:'):
   return q
 return hH
def n():
 global S
 S=0
def d(Q):
 global S
 s=0
 S=0
 for e in Q:
  S+=1
  X=e.find('//')
  if X!=-1:
   e=e[:X]
  e=e.strip()
  if e=='':
   continue
  if e[0]=='(' and e[-1]==')': 
   O=e[1:-1]
   if not H(O):
    raise AssemblerError(f"Error: line {linenum}: invalid label '{label}'")
   if O in a:
    raise AssemblerError(f"Error: line {linenum}: duplicate label '{label}'")
   a[O]=s
  else: 
   s+=1
def J(Q):
 global S
 S=0
 l=16
 x=[]
 for e in Q:
  S+=1
  X=e.find('//')
  if X!=-1:
   e=e[:X]
  e=e.strip()
  if e=='':
   continue
  if e[0]=='(' and e[-1]==')': 
   pass
  elif e[0]=='@': 
   V,g=p(e)
   if V==R:
    if g in a:
     x.append(G(a[g]))
    else:
     a[g]=l
     x.append(G(l))
     l+=1
   elif V==b:
    x.append(G(g))
   else:
    raise AssemblerError(f"Error: line {linenum}: invalid address '{addr}'")
  else:
   B,u,o=U(e)
   x.append(T(B,u,o))
 return x
def p(aInstr):
 E=aInstr[1:]
 if E[0].isdigit():
  try:
   D=hn(E)
   return b,D
  except hd:
   return hJ,E
 else:
  if H(E):
   return R,E
  else:
   return hJ,E
def W(n):
 K=''
 while hH:
  K=hp(n%2)+K
  n=n//2
  if n==0:
   break
 return K
def G(g):
 C=W(g)
 z=hW(C)
 if z>15:
  raise AssemblerError(f"Error: line {linenum}: too large address '{addr}'")
 else:
  v=('0'*(16-z)+C)
  return hn(v,2)
def U(cInstr):
 P=cInstr.split(';',maxsplit=1)
 L=hW(P)
 if L==1:
  N=P[0]
  o=''
 elif L==2:
  N,o=P
 r=N.split('=',maxsplit=1)
 m=hW(r)
 if m==1:
  B=''
  u=r[0]
 elif m==2:
  B,u=r
 return B,u,o
def T(B,u,o):
 v=('111'+Y(u)+j(B)+F(o))
 return hn(v,2)
def Y(u):
 if u in i:
  return i[u]
 else:
  raise AssemblerError(f"Error: line {linenum}: unrecognized computation '{comp}'")
def j(B):
 if B in M:
  return M[B]
 else:
  raise AssemblerError(f"Error: line {linenum}: unrecognized destination '{des}'")
def F(o):
 if o in A:
  return A[o]
 else:
  raise AssemblerError(f"Error: line {linenum}: unrecognized jump '{jump}'")
def assemble(asm):
 n()
 Q=asm.split("\n")
 d(Q)
 return J(Q)
# Created by pyminifier (https://github.com/liftoff/pyminifier)

