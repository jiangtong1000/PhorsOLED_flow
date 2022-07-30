# Workflow for Phorsphorescent OLED Metal Complexe Molecules

- The workflow is supported by [dflow](https://github.com/deepmodeling/dflow), a Python framework for constructing scientific computing workflows.

- Current workdflow is designed for [Bohrium](https://bohrium.dp.tech/), a cloud computing service platform with out-of-the-box feature. 

- Users should modify the `oled_dflow.py` if using `Slurm` in your own PC or HPC cluster, examples will be provided in the future.

- The Borium users should firstly config the username and password in `oled_dflow.py`:

  ```python
  lebesgue_context = LebesgueContext(
                username="Bohrium username",
                password="Bohrium password",
  ```
  
  Your database should contain folders named as `mol1, mol2, mol3,...` that contains the molecular structure (`.gjf`) in each of it.

  ```bash
  conda activate your-dflow-environment
  git clone https://github.com/jiangtong1000/PhorsOLED_workflow.git
  cd PhorsOLED_workflow
  cp -r your_database .
  python oled_dflow.py
  ```
  
  and it carries out the following steps automatically.
  
  ```mermaid
    graph
   T[Workflow] --> E
   T-->E2
  E[mol1] -->|Gaussian|F(optimize s0)
  F -->|Gaussian|A{optimize t1}
  A -->|Dalton|B(oscilator strength)
  A -->|ORCA|C(spin-orbit coupling)
  B -->D{Outputs}
  C --> D
  A --> D
  F --> D{All Parameters}
  D -->|MOMAP| G{decay rate, PLQY}
  E2[mol2] -->|Gaussian|F2(optimize s0)
  F2 -->|Gaussian|A2{optimize t1}
  A2 -->|Dalton|B2(oscilator strength)
  A2 -->|ORCA|C2(spin-orbit coupling)
  B2 -->D2{Outputs}
  C2 --> D2
  A2 --> D2
  F2 --> D2{All Parameters}
  D2 -->|MOMAP| G2{decay rate, PLQY}
   T[Workflow] --> E3(mol3)
   E3[mol3] -->|Gaussian|F3(optimize s0)
  F3 -->|Gaussian|A3{optimize t1}
  A3 -->|Dalton|B3(oscilator strength)
  A3 -->|ORCA|C3(spin-orbit coupling)
  B3 -->D3{Outputs}
  C3 --> D3
  A3 --> D3
  F3 --> D3{All Parameters}
  D3 -->|MOMAP| G3{decay rate, PLQY}
     T[Workflow] --> E4(...)
  ```
