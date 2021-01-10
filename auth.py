import io
import os
import json
import base64
import requests
import configparser

# I made this script a few months ago and yes, it sucks, but it works

def get_auth_token():
    GameUserSettingsPath = 'C:\\Users\\' + os.getlogin() + '\\AppData\\Local\\EpicGamesLauncher\\Saved\\Config\\Windows\\GameUserSettings.ini'
    config_text = open(GameUserSettingsPath).read()
    
    if 'Data=' in config_text:
        data = config_text.split('Data=')[1].split('\n')[0]
        old_data = data
        decoded_data = base64.b64decode(data).decode('ascii')
        decoded_data = json.loads(decoded_data)
        old_refresh_token = decoded_data[0]['Token']

    if old_refresh_token:
        data = requests.post('https://account-public-service-prod03.ol.epicgames.com/account/api/oauth/token',headers={'Authorization': 'basic MzRhMDJjZjhmNDQxNGUyOWIxNTkyMTg3NmRhMzZmOWE6ZGFhZmJjY2M3Mzc3NDUwMzlkZmZlNTNkOTRmYzc2Y2Y='},data={'token_type': 'eg1','grant_type': 'refresh_token','refresh_token': old_refresh_token}).json()

        if not 'refresh_token' in data:
            if data['errorCode'] == 'errors.com.epicgames.account.auth_token.invalid_refresh_token':
                raise Exception('Failed to authorize using the refresh token!')
            else:
                raise Exception(f"{data['errorCode']} bruh, what?")                

        new_refresh_token = data['refresh_token']
        new_data = decoded_data
        new_data[0]['Token'] = new_refresh_token
        new_data[0]['DisplayName'] = data['displayName']

        new_data = base64.b64encode(json.dumps(new_data).encode("utf-8")).decode("utf-8")

        config_text = config_text.replace(old_data, new_data)
        open(GameUserSettingsPath, 'w+').write(config_text)

        exchange_code = requests.get(f'https://account-public-service-prod.ol.epicgames.com/account/api/oauth/exchange',headers={'Authorization': f'bearer {data["access_token"]}','Content-Type': 'application/json'}).json()
        fn_access_token = requests.post(f'https://account-public-service-prod03.ol.epicgames.com/account/api/oauth/token',headers = {'Authorization': 'basic ZWM2ODRiOGM2ODdmNDc5ZmFkZWEzY2IyYWQ4M2Y1YzY6ZTFmMzFjMjExZjI4NDEzMTg2MjYyZDM3YTEzZmM4NGQ='},data = {'grant_type': 'exchange_code','token_type': 'bearer','exchange_code': exchange_code['code']}).json()
        return fn_access_token['access_token']
    else:
        raise Exception('No refresh token found!')

def get_encryption_key(session_id: str, account_id: str, token: str):
    r = requests.get(
        url = f'https://fortnite-public-service-prod11.ol.epicgames.com/fortnite/api/game/v2/matchmaking/account/{account_id}/session/{session_id}',
        headers = {
            'Authorization': f'bearer {token}',
            'User-Agent': 'Fortnite/++Fortnite+Release-14.60-CL-14786821 Windows/10.0.18363.1.256.64bit'
        }
    ).json()
    return r

def get_session_info(session_id: str, token: str):
    r = requests.get(
        url = f'https://fortnite-public-service-prod11.ol.epicgames.com/fortnite/api/matchmaking/session/{session_id}',
        headers = {
            'Authorization': f'bearer {token}',
            'User-Agent': 'Fortnite/++Fortnite+Release-14.60-CL-14786821 Windows/10.0.18363.1.256.64bit'
        }
    ).json()
    return r