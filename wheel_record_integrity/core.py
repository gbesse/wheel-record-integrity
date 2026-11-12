import zipfile,io,csv,hashlib,base64
from pathlib import PurePosixPath
def run(data):
 if 'wheel_base64'in data:
  try:raw=base64.b64decode(data['wheel_base64'],validate=True)
  except Exception as e:raise ValueError('base64')from e
  if len(raw)>2000000:raise ValueError('archive_size')
  stream=io.BytesIO(raw)
 else:
  files=data['files']
  if not isinstance(files,dict)or len(files)>1000:raise ValueError('files')
  record='example-0.1.dist-info/RECORD';csvfile=io.StringIO();writer=csv.writer(csvfile);stream=io.BytesIO()
  with zipfile.ZipFile(stream,'w')as z:
   for name,text in files.items():
    if not isinstance(text,str)or len(text)>100000:raise ValueError('file')
    raw=text.encode();encoded=base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).decode().rstrip('=');writer.writerow([name,'sha256='+encoded,str(len(raw))]);z.writestr(name,raw+b'!'if data.get('tamper')==name else raw)
   writer.writerow([record,'','']);z.writestr(record,csvfile.getvalue())
  stream.seek(0)
 try:
  with zipfile.ZipFile(stream)as z:
   names=z.namelist()
   if len(names)!=len(set(names))or len(names)>10000 or sum(i.file_size for i in z.infolist())>16000000:raise ValueError('archive_budget_or_duplicates')
   if any(PurePosixPath(n).is_absolute()or'..'in PurePosixPath(n).parts for n in names):raise ValueError('path')
   records=[n for n in names if n.endswith('.dist-info/RECORD')]
   if len(records)!=1:raise ValueError('record_count')
   record=records[0];findings=[];listed=set()
   for row in csv.reader(io.StringIO(z.read(record).decode('utf8'))):
    if len(row)!=3 or row[0]in listed:raise ValueError('record_row')
    name,digest,size=row;listed.add(name)
    if name not in names:findings.append({'name':name,'code':'missing_file'});continue
    if name==record:
     if digest or size:findings.append({'name':name,'code':'record_self_hash'})
     continue
    if not digest.startswith('sha256='):findings.append({'name':name,'code':'unsupported_or_missing_hash'});continue
    raw=z.read(name);actual=base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).decode().rstrip('=')
    if actual!=digest[7:]:findings.append({'name':name,'code':'hash_mismatch'})
    if size!=str(len(raw)):findings.append({'name':name,'code':'size_mismatch'})
   for name in names:
    if name not in listed and not name.endswith(('/','RECORD.jws','RECORD.p7s')):findings.append({'name':name,'code':'unlisted_file'})
 except zipfile.BadZipFile as e:raise ValueError('bad_zip')from e
 return {'valid':not findings,'findings':findings,'listed_files':len(listed),'publisher_identity_authenticated':False}
