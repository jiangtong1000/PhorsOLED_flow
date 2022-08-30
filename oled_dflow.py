# -*- coding: utf-8 -*-
from dflow import config, s3_config
from dflow.plugins.lebesgue import LebesgueContext
from dflow.python import (
    PythonOPTemplate,
    OP,
    OPIO,
    OPIOSign,
    Artifact,
)
from dflow import (
    InputParameter,
    OutputParameter,
    InputArtifact,
    OutputArtifact,
    upload_artifact,
    download_artifact,
    Workflow,
    Step,
    Steps
)
from pathlib import Path
from glob import glob
import time
import os
import sys
config["host"] = "http://39.106.93.187:32746"
config["k8s_api_server"] = "https://101.200.186.161:6443"
config["token"] = "eyJhbGciOiJSUzI1NiIsImtpZCI6IlhMRGZjbnNRemE4RGQyUXRMZG1MX3NXeG5TMzlQTnhnSHZkS1lGM25SODAifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJhcmdvIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6ImFyZ28tdG9rZW4tOGY4djkiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC5uYW1lIjoiYXJnbyIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6IjBhNzI1N2JhLWZkZWQtNGI2OS05YWU2LTZhY2U0M2UxNjdlNiIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDphcmdvOmFyZ28ifQ.ocRNsp_sdjM7dKpg_rYwPOKATslbDebDo807rkaVcqOScFKl11tqHbCwsekq4BZSEw-MaZjWAVsdE5jgvqIggp2qczx1QPMkBGQzkPwR4h7HbxYPUKIHkjlcvtsl06jf7urfzARUiD_UTahEFQLkUeN800Qblp-zMFBNLF2Y7_wW867drmQxynG1ssQ8agdu7yDZpwwJz-qzMMZsuZ7QNtL0pPQP2Iw_5C6jlos-Al1m3bgUJ5phh7yt-PBqwnMwEPaZWkVy9zFJc5t4J0jFc9nRnrR8fEd_OgJTTgQjHxS2DyXj9ZRUlGJA-tmHGqIJ7nuScv3lKwbb8TkeABq5DA"
s3_config["endpoint"] = "39.106.93.187:30900"


class Gaussianop(OP):
    def __init__(self, name):
        self.name = name

    @classmethod
    def get_input_sign(cls):
        return OPIOSign({"input": Artifact(Path)})

    @classmethod
    def get_output_sign(cls):
        return OPIOSign({"output": Artifact(Path)})

    @OP.exec_sign_check
    def execute(self, op_in: OPIO) -> OPIO:
        pydir = str(op_in["input"])
        sys.path.append(pydir)
        import input_gen
        if self.name in ["s0-opt", "t1-opt"]:
            worksh = ["#bin/bash\n", "\n",
                      "source /root/g16.sh\n",
                      f"g16 {self.name}.com"]
        elif self.name == "soc":
            worksh = ["export PATH=/root/soft/openmpi/bin:\$PATH\n",
                      "export LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:/root/soft/openmpi/lib\n",
                      "export LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:/root/soft/orca\n",
                      "export PATH=\$PATH:/root/soft/orca\n", "\n",
                      "orca soc.inp > soc.out"]
        elif self.name == "edme":
            worksh = ["#!/bin/bash\n",
                      "source /opt/intel/oneapi/setvars.sh\n",
                      "dalton edme t1-opt | tee log.txt"]
        os.chdir(op_in["input"])

        if self.name == "s0-opt":
            comfile = glob("*.com") + glob("*.gjf")
            assert len(comfile) == 1, f"more than 1 gjf detected"
            xyz_file = comfile[0]
        elif self.name == "t1-opt":
            xyz_file = "s0-opt.log"
        elif self.name in ["soc", "edme"]:
            xyz_file = "t1-opt.log"
        element_xyz = input_gen.read_init_xyz(xyz_file)
        if self.name in ["s0-opt", "t1-opt"]:
            multiplicity = 1 if self.name == "s0-opt" else 3
            input_gen.make_opt_input(element_xyz, multiplicity, self.name, ".")
        elif self.name == "edme":
            input_gen.make_edme_input(element_xyz, ".")
        elif self.name == "soc":
            input_gen.make_soc_input(element_xyz, ".")
        with open("work.sh", "w") as f:
            f.writelines(worksh)
        os.system("bash work.sh")
        return OPIO({
            "output": op_in["input"]
        })


