function run_alignment(modeldir,start_case)
if nargin<2,start_case=1;end
cd(modeldir);diary('alignment.log');done=onCleanup(@() diary('off'));
if ~exist('temexd_ref.mexw64','file'),mex('temexd_ref.c');end
cases={'inject','reference','monitored','f0_s36','f225_s36','f0_s10','f225_s10','f225_s10_30min'};
flags=[0 0 0 0 225 0 225 225];steps=[36 36 36 36 36 10 10 10];
hours=[0.002 1/60 1/60 1/6 1/6 1/6 1/6 .5];
for k=start_case:numel(cases)
 label=cases{k};assert(~isfile([label '_observer.csv']) && ~isfile([label '.mat']),'Existing trajectory; use a fresh isolated directory');
 bdclose('all');load_system('MultiLoop_mode1');
 b=find_system('MultiLoop_mode1','LookUnderMasks','all','FollowLinks','on','BlockType','S-Function','FunctionName','temexd_mod');assert(numel(b)==1);b=b{1};
 if k<=2,set_param(b,'FunctionName','temexd_ref');end
 set_param(b,'Parameters',sprintf('[],1431655765,%d',flags(k)));
 if flags(k)==225
  % Output-width compatibility only: selected controller indices unchanged.
  set_param('MultiLoop_mode1/TE Plant/Selector','InputPortWidth','73');
  % HourlyCost is a 41-input diagnostic, not a feedback controller.
  delete_line('MultiLoop_mode1','TE Plant/1','HourlyCost/1');
  add_block('simulink/Signal Routing/Selector','MultiLoop_mode1/Cost original41',...
   'InputPortWidth','73','Indices','1:41');
  add_line('MultiLoop_mode1','TE Plant/1','Cost original41/1');
  add_line('MultiLoop_mode1','Cost original41/1','HourlyCost/1');
 end
 set_param('MultiLoop_mode1','StopFcn','','StopTime',num2str(hours(k),17));
 % SimulationInput variables supersede base values without editing initialization.
 input=Simulink.SimulationInput('MultiLoop_mode1');input=input.setVariable('Ts_save',steps(k)/3600);
 setenv('TEP_GUARD_LOG',fullfile(modeldir,[label '_guard.csv']));setenv('TEP_GUARD_TEST','0');
 setenv('TEP_OBSERVER_LOG',fullfile(modeldir,[label '_observer.csv']));
 if k==1,setenv('TEP_OBSERVER_TEST','1');else,setenv('TEP_OBSERVER_TEST','0');end
 callback=sprintf('tep_listener=add_exec_event_listener(''%s'',''PostOutputs'',@tep_observe);',b);
 set_param('MultiLoop_mode1','StartFcn',callback);
 try
  timer=tic;result=sim(input);wall=toc(timer);save([label '.mat'],'result','-v7');
  names={'simout','xmv','tout'};
  for j=1:numel(names)
   value=result.get(names{j});
   if isstruct(value),value=value.signals.values;elseif isa(value,'timeseries'),value=value.Data;end
   writematrix(value,[label '_' names{j} '.csv']);
  end
  obs=readmatrix([label '_observer.csv']);
  fprintf('RUN=%s FLAG=%d SAVE_SEC=%g END=%g REASON=%g WALL=%g\n',label,flags(k),steps(k),obs(end,1),max(obs(:,end)),wall);
  if k==1,assert(max(obs(:,end))==99 && obs(end,1)<hours(k));
  else,assert(all(obs(:,end)==0) && obs(end,1)>=hours(k)-1e-8);end
 catch e
  fprintf('ERROR=%s\n',getReport(e,'extended','hyperlinks','off'));break;
 end
 evalin('base','clear tep_listener');
end
bdclose('all');setenv('TEP_GUARD_LOG','');setenv('TEP_OBSERVER_LOG','');setenv('TEP_OBSERVER_TEST','');
end
