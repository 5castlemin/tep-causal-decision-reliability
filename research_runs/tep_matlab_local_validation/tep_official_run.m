function tep_official_run(model_dir, output_dir)
% Guarded entry point. Requires an explicitly instrumented, isolated model copy.
if exist(output_dir,'dir')==7
    error('TEP:ExistingOutput','Output directory must be new.');
end
source=fileread(fullfile(model_dir,'temexd_mod.c'));
if isempty(strfind(source,'TEP_GUARD_LOG')) || isempty(strfind(source,'ssSetStopRequested(S,1);return;'))
    error('TEP:MissingMonitor','Prepare and verify the instrumented copy first.');
end
copyfile(model_dir,output_dir);
runner=fullfile(fileparts(fileparts(mfilename('fullpath'))),'tep_official_validation');
addpath(runner);
run_official_guarded(output_dir);
end
