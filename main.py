import requests
import time

from diaries import authorization_l2, add_diaries, get_patients_from_table, get_pk, get_last_diaries, data_by_fields, \
    save_results
from settings import login_l2, password_l2


session = requests.Session()

authorization = authorization_l2(session, login=login_l2, password=password_l2)

patients = get_patients_from_table('C3:C43')
patients_out_of_stock = get_patients_from_table('J3:J43')
patients.extend(patients_out_of_stock)
for history_number in patients:
    try:
        data = add_diaries(session, int(history_number))
        pk = data.get('pk')
        data_1 = get_pk(session, pk)
        pk_1 = data_1.get('researches')[0].get('pk')
        data_2 = get_last_diaries(session, pk_1)
        pk_2 = data_2.get('data')[0].get('pk')
        local_status = data_by_fields(session, pk_2).get('data').get('1922')
        result = save_results(connect=session, pk=pk, pk_2=pk_1, local_status=local_status, history_number=history_number)
        print(f'Дневник для истории №{history_number} создан')
        time.sleep(2)
    except Exception as e:
        print(f'Error: {e}')
        continue

session.close()
