module main;
  reg [55:0] magic = 56'd31299793024068650;
  reg [55:0] kittens;
  reg success;
  reg [6:0] memory [7:0];
  reg [2:0] idx = 0;
  
  initial 
    begin
      memory[0] = 7'h37;
      idx = idx + 5;
      memory[1] = 7'h2a;
      idx = idx + 5;
      memory[2] = 7'h6f;
      idx = idx + 5;
      memory[3] = 7'h78;
      idx = idx + 5;
      memory[4] = 7'h25;
      idx = idx + 5;
      memory[5] = 7'h4c;
      idx = idx + 5;
      memory[6] = 7'h5f;
      idx = idx + 5;
      memory[7] = 7'h58;

      magic = {
          {memory[0], memory[5]},
          {memory[6], memory[2]}, 
          {memory[4], memory[3]},
          {memory[7], memory[1]}
      };

      kittens = { magic[9:0], magic[41:22], magic[21:10], magic[55:42] };
      success = kittens == 56'd3008192072309708;
    
      $display("magic: %h", magic);
      $display("kittens: %h", kittens);
      $display("Success: %h", success);
      $finish;
    end
endmodule
