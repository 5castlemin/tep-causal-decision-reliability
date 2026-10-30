function run_official_six(modeldir)
cd(modeldir); diary('execution.log'); cleanup=onCleanup(@() diary('off'));
mex('temexd_mod.c');
labels={'A3'}; horizons=[6];
for k=1:1
 try
  bdclose('all'); load_system('MultiLoop_mode1');
  set_param('MultiLoop_mode1','StopFcn','','StopTime',num2str(horizons(k),17));
  setenv('TEP_GUARD_LOG',fullfile(modeldir,[labels{k} '.csv']));setenv('TEP_GUARD_TEST','0');
  fprintf('BEGIN_RUN=%s\n',labels{k});
  result=sim('MultiLoop_mode1','ReturnWorkspaceOutputs','on');
  save([labels{k} '.mat'],'result','-v7');
  raw=readmatrix([labels{k} '.csv']);
  fprintf('RESULT=%s t=%.12g reason=%g rows=%d\n',labels{k},raw(end,1),raw(end,end),size(raw,1));
  if false
    assert(raw(end,end)==99 && raw(end,1)<horizons(k),'guard injection failed');
  elseif any(raw(:,end)~=0) || raw(end,1)<horizons(k)-1e-8
    fprintf('STOP_FURTHER_RUNS\n');break;
  end
 catch e
  fprintf('RUN_ERROR=%s\n',getReport(e,'extended','hyperlinks','off'));break;
 end
end
bdclose('all');setenv('TEP_GUARD_LOG','');setenv('TEP_GUARD_TEST','');
end

