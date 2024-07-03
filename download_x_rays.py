import requests

from diaries import authorization_l2
from settings import login_l2, password_l2


def get_patients_search(connect) -> list:
    """Получает JSON со списком пациентов и номеров L2, забираем ФИО и возможно дату рождения"""

    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Content-Type': 'application/json',
        'DNT': '1',
        'Origin': 'http://192.168.10.161',
        'Proxy-Connection': 'keep-alive',
        'Referer': 'http://192.168.10.161/ui/search',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }

    json_data = {
        'year_period': 2023,
        'research_id': 438,
        'profile_research_id': -1,
        'case_number': '',
        'directionNumber': '',
        'hospitalId': -1,
        'dateExaminationStart': None,
        'dateExaminationEnd': None,
        'dateCreateStart': None,
        'dateCreateEnd': None,
        'docConfirm': None,
        'dateRegistredStart': None,
        'dateRegistredEnd': None,
        'dateGet': '',
        'dateReceive': '',
        'finalText': 's52.6',
        'searchStationar': False,
    }

    response = connect.post('http://192.168.10.161/api/search-param', headers=headers, json=json_data, verify=False)
    data = response.json()
    return data.get('rows')


def get_patient_info(connect, fio_patient: str) -> int:
    """По ФИО получаем данные пациента (нужен параметр pk)"""

    query = ' '.join(fio_patient.split(' ')[:3])

    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Content-Type': 'application/json',
        'DNT': '1',
        'Origin': 'http://192.168.10.161',
        'Proxy-Connection': 'keep-alive',
        'Referer': 'http://192.168.10.161/ui/directions',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }

    json_data = {
        'type': 5,
        'query': query,
        'list_all_cards': False,
        'inc_rmis': False,
        'inc_tfoms': False,
    }

    response = connect.post(
        'http://192.168.10.161/api/patients/search-card',
        headers=headers,
        json=json_data,
        verify=False,
    )
    data = response.json()
    return data.get('results')[0].get('pk')


def get_patients_researches(connect, pk: int):
    """В параметр patient подставляем pk и получаем все исследования за указанный период.
    Отсюда можно забрать сслыку на снимок из directions -> pacs"""

    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Content-Type': 'application/json',
        'DNT': '1',
        'Origin': 'http://192.168.10.161',
        'Proxy-Connection': 'keep-alive',
        'Referer': 'http://192.168.10.161/ui/directions',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }

    json_data = {
        'iss_pk': None,
        'services': [],
        'forHospSlave': False,
        'type': 3,
        'patient': pk,
        'date_from': '01.01.2023',
        'date_to': '31.12.2023',
    }

    response = connect.post(
        'http://192.168.10.161/api/directions/history',
        headers=headers,
        json=json_data,
        verify=False,
    )
    data = response.json()
    return data.get('directions')


def get_image_archive(connect, link: str):
    study = link.split('=')[1]
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Authorization': 'Basic dTI6Mg==',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Referer': f'http://dicom.imdkb.l2.ru:8042/osimis-viewer/app/index.html?study={study}',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }

    params = {
        'study': study,
    }

    response = connect.get(
        f'http://dicom.imdkb.l2.ru:8042/studies/{study}/archive',
        params=params,
        headers=headers,
        verify=False,
    )
    # response = connect.get(
    #     f'http://dicom2.imdkb.l2.ru:8042/studies/{study}/archive',
    #     headers=headers,
    #     verify=False,
    # )
    return response


session = requests.Session()

authorization = authorization_l2(session, login=login_l2, password=password_l2)

for item in get_patients_search(session):
    try:
        pk = get_patient_info(session, f'{item.get("patient_fio")} {item.get("patient_birthday")}')
        for research in get_patients_researches(session, pk):
            if ('кост' in research.get('researches') and research.get('cancel') is False) or ('локт' in research.get('researches') and research.get('cancel') is False):
                raw_data = get_image_archive(session, research.get('pacs'))
                if raw_data.status_code == 200:
                    with open(f'/Volumes/Extreme SSD/images_for_NN/2023/fracture/{item.get("patient_fio")}_{research.get("pk")}.zip', 'wb') as out:
                        try:
                            out.write(raw_data.content)
                            print(f'File {item.get("patient_fio")}_{research.get("pk")}.zip write!!!')
                        except Exception as e:
                            print(e)
    except Exception as e:
        print(e)
