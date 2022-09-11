# -*- coding: utf-8 -*-
import logging
import os
import sys

element_table = {
    'H':    1,  'He':   2,  'Li':   3,  'Be':   4,  'B':    5,
    'C':    6,  'N':    7,  'O':    8,  'F':    9,  'Ne':  10,
    'Na':  11,  'Mg':  12,  'Al':  13,  'Si':  14,  'P':   15,
    'S':   16,  'Cl':  17,  'Ar':  18,  'K':   19,  'Ca':  20,
    'Sc':  21,  'Ti':  22,  'V':   23,  'Cr':  24,  'Mn':  25,
    'Fe':  26,  'Co':  27,  'Ni':  28,  'Cu':  29,  'Zn':  30,
    'Ga':  31,  'Ge':  32,  'As':  33,  'Se':  34,  'Br':  35,
    'Kr':  36,  'Rb':  37,  'Sr':  38,  'Y':   39,  'Zr':  40,
    'Nb':  41,  'Mo':  42,  'Tc':  43,  'Ru':  44,  'Rh':  45,
    'Pd':  46,  'Ag':  47,  'Cd':  48,  'In':  49,  'Sn':  50,
    'Sb':  51,  'Te':  52,  'I':   53,  'Xe':  54,  'Cs':  55,
    'Ba':  56,  'La':  57,  'Ce':  58,  'Pr':  59,  'Nd':  60,
    'Pm':  61,  'Sm':  62,  'Eu':  63,  'Gd':  64,  'Tb':  65,
    'Dy':  66,  'Ho':  67,  'Er':  68,  'Tm':  69,  'Yb':  70,
    'Lu':  71,  'Hf':  72,  'Ta':  73,  'W':   74,  'Re':  75,
    'Os':  76,  'Ir':  77,  'Pt':  78,  'Au':  79,  'Hg':  80,
    'Tl':  81,  'Pb':  82,  'Bi':  83,  'Po':  84,  'At':  85,
    'Rn':  86,  'Fr':  87,  'Ra':  88,  'Ac':  89,  'Th':  90,
    'Pa':  91,  'U':   92,  'Np':  93,  'Pu':  94,  'Am':  95,
    'Cm':  96,  'Bk':  97,  'Cf':  98,  'Es':  99,  'Fm': 100,
    'Md': 101,  'No': 102,  'Lr': 103,  'Rf': 104,  'Db': 105,
    'Sg': 106,  'Bh': 107,  'Hs': 108,  'Mt': 109,  'Ds': 110,
    'Rg': 111,  'Cn': 112,  'Nh': 113,  'Fl': 114,  'Mc': 115,
    'Lv': 116,  'Ts': 117,  'Og': 118
}
element_table2 = {}
for ikey in element_table.keys():
    element_table2[element_table[ikey]] = ikey


def read_init_xyz(file):
    element_xyz = []
    # logger.info("Supported input filetype, gjf, com, xyz, chk")
    filename, file_extension = os.path.splitext(file)
    if file_extension in [".gjf", ".com", ".xyz"]:
        with open(file, "r") as filea:
            iatom = 1
            for icol in filea:
                icol = icol.split()
                if (len(icol) == 4):
                    if (icol[0].isalpha()):
                        try:
                            iel_xyz = [icol[0]] + [float(ix) for ix in icol[1:]]
                            element_xyz.append(iel_xyz)
                            # logger.info(f"Read coordinate of atom {iatom}, {iel_xyz}")
                            iatom = iatom + 1
                        except:
                            pass
    elif file_extension in [".log", ".out"]:
        with open(file, "r") as file:
            logs = file.readlines()
            chk_converge = logs[-1].split()
            assert ["Normal", "termination"] == chk_converge[:2], f"Not converged"
            line_idx = [idx for idx in range(len(logs))
                        if "Coordinates" in logs[idx].split(" ")][-1] + 3
            for iline in logs[line_idx:]:
                if iline.startswith(" ----"):
                    break
                else:
                    atomic_sym = element_table2[int(iline.split()[1])]
                    x, y, z = iline.split()[3:]
                    element_xyz.append([atomic_sym] +
                                       [float(x), float(y), float(z)])
    elif file_extension in [".chk"]:
        element_xyz = 'read_chk'
    return element_xyz


