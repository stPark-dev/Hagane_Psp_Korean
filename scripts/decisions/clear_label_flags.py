"""Clear speaker-label flags explained by the EBOOT plate table (0x199890); mes_j labels were wrong."""
import glob, json
IDS = {'srt:M001_7:132', 'srt:M002_1:20', 'srt:M003_2_e:13', 'srt:M003_2_e:25', 'srt:M003_5:22',
       'srt:M007_1:335', 'srt:M008_3:20', 'srt:M011_1:186', 'srt:M011_1:187', 'srt:M011_1:188',
       'srt:M011_1:224', 'srt:M011_1:227', 'srt:M013_1:43', 'srt:M013_1:50', 'srt:M013_1:57',
       'srt:M013_1:197', 'srt:M013_1:216', 'srt:M013_3:15', 'srt:M013_3:16', 'srt:M014_1:124',
       'srt:M014_1:127', 'srt:M014_3:97', 'srt:M014_3:104', 'srt:M014_3:132'}
done = 0
for p in glob.glob('text/ko/srt/*.json'):
    d = json.load(open(p))
    if not any(e['id'] in IDS for e in d['entries']):
        continue
    d = {**d, 'entries': [({**e, 'flag': ''} if e['id'] in IDS else e) for e in d['entries']]}
    done += sum(e['id'] in IDS for e in d['entries'])
    json.dump(d, open(p, 'w'), ensure_ascii=False, indent=1)
print('cleared', done)
