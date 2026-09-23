addi x1,x0,42
addi x0,x0,7
add x2,x1,x0
sw x2,1024(x0)
lw x3,1024(x0)
add x4,x3,x1
sw x4,1028(x0)
addi x5,x0,3
loop: addi x5,x5,-1
bne x5,x0,loop
jal x6,subroutine
addi x7,x0,99
sw x7,1032(x0)
jal x0,done
subroutine: addi x8,x6,0
jalr x0,0(x8)
done: lui x9,0x80000
sw x4,0(x9)
jal x0,done
