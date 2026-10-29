function tep_official_preflight(model_dir, output_dir)
% PREPARATORY ONLY: no simulation, no modification to original archive.
% Run after copying this file outside the official source directory.
if exist(model_dir,'dir') ~= 7 || exist(output_dir,'dir') ~= 7
    error('Model and output directories must already exist.');
end
old = pwd; cleanup = onCleanup(@() cd(old)); %#ok<NASGU>
cd(model_dir);
diary(fullfile(output_dir,'matlab_preflight.log'));
diaryCleanup = onCleanup(@() diary('off')); %#ok<NASGU>
fprintf('MATLAB version: %s\n', version);
ver;
fprintf('Simulink license: %d\n', license('test','Simulink'));
if ~license('test','Simulink')
    error('Simulink licence is unavailable or unverified.');
end
cfg = mex.getCompilerConfigurations('C','Selected');
if isempty(cfg)
    error('No selected supported C compiler. Run mex -setup c.');
end
disp(cfg);
fprintf('Compiling the staged C source only; original ZIP remains untouched.\n');
mex('temexd_mod.c');
load_system('MultiLoop_mode1');
fprintf('Model loaded; solver=%s, preload=%s, stop callback=%s\n', ...
    get_param('MultiLoop_mode1','Solver'), ...
    get_param('MultiLoop_mode1','PreLoadFcn'), get_param('MultiLoop_mode1','StopFcn'));
save(fullfile(output_dir,'model_preflight.mat'),'cfg');
fprintf('PRECHECK ONLY. No simulation has been run.\n');
close_system('MultiLoop_mode1',0);
end
