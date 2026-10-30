function run_original_seeds(modeldir)
cd(modeldir); diary('seed_diagnostic.log');cleanup=onCleanup(@() diary('off'));
for seed=[24121989 12101992]
 bdclose('all');load_system('MultiLoop_mode1');
 blocks=find_system('MultiLoop_mode1','LookUnderMasks','all','FollowLinks','on','BlockType','S-Function','FunctionName','temexd_mod');assert(numel(blocks)==1);
 set_param(blocks{1},'Parameters',sprintf('[],%d',seed));
 set_param('MultiLoop_mode1','StopFcn','','StopTime','6');
 name=sprintf('seed_%d',seed);setenv('TEP_GUARD_LOG',fullfile(modeldir,[name '.csv']));setenv('TEP_GUARD_TEST','0');
 try
 fprintf('SEED_BEGIN=%d PARAM=%s\n',seed,get_param(blocks{1},'Parameters'));
 result=sim('MultiLoop_mode1','ReturnWorkspaceOutputs','on');save([name '.mat'],'result','-v7');
 raw=readmatrix([name '.csv']);fprintf('SEED_END=%d TIME=%g GUARD=%g\n',seed,raw(end,1),raw(end,end));
 if any(raw(:,end)~=0)||raw(end,1)<6-1e-8,break;end
 catch e,fprintf('SEED_ERROR=%s\n',getReport(e,'extended','hyperlinks','off'));break;end
end
bdclose('all');setenv('TEP_GUARD_LOG','');
end
