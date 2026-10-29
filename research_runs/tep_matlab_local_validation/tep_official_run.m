function tep_official_run(model_dir, output_dir)
% Fail closed until a validated online measurement, state and command guard exists.
% MATLAB availability alone does not prove that runtime monitoring is working.
% Retain the explicit stage order and default model settings for future validation.
if exist(model_dir,'dir') ~= 7 || exist(output_dir,'dir') ~= 7
    error('Model and output directories must exist.');
end
error('TEP:SafetyMonitorNotVerified', ...
    ['Simulation blocked: the official model runtime signal mapping and an online ', ...
     'measurement/state/command stop callback must first be established and tested.']);
% Once that gate is independently established, invoke sim on a fresh staged model
% for 0.166... hours, save all 41 measurements, 12 commands and state/timestamps,
% check shutdown and bounds, then consider 2 h. No hardcoded success is permitted.
end
