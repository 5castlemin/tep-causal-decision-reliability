function tep_observe(block, ~)
% Read-only runtime observation. Never calls TEFUNC or changes an input.
y=double(block.OutputPort(1).Data(:));
u=double(block.InputPort(1).Data(:));
t=get_param(bdroot(block.BlockHandle),'SimulationTime');
reason=0;
if any(~isfinite(y)) || any(~isfinite(u)),reason=1;end
if any(u(1:12)<0 | u(1:12)>100),reason=3;end
if y(7)>=3000 || y(9)>=175,reason=4;end
if any(y([8 12 15])<=0 | y([8 12 15])>=100),reason=5;end
if strcmp(getenv('TEP_OBSERVER_TEST'),'1') && t>=0.0005,reason=99;end
f=fopen(getenv('TEP_OBSERVER_LOG'),'a');
assert(f>=0,'observer log unavailable');
fprintf(f,'%.17g',t);fprintf(f,',%.17g',[y;u]);fprintf(f,',%d\n',reason);fclose(f);
if reason, set_param(bdroot(block.BlockHandle),'SimulationCommand','stop');end
end
