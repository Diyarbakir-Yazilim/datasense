from unittest.mock import patch, MagicMock

def test_analyze_invalid_file(client):
    # Test uploading a .txt file, which should be rejected
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("test.txt", b"dummy content", "text/plain")}
    )
    assert response.status_code == 400
    assert "Sadece CSV veya Excel dosyaları desteklenmektedir" in response.json()["detail"]

@patch("app.api.v1.endpoints.analyze_dataset_task.apply_async")
def test_analyze_valid_csv(mock_apply_async, client):
    # Mock the returned celery task object
    mock_task = MagicMock()
    mock_task.id = "fake-task-id-123"
    mock_apply_async.return_value = mock_task

    # Test uploading a valid .csv file
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("test.csv", b"col1,col2\n1,2", "text/csv")}
    )
    
    assert response.status_code == 202
    json_resp = response.json()
    assert "job_id" in json_resp
    assert json_resp["status"] == "queued"
    
    # Verify the Celery task was actually called
    mock_apply_async.assert_called_once()

@patch("app.api.v1.endpoints.AsyncResult")
def test_get_task_status_pending(mock_async_result, client):
    # Mock the celery AsyncResult object to simulate a PENDING task
    mock_result = MagicMock()
    mock_result.state = "PENDING"
    mock_async_result.return_value = mock_result

    response = client.get("/api/v1/status/fake-task-id")
    
    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["state"] == "PENDING"
    assert "sırada bekliyor" in json_resp["status"]

# DOSYANIN EN ALTINA EKLEYEBİLİRSİNİZ:

def test_read_root(client):
    """main.py dosyasındaki root (/) endpoint'ini test eder."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to DataSense API"}

@patch("app.api.v1.endpoints.AsyncResult")
def test_get_task_status_success(mock_async_result, client):
    """Celery görevi BAŞARIYLA bittiğinde (SUCCESS) status endpoint'ini test eder."""
    mock_result = MagicMock()
    mock_result.state = "SUCCESS"
    # Celery başarılı bittiğinde genelde result içinde temizlenmiş veri özeti döner
    mock_result.result = {"cleaned_rows": 150, "dropped_columns": 2} 
    mock_async_result.return_value = mock_result

    response = client.get("/api/v1/status/fake-task-id-123")
    
    assert response.status_code == 200
    json_resp = response.json()
    assert json_resp["state"] == "SUCCESS"
    assert "result" in json_resp

@patch("app.api.v1.endpoints.AsyncResult")
def test_get_task_status_failure(mock_async_result, client):
    """Celery görevi HATA aldığında (FAILURE) status endpoint'ini test eder."""
    mock_result = MagicMock()
    mock_result.state = "FAILURE"
    mock_result.result = "ValueError: Polars parsing error" # Örnek bir hata mesajı
    mock_async_result.return_value = mock_result

    response = client.get("/api/v1/status/fake-task-id-123")
    
    assert response.status_code == 200  # Veya projeniz hata durumunda 500 dönüyorsa 500 yapın
    json_resp = response.json()
    assert json_resp["state"] == "FAILURE"