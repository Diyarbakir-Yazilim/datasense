from locust import HttpUser, task, between, events
import time

class DataSenseLoadTest(HttpUser):
    # Her kullanıcı (user) istekler arası 2-5 saniye bekler
    wait_time = between(2, 5)
    
    def on_start(self):
        """Test başlamadan önce her kullanıcı için sahte bir CSV oluşturulur."""
        header = "A,B,C,Target\n"
        lines = [f"{i},{100+i},Category{i%5},{i*1.5}\n" for i in range(100)]
        self.csv_content = (header + "".join(lines)).encode('utf-8')
        
    @task
    def upload_and_wait(self):
        # 1. Dosyayı Yükleme (Upload)
        files = {
            'file': ('load_test_data.csv', self.csv_content, 'text/csv')
        }
        
        with self.client.post("/api/v1/analyze", files=files, catch_response=True) as response:
            if response.status_code == 202:
                response.success()
                data = response.json()
                job_id = data.get("job_id")
            else:
                response.failure(f"Yükleme başarısız: {response.status_code} - {response.text}")
                return
                
        # 2. İşlem tamamlanana kadar durumu sorma (Polling)
        max_retries = 60 # Maksimum 2 dakika bekle (2 sn aralıklarla)
        retries = 0
        
        while retries < max_retries:
            with self.client.get(f"/api/v1/status/{job_id}", catch_response=True, name="/api/v1/status/[job_id]") as status_resp:
                if status_resp.status_code == 200:
                    status_data = status_resp.json()
                    state = status_data.get("state")
                    
                    if state == "SUCCESS":
                        status_resp.success()
                        break
                    elif state in ["FAILURE", "FAILED_TASK"]:
                        status_resp.failure(f"Görev başarısız: {status_data}")
                        break
                    else:
                        # İşlem devam ediyor
                        status_resp.success()
                else:
                    status_resp.failure(f"Status çekilemedi: {status_resp.status_code}")
                    
            time.sleep(2)
            retries += 1
            
        if retries == max_retries:
            events.request.fire(
                request_type="GET",
                name="/api/v1/status/[job_id] (timeout)",
                response_time=0,
                response_length=0,
                exception=Exception("İşlem zaman aşımına uğradı")
            )
