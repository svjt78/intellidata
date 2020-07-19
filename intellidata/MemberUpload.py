import csv
from MemberUploadHelper import BulkCreateManager

with open('members.csv', 'rb') as csv_file:
    bulk_mgr = BulkCreateManager(chunk_size=20)
    for row in csv.reader(csv_file):
        bulk_mgr.add(MyModel(attr1=row['attr1'], attr2=row['attr2']))
    bulk_mgr.done()
