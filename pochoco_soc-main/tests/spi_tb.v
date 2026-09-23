`timescale 1ns/1ps
module spi_tb;
reg clk=0,rst=0,req=0,we=0,sclk=0,mosi=0,cs=1;
always #5 clk=~clk;
reg [7:0] addr=0; reg [31:0] wd=0;
wire [31:0] rd; wire miso;
pochoco_spi_slave dut(clk,rst,1'b1,req,we,addr,wd,4'hf,rd,sclk,mosi,cs,miso);
reg [7:0] result; integer i;
task transfer;
 input [7:0] value;
 begin
  result=0;
  for(i=7;i>=0;i=i-1) begin
   mosi=value[i]; #100; result={result[6:0],miso}; sclk=1; #100; sclk=0; #100;
  end
 end
endtask
initial begin
 #2; rst=0; #20; rst=1;
 @(negedge clk); req=1; we=1; addr=8; wd=8'ha5;
 @(negedge clk); req=0; we=0; cs=0; #100;
 transfer(8'h37);
 if(result !== 8'ha5 || dut.price_q !== 8'h37) $fatal(1,"first SPI byte");
 transfer(8'hc9);
 if(result !== 8'ha5 || dut.price_q !== 8'hc9) $fatal(1,"consecutive SPI byte");
 cs=1; #100;
 req=1; addr=4; #20; req=0; #20;
 if(dut.new_price_q !== 0) $fatal(1,"read clear");
 transfer(8'hff);
 if(dut.price_q !== 8'hc9 || dut.new_price_q !== 0) $fatal(1,"inactive CS received data");
 $display("PASS SPI: consecutive bytes, MISO, read clear, inactive CS"); $finish;
end
endmodule
