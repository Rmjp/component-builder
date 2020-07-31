import sys
e={"R0":0,"R1":1,"R2":2,"R3":3,"R4":4,"R5":5,"R6":6,"R7":7,"R8":8,"R9":9,"R10":10,"R11":11,"R12":12,"R13":13,"R14":14,"R15":15,"SP":0,"LCL":1,"ARG":2,"THIS":3,"THAT":4,"SCREEN":16384,"KBD":24576}
L={}
V={'0':'0101010','1':'0111111','-1':'0111010','D':'0001100','A':'0110000','!D':'0001101','!A':'0110001','-D':'0001111','-A':'0110011','D+1':'0011111','A+1':'0110111','D-1':'0001110','A-1':'0110010','D+A':'0000010','D-A':'0010011','A-D':'0000111','D&A':'0000000','D|A':'0010101','M':'1110000','!M':'1110001','-M':'1110011','M+1':'1110111','M-1':'1110010','D+M':'1000010','D-M':'1010011','M-D':'1000111','D&M':'1000000','D|M':'1010101'}
K={'':'000','M':'001','D':'010','MD':'011','A':'100','AM':'101','AD':'110','AMD':'111'}
o={'':'000','JGT':'001','JEQ':'010','JGE':'011','JLT':'100','JNE':'101','JLE':'110','JMP':'111'}
H=1
b=2
z=0
class AssemblerError(Exception):
 def __init__(J,P):
  J.message=P
  super().__init__(P)
 def __str__(J):
  return J.message
def x():
 for k in L:
  print(f'{sym:>15} {symtab[sym]:6}')
def S(symbol):
 if symbol=='':
  return False
 if symbol[0].isdigit():
  return False
 for c in symbol:
  if(not c.isalnum())and(c not in '_.$:'):
   return False
 return True
def j():
 global z
 z=0
 L.clear()
 for k in e:
  L[k]=e[k]
def w(c):
 global z
 n=0
 z=0
 for B in c:
  z+=1
  g=B.find('//')
  if g!=-1:
   B=B[:g]
  B=B.strip()
  if B=='':
   continue
  if B[0]=='(' and B[-1]==')': 
   v=B[1:-1]
   if not S(v):
    raise AssemblerError(f"Error: line {z}: invalid label '{v}'")
   if v in L:
    raise AssemblerError(f"Error: line {z}: duplicate label '{v}'")
   L[v]=n
  else: 
   n+=1
def E(c):
 global z
 z=0
 N=16
 d=[]
 for B in c:
  z+=1
  g=B.find('//')
  if g!=-1:
   B=B[:g]
  B=B.strip()
  if B=='':
   continue
  if B[0]=='(' and B[-1]==')': 
   pass
  elif B[0]=='@': 
   F,a=X(B)
   if F==b:
    if a in L:
     d.append(y(L[a]))
    else:
     L[a]=N
     d.append(y(N))
     N+=1
   elif F==H:
    d.append(y(a))
   else:
    raise AssemblerError(f"Error: line {z}: invalid address '{a}'")
  else:
   f,M,I=l(B)
   d.append(p(f,M,I))
 return d
def X(aInstr):
 O=aInstr[1:]
 if O[0].isdigit():
  try:
   r=int(O)
   return H,r
  except ValueError:
   return None,O
 else:
  if S(O):
   return b,O
  else:
   return None,O
def h(n):
 t=''
 while True:
  t=str(n%2)+t
  n=n//2
  if n==0:
   break
 return t
def y(a):
 Q=h(a)
 T=len(Q)
 if T>15:
  raise AssemblerError(f"Error: line {z}: too large address '{a}'")
 else:
  i=('0'*(16-T)+Q)
  return int(i,2)
def l(cInstr):
 Y=cInstr.split(';',maxsplit=1)
 m=len(Y)
 if m==1:
  C=Y[0]
  I=''
 elif m==2:
  C,I=Y
 D=C.split('=',maxsplit=1)
 U=len(D)
 if U==1:
  f=''
  M=D[0]
 elif U==2:
  f,M=D
 return f,M,I
def p(f,M,I):
 i=('111'+q(M)+u(f)+s(I))
 return int(i,2)
def q(M):
 if M in V:
  return V[M]
 else:
  raise AssemblerError(f"Error: line {z}: unrecognized computation '{M}'")
def u(f):
 if f in K:
  return K[f]
 else:
  raise AssemblerError(f"Error: line {z}: unrecognized destination '{f}'")
def s(I):
 if I in o:
  return o[I]
 else:
  raise AssemblerError(f"Error: line {z}: unrecognized jump '{I}'")
def assemble(asm):
 j()
 c=asm.split("\n")
 w(c)
 return E(c)
# Created by pyminifier (https://github.com/liftoff/pyminifier)

