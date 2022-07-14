import os
from glob import glob
import input_gen
import json
import sys

assert len(sys.argv) == 2

job_type = sys.argv[1]
image_dic = {"s0": "LBG_Gaussian_1_v2",
"t1": "LBG_Gaussian_1_v2",
"edme": "LBG_Dalton_1_v1",
"soc": "LBG_Orca_1_v2"}


task_json = {
    "job_name": "",
    "command": " bash work.sh",
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

sourcefiles = {"s0": "./*.gjf",
"t1": "*/s0_opt/s0_opt.log",
"edme": "*/t1_opt/t1_opt.log",
"soc": "*/t1_opt/t1_opt.log"}

if job_type in ["s0", "t1"]:
    worksh = ["#!/bin/bash\n", "\n"
        "source /opt/Miniconda/bin/activate\n",
        "source /root/g16.sh\n",
        f"g16 {job_type}_opt.com"]
elif job_type == "soc":
    worksh = ["export PATH=/root/soft/openmpi/bin:$PATH\n",
        "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/root/soft/openmpi/lib\n",
        "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/root/soft/orca\n"
        "export PATH=$PATH:/root/soft/orca\n", "\n",
        "orca soc.inp > soc.out"]
elif job_type == "edme":
    worksh = ["#!/bin/bash\n",
        "source /opt/intel/oneapi/setvars.sh\n",
        "dalton edme t1_opt | tee log.txt"]


for file in glob(sourcefiles[job_type]):
    filename, file_extension = os.path.splitext(file)
    if not os.path.exists(f"{filename}"):
        os.system(f"mkdir {filename}")
    os.system(f"mkdir {filename}/{job_type}")
    with open(f"{filename}/{job_type}/work.sh", "w") as f:
        f.writelines(worksh)
    task_json["job_name"] = f"{filename}_{job_type}"
    dump_dir = f"./{filename}/{job_type}/"
    element_xyz = gen.read_init_xyz(f"{file}")
    if job_type in ["s0", "t1"]:
        multiplicity = 1 if job_type == "s0" else 3
        input_gen.make_opt_input(file, multiplicity, dump_dir)
    elif job_type == "edme":
        input_gen.make_edme_input(file, dump_dir)
        os.system(f"cp edme.dal {dump_dir}")
    elif job_type == "soc":
        input_gen.make_soc_input(file, dump_dir)

    with open(f'{filename}/{filename}_{job_type}.json', 'w') as f:
        json.dump(task_json, f)
    os.system(f"lbg job submit -i {filename}/{filename}_{job_type}.json -p {filename}/{job_type} | tee {filename}/edme/log")
    with open(f"{filename}/{job_type}/log", "r") as filea:
        for line in filea:
            line = line.split(" ")
            if "ID:" in line:
                job_id[filename] = line[-1]
    with open(f'jobids_{job_type}.json', 'w') as f:
        json.dump(job_id, f)
