`timescale 1ns/1ps
module periph_tb;
reg clk=0,rst=0,sel=1,req=0,we=0; always #5 clk=~clk;
reg [7:0] addr=0; reg [31:0] wd=0; reg [3:0] be=15,btn=0;
wire [31:0] rd; wire [3:0] leds; wire [6:0] s1,s2;
pochoco_periph dut(clk,rst,sel,req,we,addr,wd,be,rd,leds,btn,s1,s2);
reg [31:0] stamp;
initial begin
 #2; rst=0; #20; rst=1;
 @(negedge clk); req=1; we=1; addr=4; wd=5;
 @(posedge clk); stamp=dut.cycle_q;
 @(negedge clk); req=0; we=0;
 if(leds !== 5 || dut.led_cycle_q !== stamp) $fatal(1,"LED timestamp");
 req=1; we=1; be=2; wd=10;
 @(negedge clk); req=0; we=0;
 if(leds !== 5) $fatal(1,"byte enable");
 req=1; addr=16;
 @(negedge clk);
 if(rd !== stamp) $fatal(1,"timestamp read");
 req=0; btn=1;
 repeat(10) @(negedge clk);
 btn=0; repeat(10) @(negedge clk);
 if(dut.btn_q !== 0) $fatal(1,"bounce accepted");
 btn=3; repeat(250010) @(negedge clk);
 req=1; addr=8;
 @(negedge clk);
 if(rd !== 3) $fatal(1,"debounced buttons");
 $display("PASS peripherals: timestamp, byte enables, synchronization/debounce"); $finish;
end
endmodule
