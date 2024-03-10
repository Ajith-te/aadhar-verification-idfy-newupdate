import uuid

def generate_id():
    return str(uuid.uuid4())[:8] + '-' + str(uuid.uuid4())[:4] + '-' + str(uuid.uuid4())[:4] + '-' + str(uuid.uuid4())[:4] + '-' + str(uuid.uuid4())[:12]