def make_opt_input(element_xyz, multiplicity, name, dump_dir=None, charge=0,
                   functional="b3lyp", basis='6-31G**',
                   pseudo_basis="Lanl2DZ", nproc=16, mem=60):
    assert name in ["s0-opt", "t1-opt"], "job type wrong"
    elems = set([ielems[0] for ielems in element_xyz])
    heavymetals = ["Ir", "Pt", "Os"]
    metal = set(heavymetals).intersection(elems)
    elems = list(elems - metal)
    elems = " ".join(elems)
    assert len(metal) == 1, f"Heavy metals {heavymetals} not detected or more than 1"
    chk = name
    if dump_dir is None:
        dump_dir = "./s0-opt" if multiplicity == 1 else './t1-opt'
    keywords = f"opt freq {functional}/gen pseudo=read"
    if element_xyz == 'read_chk':
        keywords = f"opt freq {functional}/gen pseudo=read geom=chk"
    chkkeywords = f'%chk={chk}.chk'
    nprockeywords = f'%nproc={nproc}'
    memkeywords = f'%mem={mem}gb'
    titlekeywords = 'OLED project'
    chargekeywords = f'{charge} {multiplicity}'
    buff = [chkkeywords, nprockeywords, memkeywords, '# {}'.format(keywords), '', titlekeywords, '', chargekeywords]
    if element_xyz != 'read_chk':
        for ixyz in element_xyz:
            buff.append(f"{ixyz[0]} {ixyz[1]} {ixyz[2]} {ixyz[3]}")
    buff.append('')
    pseudo_element = metal.pop()
    other_element = elems
    buff.append('%s 0' % (pseudo_element))
    buff.append(pseudo_basis)
    buff.append('****')
    buff.append('%s 0' % (other_element))
    buff.append(basis)
    buff.append('****')
    buff.append('')
    buff.append('%s 0' % (pseudo_element))
    buff.append(pseudo_basis)
    buff.append('\n')
    output = "\n".join(buff)
    if name == "s0-opt":
        with open(f"{dump_dir}/s0-opt.com", "w") as text_file:
            text_file.write("%s" % output)
    elif name == "t1-opt":
        with open(f"{dump_dir}/t1-opt.com", "w") as text_file:
            text_file.write("%s" % output)


def make_tda_input(t1log, dump_dir='tda', nproc=16, mem=60, basis='6-31G**', pseudo_basis="Lanl2DZ"):
    element_xyz = read_init_xyz(t1log)
    elems = set([ielems[0] for ielems in element_xyz])
    heavymetals = ["Ir", "Pt", "Os"]
    metal = set(heavymetals).intersection(elems)
    elems = list(elems - metal)
    elems = " ".join(elems)
    assert len(metal) == 1, f"Heavy metals {heavymetals} not detected or more than 1"
    chkkeywords = '%chk=t1-tda.chk'
    nprockeywords = f'%nprocshared={nproc}'
    memkeywords = f'%mem={mem}gb'
    titlekeywords = 't1TDA'
    chargekeywords = '0 1'
    keywords = "TDA(triplet,NStates=3,Root=1) PBEpbe/gen IOP(3/76=1000003333) Iop(3/77=0666706667)  pseudo=read geom=chk"
    buff = [chkkeywords, nprockeywords, memkeywords, '# {}'.format(keywords), '', titlekeywords, '', chargekeywords]
    pseudo_element = metal.pop()
    other_element = elems
    buff.append('%s 0' % (pseudo_element))
    buff.append(pseudo_basis)
    buff.append('****')
    buff.append('%s 0' % (other_element))
    buff.append(basis)
    buff.append('****')
    buff.append('')
    buff.append('%s 0' % (pseudo_element))
    buff.append(pseudo_basis)
    buff.append('\n')
    output = "\n".join(buff)
    with open(f"{dump_dir}/t1-tda.com", "w") as text_file:
        text_file.write("%s" % output)


def make_edme_input(element_xyz, dump_dir="edme"):
    make_opt_input(element_xyz, 3, "t1-opt", dump_dir)
    python_path = sys.executable
    os.system(f"{python_path} gjf2mol.py {dump_dir}/t1-opt.com")
    with open(f"{dump_dir}/t1-opt.mol", "r") as file:
        mols = file.readlines()
        metal_idx = [idx for idx in range(len(mols))
                     if len(set(["Ir", "Pt", "Os"]).intersection(mols[idx].strip().split(" ")))==1]
        if len(metal_idx) == 1:
            line_i = mols[metal_idx[0]-1]
            line_i = line_i.strip().split(" ")[:2]
            line_i.append("Basis=lanl2dz_ecp ECP=lanl2dz_ecp\n")
            mols[metal_idx[0]-1] = " ".join(line_i)
        else:
            # logger.error("Heavy metal Ir, Pt, Os not found")
            assert False
    with open(f"{dump_dir}/t1-opt.mol", "w") as file:
        file.writelines(mols)


def make_soc_input(element_xyz, dump_dir='soc'):
    elems = set([ielems[0] for ielems in element_xyz])
    heavymetals = ["Ir", "Pt", "Os"]
    metal = set(heavymetals).intersection(elems)
    metal = metal.pop()
    with open(f"{dump_dir}/soc.inp", "w") as file:
        inps = ["! B3LYP ZORA ZORA-def2-SVP SARC/J RI-SOMF(1X) nopop\n",
                "%tddft\n", "nroots 25\n", "dosoc true\n", "tda false\n", "end\n",
                f"%basis newgto {metal} \"SARC-ZORA-SVP\" end\n", "end\n", "* xyz 0 1\n"]
        for ixyz in element_xyz:
            inps.append(f"{ixyz[0]} {ixyz[1]} {ixyz[2]} {ixyz[3]}\n")
        inps.append("end")
        file.writelines(inps)
