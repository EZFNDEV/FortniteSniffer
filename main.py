import os
import time
import auth
import dpkt
import json
import socket
import requests
from logs import *
from threading import Thread

if os.path.exists('sessions.json'):
    sessions = json.loads(open('sessions.json').read())
else:
    sessions = {}

def inet_to_str(inet):
    try:
        return socket.inet_ntop(socket.AF_INET, inet)
    except ValueError:
        return socket.inet_ntop(socket.AF_INET6, inet)

def log_sessions():
    token = auth.get_auth_token()
    build_version = get_build_verion()
    while True:
        print('Waiting, please start a (new) Match')
        server_address, server_port, account_id, session_id = wait_for_session_start()
        encryption_key = auth.get_encryption_key(session_id, account_id, token)
        session_info = auth.get_session_info(session_id, token)
        playlist = session_info['attributes']['PLAYLISTNAME_s']
        buildUniqueId = session_info['buildUniqueId']
        sessions[session_id] = {
            'EncryptionKey': encryption_key['key'],
            'ServerAddress': server_address,
            'ServerPort': int(server_port), # Useful so we can later filter the packets
            'SessionID': session_id,
            'Playlist': playlist,
            'buildUniqueId': buildUniqueId,
            'BuildVersion': build_version,
            'SavedPackets': False
        }
        open('sessions.json', 'w+').write(json.dumps(sessions, indent=2))
        print(f'Added new session (Server Address: {server_address}, Server Port: {server_port}, EncryptionKey: {encryption_key["key"]}, SessionID: {session_id}, PlaylistID: {playlist})')

def read_pcap():
    print('Reading the pcap file...')
    packets = []
    server_addresses = [session['ServerAddress'] for session in list(sessions.values())]
    for _, pkt in dpkt.pcap.Reader(open(pcap_path, 'rb')):
        eth = dpkt.ethernet.Ethernet(pkt) 
        if eth.type != dpkt.ethernet.ETH_TYPE_IP:
            continue

        src = inet_to_str(eth.data.src)
        dst = inet_to_str(eth.data.dst)
        if dst in server_addresses or src in server_addresses:
            payload = pkt.hex()[42 * 2:] # Skip to the UDP Payload
            if payload.endswith('000000000000'):
                payload = payload[:-len("000000000000")]
            
            if not src in server_addresses:
                packets.append({'from_server': False, 'payload': payload, 'dst_port': eth.data.data.dport, 'src_port': eth.data.data.sport, 'src': src, 'dst': dst})
            else:
                packets.append({'from_server': True, 'payload': payload, 'dst_port': eth.data.data.dport, 'src_port': eth.data.data.sport, 'src': src, 'dst': dst})

    filter_packets(packets)

def filter_packets(packets):
    # Filter the packets
    for session in sessions.values():
        if session['SavedPackets']:
            continue

        s_packets = []
        for packet in packets:
            if (packet['dst_port'] == session['ServerPort'] or packet['src_port'] == session['ServerPort']) and (packet['src'] == session['ServerAddress'] or packet['dst'] == session['ServerAddress']):
                # if len(s_packets) == 0 and packet['payload'] != '1700000000000000000000000000000000000000000000000000000080': # Doubt that anyone has older packets...
                #     session['SavedPackets'] = False
                #     print(f'Invalid Packets for {session["SessionID"]}!')
                #     break

                s_packets.append({
                    'from_server': packet['from_server'],
                    'payload': packet['payload']
                })

        if len(s_packets) > 0:
            open(f'Packets/{session["SessionID"]}.json', 'w+').write(json.dumps(s_packets))
            session['SavedPackets'] = True
            print(f'Saved Packets ({len(s_packets)}) for {session["SessionID"]}')

if not os.path.exists('Packets'):
    os.mkdir('Packets')

# Log the session
session_log = Thread(target=log_sessions)   
session_log.start()

pcap_path = input('Enter the PCAP path when you are done.\n')
if not (os.path.exists(pcap_path)):
    raise Exception('Could not find the file.')

# Start reading the pcap
read_pcap()

open('sessions.json', 'w+').write(json.dumps(sessions, indent=2))
input('Sucessfully added the packets to the sessions!')
os._exit(1)