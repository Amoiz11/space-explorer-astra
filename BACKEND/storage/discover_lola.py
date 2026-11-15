import httpx
import re

url_float = 'https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/float_img/'
r = httpx.get(url_float, timeout=20)
print('--- FLOAT_IMG SOUTH POLAR LDEM ---')
for m in re.finditer(r'(\d+)\s+<A HREF="([^"]*?)">(ldem_[^"]*?\.img)</A>', r.text, re.I):
    size = int(m.group(1))
    fname = m.group(3)
    if 's_' in fname.lower() or '45s' in fname or '60s' in fname or '75s' in fname or '85s' in fname or '875s' in fname:
        print(f"{fname:30s} {size:12d} bytes ({size/(1024*1024):8.2f} MB)")

url_img = 'https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/'
r2 = httpx.get(url_img, timeout=20)
print('\n--- INT IMG SOUTH POLAR LDEM / LDEC ---')
for m in re.finditer(r'(\d+)\s+<A HREF="([^"]*?)">(ld[a-z]+_[^"]*?\.img)</A>', r2.text, re.I):
    size = int(m.group(1))
    fname = m.group(3)
    if '45s' in fname or '60s' in fname or '75s' in fname or '85s' in fname or '875s' in fname:
        print(f"{fname:30s} {size:12d} bytes ({size/(1024*1024):8.2f} MB)")
