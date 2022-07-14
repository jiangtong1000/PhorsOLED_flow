import os
from glob import glob
import input_gen
import json
import sys

assert len(sys.argv) == 2
job_type = sys.argv[1]
image_dic = {
    "s0-opt": "LBG_Gaussian_1_v2",
    "t1-opt": "LBG_Gaussian_1_v2",
    "edme": "LBG_Dalton_1_v1",
    "soc": "LBG_Orca_1_v2"
}
task_json = {
    "job_name": "",
    "command": "bash work.sh",
    "log_file": "log",
    "backward_files": [],
    "job_group_id": "",
    "program_id": 10181,
    "image_name": image_dic[job_type],
    "machine_type": "c32_m64_cpu",
    "disk_size": 200,
    "platform": "ali"
}
job_id = {}
if job_type in ["s0-opt", "t1-opt"]:
    worksh = ["#bin/bash\n", "\n",
              "source /opt/Miniconda/bin/activate\n",
              "source /root/g16.sh\n",
              f"g16 {job_type}.com"]
elif job_type == "soc":
    worksh = ["export PATH=/root/soft/openmpi/bin:$PATH\n",
              "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/root/soft/openmpi/lib\n",
              "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/root/soft/orca\n",
              "export PATH=$PATH:/root/soft/orca\n", "\n",
              "orca soc.inp > soc.out"]
elif job_type == "edme":
    worksh = ["#!/bin/bash\n",
              "source /opt/intel/oneapi/setvars.sh\n",
              "dalton edme t1-opt | tee log.txt"]
for file in glob("*.gjf"):
    filename, file_extension = os.path.splitext(file)
    if not os.path.exists(f"{filename}"):
        os.system(f"mkdir {filename}")
    os.system(f"mkdir {filename}/{job_type}")
    with open(f"{filename}/{job_type}/work.sh", "w") as f:
        f.writelines(worksh)
    task_json["job_name"] = f"{filename}_{job_type}"
    dump_dir = f"./{filename}/{job_type}/"
    xyz_files = {"s0-opt": f"{filename}.gjf",
                 "t1-opt": f"{filename}/s0-opt/s0-opt.log",
                 "soc": f"{filename}/t1-opt/t1-opt.log",
                 "edme": f"{filename}/t1-opt/t1-opt.log"}
    element_xyz = input_gen.read_init_xyz(xyz_files[job_type])
    if job_type in ["s0-opt", "t1-opt"]:
        multiplicity = 1 if job_type == "s0-opt" else 3
        input_gen.make_opt_input(element_xyz, multiplicity, dump_dir)
    elif job_type == "edme":
        input_gen.make_edme_input(element_xyz, dump_dir)
        os.system(f"cp edme.dal {dump_dir}")
    elif job_type == "soc":
        input_gen.make_soc_input(element_xyz, dump_dir)

    with open(f'{filename}/{filename}_{job_type}.json', 'w') as f:
        json.dump(task_json, f)
    os.system(f"lbg job submit -i {filename}/{filename}_{job_type}.json -p {filename}/{job_type} | tee {filename}/{job_type}/log")
    with open(f"{filename}/{job_type}/log", "r") as filea:
        for line in filea:
            line = line.split(" ")
            if "ID:" in line:
                job_id[filename] = line[-1]
    with open(f'jobids_{job_type}.json', 'w') as f:
        json.dump(job_id, f)
