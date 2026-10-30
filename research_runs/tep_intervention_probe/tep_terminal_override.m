function tep_terminal_override(block)
% Explicit terminal-input adapter. Does not replace the controller or TE code.
block.NumInputPorts=1;block.NumOutputPorts=1;
block.SetPreCompInpPortInfoToDynamic;block.SetPreCompOutPortInfoToDynamic;
block.InputPort(1).Dimensions=40;block.OutputPort(1).Dimensions=40;
block.InputPort(1).DirectFeedthrough=true;
block.SampleTimes=[0 0];block.SimStateCompliance='DefaultSimState';
block.RegBlockMethod('Outputs',@outputs);
end
function outputs(block)
u=block.InputPort(1).Data;t=block.CurrentTime;
if strcmp(getenv('TEP_PROBE_ACTIVE'),'1') && t>=.05 && t<.1
 u(10)=str2double(getenv('TEP_PROBE_VALUE'));
end
assert(all(isfinite(u)) && all(u(1:12)>=0 & u(1:12)<=100));
block.OutputPort(1).Data=u;
end
