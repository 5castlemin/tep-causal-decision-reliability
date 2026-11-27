# S4 error-value mechanism framework

**Status: proposed framework; no new mechanism model fitted.** Define the realized value of a feasible edit as `V(e|G)=R(G)-R(G after e)`. The target is an SCM-level outcome; edits within a graph are repeated, dependent candidates.

Candidate structural predictors include error class (FN/FP/REV/UNRES), prespecified task-role class (causal path, backdoor, composite, other task-zone), distance/location, alternative path count, reachability change, ancestor change, within-path co-errors, initial error burden, and edit feasibility. Record zero support explicitly; do not impute unsupported categories as zero effect.

Separate predictors available to a feasible policy from oracle diagnostics. Reference-relative error class, true path/effect, true optimal action, and realized regret require benchmark truth and must not be policy inputs. Observable graph features may be considered for policy design only after independent confirmation.

Use descriptive SCM-clustered summaries first. If there is adequate support, a prespecified hierarchical model may estimate associations with SCM random intercepts and cluster-robust uncertainty. Sparse cells, collinearity, and small opportunity-rich sample counts may make model estimates unstable; in that case report distributions and intervals, not adjusted causal effects. Error-class means are not causal effects of changing an error type.

S3-completion coverage: candidate-level realized Regret gains and score gains were retained for 203 feasible edit rows and summarized within SCM for ranking. The broader requested structural-role covariates above were not included in the completion-v3 public schema and have not been modeled. Therefore this document is a mechanism-analysis framework, not a completed answer to which causal factor explains value.
