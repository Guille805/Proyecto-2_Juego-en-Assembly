`timescale 1ns/1ps
module core_tb;
reg clk=0,rst=0; always #5 clk=~clk;
wire ir,dr,dw; wire [3:0] be; wire [31:0] ia,id,da,wd,rd;
espino_core core(clk,rst,ir,ia,id,dr,dw,be,da,wd,rd);
pochoco_ram #(.NumWords(512),.MemFile("core.hex")) ram
(clk,ir,ia,id,dr && !da[31],dw,be,da,wd,rd);
initial begin
  #22 rst=1;
  #10000 $fatal(1,"core timeout");
end
always @(posedge clk) if(rst && dr && dw && da==32'h80000000) begin
  if(wd !== 84 || ram.mem[256] !== 42 || ram.mem[257] !== 84 || ram.mem[258] !== 99)
    $fatal(1,"core arithmetic/load/store/jump mismatch");
  $display("PASS core: dependencies, x0, RAM, branches, JAL/JALR"); $finish;
end
endmodule
