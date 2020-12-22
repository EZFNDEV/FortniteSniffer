import os, time

def wait_for_session_start():
    log_path = f'C:\\Users\\' + os.getlogin() + '\\AppData\\Local\\FortniteGame\\Saved\\Logs\\FortniteGame.log'
    if not os.path.exists(log_path):
        raise Exception('Could not find the Fortnite logs')

    file = open(log_path)
    file.seek(os.path.getsize(log_path)) # Skip to the end
    while True:
        pos = file.tell()
        line = file.readline()
        if not line:
            time.sleep(1)
        else:
            if 'LogNet: Browse: ' in line and not 'LogNet: Browse: /Game/Maps/Frontend?closed' in line and 'EncryptionToken' in line:
                server_address = line.split('LogNet: Browse: ')[1].split(':')[0].strip('\n')
                server_port = line.split('LogNet: Browse: ')[1].split(':')[1].split('/')[0].strip('\n')
                account_id = line.split('EncryptionToken=')[1].split(':')[0].strip('\n')
                session_id = line.split('EncryptionToken=')[1].split(':')[1].strip('\n')

                return server_address, server_port, account_id, session_id

def get_build_verion():
    log_path = f'C:\\Users\\' + os.getlogin() + '\\AppData\\Local\\FortniteGame\\Saved\\Logs\\FortniteGame.log'
    if not os.path.exists(log_path):
        raise Exception('Could not find the Fortnite logs')
    
    try:
        lines = open(log_path).readlines()
    except:
        lines = open(log_path, 'rb').read().decode('utf8').split('\r\n')
    
    for line in lines[1:]:
        # Get the "CategoryName"
        if line.split(':')[0].startswith('[20'):
            CategoryName = line.split(']')[2].split(':')[0]
        else:
            CategoryName = line.split(':')[0]
        
        # This does not always exist
        try:
            LogSubType = line.split(':')[1].strip()
            Result = ':'.join(line.split(':')[2:]).strip()
        except Exception as e:
            LogSubType = ""
            Result = ""
            
        # Get by CategoryName
        if CategoryName == 'LogInit':
            if LogSubType == 'Build':
                return Result