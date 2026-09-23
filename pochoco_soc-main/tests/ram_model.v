// Simulation-only model for the MODE=0 subset used by the register bank.
// This is not a substitute for timing simulation of the iCE40 primitive.
module SB_RAM40_4K #(parameter READ_MODE=0, WRITE_MODE=0, parameter [255:0] INIT_0=0)
(input [10:0] RADDR,WADDR, input RCLK,RCLKE,RE,WCLK,WCLKE,WE,
 input [15:0] WDATA,MASK, output reg [15:0] RDATA);
reg [15:0] mem[0:255]; integer i,j;
initial begin
  for(i=0;i<256;i=i+1) mem[i]=0;
  for(i=0;i<16;i=i+1) mem[i]=INIT_0[i*16+:16];
end
always @(posedge RCLK) if(RCLKE && RE) RDATA <= mem[RADDR[7:0]];
always @(posedge WCLK) if(WCLKE && WE)
  for(j=0;j<16;j=j+1) if(!MASK[j]) mem[WADDR[7:0]][j] <= WDATA[j];
endmodule