def main():
    image_dic = {
        "s0-opt": "LBG_Gaussian_1_v2",
        "t1-opt": "LBG_Gaussian_1_v2",
        "edme": "LBG_Dalton_1_v1",
        "soc": "LBG_Orca_1_v2"
    }
    lebesgue_context = LebesgueContext(
        username="",
        password="",
        executor="lebesgue_v2",
        extra={
                "scass_type": "c32_m64_cpu",
                "program_id": 10181,
        },
    )

    wf = Workflow(name="batch", context=lebesgue_context, host="http://39.106.93.187:32746")
    property_steps = []

    for file in glob("mol*"):
        mol_idx = file.split("mol")[1]
        steps = Steps(f"mol{mol_idx}")
        os.system(f"cp edme.dal {file}; cp gjf2mol.py {file}; cp input_gen.py {file}")
        s0op = PythonOPTemplate(Gaussianop("s0-opt"), image=image_dic["s0-opt"], command=["python3"])
        s0op.outputs.parameters["job_id"] = OutputParameter(value_from_path="/tmp/executor_info/job_id")
        s0op.outputs.artifacts["job_id"] = OutputArtifact("/tmp/executor_info")
        S0_Opt = Step(
            f"{mol_idx}-s0-opt",
            s0op,
            artifacts={"input": upload_artifact([f"{file}"])},
        )

        t1op = PythonOPTemplate(Gaussianop("t1-opt"), image=image_dic["t1-opt"], command=["python3"])
        t1op.outputs.parameters["job_id"] = OutputParameter(value_from_path="/tmp/executor_info/job_id")
        t1op.outputs.artifacts["job_id"] = OutputArtifact("/tmp/executor_info")
        T1_Opt = Step(
            f"{mol_idx}-t1-opt",
            t1op,
            artifacts={"input": S0_Opt.outputs.artifacts["output"]},
        )

        socop = PythonOPTemplate(Gaussianop("soc"), image=image_dic["soc"], command=["python3"])
        socop.outputs.parameters["job_id"] = OutputParameter(value_from_path="/tmp/executor_info/job_id")
        socop.outputs.artifacts["job_id"] = OutputArtifact("/tmp/executor_info")
        soc = Step(
            f"{mol_idx}-soc",
            socop,
            artifacts={"input": T1_Opt.outputs.artifacts["output"]},
        )
        edmeop = PythonOPTemplate(Gaussianop("edme"), image=image_dic["edme"], command=["python3"])
        edmeop.outputs.parameters["job_id"] = OutputParameter(value_from_path="/tmp/executor_info/job_id")
        edmeop.outputs.artifacts["job_id"] = OutputArtifact("/tmp/executor_info")
        edme = Step(
            f"{mol_idx}-edme",
            edmeop,
            artifacts={"input": T1_Opt.outputs.artifacts["output"]},
        )

        steps.add(S0_Opt)
        steps.add(T1_Opt)
        # steps.add([soc, edme])
        steps.add([soc])
        step = Step(f"mol{mol_idx}", steps)

        property_steps.append(step)

    wf.add(property_steps)
    wf.submit()
    # while wf.query_status() in ["Pending","Running"]:
    #     time.sleep(4)
    # assert(wf.query_status() == 'Succeeded')
    # step = wf.query_step(name="sp")[0]
    # download_artifact(step.outputs.artifacts["output"])


if __name__ == "__main__":
    main()
