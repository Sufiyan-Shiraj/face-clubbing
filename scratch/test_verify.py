import re
import json

report = open('REPORT.md', encoding='utf-8').read()
sec12_10_part = report.split('### 12.10')[1].split('### 12.11')[0]
neg = json.load(open('scratch/negative_distribution.json'))

row_pattern = re.compile(r'\|\s*\*\*\$\\le\s+([\d\.]+)\$\*\*\s*\|\s*\*\*(\d+)\*\*[^\(]*\([^\)]*\)\s*\|\s*\*\*(\d+)\*\*[^\(]*\([^\)]*\)\s*\|\s*(\d+)\s*\|')
matches = row_pattern.findall(sec12_10_part)
print('Found 12.10 rows:', len(matches))
assert len(matches) == 7
for t_str, std_c, flp_c, tot in matches:
    t_key = str(float(t_str))
    assert int(std_c) == neg['thresholds'][t_key]['standard_count']
    assert int(flp_c) == neg['thresholds'][t_key]['flip_count']
    assert int(tot) == neg['total_pairs']
print('Check 12.10 PASSED!')

sec12_11_part = report.split('### 12.11')[1].split('### 12.12')[0]
rec = json.load(open('scratch/recall_false_pairs_report.json'))
rec_by_t = {row['threshold']: row for row in rec['table']}

row11_pattern = re.compile(r'\|\s*\*\*\$\\le\s+([\d\.]+)\$\*\*\s*\|\s*[\*]*(\d+)\s*\/\s*(\d+)[^|]*\|\s*[\*]*(\d+)\s*\/\s*(\d+)[^|]*\|\s*[\*]*(\d+)\s*\/\s*(\d+)[^|]*\|\s*[\*]*(\d+)\s*\/\s*(\d+)[^|]*\|')
matches11 = row11_pattern.findall(sec12_11_part)
print('Found 12.11 rows:', len(matches11))
assert len(matches11) == 7
for t_str, s_rc, s_rt, s_fc, s_ft, f_rc, f_rt, f_fc, f_ft in matches11:
    t_val = round(float(t_str), 2)
    row_data = rec_by_t[t_val]
    print(t_str, s_rc, s_rt, s_fc, s_ft, f_rc, f_rt, f_fc, f_ft)
    assert int(s_rc) == row_data['true_recall_std_count']
    assert int(s_rt) == rec['total_true_pairs']
    assert int(s_fc) == row_data['false_pairs_std_count']
    assert int(s_ft) == rec['total_neg_pairs']
    assert int(f_rc) == row_data['true_recall_flip_count']
    assert int(f_rt) == rec['total_true_pairs']
    assert int(f_fc) == row_data['false_pairs_flip_count']
    assert int(f_ft) == rec['total_neg_pairs']
print('Check 12.11 PASSED!')

sec12_12_part = report.split('### 12.12')[1].split('### 12.13')[0]
flp = json.load(open('scratch/flip_average_full_experiment_results.json'))

c_m = re.search(r'\*\*Total Person Clusters\*\*\s*\|\s*(\d+)\s*\|\s*\*\*(\d+)\*\*', sec12_12_part)
s_m = re.search(r'\*\*Singletons\*\*\s*\|\s*(\d+)[^|]*\|\s*\*\*(\d+)[^|]*\*\*', sec12_12_part)
uf_m = re.search(r'\*\*Unrecognized Faces\*\*\s*\|\s*(\d+)\s*\|\s*\*\*(\d+)\*\*', sec12_12_part)
up_m = re.search(r'\*\*Unrecognized Photos\*\*\s*\|\s*(\d+)\s*\|\s*\*\*(\d+)\*\*', sec12_12_part)
col_m = re.search(r'\*\*Collision Clusters\*\*\s*\|\s*(\d+)[^|]*\|\s*\*\*(\d+)[^|]*\*\*', sec12_12_part)
ex_m = re.search(r'\*\*Extra Collision Faces\*\*\s*\|\s*(\d+)\s*\|\s*\*\*(\d+)\*\*', sec12_12_part)
gt50_m = re.search(r'\*\*Ground-Truth Pairs \$\\le 0\.50\$\*\*\s*\|\s*(\d+)\s*\/\s*(\d+)[^|]*\|\s*\*\*(\d+)\s*\/\s*(\d+)', sec12_12_part)
gt60_m = re.search(r'\*\*Ground-Truth Pairs \$\\le 0\.60\$\*\*\s*\|\s*(\d+)\s*\/\s*(\d+)[^|]*\|\s*\*\*(\d+)\s*\/\s*(\d+)', sec12_12_part)

print('12.12 c:', c_m.groups())
print('12.12 s:', s_m.groups())
print('12.12 uf:', uf_m.groups())
print('12.12 up:', up_m.groups())
print('12.12 col:', col_m.groups())
print('12.12 ex:', ex_m.groups())
print('12.12 gt50:', gt50_m.groups())
print('12.12 gt60:', gt60_m.groups())

assert int(c_m.group(2)) == flp['clusters']
assert int(s_m.group(2)) == flp['singletons']
assert int(uf_m.group(2)) == flp['unrecognized_faces']
assert int(up_m.group(2)) == flp['unrecognized_photos']
assert int(col_m.group(2)) == flp['colliding_clusters']
assert int(ex_m.group(2)) == flp['extra_faces']
assert int(gt50_m.group(3)) == flp['ground_truth_le_0_50']
assert int(gt60_m.group(3)) == flp['ground_truth_le_0_60']
print('Check 12.12 PASSED!')
