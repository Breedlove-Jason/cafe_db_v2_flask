import json
import pytest
from app import create_app, db, Cafe, parse_time, parse_legacy_csv, ROOT

@pytest.fixture
def app():
    return create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite://', 'SAMPLE_CATALOG': True})

@pytest.fixture
def client(app):
    return app.test_client()

def test_home_and_health(client):
    response=client.get('/')
    assert response.status_code == 200
    assert b'BrewDesk' in response.data
    assert "frame-ancestors 'none'" in response.headers['Content-Security-Policy']
    assert client.get('/health').json == {'status': 'ok'}

def test_catalog_imported_from_original(client):
    data=client.get('/api/cafes').json
    assert data['count'] == 5 and data['sample_catalog']
    assert all(c['sample'] for c in data['cafes'])
    lighthouse=next(c for c in data['cafes'] if c['name']=='Lighthaus')
    assert lighthouse['coffee_rating']==4 and lighthouse['open_time']=='11:00'

def test_search_case_and_literal_wildcards(client):
    assert client.get('/api/cafes?q=ESTERS').json['count']==1
    assert client.get('/api/cafes?q=%25').json['count']==0
    assert client.get('/api/cafes?q=%27%20OR%201=1--').json['count']==0

def test_filters_and_sort(client):
    data=client.get('/api/cafes?wifi=3&power=3').json
    assert {c['name'] for c in data['cafes']}=={'Mare Street Market','Starbucks'}
    assert data['cafes'][0]['name']=='Starbucks'
    cafes=client.get('/api/cafes?sort=name').json['cafes']
    assert [c['name'] for c in cafes]==sorted(c['name'] for c in cafes)

@pytest.mark.parametrize('query',['wifi=-1','power=9','coffee=1.5','wifi=oops','sort=bad','q='+'x'*121])
def test_invalid_filters_rejected(client,query):
    assert client.get('/api/cafes?'+query).status_code==400

def test_public_cannot_mutate_catalog(client):
    assert client.get('/delete/1').status_code==404
    assert client.post('/api/cafes',json={'name':'Injected'}).status_code==405
    assert client.post('/add',data={'name':'Injected'}).status_code==404
    assert client.get('/api/cafes').json['count']==5

@pytest.mark.parametrize('value,expected',[('8AM','08:00'),(' 3:30PM','15:30'),('12AM','00:00'),('12PM','12:00'),('23:59','23:59')])
def test_legacy_times(value,expected):
    assert parse_time(value)==expected

def test_invalid_time():
    with pytest.raises(ValueError):parse_time('25:99')

def test_seed_matches_csv():
    assert parse_legacy_csv(ROOT/'data/legacy-cafes.csv') == json.loads((ROOT/'data/catalog.json').read_text())

def test_import_is_repeatable_and_non_destructive(app):
    result=app.test_cli_runner().invoke(args=['import-legacy',str(ROOT/'data/legacy-cafes.csv')])
    assert result.exit_code==0 and 'Imported 0 cafes' in result.output
    with app.app_context():assert db.session.query(Cafe).count()==5

def test_invalid_import_does_not_write(app,tmp_path):
    source=tmp_path/'invalid.csv'
    source.write_text('Cafe Name,Location,Open,Close,Coffee,Wifi,Power\nBad,javascript:alert(1),8AM,5PM,☕,💪,🔌\n')
    result=app.test_cli_runner().invoke(args=['import-legacy',str(source)])
    assert result.exit_code!=0
    with app.app_context():assert db.session.query(Cafe).count()==5
