`timescale 1ns/1ps
module decoder_tb;
reg [31:0] insn; wire illegal,rw,lr,lw,br,j,jr;
espino_decoder dut(.instr_i(insn),.illegal_insn_o(illegal),.rf_we_o(rw),
 .lsu_req_o(lr),.lsu_we_o(lw),.is_branch_o(br),.is_jal_o(j),.is_jalr_o(jr));
task reject;
 input [31:0] value;
 begin insn=value; #1;
 if(!illegal || rw || lr || lw || br || j || jr) $fatal(1,"illegal instruction side effect %h",value);
 end
endtask
initial begin
 reject(32'h00101813); // x16 + disabled shift
 reject(32'h00101093); // disabled SLLI
 reject(32'h021080b3); // MUL must not execute as ADD
 reject(32'h01002023); // store x16 must not alias x0
 reject(32'h00003083); // invalid load width
 reject(32'h00000073); // no traps/ECALL implemented
 insn=32'h800000b7; #1;
 if(illegal || !rw) $fatal(1,"LUI immediate mistaken for register");
 $display("PASS decoder: reserved registers/opcodes have no side effects"); $finish;
end
endmodule
