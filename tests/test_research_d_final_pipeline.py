import unittest

import numpy as np

from research.external_validation.semisynthetic_final import final_analyze as analysis
from research.external_validation.semisynthetic_final import final_pipeline as final


class ResearchDFinalPipelineTests(unittest.TestCase):
    def test_locked_final_contract_and_seed_schedule(self):
        c=final.contract()
        self.assertEqual(c["status"],"LOCKED_FOR_FINAL_EVALUATION")
        self.assertEqual(c["sample"]["g0_ids"],list(range(703001,703201)))
        self.assertEqual(len(set(c["task"]["actions"])),5)
        self.assertEqual(c["sample"]["evaluation_rows_per_action"]*5,12500)
        self.assertFalse(c["sample"]["g0_ids"]==list(range(702001,702033)))

    def test_final_seed_domains_are_deterministic_and_separate(self):
        labels=[*[f"g0|{x}" for x in final.g0_seed_ids()],
            *[f"action|{i}|{repr(float(a))}" for i,a in enumerate(final.contract()["task"]["actions"])],
            "bootstrap|primary-two-source","bootstrap|m4-vs-fullgreedy",
            "bootstrap|paired-cost","resource-benchmark"]
        seeds=[final.derive_final_seed(x) for x in labels]
        self.assertEqual(seeds,[final.derive_final_seed(x) for x in labels])
        self.assertEqual(len(seeds),len(set(seeds)))
        self.assertTrue(all(0<=x<2**32 for x in seeds))

    def test_chunked_shared_action_loss_bootstrap_is_reproducible(self):
        actions=[0.1,0.2,0.3]
        rec={"g0_seed_ids":[1,2,3],"recommendations":[]}
        for sid, pair in zip(rec["g0_seed_ids"],[(0,0),(1,1),(2,0)]):
            for policy, ix in (("S0",pair[0]),("M1+M2+M3+M4",pair[1])):
                rec["recommendations"].append({"g0_seed_id":sid,"budget":2,
                    "policy_id":policy,"recommended_action":actions[ix]})
        vectors=[np.asarray([0.2,0.1,0.4,0.3]),np.asarray([0.5,0.4,0.6,0.3]),
                 np.asarray([0.3,0.7,0.5,0.6])]
        first=analysis.paired_bootstrap(vectors,actions,rec,0.4,0.2,reps=256,seed=813,chunk=32)
        second=analysis.paired_bootstrap(vectors,actions,rec,0.4,0.2,reps=256,seed=813,chunk=32)
        self.assertEqual(first,second)
        self.assertEqual(first["replicates"],256)
        self.assertEqual(first["chunk_replicates"],32)
        self.assertTrue(first["two_source_95"][0] <= first["two_source_95"][1])

    def test_same_recommendation_has_zero_paired_loss_contrast(self):
        actions=[0.1,0.2]
        rec={"g0_seed_ids":[1,2],"recommendations":[]}
        for sid in rec["g0_seed_ids"]:
            for policy in ("S0","M1+M2+M3+M4"):
                rec["recommendations"].append({"g0_seed_id":sid,"budget":2,
                    "policy_id":policy,"recommended_action":0.1})
        vectors=[np.asarray([1.0,2.0,1.5]),np.asarray([2.0,3.0,2.5])]
        result=analysis.paired_bootstrap(vectors,actions,rec,1.4,0.7,reps=128,seed=55,chunk=32)
        self.assertEqual(result["primary_point"],0.0)
        self.assertEqual(result["two_source_95"],[0.0,0.0])

    def test_policy_engine_rate_report_reconstructs_integer_error_counts(self):
        report={"M1":{"numerator":2},"M2":{"numerator":3},
            "M3_accuracy":{"numerator":5,"denominator":7},
            "M3_unresolved":{"numerator":1},
            "M4":{k:{"numerator":i} for i,k in enumerate(("FN","FP","REV","UNRES"),1)}}
        self.assertEqual(analysis.error_counts_from_report(report),{
            "M1_FN":2,"M2_FP":3,"M3_REV":2,"M3_UNRES":1,
            "M4_FN":1,"M4_FP":2,"M4_REV":3,"M4_UNRES":4})


if __name__=="__main__":
    unittest.main()
