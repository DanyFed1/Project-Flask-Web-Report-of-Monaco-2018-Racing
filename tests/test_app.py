from app import app
from bs4 import BeautifulSoup
import pytest

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['DEBUG'] = False
    with app.test_client() as client:
        yield client

def test_index_redirect(client):
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200
    assert '/report' in response.request.path

def test_report_page(client):
    response = client.get('/report/')
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, 'html.parser')
    table = soup.find("table", class_="table-striped")
    assert table is not None

def test_drivers_page(client):
    response = client.get('/report/drivers/')
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, 'html.parser')
    drivers_list = soup.find("ul", class_="list-group")
    assert drivers_list is not None

def test_driver_info_page(client):
    driver_id = 'SVF'  # Example driver ID
    response = client.get(f'/report/drivers/{driver_id}')
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, 'html.parser')
    driver_name = soup.find(string='Sebastian Vettel')
    assert driver_name is not None

def test_order_parameter(client):
    response = client.get('/report/drivers/?order=desc')
    assert response.status_code == 200

#usage: pytest tests/test_app.py
#coverage run -m pytest tests/test_app.py
#coverage report -m



