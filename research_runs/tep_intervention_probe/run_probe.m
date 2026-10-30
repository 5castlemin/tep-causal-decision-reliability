function run_probe(modeldir,contractfile)
contract=jsondecode(fileread(contractfile));cd(modeldir);diary('probe.log');done=onCleanup(@() diary('off'));
for active=0:1
 assert(~isfile(sprintf('probe_%d_guard.csv',active)) && ~isfile(sprintf('probe_%d.mat',active)),'Existing trajectory; use a fresh isolated directory');
 bdclose('all');load_system('MultiLoop_mode1');
 b='MultiLoop_mode1/TE Plant/TE Code';
 set_param(b,'Parameters',sprintf('[],%d,225',contract.seed));
 set_param('MultiLoop_mode1/TE Plant/Selector','InputPortWidth','73');
 delete_line('MultiLoop_mode1','TE Plant/1','HourlyCost/1');
 add_block('simulink/Signal Routing/Selector','MultiLoop_mode1/Cost original41','InputPortWidth','73','Indices','1:41');
 add_line('MultiLoop_mode1','TE Plant/1','Cost original41/1');add_line('MultiLoop_mode1','Cost original41/1','HourlyCost/1');
 parent=get_param(b,'Parent');ph=get_param(b,'PortHandles');line=get_param(ph.Inport(1),'Line');source=get_param(line,'SrcPortHandle');
 sourceblock=get_param(source,'Parent');sourceport=get_param(source,'PortNumber');
 src=[get_param(sourceblock,'Name') '/' num2str(sourceport)];dst=[get_param(b,'Name') '/1'];
 delete_line(parent,src,dst);
 add_block('simulink/User-Defined Functions/Level-2 MATLAB S-Function',[parent '/Terminal override'],'FunctionName','tep_terminal_override');
 add_line(parent,src,'Terminal override/1');add_line(parent,'Terminal override/1',dst);
 label=sprintf('probe_%d',active);
 setenv('TEP_PROBE_ACTIVE',num2str(active));setenv('TEP_PROBE_VALUE',num2str(contract.value_percent,17));
 setenv('TEP_GUARD_LOG',fullfile(modeldir,[label '_guard.csv']));setenv('TEP_GUARD_TEST','0');
 setenv('TEP_OBSERVER_LOG',fullfile(modeldir,[label '_observer.csv']));setenv('TEP_OBSERVER_TEST','0');
 set_param('MultiLoop_mode1','StopFcn','','StopTime',num2str(contract.horizon_hours,17),...
  'StartFcn',sprintf('tep_listener=add_exec_event_listener(''%s'',''PostOutputs'',@tep_observe);',b));
 input=Simulink.SimulationInput('MultiLoop_mode1');input=input.setVariable('Ts_save',contract.save_seconds/3600);
 try
  timer=tic;result=sim(input);wall=toc(timer);save([label '.mat'],'result','-v7');
  for name={'simout','xmv','tout'}
   v=result.get(name{1});if isstruct(v),v=v.signals.values;elseif isa(v,'timeseries'),v=v.Data;end
   writematrix(v,[label '_' name{1} '.csv']);
  end
  g=readmatrix([label '_guard.csv']);fprintf('PROBE=%d END=%g GUARD=%g WALL=%g VALUE=%.17g\n',active,g(end,1),max(g(:,end)),wall,contract.value_percent);
  assert(all(g(:,end)==0) && g(end,1)>=contract.horizon_hours-1e-8);
 catch e,fprintf('ERROR=%s\n',getReport(e,'extended','hyperlinks','off'));break;end
 evalin('base','clear tep_listener');
end
bdclose('all');setenv('TEP_GUARD_LOG','');setenv('TEP_OBSERVER_LOG','');setenv('TEP_PROBE_ACTIVE','');
end
